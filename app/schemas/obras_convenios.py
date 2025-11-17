from datetime import date
from typing import List

from pydantic import BaseModel


class ObrasPorSituacao(BaseModel):
    situacao: str
    quantidade: int
    valor_total: float


class ObraAtrasada(BaseModel):
    id: int
    descricao: str
    data_fim_prevista: date
    situacao: str


class ObrasResumoResponse(BaseModel):
    qtde_obras_por_situacao: List[ObrasPorSituacao]
    execucao_fisica_media: float
    obras_atrasadas: List[ObraAtrasada]


class ConvenioPorOrgao(BaseModel):
    orgao_repassador: str
    quantidade: int
    valor_global: float


class ExecucaoFinanceiraConvenio(BaseModel):
    convenio_id: int
    descricao: str
    percentual_execucao_financeira: float
    risco: str


class ConveniosResumoResponse(BaseModel):
    qtde_convenios_por_orgao_repassador: List[ConvenioPorOrgao]
    percentual_execucao_financeira_por_convenio: List[ExecucaoFinanceiraConvenio]
    convenios_em_risco: List[ExecucaoFinanceiraConvenio]
