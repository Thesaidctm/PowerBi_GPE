let
    Fonte = MySql.Database(
        "SEU_SERVIDOR",
        "gpdcoronelmurta",
        [
            Query = "SELECT * FROM vw_contratos_gestao;"
        ]
    ),
    #"Tipos alterados" = Table.TransformColumnTypes(
        Fonte,
        {
            {"contrato_id", Int64.Type},
            {"numero_contrato", type text},
            {"processo_id", Int64.Type},
            {"data_assinatura", type date},
            {"vigencia_inicio", type date},
            {"vigencia_fim", type date},
            {"valor_total", type number},
            {"dias_para_vencer", Int64.Type}
        }
    )
in
    #"Tipos alterados"
