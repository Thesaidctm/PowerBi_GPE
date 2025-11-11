let
    Fonte = MySql.Database(
        "SEU_SERVIDOR",
        "gpdcoronelmurta",
        [
            Query = "SELECT * FROM vw_execucao_receita_mensal;"
        ]
    )
in
    Fonte
