let
    Fonte = MySql.Database(
        "SEU_SERVIDOR",
        "gpdcoronelmurta",
        [
            Query = "SELECT * FROM vw_execucao_despesa_mensal;"
        ]
    )
in
    Fonte
