from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..schemas.obras_convenios import (
    ConvenioPorOrgao,
    ConveniosResumoResponse,
    ExecucaoFinanceiraConvenio,
    ObraAtrasada,
    ObrasPorSituacao,
    ObrasResumoResponse,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard-obras-convenios"])


@router.get("/obras/resumo", response_model=ObrasResumoResponse)
async def get_obras_resumo(session: AsyncSession = Depends(get_session)) -> ObrasResumoResponse:
    situacao_result = await session.execute(
        text(
            """
            SELECT situacao, COUNT(*) AS quantidade, COALESCE(SUM(valor_total), 0) AS valor_total
            FROM obr_obra
            GROUP BY situacao
            ORDER BY quantidade DESC
            """
        )
    )
    qtde_obras_por_situacao: List[ObrasPorSituacao] = [
        ObrasPorSituacao(
            situacao=row.situacao,
            quantidade=int(row.quantidade or 0),
            valor_total=float(row.valor_total or 0),
        )
        for row in situacao_result.all()
    ]

    execucao_fisica_media_result = await session.execute(
        text(
            """
            SELECT AVG(percentual_execucao) AS execucao_fisica_media
            FROM obr_medicao
            """
        )
    )
    execucao_fisica_media = float(execucao_fisica_media_result.scalar() or 0)

    obras_atrasadas_result = await session.execute(
        text(
            """
            SELECT id, descricao, data_fim_prevista, situacao
            FROM obr_obra
            WHERE data_fim_prevista < :hoje AND situacao NOT IN ('concluida', 'concluída')
            ORDER BY data_fim_prevista
            """
        ),
        {"hoje": datetime.utcnow().date()},
    )
    obras_atrasadas = [
        ObraAtrasada(
            id=row.id,
            descricao=row.descricao,
            data_fim_prevista=row.data_fim_prevista,
            situacao=row.situacao,
        )
        for row in obras_atrasadas_result.all()
    ]

    return ObrasResumoResponse(
        qtde_obras_por_situacao=qtde_obras_por_situacao,
        execucao_fisica_media=execucao_fisica_media,
        obras_atrasadas=obras_atrasadas,
    )


@router.get("/convenios/resumo", response_model=ConveniosResumoResponse)
async def get_convenios_resumo(
    session: AsyncSession = Depends(get_session),
) -> ConveniosResumoResponse:
    convenios_por_orgao_result = await session.execute(
        text(
            """
            SELECT orgao_repassador, COUNT(*) AS quantidade, COALESCE(SUM(valor_global), 0) AS valor_global
            FROM cont_convenio
            GROUP BY orgao_repassador
            ORDER BY valor_global DESC
            """
        )
    )
    convenios_por_orgao = [
        ConvenioPorOrgao(
            orgao_repassador=row.orgao_repassador,
            quantidade=int(row.quantidade or 0),
            valor_global=float(row.valor_global or 0),
        )
        for row in convenios_por_orgao_result.all()
    ]

    execucao_financeira_result = await session.execute(
        text(
            """
            SELECT c.id AS convenio_id,
                   c.descricao,
                   COALESCE(SUM(mov.valor_pago), 0) / NULLIF(c.valor_global, 0) * 100 AS percentual_execucao_financeira,
                   CASE
                       WHEN c.data_fim_prevista < CURRENT_DATE THEN 'prazo expirada'
                       WHEN COALESCE(SUM(mov.valor_pago), 0) / NULLIF(c.valor_global, 0) < 0.3 THEN 'baixa execucao'
                       ELSE 'regular'
                   END AS risco
            FROM cont_convenio c
            LEFT JOIN ct_conv_movimento mov ON mov.convenio_id = c.id
            GROUP BY c.id, c.descricao, c.valor_global, c.data_fim_prevista
            ORDER BY percentual_execucao_financeira
            """
        )
    )
    execucao_financeira = [
        ExecucaoFinanceiraConvenio(
            convenio_id=row.convenio_id,
            descricao=row.descricao,
            percentual_execucao_financeira=float(row.percentual_execucao_financeira or 0),
            risco=row.risco,
        )
        for row in execucao_financeira_result.all()
    ]

    convenios_em_risco = [c for c in execucao_financeira if c.risco != "regular"]

    return ConveniosResumoResponse(
        qtde_convenios_por_orgao_repassador=convenios_por_orgao,
        percentual_execucao_financeira_por_convenio=execucao_financeira,
        convenios_em_risco=convenios_em_risco,
    )
