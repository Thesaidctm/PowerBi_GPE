from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..schemas.licitacoes_contratos import (
    ContratoProximoVencimento,
    ContratosProximosVencimentosResponse,
    LicitacaoModalidadeResumo,
    LicitacaoStatusResumo,
    LicitacoesResumoResponse,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard-licitacoes-contratos"])


async def fetch_scalar(session: AsyncSession, query: str, params: Dict[str, Any]) -> float:
    result = await session.execute(text(query), params)
    value = result.scalar()
    return float(value or 0)


async def fetch_status_list(
    session: AsyncSession, query: str, params: Dict[str, Any]
) -> List[LicitacaoStatusResumo]:
    result = await session.execute(text(query), params)
    return [LicitacaoStatusResumo(status=row[0], quantidade=int(row[1] or 0)) for row in result]


async def fetch_modalidade_list(
    session: AsyncSession, query: str, params: Dict[str, Any]
) -> List[LicitacaoModalidadeResumo]:
    result = await session.execute(text(query), params)
    return [
        LicitacaoModalidadeResumo(modalidade=row[0], quantidade=int(row[1] or 0))
        for row in result
    ]


@router.get("/licitacoes/resumo", response_model=LicitacoesResumoResponse)
async def get_licitacoes_resumo(
    ano: int = Query(..., description="Ano de referência"),
    session: AsyncSession = Depends(get_session),
) -> LicitacoesResumoResponse:
    status_resumo = await fetch_status_list(
        session,
        """
        SELECT ls.descricao AS status, COUNT(*) AS quantidade
        FROM licit_processo lp
        JOIN licit_status ls ON ls.id = lp.status_id
        WHERE YEAR(lp.data_abertura) = :ano
        GROUP BY ls.descricao
        ORDER BY quantidade DESC
        """,
        {"ano": ano},
    )

    modalidade_resumo = await fetch_modalidade_list(
        session,
        """
        SELECT lm.descricao AS modalidade, COUNT(*) AS quantidade
        FROM licit_processo lp
        JOIN licit_modalidade lm ON lm.id = lp.modalidade_id
        WHERE YEAR(lp.data_abertura) = :ano
        GROUP BY lm.descricao
        ORDER BY quantidade DESC
        """,
        {"ano": ano},
    )

    valor_total_licitado = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(lp.valor_estimado), 0)
        FROM licit_processo lp
        WHERE YEAR(lp.data_abertura) = :ano
        """,
        {"ano": ano},
    )

    valor_total_contratado = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(valor_contratado), 0)
        FROM licit_contrato
        WHERE YEAR(data_inicio) = :ano
        """,
        {"ano": ano},
    )

    tempo_medio_result = await session.execute(
        text(
            """
            SELECT AVG(DATEDIFF(lp.data_homologacao, lp.data_abertura)) AS tempo_medio
            FROM licit_processo lp
            WHERE YEAR(lp.data_abertura) = :ano AND lp.data_homologacao IS NOT NULL
            """
        ),
        {"ano": ano},
    )
    tempo_medio = float(tempo_medio_result.scalar() or 0)

    return LicitacoesResumoResponse(
        ano=ano,
        quantidade_processos_por_status=status_resumo,
        quantidade_por_modalidade=modalidade_resumo,
        valor_total_licitado_ano=valor_total_licitado,
        valor_total_contratado_ano=valor_total_contratado,
        tempo_medio_entre_abertura_e_homologacao=tempo_medio,
    )


@router.get("/contratos/proximos-vencimentos", response_model=ContratosProximosVencimentosResponse)
async def get_contratos_proximos_vencimentos(
    dias: int = Query(90, description="Quantidade de dias para o corte de vencimento"),
    session: AsyncSession = Depends(get_session),
) -> ContratosProximosVencimentosResponse:
    hoje = datetime.utcnow().date()
    limite = hoje + timedelta(days=dias)

    result = await session.execute(
        text(
            """
            SELECT lc.id,
                   lc.numero,
                   f.nome AS fornecedor,
                   lc.valor_global AS valor,
                   lc.data_fim,
                   COALESCE(ls.descricao, 'vigente') AS status
            FROM licit_contrato lc
            LEFT JOIN fornecedor f ON f.id = lc.fornecedor_id
            LEFT JOIN licit_status ls ON ls.id = lc.status_id
            WHERE lc.data_fim BETWEEN :hoje AND :limite
            ORDER BY lc.data_fim
            """
        ),
        {"hoje": hoje, "limite": limite},
    )

    contratos = [
        ContratoProximoVencimento(
            id=row.id,
            numero=row.numero,
            fornecedor=row.fornecedor,
            valor=float(row.valor or 0),
            data_fim=row.data_fim,
            status=row.status,
        )
        for row in result.all()
    ]

    return ContratosProximosVencimentosResponse(dias=dias, contratos=contratos)
