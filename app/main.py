from fastapi import FastAPI

from .routers import (
    dashboard_licitacoes_contratos,
    dashboard_obras_convenios,
    dashboard_overview,
    dashboard_receita_despesa,
)

app = FastAPI(title="Modulo Gestor", version="0.1.0")

app.include_router(dashboard_overview.router)
app.include_router(dashboard_receita_despesa.router)
app.include_router(dashboard_licitacoes_contratos.router)
app.include_router(dashboard_obras_convenios.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
