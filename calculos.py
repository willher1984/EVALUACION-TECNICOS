import pandas as pd
from pandas.tseries.offsets import BDay


def calcular_resumen(base_mes, garantias, periodo):

    # =========================
    # GARANTÍAS DEL MES
    # =========================

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

    # =========================
    # DÍAS HÁBILES
    # =========================

    inicio_mes = periodo.start_time

    ultima_fecha = base_mes["Fecha"].max()

    if pd.notna(ultima_fecha) and ultima_fecha.to_period("M") == periodo:
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

    dias_habiles_mes_completo = len(
        pd.date_range(
            periodo.start_time,
            periodo.end_time,
            freq=BDay()
        )
    )

    # =========================
    # RESUMEN
    # =========================

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

    # =========================
    # FALLA JOVEN
    # =========================

    resumen["Falla_Joven"] = (
        resumen["Garantias"]
        / resumen["Completadas"]
        * 100
    ).fillna(0).round(2)

    resumen["Nota_Falla_Joven"] = (
        100 - resumen["Falla_Joven"]
    ).clip(
        lower=0,
        upper=100
    ).round(2)

    # =========================
    # DÍAS HÁBILES
    # =========================

    resumen["Dias_Habiles"] = dias_habiles

    # =========================
    # META AJUSTADA
    # =========================

    def calcular_meta(vehiculo):

        vehiculo = str(vehiculo).upper()

        if "MOTO" in vehiculo:
            meta_mes = 46
        else:
            meta_mes = 84

        meta_ajustada = (
            meta_mes
            * dias_habiles
            / dias_habiles_mes_completo
        )

        return round(meta_ajustada, 2)

    resumen["Meta"] = resumen["VEHICULO"].apply(
        calcular_meta
    )

    # =========================
    # PRODUCTIVIDAD
    # =========================
    # Órdenes promedio por día

    resumen["Productividad"] = (
        resumen["Completadas"]
        / resumen["Dias_Habiles"]
    ).fillna(0).round(2)

    # Nota Productividad sobre 100

    resumen["Nota_Productividad"] = (
        resumen["Completadas"]
        / resumen["Meta"]
        * 100
    ).clip(
        upper=100
    ).fillna(0).round(2)

    # =========================
    # EFECTIVIDAD
    # =========================

    resumen["Efectividad"] = (
        resumen["Completadas"]
        / resumen["Asignadas"]
        * 100
    ).clip(
        upper=100
    ).fillna(0).round(2)

    resumen["Nota_Efectividad"] = (
        resumen["Efectividad"]
    ).round(2)

    # =========================
    # ASISTENCIA
    # =========================

    resumen["Asistencia"] = (
        resumen["Dias_Laborados"]
        / resumen["Dias_Habiles"]
        * 100
    ).clip(
        upper=100
    ).fillna(0).round(2)

    resumen["Nota_Asistencia"] = (
        resumen["Asistencia"]
    ).round(2)

    # =========================
    # TOTAL SOBRE 100
    # =========================

    resumen["Total"] = (
        resumen["Nota_Productividad"] * 0.25
        + resumen["Nota_Efectividad"] * 0.25
        + resumen["Nota_Asistencia"] * 0.25
        + resumen["Nota_Falla_Joven"] * 0.25
    ).round(2)

    return resumen
