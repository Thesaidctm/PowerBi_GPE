from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..schemas.rh_pessoal import HeadcountResumo, RHPessoalResponse, SerieMensal

router = APIRouter(prefix="/dashboard", tags=["dashboard-rh-pessoal"])


async def fetch_scalar(session: AsyncSession, query: str, params: Dict[str, Any]) -> float:
    result = await session.execute(text(query), params)
    value = result.scalar()
    return float(value or 0)


@router.get("/rh/resumo", response_model=RHPessoalResponse)
async def get_rh_resumo(
    ano: int = Query(default_factory=lambda: datetime.utcnow().year, description="Ano de referência"),
    session: AsyncSession = Depends(get_session),
) -> RHPessoalResponse:
    gasto_pessoal_ano = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(valor_total), 0)
        FROM rh_calculo
        WHERE ano = :ano
        """,
        {"ano": ano},
    )

    gasto_mensal_result = await session.execute(
        text(
            """
            SELECT mes, COALESCE(SUM(valor_total), 0) AS valor
            FROM rh_calculo
            WHERE ano = :ano
            GROUP BY mes
            ORDER BY mes
            """
        ),
        {"ano": ano},
    )
    gasto_pessoal_mensal = [
        SerieMensal(mes=int(row.mes), valor=float(row.valor or 0)) for row in gasto_mensal_result
    ]

    rcl_result = await session.execute(
        text(
            """
            -- Se não existir a view dclrf com receita corrente líquida, ajuste a origem
            SELECT COALESCE(SUM(valor_rcl), 0)
            FROM dclrf
            WHERE ano = :ano
            """
        ),
        {"ano": ano},
    )
    rcl = float(rcl_result.scalar() or 0)
    percentual_rcl = (gasto_pessoal_ano / rcl * 100) if rcl else None

    headcount_tipo_result = await session.execute(
        text(
            """
            SELECT COALESCE(rv.descricao, 'Tipo') AS categoria, COUNT(*) AS quantidade
            FROM rh_funcionario rf
            LEFT JOIN rh_vinculo rv ON rv.id = rf.vinculo_id
            WHERE rf.ano = :ano
            GROUP BY categoria
            """
        ),
        {"ano": ano},
    )
    headcount_por_tipo_vinculo = [
        HeadcountResumo(categoria=row.categoria, quantidade=int(row.quantidade or 0))
        for row in headcount_tipo_result
    ]

    headcount_orgao_result = await session.execute(
        text(
            """
            SELECT COALESCE(o.nome, 'Orgão') AS categoria, COUNT(*) AS quantidade
            FROM funcionarios f
            LEFT JOIN orgao o ON o.id = f.orgao_id
            WHERE f.ano = :ano
            GROUP BY categoria
            """
        ),
        {"ano": ano},
    )
    headcount_por_orgao = [
        HeadcountResumo(categoria=row.categoria, quantidade=int(row.quantidade or 0))
        for row in headcount_orgao_result
    ]

    ferias_result = await session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM rh_calculo_item
            WHERE ano = :ano AND LOWER(tipo_evento) LIKE '%ferias%'
            """
        ),
        {"ano": ano},
    )
    qtde_ferias = int(ferias_result.scalar() or 0)

    licencas_result = await session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM rh_calculo_item
            WHERE ano = :ano AND LOWER(tipo_evento) LIKE '%licenca%'
            """
        ),
        {"ano": ano},
    )
    qtde_licencas = int(licencas_result.scalar() or 0)

    rescisao_result = await session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM rh_calculo_item
            WHERE ano = :ano AND LOWER(tipo_evento) LIKE '%rescis%'
            """
        ),
        {"ano": ano},
    )
    qtde_rescisoes = int(rescisao_result.scalar() or 0)

    observacao = (
        "Confirme colunas: valor_total em rh_calculo, tipo_evento em rh_calculo_item, ano em funcionarios/rh_funcionario."
    )

    return RHPessoalResponse(
        ano=ano,
        gasto_pessoal_ano=gasto_pessoal_ano,
        gasto_pessoal_mensal=gasto_pessoal_mensal,
        percentual_despesa_pessoal_sobre_rcl=percentual_rcl,
        headcount_por_tipo_vinculo=headcount_por_tipo_vinculo,
        headcount_por_orgao=headcount_por_orgao,
        qtde_ferias_no_periodo=qtde_ferias,
        qtde_licencas=qtde_licencas,
        qtde_rescisoes=qtde_rescisoes,
        observacao=observacao,
    )
