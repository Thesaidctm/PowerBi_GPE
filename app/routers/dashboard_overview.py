from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..schemas.overview import OverviewCards, OverviewResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard-overview"])


async def fetch_scalar(session: AsyncSession, query: str, params: Dict[str, Any]) -> float:
    result = await session.execute(text(query), params)
    value = result.scalar()
    return float(value or 0)


async def fetch_count(session: AsyncSession, query: str, params: Dict[str, Any]) -> int:
    result = await session.execute(text(query), params)
    value = result.scalar()
    return int(value or 0)


@router.get("/overview", response_model=OverviewResponse)
async def get_dashboard_overview(
    ano: int | None = None, session: AsyncSession = Depends(get_session)
) -> OverviewResponse:
    ano_ref = ano or datetime.utcnow().year

    receita_prevista_ano = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(valor_previsto), 0)
        FROM receita_loa
        WHERE ano = :ano
        """,
        {"ano": ano_ref},
    )

    receita_realizada_ano = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(valor_arrecadado), 0)
        FROM view_mov_rec
        WHERE ano = :ano
        """,
        {"ano": ano_ref},
    )

    despesa_dotacao_atualizada_ano = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(dotacao_atualizada), 0)
        FROM view_desp_executada
        WHERE ano = :ano
        """,
        {"ano": ano_ref},
    )

    despesa_empenhada_ano = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(empenhado), 0)
        FROM view_desp_executada
        WHERE ano = :ano
        """,
        {"ano": ano_ref},
    )

    despesa_liquidada_ano = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(liquidado), 0)
        FROM view_desp_executada
        WHERE ano = :ano
        """,
        {"ano": ano_ref},
    )

    despesa_paga_ano = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(valor_pago), 0)
        FROM view_mov_pagamento
        WHERE ano = :ano
        """,
        {"ano": ano_ref},
    )

    caixa_disponivel = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(saldo_final), 0)
        FROM ts_conta_banc_saldo_ano
        WHERE ano = :ano
        """,
        {"ano": ano_ref},
    )

    estoque_divida_ativa_total = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(valor_atualizado), 0)
        FROM divida_ativa
        WHERE ano_referencia = :ano
        """,
        {"ano": ano_ref},
    )

    recuperacao_divida_ativa_ano = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(valor_pago), 0)
        FROM duam_baixa
        WHERE YEAR(data_baixa) = :ano
        """,
        {"ano": ano_ref},
    )

    qtde_licitacoes_em_andamento = await fetch_count(
        session,
        """
        SELECT COUNT(*)
        FROM licit_processo lp
        JOIN licit_status ls ON ls.id = lp.status_id
        WHERE YEAR(lp.data_abertura) = :ano AND ls.descricao IN ('em andamento', 'publicado', 'disputa')
        """,
        {"ano": ano_ref},
    )

    qtde_licitacoes_homologadas_ano = await fetch_count(
        session,
        """
        SELECT COUNT(*)
        FROM licit_processo lp
        JOIN licit_status ls ON ls.id = lp.status_id
        WHERE YEAR(lp.data_abertura) = :ano AND ls.descricao = 'homologado'
        """,
        {"ano": ano_ref},
    )

    qtde_obras_em_execucao = await fetch_count(
        session,
        """
        SELECT COUNT(*)
        FROM obr_obra
        WHERE situacao IN ('em execucao', 'execução')
        """,
        {},
    )

    qtde_obras_paralisadas = await fetch_count(
        session,
        """
        SELECT COUNT(*)
        FROM obr_obra
        WHERE LOWER(situacao) LIKE '%paralisada%'
        """,
        {},
    )

    resultado_primario_simplificado = receita_realizada_ano - despesa_empenhada_ano

    cards = OverviewCards(
        receita_prevista_ano=receita_prevista_ano,
        receita_realizada_ano=receita_realizada_ano,
        despesa_dotacao_atualizada_ano=despesa_dotacao_atualizada_ano,
        despesa_empenhada_ano=despesa_empenhada_ano,
        despesa_liquidada_ano=despesa_liquidada_ano,
        despesa_paga_ano=despesa_paga_ano,
        resultado_primario_simplificado=resultado_primario_simplificado,
        caixa_disponivel=caixa_disponivel,
        estoque_divida_ativa_total=estoque_divida_ativa_total,
        recuperacao_divida_ativa_ano=recuperacao_divida_ativa_ano,
        qtde_licitacoes_em_andamento=qtde_licitacoes_em_andamento,
        qtde_licitacoes_homologadas_ano=qtde_licitacoes_homologadas_ano,
        qtde_obras_em_execucao=qtde_obras_em_execucao,
        qtde_obras_paralisadas=qtde_obras_paralisadas,
    )

    observacao = (
        "Colunas das views/tabelas podem precisar de ajustes conforme o schema real."
    )

    return OverviewResponse(ano=ano_ref, cards=cards, observacao=observacao)
