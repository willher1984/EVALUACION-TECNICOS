import pandas as pd
from pandas.tseries.offsets import BDay


def calcular_resumen(base_mes, garantias, periodo):

    garantias_mes = garantias[
        garantias["Fecha"].dt.to_period("M") == periodo
    ]

    ordenes_con_garantia = set(
        garantias_mes["Orden Original"]
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.strip()
        .unique()
    )

    base_mes = base_mes.copy()

    base_mes["Tiene_Garantia"] = (
        base_mes["Orden"]
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.strip()
        .isin(ordenes_con_garantia)
    )

    inicio_mes = periodo.start_time

    

    ultima_fecha = base_mes["Fecha"].max()

    if ultima_fecha.to_period("M") == periodo:
        fin_mes = ultima_fecha
    else:
        fin_mes = periodo.end_time

    dias_habiles = len(
        pd.date_range(
            inicio_mes,
            fin_mes,
            freq=BDay()
        )
    )

    resumen = (
        base_mes.groupby(
            [
                "CC Tecnico",
                "Tecnico",
                "SUPERVISOR",
                "VEHICULO"
            ],
            dropna=False
        )
        .agg(
            Asignadas=("Orden", "count"),

            Completadas=(
                "Estado",
                lambda x: (
                    x.astype(str)
                    .str.upper()
                    .str.contains("COMPLET")
                ).sum()
            ),

            Dias_Laborados=(
                "Fecha",
                lambda x: x.dt.date.nunique()
            ),

            Garantias=("Tiene_Garantia", "sum"),
        )
        .reset_index()
    )

    resumen["Falla_Joven"] = (
        resumen["Garantias"]
        / resumen["Completadas"]
        * 100
    ).fillna(0).round(2)

    resumen["Nota_Falla_Joven"] = (
        30 * (1 - resumen["Falla_Joven"] / 100)
    ).clip(lower=0).round(2)

    resumen["Dias_Habiles"] = dias_habiles

    def calcular_meta(vehiculo):

        vehiculo = str(vehiculo).upper()

        if "MOTO" in vehiculo:
            return dias_habiles * 2

        return dias_habiles * 3.5

    resumen["Meta"] = resumen["VEHICULO"].apply(
        calcular_meta
    )

    resumen["Productividad"] = (
        resumen["Completadas"]
        / resumen["Dias_Habiles"]
    ).round(2)

    resumen["Efectividad"] = (
        resumen["Completadas"]
        / resumen["Asignadas"]
        * 100
    ).round(2)

    resumen["Asistencia"] = (
        resumen["Dias_Laborados"]
        / resumen["Dias_Habiles"]
        * 100
    ).round(2)

    def nota_productividad(row):

        if "MOTO" in str(row["VEHICULO"]).upper():
            meta = 2
        else:
            meta = 3.5

        cumplimiento = row["Productividad"] / meta

        if cumplimiento >= 1:
            return 30
        elif cumplimiento >= 0.85:
            return 24
        elif cumplimiento >= 0.70:
            return 15
        else:
            return 5

    resumen["Nota_Productividad"] = resumen.apply(
        nota_productividad,
        axis=1
    )

    resumen["Nota_Efectividad"] = (
        resumen["Efectividad"]
        / 100 * 25
    ).round(2)

    resumen["Nota_Asistencia"] = (
        resumen["Asistencia"]
        / 100 * 15
    ).round(2)

    resumen["Total"] = (
        resumen["Nota_Productividad"]
        + resumen["Nota_Efectividad"]
        + resumen["Nota_Falla_Joven"]
        + resumen["Nota_Asistencia"]
    ).round(2)

    return resumen
