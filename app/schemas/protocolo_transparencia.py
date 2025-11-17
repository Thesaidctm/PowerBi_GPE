from typing import List

from pydantic import BaseModel


class ResumoQuantidade(BaseModel):
    categoria: str
    quantidade: int


class ProtocoloResponse(BaseModel):
    ano: int
    total_protocolos_ano: int
    protocolos_por_situacao: List[ResumoQuantidade]
    tempo_medio_tramitacao: float
    top_assuntos: List[ResumoQuantidade]
    observacao: str | None = None


class EsicResponse(BaseModel):
    ano: int
    pedidos_informacao_recebidos: int
    respondidos_no_prazo: int
    respondidos_fora_do_prazo: int
    em_andamento: int
    observacao: str | None = None
