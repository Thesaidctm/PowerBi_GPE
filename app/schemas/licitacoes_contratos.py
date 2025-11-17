from datetime import date
from typing import List

from pydantic import BaseModel


class LicitacaoStatusResumo(BaseModel):
    status: str
    quantidade: int


class LicitacaoModalidadeResumo(BaseModel):
    modalidade: str
    quantidade: int


class LicitacoesResumoResponse(BaseModel):
    ano: int
    quantidade_processos_por_status: List[LicitacaoStatusResumo]
    quantidade_por_modalidade: List[LicitacaoModalidadeResumo]
    valor_total_licitado_ano: float
    valor_total_contratado_ano: float
    tempo_medio_entre_abertura_e_homologacao: float


class ContratoProximoVencimento(BaseModel):
    id: int
    numero: str
    fornecedor: str
    valor: float
    data_fim: date
    status: str


class ContratosProximosVencimentosResponse(BaseModel):
    dias: int
    contratos: List[ContratoProximoVencimento]
