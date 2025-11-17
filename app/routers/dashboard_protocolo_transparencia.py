from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..schemas.protocolo_transparencia import EsicResponse, ProtocoloResponse, ResumoQuantidade

router = APIRouter(prefix="/dashboard", tags=["dashboard-protocolo-transparencia"])


async def fetch_quantidades(session: AsyncSession, query: str, params: Dict[str, Any]) -> list[ResumoQuantidade]:
    result = await session.execute(text(query), params)
    return [ResumoQuantidade(categoria=row[0], quantidade=int(row[1] or 0)) for row in result]


@router.get("/protocolo/resumo", response_model=ProtocoloResponse)
async def get_protocolo_resumo(
    ano: int = Query(default_factory=lambda: datetime.utcnow().year),
    session: AsyncSession = Depends(get_session),
) -> ProtocoloResponse:
    total_result = await session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM prot_protocolo
            WHERE YEAR(data_criacao) = :ano
            """
        ),
        {"ano": ano},
    )
    total_protocolos = int(total_result.scalar() or 0)

    protocolos_por_situacao = await fetch_quantidades(
        session,
        """
        SELECT COALESCE(ps.descricao, 'Situação') AS categoria, COUNT(*) AS quantidade
        FROM prot_protocolo pp
        LEFT JOIN prot_status ps ON ps.id = pp.status_id
        WHERE YEAR(pp.data_criacao) = :ano
        GROUP BY categoria
        ORDER BY quantidade DESC
        """,
        {"ano": ano},
    )

    tempo_medio_result = await session.execute(
        text(
            """
            SELECT AVG(DATEDIFF(COALESCE(pp.data_conclusao, CURRENT_DATE), pp.data_criacao))
            FROM prot_protocolo pp
            WHERE YEAR(pp.data_criacao) = :ano
            """
        ),
        {"ano": ano},
    )
    tempo_medio = float(tempo_medio_result.scalar() or 0)

    top_assuntos = await fetch_quantidades(
        session,
        """
        SELECT COALESCE(pa.descricao, 'Assunto') AS categoria, COUNT(*) AS quantidade
        FROM prot_protocolo pp
        LEFT JOIN prot_assunto pa ON pa.id = pp.assunto_id
        WHERE YEAR(pp.data_criacao) = :ano
        GROUP BY categoria
        ORDER BY quantidade DESC
        LIMIT 10
        """,
        {"ano": ano},
    )

    observacao = "Confirme colunas data_criacao, data_conclusao, assunto_id/status_id nas tabelas de protocolo."

    return ProtocoloResponse(
        ano=ano,
        total_protocolos_ano=total_protocolos,
        protocolos_por_situacao=protocolos_por_situacao,
        tempo_medio_tramitacao=tempo_medio,
        top_assuntos=top_assuntos,
        observacao=observacao,
    )


@router.get("/esic/resumo", response_model=EsicResponse)
async def get_esic_resumo(
    ano: int = Query(default_factory=lambda: datetime.utcnow().year),
    session: AsyncSession = Depends(get_session),
) -> EsicResponse:
    recebidos_result = await session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM esic_registrar_pedidos
            WHERE YEAR(data_pedido) = :ano
            """
        ),
        {"ano": ano},
    )
    pedidos_informacao_recebidos = int(recebidos_result.scalar() or 0)

    respondidos_no_prazo_result = await session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM esic_registrar_pedidos erp
            WHERE YEAR(erp.data_pedido) = :ano
              AND erp.data_resposta IS NOT NULL
              AND DATEDIFF(erp.data_resposta, erp.data_pedido) <= prazo_dias
            """
        ),
        {"ano": ano},
    )
    respondidos_no_prazo = int(respondidos_no_prazo_result.scalar() or 0)

    respondidos_fora_prazo_result = await session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM esic_registrar_pedidos erp
            WHERE YEAR(erp.data_pedido) = :ano
              AND erp.data_resposta IS NOT NULL
              AND DATEDIFF(erp.data_resposta, erp.data_pedido) > prazo_dias
            """
        ),
        {"ano": ano},
    )
    respondidos_fora_do_prazo = int(respondidos_fora_prazo_result.scalar() or 0)

    em_andamento_result = await session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM esic_registrar_pedidos erp
            WHERE YEAR(erp.data_pedido) = :ano AND erp.data_resposta IS NULL
            """
        ),
        {"ano": ano},
    )
    em_andamento = int(em_andamento_result.scalar() or 0)

    observacao = "Ajuste nomes das colunas de datas/prazo na tabela esic_registrar_pedidos conforme o schema." \
        " Se usar tabelas de histórico, alinhe a query."

    return EsicResponse(
        ano=ano,
        pedidos_informacao_recebidos=pedidos_informacao_recebidos,
        respondidos_no_prazo=respondidos_no_prazo,
        respondidos_fora_do_prazo=respondidos_fora_do_prazo,
        em_andamento=em_andamento,
        observacao=observacao,
    )
