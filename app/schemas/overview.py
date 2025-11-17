from typing import Optional

from pydantic import BaseModel


class OverviewCards(BaseModel):
    receita_prevista_ano: float
    receita_realizada_ano: float
    despesa_dotacao_atualizada_ano: float
    despesa_empenhada_ano: float
    despesa_liquidada_ano: float
    despesa_paga_ano: float
    resultado_primario_simplificado: float
    caixa_disponivel: float
    estoque_divida_ativa_total: float
    recuperacao_divida_ativa_ano: float
    qtde_licitacoes_em_andamento: int
    qtde_licitacoes_homologadas_ano: int
    qtde_obras_em_execucao: int
    qtde_obras_paralisadas: int


class OverviewResponse(BaseModel):
    ano: int
    cards: OverviewCards
    observacao: Optional[str] = None
