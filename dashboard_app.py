import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from dash import Dash, Input, Output, dash_table, dcc, html
from dotenv import load_dotenv
import plotly.express as px

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = httpx.Timeout(10.0)


def format_currency(valor: Optional[float]) -> str:
    if valor is None:
        return "-"
    formatted = f"{valor:,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def format_number(valor: Optional[float]) -> str:
    if valor is None:
        return "-"
    formatted = f"{valor:,.0f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return formatted


def api_get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    url = f"{API_URL}{path}"
    response = httpx.get(url, params=params, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def get_overview(ano: Optional[int] = None) -> Any:
    params = {"ano": ano} if ano else None
    return api_get("/dashboard/overview", params=params)


def get_receita_resumo(ano: int) -> Any:
    return api_get("/dashboard/receita/resumo", params={"ano": ano})


def get_despesa_resumo(ano: int) -> Any:
    return api_get("/dashboard/despesa/resumo", params={"ano": ano})


def get_licitacoes_resumo(ano: int) -> Any:
    return api_get("/dashboard/licitacoes/resumo", params={"ano": ano})


def get_contratos_proximos_vencimentos(dias: int) -> Any:
    return api_get("/dashboard/contratos/proximos-vencimentos", params={"dias": dias})


def get_obras_resumo() -> Any:
    return api_get("/dashboard/obras/resumo")


def get_convenios_resumo() -> Any:
    return api_get("/dashboard/convenios/resumo")


def card_component(titulo: str, valor: str) -> html.Div:
    return html.Div(
        [
            html.Div(titulo, style={"fontSize": "14px", "color": "#555"}),
            html.Div(valor, style={"fontSize": "20px", "fontWeight": "bold", "color": "#111"}),
        ],
        style={
            "padding": "12px 16px",
            "border": "1px solid #e0e0e0",
            "borderRadius": "8px",
            "backgroundColor": "#fafafa",
            "boxShadow": "0 1px 3px rgba(0,0,0,0.08)",
            "minWidth": "180px",
        },
    )


def error_alert(message: str) -> html.Div:
    return html.Div(
        message,
        style={
            "padding": "12px",
            "border": "1px solid #f5c2c7",
            "backgroundColor": "#f8d7da",
            "color": "#842029",
            "borderRadius": "6px",
        },
    )


def build_bar_figure(
    data: List[Dict[str, Any]], x: str, y: str, title: str, labels: Optional[Dict[str, str]] = None
):
    if not data:
        return px.bar(title=f"{title} (sem dados)")
    fig = px.bar(data, x=x, y=y, title=title, labels=labels)
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    return fig


def build_month_label(mes: int) -> str:
    meses = [
        "Jan",
        "Fev",
        "Mar",
        "Abr",
        "Mai",
        "Jun",
        "Jul",
        "Ago",
        "Set",
        "Out",
        "Nov",
        "Dez",
    ]
    if 1 <= mes <= 12:
        return meses[mes - 1]
    return str(mes)


app = Dash(__name__, title="Módulo Gestor - Coronel Murta")

app.layout = html.Div(
    [
        html.H1(
            "Módulo Gestor - Painel da Prefeitura",
            style={"textAlign": "center", "marginBottom": "24px", "marginTop": "16px"},
        ),
        html.Div(
            [
                html.Label("Ano de referência", htmlFor="ano-input"),
                dcc.Input(
                    id="ano-input",
                    type="number",
                    value=datetime.utcnow().year,
                    debounce=True,
                    min=2000,
                    max=2100,
                    style={"marginLeft": "12px", "width": "120px"},
                ),
            ],
            style={"display": "flex", "alignItems": "center", "justifyContent": "center", "gap": "12px"},
        ),
        dcc.Tabs(
            id="tabs",
            value="overview",
            children=[
                dcc.Tab(label="Visão Geral", value="overview"),
                dcc.Tab(label="Receitas & Despesas", value="financeiro"),
                dcc.Tab(label="Licitações & Contratos", value="licitacoes"),
                dcc.Tab(label="Obras & Convênios", value="obras"),
            ],
            style={"marginTop": "16px"},
        ),
        html.Div(id="tab-content", style={"padding": "16px"}),
        dcc.Interval(id="overview-interval", interval=60_000, n_intervals=0),
    ]
)


@app.callback(Output("tab-content", "children"), Input("tabs", "value"))
def render_tab_content(tab_value: str):
    if tab_value == "overview":
        return html.Div(
            [
                dcc.Loading(html.Div(id="overview-cards"), type="circle"),
            ]
        )
    if tab_value == "financeiro":
        return html.Div(
            [
                dcc.Loading(
                    [
                        html.Div(
                            [html.Div(id="totais-receita-despesa", style={"display": "flex", "gap": "12px"})],
                            style={"marginBottom": "16px"},
                        ),
                        html.Div(
                            [
                                dcc.Graph(id="receita-mensal-graph"),
                                dcc.Graph(id="despesa-mensal-graph"),
                            ]
                        ),
                    ],
                    type="circle",
                )
            ]
        )
    if tab_value == "licitacoes":
        return html.Div(
            [
                dcc.Loading(
                    [
                        html.Div(
                            [
                                dcc.Graph(id="licitacoes-status-graph"),
                                dcc.Graph(id="licitacoes-modalidade-graph"),
                            ]
                        ),
                        html.H4("Contratos próximos do vencimento (90 dias)"),
                        dash_table.DataTable(
                            id="contratos-table",
                            columns=[
                                {"name": "Número", "id": "numero"},
                                {"name": "Fornecedor", "id": "fornecedor"},
                                {"name": "Data de fim", "id": "data_fim"},
                                {"name": "Valor", "id": "valor"},
                                {"name": "Situação", "id": "status"},
                            ],
                            style_table={"overflowX": "auto"},
                            style_cell={"textAlign": "left", "padding": "8px"},
                            style_header={"backgroundColor": "#f0f0f0", "fontWeight": "bold"},
                        ),
                    ],
                    type="circle",
                )
            ]
        )
    return html.Div(
        [
            dcc.Loading(
                [
                    html.Div(
                        [
                            dcc.Graph(id="obras-situacao-graph"),
                            dash_table.DataTable(
                                id="obras-atrasadas-table",
                                columns=[
                                    {"name": "ID", "id": "id"},
                                    {"name": "Descrição", "id": "descricao"},
                                    {"name": "Data fim prevista", "id": "data_fim_prevista"},
                                    {"name": "Situação", "id": "situacao"},
                                ],
                                style_table={"overflowX": "auto"},
                                style_cell={"textAlign": "left", "padding": "8px"},
                                style_header={"backgroundColor": "#f0f0f0", "fontWeight": "bold"},
                            ),
                        ]
                    ),
                    html.H4("Convênios por órgão repassador"),
                    dcc.Graph(id="convenios-orgaos-graph"),
                    html.H4("Convênios em risco"),
                    dash_table.DataTable(
                        id="convenios-risco-table",
                        columns=[
                            {"name": "Convênio", "id": "descricao"},
                            {"name": "% Execução", "id": "percentual_execucao_financeira"},
                            {"name": "Risco", "id": "risco"},
                        ],
                        style_table={"overflowX": "auto"},
                        style_cell={"textAlign": "left", "padding": "8px"},
                        style_header={"backgroundColor": "#f0f0f0", "fontWeight": "bold"},
                    ),
                ],
                type="circle",
            )
        ]
    )


@app.callback(
    Output("overview-cards", "children"),
    Input("overview-interval", "n_intervals"),
    Input("ano-input", "value"),
)
def update_overview_cards(_, ano: Optional[int]):
    try:
        data = get_overview(ano)
    except Exception as exc:  # noqa: BLE001
        return error_alert(f"Erro ao buscar visão geral: {exc}")

    cards = data.get("cards", {})
    indicadores = [
        ("Receita prevista no ano", cards.get("receita_prevista_ano"), True),
        ("Receita realizada no ano", cards.get("receita_realizada_ano"), True),
        ("Despesa dotação atualizada", cards.get("despesa_dotacao_atualizada_ano"), True),
        ("Despesa empenhada", cards.get("despesa_empenhada_ano"), True),
        ("Despesa liquidada", cards.get("despesa_liquidada_ano"), True),
        ("Despesa paga", cards.get("despesa_paga_ano"), True),
        ("Resultado primário simplificado", cards.get("resultado_primario_simplificado"), True),
        ("Caixa disponível", cards.get("caixa_disponivel"), True),
        ("Estoque de dívida ativa", cards.get("estoque_divida_ativa_total"), True),
        ("Recuperação de dívida ativa no ano", cards.get("recuperacao_divida_ativa_ano"), True),
        ("Licitações em andamento", cards.get("qtde_licitacoes_em_andamento"), False),
        ("Licitações homologadas no ano", cards.get("qtde_licitacoes_homologadas_ano"), False),
        ("Obras em execução", cards.get("qtde_obras_em_execucao"), False),
        ("Obras paralisadas", cards.get("qtde_obras_paralisadas"), False),
    ]

    card_components = []
    for titulo, valor, monetario in indicadores:
        display = format_currency(valor) if monetario else format_number(valor)
        card_components.append(card_component(titulo, display))

    return html.Div(card_components, style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(220px, 1fr))", "gap": "12px"})


@app.callback(
    Output("receita-mensal-graph", "figure"),
    Output("despesa-mensal-graph", "figure"),
    Output("totais-receita-despesa", "children"),
    Input("ano-input", "value"),
)
def update_financeiro(ano: Optional[int]):
    if not ano:
        return px.bar(title="Receita mensal"), px.bar(title="Despesa mensal"), error_alert("Selecione um ano válido.")

    try:
        receita = get_receita_resumo(ano)
        despesa = get_despesa_resumo(ano)
    except Exception as exc:  # noqa: BLE001
        alert = error_alert(f"Erro ao buscar dados financeiros: {exc}")
        return px.bar(title="Receita mensal"), px.bar(title="Despesa mensal"), alert

    receita_mensal = [
        {"Mês": build_month_label(item.get("mes", 0)), "Valor": item.get("receita_realizada_mes", 0)}
        for item in receita.get("serie_mensal", [])
    ]
    despesa_mensal = [
        {"Mês": build_month_label(item.get("mes", 0)), "Empenhado": item.get("empenhado", 0), "Pago": item.get("pago", 0)}
        for item in despesa.get("serie_mensal", [])
    ]

    fig_receita = build_bar_figure(receita_mensal, x="Mês", y="Valor", title="Receita mensal")
    fig_despesa = build_bar_figure(despesa_mensal, x="Mês", y="Empenhado", title="Despesa mensal (empenhado vs pago)")
    if despesa_mensal:
        fig_despesa.add_bar(x=[item["Mês"] for item in despesa_mensal], y=[item.get("Pago", 0) for item in despesa_mensal], name="Pago")
        fig_despesa.update_layout(barmode="group")

    total_cards = html.Div(
        [
            card_component("Receita prevista", format_currency(receita.get("receita_prevista"))),
            card_component("Receita realizada", format_currency(receita.get("receita_realizada"))),
            card_component("Dotação atualizada", format_currency(despesa.get("dotacao_atualizada"))),
            card_component("Despesa empenhada", format_currency(despesa.get("empenhado"))),
            card_component("Despesa liquidada", format_currency(despesa.get("liquidado"))),
            card_component("Despesa paga", format_currency(despesa.get("pago"))),
        ],
        style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(220px, 1fr))", "gap": "12px"},
    )

    return fig_receita, fig_despesa, total_cards


