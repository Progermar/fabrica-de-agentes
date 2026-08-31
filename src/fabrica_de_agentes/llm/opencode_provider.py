"""Provedor de LLM usando o servidor HTTP do OpenCode."""

from __future__ import annotations

import base64
import json
import os
import urllib.request
from urllib.error import HTTPError, URLError

from fabrica_de_agentes.llm.base import LLMProvider, LLMResponse

DEFAULT_AGENT = "account-intelligence"


class OpenCodeProvider(LLMProvider):
    """Provedor de LLM conectado ao servidor OpenCode via HTTP.

    Requer que 'opencode serve' esteja rodando e a variavel de ambiente
    OPENCODE_SERVER_PASSWORD esteja configurada.

    Usa o campo system separado do campo parts (mensagem do usuario).
    Envia agent restrito para Analysis de texto apenas.

    Args:
        base_url: URL base do servidor OpenCode.
        username: Usuario para autenticacao HTTP basic.
        password: Senha para autenticacao HTTP basic.
        timeout: Timeout em segundos para chamadas HTTP.
        agent: ID do agente a ser usado (default: account-intelligence).
    """

    def __init__(
        self,
        base_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        timeout: int = 120,
        agent: str = DEFAULT_AGENT,
    ):
        self._base_url = base_url or "http://127.0.0.1:4096"
        self._username = username or os.environ.get("OPENCODE_SERVER_USERNAME", "opencode")
        self._password = password or os.environ.get("OPENCODE_SERVER_PASSWORD", "")
        self._timeout = timeout
        self._session_id: str | None = None
        self._agent = agent

        if not self._password:
            raise ValueError(
                "OPENCODE_SERVER_PASSWORD nao configurada. "
                "Defina a variavel de ambiente OPENCODE_SERVER_PASSWORD "
                "ou passe password no construtor."
            )

    def _auth_header(self) -> str:
        """Gera header de autenticacao HTTP basic."""
        creds = base64.b64encode(
            f"{self._username}:{self._password}".encode()
        ).decode()
        return f"Basic {creds}"

    def _request(self, method: str, path: str, data: dict | None = None) -> dict:
        """Realiza uma requisicao HTTP autenticada ao servidor OpenCode."""
        url = f"{self._base_url}{path}"
        body = json.dumps(data).encode() if data else None

        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Authorization", self._auth_header())
        req.add_header("Content-Type", "application/json")

        try:
            resp = urllib.request.urlopen(req, timeout=self._timeout)
            content = resp.read().decode()
            if not content.strip():
                return {}
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"raw": content}
        except HTTPError as e:
            body_text = e.read().decode() if e.fp else ""
            raise RuntimeError(
                f"OpenCode HTTP {e.code} em {method} {path}: {body_text}"
            ) from e
        except URLError as e:
            raise RuntimeError(
                f"OpenCode indisponivel em {self._base_url}: {e.reason}"
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"OpenCode indisponivel em {self._base_url}: {e}"
            ) from e

    def health_check(self) -> bool:
        """Verifica se o servidor OpenCode esta respondendo."""
        try:
            result = self._request("GET", "/global/health")
            return result.get("healthy", False)
        except RuntimeError:
            return False

    def _ensure_session(self) -> str:
        """Cria uma sessao se nao existir."""
        if self._session_id is None:
            result = self._request("POST", "/session", {})
            self._session_id = result["id"]
        return self._session_id

    def chat(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Envia um prompt ao OpenCode e retorna a resposta estruturada.

        Usa o campo 'system' separadamente (nao concatena com prompt).
        Envia o agente restrito via campo 'agent'.
        """
        session_id = self._ensure_session()

        message_data: dict = {
            "parts": [{"type": "text", "text": prompt}],
        }

        if system:
            message_data["system"] = system

        if self._agent:
            message_data["agent"] = self._agent

        result = self._request(
            "POST",
            f"/session/{session_id}/message",
            message_data,
        )

        info = result.get("info", {})
        parts = result.get("parts", [])

        response_text = ""
        for part in parts:
            if part.get("type") == "text":
                response_text += part.get("text", "")

        if not response_text and "raw" in result:
            response_text = result["raw"]

        tokens_in = info.get("tokens", {}).get("input", 0)
        tokens_out = info.get("tokens", {}).get("output", 0)
        cost = info.get("cost", 0.0)
        model = info.get("modelID", "")

        return LLMResponse(
            text=response_text,
            model=model,
            tokens_input=tokens_in,
            tokens_output=tokens_out,
            cost_dollars=cost,
        )

    def new_session(self) -> str:
        """Cria uma nova sessao e retorna o ID."""
        result = self._request("POST", "/session", {})
        self._session_id = result["id"]
        return self._session_id
