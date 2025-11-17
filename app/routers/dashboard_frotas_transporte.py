from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..schemas.frotas_transporte import (
    FrotasResponse,
    LicenciamentoStatus,
    TransporteEscolarResponse,
    VeiculoConsumo,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard-frotas-transporte"])


async def fetch_list(session: AsyncSession, query: str, params: Dict[str, Any]) -> list[VeiculoConsumo]:
    result = await session.execute(text(query), params)
    return [VeiculoConsumo(veiculo=row[0], valor=float(row[1] or 0)) for row in result]


@router.get("/frotas/resumo", response_model=FrotasResponse)
async def get_frotas_resumo(
    mes: int = Query(default_factory=lambda: datetime.utcnow().month, ge=1, le=12),
    ano: int = Query(default_factory=lambda: datetime.utcnow().year),
    session: AsyncSession = Depends(get_session),
) -> FrotasResponse:
    consumo_combustivel = await fetch_list(
        session,
        """
        SELECT COALESCE(v.placa, 'Veículo') AS veiculo, COALESCE(SUM(cci.valor_total), 0) AS valor
        FROM ctrl_combustivel_item cci
        JOIN ctrl_combustivel cc ON cc.id = cci.ctrl_combustivel_id
        LEFT JOIN veiculos v ON v.id = cc.veiculo_id
        WHERE MONTH(cc.data_abastecimento) = :mes AND YEAR(cc.data_abastecimento) = :ano
        GROUP BY veiculo
        ORDER BY valor DESC
        """,
        {"mes": mes, "ano": ano},
    )

    custo_por_km = await fetch_list(
        session,
        """
        SELECT COALESCE(v.placa, 'Veículo') AS veiculo,
               COALESCE(SUM(cci.valor_total) / NULLIF(SUM(cci.km_rodado), 0), 0) AS valor
        FROM ctrl_combustivel_item cci
        JOIN ctrl_combustivel cc ON cc.id = cci.ctrl_combustivel_id
        LEFT JOIN veiculos v ON v.id = cc.veiculo_id
        WHERE MONTH(cc.data_abastecimento) = :mes AND YEAR(cc.data_abastecimento) = :ano
        GROUP BY veiculo
        ORDER BY valor DESC
        """,
        {"mes": mes, "ano": ano},
    )

    viagens_por_veiculo = await fetch_list(
        session,
        """
        SELECT COALESCE(v.placa, 'Veículo') AS veiculo, COUNT(*) AS valor
        FROM viagens vi
        LEFT JOIN veiculos v ON v.id = vi.veiculo_id
        WHERE MONTH(vi.data_viagem) = :mes AND YEAR(vi.data_viagem) = :ano
        GROUP BY veiculo
        ORDER BY valor DESC
        """,
        {"mes": mes, "ano": ano},
    )

    licenciamento_result = await session.execute(
        text(
            """
            SELECT COALESCE(v.placa, 'Veículo') AS veiculo,
                   cl.data_vencimento,
                   CASE
                        WHEN cl.data_vencimento < CURRENT_DATE THEN 'vencido'
                        WHEN cl.data_vencimento BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL 60 DAY) THEN 'a vencer'
                        ELSE 'vigente'
                   END AS status
            FROM ctrl_licenciamento cl
            LEFT JOIN veiculos v ON v.id = cl.veiculo_id
            WHERE cl.data_vencimento BETWEEN CURRENT_DATE - INTERVAL 30 DAY AND CURRENT_DATE + INTERVAL 120 DAY
            ORDER BY cl.data_vencimento
            """
        )
    )
    veiculos_licenciamento = [
        LicenciamentoStatus(
            veiculo=row.veiculo,
            data_vencimento=row.data_vencimento.isoformat() if row.data_vencimento else None,
            status=row.status,
        )
        for row in licenciamento_result
    ]

    observacao = "Confirme colunas km_rodado, valor_total e data_abastecimento em ctrl_combustivel_item." \
        " Ajuste data_vencimento em ctrl_licenciamento se necessário."

    return FrotasResponse(
        mes=mes,
        ano=ano,
        consumo_combustivel_por_veiculo=consumo_combustivel,
        custo_por_km_por_veiculo=custo_por_km,
        viagens_por_veiculo=viagens_por_veiculo,
        veiculos_com_licenciamento_vencido_ou_a_vencer=veiculos_licenciamento,
        observacao=observacao,
    )


@router.get("/transporte-escolar/resumo", response_model=TransporteEscolarResponse)
async def get_transporte_escolar_resumo(
    ano: int = Query(default_factory=lambda: datetime.utcnow().year),
    session: AsyncSession = Depends(get_session),
) -> TransporteEscolarResponse:
    viagens_rota_result = await session.execute(
        text(
            """
            SELECT COALESCE(r.nome, 'Rota') AS veiculo, COUNT(*) AS valor
            FROM transporte_escolar te
            LEFT JOIN rota r ON r.id = te.rota_id
            WHERE te.ano = :ano
            GROUP BY veiculo
            ORDER BY valor DESC
            """
        ),
        {"ano": ano},
    )
    viagens_por_rota = [VeiculoConsumo(veiculo=row.veiculo, valor=float(row.valor or 0)) for row in viagens_rota_result]

    alunos_rota_result = await session.execute(
        text(
            """
            SELECT COALESCE(r.nome, 'Rota') AS veiculo, COALESCE(SUM(te.alunos_atendidos), 0) AS valor
            FROM transporte_escolar te
            LEFT JOIN rota r ON r.id = te.rota_id
            WHERE te.ano = :ano
            GROUP BY veiculo
            ORDER BY valor DESC
            """
        ),
        {"ano": ano},
    )
    alunos_por_rota = [VeiculoConsumo(veiculo=row.veiculo, valor=float(row.valor or 0)) for row in alunos_rota_result]

    observacao = "Ajuste colunas alunos_atendidos e ano em transporte_escolar conforme o schema."

    return TransporteEscolarResponse(
        ano=ano,
        viagens_por_rota=viagens_por_rota,
        alunos_atendidos_por_rota=alunos_por_rota,
        observacao=observacao,
    )