@app.callback(
    Output("licitacoes-status-graph", "figure"),
    Output("licitacoes-modalidade-graph", "figure"),
    Output("contratos-table", "data"),
    Input("ano-input", "value"),
)
def update_licitacoes(ano: Optional[int]):
    if not ano:
        return px.bar(title="Licitações por status"), px.bar(title="Licitações por modalidade"), []

    try:
        licitacoes = get_licitacoes_resumo(ano)
        contratos = get_contratos_proximos_vencimentos(90)
    except Exception as exc:  # noqa: BLE001
        alert_fig = px.bar(title=f"Erro: {exc}")
        return alert_fig, alert_fig, []

    status_data = licitacoes.get("quantidade_processos_por_status", [])
    modalidade_data = licitacoes.get("quantidade_por_modalidade", [])

    fig_status = build_bar_figure(status_data, x="status", y="quantidade", title="Licitações por status")
    fig_modalidade = build_bar_figure(modalidade_data, x="modalidade", y="quantidade", title="Licitações por modalidade")

    contratos_data = []
    for contrato in contratos.get("contratos", []):
        contratos_data.append(
            {
                "numero": contrato.get("numero"),
                "fornecedor": contrato.get("fornecedor"),
                "data_fim": contrato.get("data_fim"),
                "valor": format_currency(contrato.get("valor")),
                "status": contrato.get("status"),
            }
        )

    return fig_status, fig_modalidade, contratos_data


