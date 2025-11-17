from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..schemas.tributos_divida_ativa import (
    AtividadeResumo,
    BairroArrecadacao,
    ContribuinteResumo,
    DividaAtivaResponse,
    EstoqueDividaAtiva,
    IPTUResponse,
    ISSResponse,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard-tributos-divida-ativa"])


async def fetch_scalar(session: AsyncSession, query: str, params: Dict[str, Any]) -> float:
    result = await session.execute(text(query), params)
    value = result.scalar()
    return float(value or 0)


@router.get("/tributos/iptu", response_model=IPTUResponse)
async def get_iptu_resumo(
    ano: int = Query(default_factory=lambda: datetime.utcnow().year, description="Ano de referência"),
    session: AsyncSession = Depends(get_session),
) -> IPTUResponse:
    iptu_lancado_ano = await fetch_scalar(
        session,
        """
        -- Ajuste o nome da coluna com o valor lançado, por exemplo valor_total
        SELECT COALESCE(SUM(valor_lancado), 0)
        FROM calculo_iptu_ano
        WHERE ano = :ano
        """,
        {"ano": ano},
    )

    iptu_arrecadado_ano = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(valor_pago), 0)
        FROM view_bci_iptu
        WHERE ano = :ano
        """,
        {"ano": ano},
    )

    result = await session.execute(
        text(
            """
            SELECT b.nome AS bairro, COALESCE(SUM(v.valor_pago), 0) AS valor
            FROM view_iptu v
            LEFT JOIN bairro b ON b.id = v.bairro_id
            WHERE v.ano = :ano
            GROUP BY b.nome
            ORDER BY valor DESC
            LIMIT 10
            """
        ),
        {"ano": ano},
    )
    ranking_bairros = [
        BairroArrecadacao(bairro=row.bairro or "Não informado", valor_arrecadado=float(row.valor or 0))
        for row in result
    ]

    taxa_inadimplencia = 0.0
    if iptu_lancado_ano:
        taxa_inadimplencia = max(0.0, (iptu_lancado_ano - iptu_arrecadado_ano) / iptu_lancado_ano)

    observacao = "Revise nomes de colunas (valor_lancado, valor_pago, bairro_id) conforme o schema real."

    return IPTUResponse(
        ano=ano,
        iptu_lancado_ano=iptu_lancado_ano,
        iptu_arrecadado_ano=iptu_arrecadado_ano,
        taxa_inadimplencia=taxa_inadimplencia,
        ranking_bairros_por_arrecadacao=ranking_bairros,
        observacao=observacao,
    )


@router.get("/tributos/iss", response_model=ISSResponse)
async def get_iss_resumo(
    ano: int = Query(default_factory=lambda: datetime.utcnow().year, description="Ano de referência"),
    session: AsyncSession = Depends(get_session),
) -> ISSResponse:
    iss_declarado = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(valor_declarado), 0)
        FROM iss_mensal
        WHERE ano = :ano
        """,
        {"ano": ano},
    )

    iss_pago = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(valor_pago), 0)
        FROM iss_mensal
        WHERE ano = :ano
        """,
        {"ano": ano},
    )

    atividade_result = await session.execute(
        text(
            """
            SELECT COALESCE(r.descricao, 'Não informado') AS atividade, COALESCE(SUM(ni.valor_total), 0) AS valor
            FROM nota_iss ni
            LEFT JOIN economico e ON e.id = ni.economico_id
            LEFT JOIN economico_atividades ea ON ea.economico_id = e.id
            LEFT JOIN ramopertinente r ON r.id = ea.ramo_id
            WHERE YEAR(ni.data_emissao) = :ano
            GROUP BY atividade
            ORDER BY valor DESC
            LIMIT 10
            """
        ),
        {"ano": ano},
    )
    notas_por_atividade = [
        AtividadeResumo(atividade=row.atividade, valor=float(row.valor or 0)) for row in atividade_result
    ]

    contribuintes_result = await session.execute(
        text(
            """
            SELECT COALESCE(e.nome_fantasia, 'Contribuinte') AS contribuinte, COALESCE(SUM(ni.valor_total), 0) AS valor
            FROM nota_iss ni
            LEFT JOIN economico e ON e.id = ni.economico_id
            WHERE YEAR(ni.data_emissao) = :ano
            GROUP BY contribuinte
            ORDER BY valor DESC
            LIMIT 10
            """
        ),
        {"ano": ano},
    )
    top_contribuintes = [
        ContribuinteResumo(contribuinte=row.contribuinte, valor=float(row.valor or 0))
        for row in contribuintes_result
    ]

    observacao = "Ajuste nomes de colunas de notas ISS conforme o schema (valor_total, data_emissao)."

    return ISSResponse(
        ano=ano,
        iss_declarado_ano=iss_declarado,
        iss_pago_ano=iss_pago,
        notas_por_atividade=notas_por_atividade,
        top_contribuintes_iss=top_contribuintes,
        observacao=observacao,
    )


@router.get("/divida-ativa/resumo", response_model=DividaAtivaResponse)
async def get_divida_ativa_resumo(
    ano: int = Query(default_factory=lambda: datetime.utcnow().year, description="Ano de referência"),
    session: AsyncSession = Depends(get_session),
) -> DividaAtivaResponse:
    estoque_total = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(valor_atualizado), 0)
        FROM divida_ativa
        WHERE ano_referencia = :ano
        """,
        {"ano": ano},
    )

    estoque_result = await session.execute(
        text(
            """
            SELECT COALESCE(da.tributo, 'Tributo') AS tributo, COALESCE(SUM(da.valor_atualizado), 0) AS valor
            FROM divida_ativa da
            LEFT JOIN divida_ativa_itens dai ON dai.divida_id = da.id
            WHERE da.ano_referencia = :ano
            GROUP BY tributo
            ORDER BY valor DESC
            """
        ),
        {"ano": ano},
    )
    estoque_por_tributo = [
        EstoqueDividaAtiva(tributo=row.tributo, valor=float(row.valor or 0))
        for row in estoque_result
    ]

    valor_recuperado = await fetch_scalar(
        session,
        """
        SELECT COALESCE(SUM(db.valor_pago), 0)
        FROM duam_baixa db
        WHERE YEAR(db.data_baixa) = :ano
        """,
        {"ano": ano},
    )

    acordos_result = await session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM acordo_parcelamento ap
            WHERE YEAR(ap.data_acordo) = :ano
            """
        ),
        {"ano": ano},
    )
    quantidade_acordos = int(acordos_result.scalar() or 0)

    observacao = (
        "Confirme colunas: tributo em divida_ativa, data_acordo em acordo_parcelamento, valor_pago em duam_baixa."
    )

    return DividaAtivaResponse(
        ano=ano,
        estoque_divida_ativa_total=estoque_total,
        estoque_por_tributo=estoque_por_tributo,
        valor_recuperado_ano=valor_recuperado,
        quantidade_acordos_parcelamento_ano=quantidade_acordos,
        observacao=observacao,
    )
