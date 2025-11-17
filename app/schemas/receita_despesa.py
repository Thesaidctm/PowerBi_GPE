from typing import List

from pydantic import BaseModel


class ReceitaMensal(BaseModel):
    mes: int
    receita_realizada_mes: float
    receita_mes_ano_anterior: float


class ReceitaPorCategoria(BaseModel):
    categoria: str
    valor: float


class ReceitaResumoResponse(BaseModel):
    ano: int
    receita_prevista: float
    receita_realizada: float
    serie_mensal: List[ReceitaMensal]
    receita_por_origem: List[ReceitaPorCategoria]
    receita_por_natureza: List[ReceitaPorCategoria]
    receita_por_fonte: List[ReceitaPorCategoria]


class DespesaMensal(BaseModel):
    mes: int
    empenhado: float
    liquidado: float
    pago: float


class DespesaPorCategoria(BaseModel):
    categoria: str
    valor: float


class DespesaResumoResponse(BaseModel):
    ano: int
    dotacao_inicial: float
    dotacao_atualizada: float
    empenhado: float
    liquidado: float
    pago: float
    serie_mensal: List[DespesaMensal]
    despesa_por_orgao: List[DespesaPorCategoria]
    despesa_por_funcao: List[DespesaPorCategoria]
    despesa_por_programa: List[DespesaPorCategoria]