@app.callback(
    Output("obras-situacao-graph", "figure"),
    Output("obras-atrasadas-table", "data"),
    Output("convenios-orgaos-graph", "figure"),
    Output("convenios-risco-table", "data"),
    Input("tabs", "value"),
)
def update_obras_convenios(tab_value: str):
    if tab_value != "obras":
        return px.bar(title="Obras por situação"), [], px.bar(title="Convênios por órgão repassador"), []

    try:
        obras = get_obras_resumo()
        convenios = get_convenios_resumo()
    except Exception as exc:  # noqa: BLE001
        alert_fig = px.bar(title=f"Erro: {exc}")
        return alert_fig, [], alert_fig, []

    obras_data = obras.get("qtde_obras_por_situacao", [])
    obras_fig = build_bar_figure(
        obras_data,
        x="situacao",
        y="quantidade",
        title="Obras por situação",
        labels={"situacao": "Situação", "quantidade": "Quantidade"},
    )

    obras_atrasadas = obras.get("obras_atrasadas", [])
    obras_atrasadas_data = []
    for obra in obras_atrasadas:
        obras_atrasadas_data.append(
            {
                "id": obra.get("id"),
                "descricao": obra.get("descricao"),
                "data_fim_prevista": obra.get("data_fim_prevista"),
                "situacao": obra.get("situacao"),
            }
        )

    convenios_orgaos = convenios.get("qtde_convenios_por_orgao_repassador", [])
    convenios_fig = build_bar_figure(
        convenios_orgaos,
        x="orgao_repassador",
        y="quantidade",
        title="Convênios por órgão repassador",
        labels={"orgao_repassador": "Órgão repassador", "quantidade": "Quantidade"},
    )

    convenios_risco_data = []
    for convenio in convenios.get("convenios_em_risco", []):
        convenios_risco_data.append(
            {
                "descricao": convenio.get("descricao"),
                "percentual_execucao_financeira": f"{convenio.get('percentual_execucao_financeira', 0):.1f}%",
                "risco": convenio.get("risco"),
            }
        )

    return obras_fig, obras_atrasadas_data, convenios_fig, convenios_risco_data


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
