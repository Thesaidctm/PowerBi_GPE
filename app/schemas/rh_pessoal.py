from typing import List

from pydantic import BaseModel


class SerieMensal(BaseModel):
    mes: int
    valor: float


class HeadcountResumo(BaseModel):
    categoria: str
    quantidade: int


class RHPessoalResponse(BaseModel):
    ano: int
    gasto_pessoal_ano: float
    gasto_pessoal_mensal: List[SerieMensal]
    percentual_despesa_pessoal_sobre_rcl: float | None = None
    headcount_por_tipo_vinculo: List[HeadcountResumo]
    headcount_por_orgao: List[HeadcountResumo]
    qtde_ferias_no_periodo: int
    qtde_licencas: int
    qtde_rescisoes: int
    observacao: str | None = None
