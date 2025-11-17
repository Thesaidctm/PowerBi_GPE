from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..schemas.receita_despesa import (
    DespesaMensal,
    DespesaPorCategoria,
    DespesaResumoResponse,
    ReceitaMensal,
    ReceitaPorCategoria,
    ReceitaResumoResponse,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard-receita-despesa"])


async def fetch_scalar(session: AsyncSession, query: str, params: Dict[str, Any]) -> float:
    result = await session.execute(text(query), params)
    value = result.scalar()
    return float(value or 0)


async def fetch_category_list(
    session: AsyncSession, query: str, params: Dict[str, Any]
) -> List[ReceitaPorCategoria]:
    result = await session.execute(text(query), params)
    return [
        ReceitaPorCategoria(categoria=row[0], valor=float(row[1] or 0))
        for row in result.all()
    ]


@router.get("/receita/resumo", response_model=ReceitaResumoResponse)
async def get_receita_resumo(
    ano: int = Query(..., description="Ano de referência, ex: 2024"),
    session: AsyncSession = Depends(get_session),
) -> ReceitaResumoResponse:
    receita_prevista = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(valor_previsto), 0)
        FROM receita_loa
        WHERE ano = :ano
        """,
        {"ano": ano},
    )

    receita_realizada = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(valor_arrecadado), 0)
        FROM view_mov_rec
        WHERE ano = :ano
        """,
        {"ano": ano},
    )

    serie_result = await session.execute(
        text(
            """
            SELECT mes,
                   COALESCE(SUM(valor_arrecadado), 0) AS receita_realizada_mes,
                   COALESCE(SUM(valor_arrecadado_ano_anterior), 0) AS receita_mes_ano_anterior
            FROM view_mov_rec
            WHERE ano = :ano
            GROUP BY mes
            ORDER BY mes
            """
        ),
        {"ano": ano},
    )
    serie_mensal = [
        ReceitaMensal(
            mes=row.mes,
            receita_realizada_mes=float(row.receita_realizada_mes or 0),
            receita_mes_ano_anterior=float(row.receita_mes_ano_anterior or 0),
        )
        for row in serie_result.all()
    ]

    receita_por_origem = await fetch_category_list(
        session,
        """
        SELECT orc.descricao AS categoria, COALESCE(SUM(r.valor_arrecadado), 0) AS valor
        FROM view_mov_rec r
        JOIN origem_receita orc ON orc.id = r.origem_id
        WHERE r.ano = :ano
        GROUP BY orc.descricao
        ORDER BY valor DESC
        """,
        {"ano": ano},
    )

    receita_por_natureza = await fetch_category_list(
        session,
        """
        SELECT n.descricao AS categoria, COALESCE(SUM(r.valor_arrecadado), 0) AS valor
        FROM view_mov_rec r
        JOIN natureza n ON n.id = r.natureza_id
        WHERE r.ano = :ano
        GROUP BY n.descricao
        ORDER BY valor DESC
        """,
        {"ano": ano},
    )

    receita_por_fonte = await fetch_category_list(
        session,
        """
        SELECT f.descricao AS categoria, COALESCE(SUM(r.valor_arrecadado), 0) AS valor
        FROM view_mov_rec r
        JOIN fonte f ON f.id = r.fonte_id
        WHERE r.ano = :ano
        GROUP BY f.descricao
        ORDER BY valor DESC
        """,
        {"ano": ano},
    )

    return ReceitaResumoResponse(
        ano=ano,
        receita_prevista=receita_prevista,
        receita_realizada=receita_realizada,
        serie_mensal=serie_mensal,
        receita_por_origem=receita_por_origem,
        receita_por_natureza=receita_por_natureza,
        receita_por_fonte=receita_por_fonte,
    )


def _build_despesa_categoria_list(rows) -> List[DespesaPorCategoria]:
    return [
        DespesaPorCategoria(categoria=row[0], valor=float(row[1] or 0))
        for row in rows
    ]


@router.get("/despesa/resumo", response_model=DespesaResumoResponse)
async def get_despesa_resumo(
    ano: int = Query(..., description="Ano de referência, ex: 2024"),
    session: AsyncSession = Depends(get_session),
) -> DespesaResumoResponse:
    dotacao_inicial = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(dotacao_inicial), 0)
        FROM view_loa_desp
        WHERE ano = :ano
        """,
        {"ano": ano},
    )

    dotacao_atualizada = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(dotacao_atualizada), 0)
        FROM view_desp_executada
        WHERE ano = :ano
        """,
        {"ano": ano},
    )

    empenhado = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(empenhado), 0)
        FROM view_desp_executada
        WHERE ano = :ano
        """,
        {"ano": ano},
    )

    liquidado = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(liquidado), 0)
        FROM view_desp_executada
        WHERE ano = :ano
        """,
        {"ano": ano},
    )

    pago = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(valor_pago), 0)
        FROM view_mov_pagamento
        WHERE ano = :ano
        """,
        {"ano": ano},
    )

    serie_result = await session.execute(
        text(
            """
            SELECT mes,
                   COALESCE(SUM(empenhado), 0) AS empenhado,
                   COALESCE(SUM(liquidado), 0) AS liquidado,
                   COALESCE(SUM(valor_pago), 0) AS pago
            FROM view_desp_executada
            WHERE ano = :ano
            GROUP BY mes
            ORDER BY mes
            """
        ),
        {"ano": ano},
    )
    serie_mensal = [
        DespesaMensal(
            mes=row.mes,
            empenhado=float(row.empenhado or 0),
            liquidado=float(row.liquidado or 0),
            pago=float(row.pago or 0),
        )
        for row in serie_result.all()
    ]

    orgao_result = await session.execute(
        text(
            """
            SELECT o.descricao AS categoria, COALESCE(SUM(vd.empenhado), 0) AS valor
            FROM view_desp_executada vd
            JOIN orgao o ON o.id = vd.orgao_id
            WHERE vd.ano = :ano
            GROUP BY o.descricao
            ORDER BY valor DESC
            """
        ),
        {"ano": ano},
    )

    funcao_result = await session.execute(
        text(
            """
            SELECT f.descricao AS categoria, COALESCE(SUM(vd.empenhado), 0) AS valor
            FROM view_desp_executada vd
            JOIN funcao f ON f.id = vd.funcao_id
            WHERE vd.ano = :ano
            GROUP BY f.descricao
            ORDER BY valor DESC
            """
        ),
        {"ano": ano},
    )

    programa_result = await session.execute(
        text(
            """
            SELECT p.descricao AS categoria, COALESCE(SUM(vd.empenhado), 0) AS valor
            FROM view_desp_executada vd
            JOIN programa p ON p.id = vd.programa_id
            WHERE vd.ano = :ano
            GROUP BY p.descricao
            ORDER BY valor DESC
            """
        ),
        {"ano": ano},
    )

    return DespesaResumoResponse(
        ano=ano,
        dotacao_inicial=dotacao_inicial,
        dotacao_atualizada=dotacao_atualizada,
        empenhado=empenhado,
        liquidado=liquidado,
        pago=pago,
        serie_mensal=serie_mensal,
        despesa_por_orgao=_build_despesa_categoria_list(orgao_result.all()),
        despesa_por_funcao=_build_despesa_categoria_list(funcao_result.all()),
        despesa_por_programa=_build_despesa_categoria_list(programa_result.all()),
    )
