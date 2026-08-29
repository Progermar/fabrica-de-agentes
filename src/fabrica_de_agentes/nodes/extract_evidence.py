"""No 4: Extract Evidence - Extracao de evidencias das fontes."""

from fabrica_de_agentes.state import AccountIntelligenceState, Evidence


def extract_evidence(state: AccountIntelligenceState) -> dict:
    """Extrai evidencias estruturadas das fontes coletadas.

    Na V1 real, este no usaria LLM para extrair e classificar evidencias.
    Nesta versao esqueleto, gera evidencias mockadas.
    """
    company = state.target_company

    mock_evidence = [
        Evidence(
            claim=f"{company} atua no segmento de servicos contabeis",
            source_url=f"https://example.com/{company.lower().replace(' ', '-')}/1",
            confidence="media",
            category="perfil",
        ),
        Evidence(
            claim=f"{company} utiliza sistemas de gestao para sua operacao",
            source_url=f"https://example.com/{company.lower().replace(' ', '-')}/2",
            confidence="baixa",
            category="stack",
        ),
        Evidence(
            claim=f"{company} possui equipe de tecnologia propria",
            source_url=f"https://example.com/{company.lower().replace(' ', '-')}/3",
            confidence="baixa",
            category="stack",
        ),
    ]

    return {"evidence": mock_evidence}
