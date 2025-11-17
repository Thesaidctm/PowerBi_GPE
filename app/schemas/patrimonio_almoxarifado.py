from typing import List

from pydantic import BaseModel


class ResumoValor(BaseModel):
    categoria: str
    valor: float


class PatrimonioResponse(BaseModel):
    valor_total_bens: float
    valor_depreciacao_acumulada: float
    bens_por_orgao: List[ResumoValor]
    bens_por_natureza_ou_grupo: List[ResumoValor]
    observacao: str | None = None


class ConsumoResumo(BaseModel):
    item: str
    valor: float


class EstoqueProduto(BaseModel):
    produto: str
    quantidade: float


class AlmoxarifadoResponse(BaseModel):
    mes: int
    ano: int
    consumo_por_orgao_no_mes: List[ConsumoResumo]
    consumo_por_produto: List[ConsumoResumo]
    estoque_atual_por_produto: List[EstoqueProduto]
    observacao: str | None = None
