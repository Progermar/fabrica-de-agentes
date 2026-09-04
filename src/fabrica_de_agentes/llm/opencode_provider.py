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

    Valida que o agente configurado existe no servidor via GET /agent
    antes do primeiro chat.

    Args:
        base_url: URL base do servidor OpenCode.
        username: Usuario para autenticacao HTTP basic.
        password: Senha para autenticacao HTTP basic.
        timeout: Timeout em segundos para chamadas HTTP.
        agent: ID do agente a ser usado (default: account-intelligence).
        validate_agent: Se True, valida que o agente existe no servidor.
    """

    def __init__(
        self,
        base_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        timeout: int = 300,
        agent: str = DEFAULT_AGENT,
        validate_agent: bool = True,
        model: str | None = None,
    ):
        self._base_url = base_url or os.environ.get(
            "OPENCODE_SERVER_URL", "http://127.0.0.1:4096"
        )
        self._username = username or os.environ.get("OPENCODE_SERVER_USERNAME", "opencode")
        self._password = password or os.environ.get("OPENCODE_SERVER_PASSWORD", "")
        self._timeout = timeout
        self._session_id: str | None = None
        self._agent = agent
        self._agent_validated = False
        self._model = model or os.environ.get("OPENCODE_MODEL", "")

        if validate_agent:
            self._validate_agent_exists()

    def _auth_header(self) -> str | None:
        """Gera header de autenticacao HTTP basic. Retorna None se sem senha."""
        if not self._password:
            return None
        creds = base64.b64encode(
            f"{self._username}:{self._password}".encode()
        ).decode()
        return f"Basic {creds}"

    def _request(self, method: str, path: str, data: dict | None = None) -> dict:
        """Realiza uma requisicao HTTP autenticada ao servidor OpenCode."""
        url = f"{self._base_url}{path}"
        body = json.dumps(data).encode() if data else None

        req = urllib.request.Request(url, data=body, method=method)
        auth = self._auth_header()
        if auth:
            req.add_header("Authorization", auth)
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

    def _validate_agent_exists(self) -> None:
        """Valida que o agente configurado existe no servidor GET /agent."""
        if self._agent_validated:
            return

        try:
            result = self._request("GET", "/agent")
        except RuntimeError:
            raise RuntimeError(
                f"Agente '{self._agent}' nao encontrado no OpenCode. "
                f"Inicie o servidor a partir do projeto onde "
                f".opencode/agents/{self._agent}.md esta disponivel."
            )

        agents_list = result if isinstance(result, list) else result.get("agents", [])

        agent_ids = []
        for a in agents_list:
            if isinstance(a, dict):
                agent_ids.append(a.get("id", a.get("name", "")))
            elif isinstance(a, str):
                agent_ids.append(a)

        if self._agent not in agent_ids:
            raise RuntimeError(
                f"Agente '{self._agent}' nao encontrado no OpenCode. "
                f"Agentes disponiveis: {agent_ids}. "
                f"Inicie o servidor a partir do projeto onde "
                f".opencode/agents/{self._agent}.md esta disponivel."
            )

        self._agent_validated = True

    def health_check(self) -> bool:
        """Verifica se o servidor OpenCode esta respondendo."""
        try:
            result = self._request("GET", "/global/health")
            return result.get("healthy", False)
        except RuntimeError:
            return False

    def _model_ref(self) -> dict | None:
        """Retorna o ModelRef para a sessao V1, ou None se sem modelo."""
        if not self._model:
            return None
        if "/" in self._model:
            provider_id, model_id = self._model.split("/", 1)
        else:
            provider_id, model_id = "", self._model
        return {"id": model_id, "providerID": provider_id}

    def _ensure_session(self) -> str:
        """Cria uma sessao se nao existir, incluindo agent e model."""
        if self._session_id is None:
            session_body: dict = {}
            if self._agent:
                session_body["agent"] = self._agent
            model_ref = self._model_ref()
            if model_ref:
                session_body["model"] = model_ref
            result = self._request("POST", "/session", session_body)
            self._session_id = result["id"]
        return self._session_id

    def chat(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.0,
    ) -> LLMResponse:
        """Envia um prompt ao OpenCode e retorna a resposta estruturada.

        Valida o agente antes do primeiro chat.
        Usa o campo 'system' separadamente (nao concatena com prompt).
        Envia o agente restrito via campo 'agent'.
        """
        if not self._agent_validated:
            self._validate_agent_exists()

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

        error = info.get("error")
        if error:
            error_data = error.get("data", {}) if isinstance(error, dict) else {}
            error_name = error.get("name", "") if isinstance(error, dict) else str(error)
            error_msg = error_data.get("message", "") if isinstance(error_data, dict) else ""
            error_status = error_data.get("statusCode", "") if isinstance(error_data, dict) else ""
            provider_id = info.get("providerID", "")
            model_id = info.get("modelID", "")
            raise RuntimeError(
                f"OpenCode LLM erro: {error_name} - {error_msg} "
                f"(HTTP {error_status}, provider={provider_id}, model={model_id})"
            )

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
        session_body: dict = {}
        if self._agent:
            session_body["agent"] = self._agent
        model_ref = self._model_ref()
        if model_ref:
            session_body["model"] = model_ref
        result = self._request("POST", "/session", session_body)
        self._session_id = result["id"]
        return self._session_id
