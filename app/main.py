from fastapi import FastAPI

from .routers import (
    dashboard_frotas_transporte,
    dashboard_licitacoes_contratos,
    dashboard_obras_convenios,
    dashboard_overview,
    dashboard_patrimonio_almoxarifado,
    dashboard_protocolo_transparencia,
    dashboard_receita_despesa,
    dashboard_rh_pessoal,
    dashboard_tributos_divida_ativa,
)

app = FastAPI(title="Modulo Gestor", version="0.1.0")

app.include_router(dashboard_overview.router)
app.include_router(dashboard_receita_despesa.router)
app.include_router(dashboard_licitacoes_contratos.router)
app.include_router(dashboard_obras_convenios.router)
app.include_router(dashboard_tributos_divida_ativa.router)
app.include_router(dashboard_rh_pessoal.router)
app.include_router(dashboard_patrimonio_almoxarifado.router)
app.include_router(dashboard_frotas_transporte.router)
app.include_router(dashboard_protocolo_transparencia.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
