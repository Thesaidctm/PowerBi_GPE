from typing import List

from pydantic import BaseModel


class VeiculoConsumo(BaseModel):
    veiculo: str
    valor: float


class LicenciamentoStatus(BaseModel):
    veiculo: str
    data_vencimento: str | None = None
    status: str


class FrotasResponse(BaseModel):
    mes: int
    ano: int
    consumo_combustivel_por_veiculo: List[VeiculoConsumo]
    custo_por_km_por_veiculo: List[VeiculoConsumo]
    viagens_por_veiculo: List[VeiculoConsumo]
    veiculos_com_licenciamento_vencido_ou_a_vencer: List[LicenciamentoStatus]
    observacao: str | None = None


class TransporteEscolarResponse(BaseModel):
    ano: int
    viagens_por_rota: List[VeiculoConsumo]
    alunos_atendidos_por_rota: List[VeiculoConsumo]
    observacao: str | None = None
