from typing import List

from pydantic import BaseModel


class BairroArrecadacao(BaseModel):
    bairro: str
    valor_arrecadado: float


class AtividadeResumo(BaseModel):
    atividade: str
    valor: float


class ContribuinteResumo(BaseModel):
    contribuinte: str
    valor: float


class IPTUResponse(BaseModel):
    ano: int
    iptu_lancado_ano: float
    iptu_arrecadado_ano: float
    taxa_inadimplencia: float
    ranking_bairros_por_arrecadacao: List[BairroArrecadacao]
    observacao: str | None = None


class ISSResponse(BaseModel):
    ano: int
    iss_declarado_ano: float
    iss_pago_ano: float
    notas_por_atividade: List[AtividadeResumo]
    top_contribuintes_iss: List[ContribuinteResumo]
    observacao: str | None = None


class EstoqueDividaAtiva(BaseModel):
    tributo: str
    valor: float


class DividaAtivaResponse(BaseModel):
    ano: int
    estoque_divida_ativa_total: float
    estoque_por_tributo: List[EstoqueDividaAtiva]
    valor_recuperado_ano: float
    quantidade_acordos_parcelamento_ano: int
    observacao: str | None = None
