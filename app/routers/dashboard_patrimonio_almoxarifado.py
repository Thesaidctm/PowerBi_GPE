from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..schemas.patrimonio_almoxarifado import (
    AlmoxarifadoResponse,
    ConsumoResumo,
    EstoqueProduto,
    PatrimonioResponse,
    ResumoValor,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard-patrimonio-almoxarifado"])


async def fetch_scalar(session: AsyncSession, query: str, params: Dict[str, Any]) -> float:
    result = await session.execute(text(query), params)
    value = result.scalar()
    return float(value or 0)


@router.get("/patrimonio/resumo", response_model=PatrimonioResponse)
async def get_patrimonio_resumo(
    session: AsyncSession = Depends(get_session),
) -> PatrimonioResponse:
    valor_total_bens = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(valor_aquisicao), 0)
        FROM patrimonio
        """,
        {},
    )

    valor_depreciacao_acumulada = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(valor_depreciado), 0)
        FROM ptr_depreciacao
        """,
        {},
    )

    bens_orgao_result = await session.execute(
        text(
            """
            SELECT COALESCE(o.nome, 'Orgão') AS categoria, COALESCE(SUM(p.valor_aquisicao), 0) AS valor
            FROM patrimonio p
            LEFT JOIN patrimonio_responsavel pr ON pr.patrimonio_id = p.id
            LEFT JOIN orgao o ON o.id = pr.orgao_id
            GROUP BY categoria
            ORDER BY valor DESC
            """
        ),
    )
    bens_por_orgao = [
        ResumoValor(categoria=row.categoria, valor=float(row.valor or 0)) for row in bens_orgao_result
    ]

    bens_natureza_result = await session.execute(
        text(
            """
            SELECT COALESCE(p.natureza, 'Natureza') AS categoria, COALESCE(SUM(p.valor_aquisicao), 0) AS valor
            FROM patrimonio p
            GROUP BY categoria
            ORDER BY valor DESC
            """
        ),
    )
    bens_por_natureza = [
        ResumoValor(categoria=row.categoria, valor=float(row.valor or 0)) for row in bens_natureza_result
    ]

    observacao = "Ajuste colunas: valor_aquisicao, valor_depreciado, natureza conforme o schema real."

    return PatrimonioResponse(
        valor_total_bens=valor_total_bens,
        valor_depreciacao_acumulada=valor_depreciacao_acumulada,
        bens_por_orgao=bens_por_orgao,
        bens_por_natureza_ou_grupo=bens_por_natureza,
        observacao=observacao,
    )


@router.get("/almoxarifado/resumo", response_model=AlmoxarifadoResponse)
async def get_almoxarifado_resumo(
    mes: int = Query(default_factory=lambda: datetime.utcnow().month, ge=1, le=12),
    ano: int = Query(default_factory=lambda: datetime.utcnow().year),
    session: AsyncSession = Depends(get_session),
) -> AlmoxarifadoResponse:
    consumo_orgao_result = await session.execute(
        text(
            """
            SELECT COALESCE(o.nome, 'Orgão') AS item, COALESCE(SUM(se.valor_total), 0) AS valor
            FROM saida_estoque se
            LEFT JOIN orgao o ON o.id = se.orgao_id
            WHERE MONTH(se.data_saida) = :mes AND YEAR(se.data_saida) = :ano
            GROUP BY item
            ORDER BY valor DESC
            """
        ),
        {"mes": mes, "ano": ano},
    )
    consumo_por_orgao = [
        ConsumoResumo(item=row.item, valor=float(row.valor or 0)) for row in consumo_orgao_result
    ]

    consumo_produto_result = await session.execute(
        text(
            """
            SELECT COALESCE(p.nome, 'Produto') AS item, COALESCE(SUM(si.valor_total), 0) AS valor
            FROM saida_item si
            JOIN saida_estoque se ON se.id = si.saida_id
            LEFT JOIN produto p ON p.id = si.produto_id
            WHERE MONTH(se.data_saida) = :mes AND YEAR(se.data_saida) = :ano
            GROUP BY item
            ORDER BY valor DESC
            """
        ),
        {"mes": mes, "ano": ano},
    )
    consumo_por_produto = [
        ConsumoResumo(item=row.item, valor=float(row.valor or 0)) for row in consumo_produto_result
    ]

    estoque_result = await session.execute(
        text(
            """
            SELECT COALESCE(p.nome, 'Produto') AS produto,
                   COALESCE(SUM(ei.quantidade), 0) - COALESCE(SUM(si.quantidade), 0) AS quantidade
            FROM produto p
            LEFT JOIN entrada_item ei ON ei.produto_id = p.id
            LEFT JOIN saida_item si ON si.produto_id = p.id
            GROUP BY produto
            ORDER BY quantidade DESC
            """
        ),
    )
    estoque_atual = [
        EstoqueProduto(produto=row.produto, quantidade=float(row.quantidade or 0))
        for row in estoque_result
    ]

    observacao = (
        "Confirme colunas de valor_total em saida_estoque/saida_item e quantidade em entrada_item/saida_item."
    )

    return AlmoxarifadoResponse(
        mes=mes,
        ano=ano,
        consumo_por_orgao_no_mes=consumo_por_orgao,
        consumo_por_produto=consumo_por_produto,
        estoque_atual_por_produto=estoque_atual,
        observacao=observacao,
    )
