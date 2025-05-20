import pandas as pd
import numpy as np

COLUMNA_OBJETIVO = "RateOil"
COLUMNA_ACUMULADO_OIL = "AccumulatedOil"
COLUMNA_TIEMPO = "Tiempo"
COLUMNA_AGUA = "RateWater"
COLUMNA_ACUMULADO_AGUA = "AccumulatedWater"
COLUMNA_BSW = "BSW"
COLUMNA_BSW_ACUMULADO = "ACCUMULATED_BSW"
N_SIMULACIONES = 1000
N_MESES_FUTURO = 60


def parse_spanish_dates(series):
    traducciones = {
        "ene": "jan", "feb": "feb", "mar": "mar", "abr": "apr",
        "may": "may", "jun": "jun", "jul": "jul", "ago": "aug",
        "sep": "sep", "oct": "oct", "nov": "nov", "dic": "dec"
    }
    series = series.str.lower()
    for esp, eng in traducciones.items():
        series = series.str.replace(f"-{esp}-", f"-{eng}-", regex=False)
    return pd.to_datetime(series, format="%d-%b-%y")


def cargar_y_preparar_datos(file, columnas):
    df = pd.read_csv(file, sep=";")[columnas].copy()
    df[COLUMNA_TIEMPO] = pd.to_datetime(df[COLUMNA_TIEMPO], dayfirst=True)
    
    #PRODUCCCION 
    df[COLUMNA_OBJETIVO] = df[COLUMNA_OBJETIVO].astype(str).str.replace(",", ".", regex=False) # TODO: Formatear datos decimales cuando tienen "," cambiarlos a "."
    df[COLUMNA_OBJETIVO] = pd.to_numeric(df[COLUMNA_OBJETIVO], errors='coerce')

    df[COLUMNA_ACUMULADO_OIL] = df[COLUMNA_ACUMULADO_OIL].astype(str).str.replace(",", ".", regex=False)
    df[COLUMNA_ACUMULADO_OIL] = pd.to_numeric(df[COLUMNA_ACUMULADO_OIL], errors='coerce')

    #AGUA
    df[COLUMNA_ACUMULADO_AGUA] = df[COLUMNA_ACUMULADO_AGUA].astype(str).str.replace(",", ".", regex=False)
    df[COLUMNA_ACUMULADO_AGUA] = pd.to_numeric(df[COLUMNA_ACUMULADO_AGUA], errors='coerce')

    df[COLUMNA_AGUA] = df[COLUMNA_AGUA].astype(str).str.replace(",", ".", regex=False)
    df[COLUMNA_AGUA] = pd.to_numeric(df[COLUMNA_AGUA], errors='coerce')

    #BSW
    df[COLUMNA_BSW] = df[COLUMNA_BSW].astype(str).str.replace(",", ".", regex=False)
    df[COLUMNA_BSW] = pd.to_numeric(df[COLUMNA_BSW], errors='coerce')

    df[COLUMNA_BSW_ACUMULADO] = df[COLUMNA_BSW_ACUMULADO].astype(str).str.replace(",", ".", regex=False)
    df[COLUMNA_BSW_ACUMULADO] = pd.to_numeric(df[COLUMNA_BSW_ACUMULADO], errors='coerce')




    df = df.dropna(subset=[COLUMNA_OBJETIVO])
    return df.sort_values(COLUMNA_TIEMPO).reset_index(drop=True)


def simular_monte_carlo(valor_inicial, media, std, n_simulaciones, n_meses):
    simulaciones = np.zeros((n_simulaciones, n_meses))
    for i in range(n_simulaciones):
        valores = [valor_inicial]
        for _ in range(n_meses - 1):
            incremento = np.random.normal(media, std)
            siguiente = max(valores[-1] + incremento, 0)
            valores.append(siguiente)
        simulaciones[i] = valores
    return simulaciones


def calcular_percentiles(simulaciones):
    return (
        np.percentile(simulaciones, 10, axis=0).tolist(),
        np.percentile(simulaciones, 50, axis=0).tolist(),
        np.percentile(simulaciones, 90, axis=0).tolist()
    )


def procesar_archivo_para_api(file):
    df = cargar_y_preparar_datos(file, [COLUMNA_TIEMPO, COLUMNA_OBJETIVO, COLUMNA_ACUMULADO_OIL, COLUMNA_ACUMULADO_AGUA, COLUMNA_AGUA, COLUMNA_BSW, COLUMNA_BSW_ACUMULADO])
    #obtener acumulado
    df["accumulated"] = df[COLUMNA_OBJETIVO]
    midpoint = len(df) // 2
    train, valid = df.iloc[:midpoint].copy(), df.iloc[midpoint:].copy()
    train["Delta"] = train[COLUMNA_OBJETIVO].diff()
    delta_mean, delta_std = train["Delta"].mean(), train["Delta"].std()

    # Simulación sobre validación histórica
    sim_valid = simular_monte_carlo(train[COLUMNA_OBJETIVO].iloc[-1], delta_mean, delta_std, N_SIMULACIONES, len(valid))
    errores = np.linalg.norm(sim_valid - valid[COLUMNA_OBJETIVO].values, axis=1)
    mejor_sim = sim_valid[np.argmin(errores)].tolist()
    fechas_validacion = pd.date_range(start=train[COLUMNA_TIEMPO].iloc[-1] + pd.DateOffset(months=1), periods=len(valid), freq='MS').strftime('%Y-%m-%d').tolist()
    p10, p50, p90 = calcular_percentiles(sim_valid)

    # Simulación a futuro
    sim_futuro = simular_monte_carlo(df[COLUMNA_OBJETIVO].iloc[-1], delta_mean, delta_std, N_SIMULACIONES, N_MESES_FUTURO)
    fechas_futuras = pd.date_range(start=df[COLUMNA_TIEMPO].iloc[-1] + pd.DateOffset(months=1), periods=N_MESES_FUTURO, freq='MS').strftime('%Y-%m-%d').tolist()
    p10_f, p50_f, p90_f = calcular_percentiles(sim_futuro)

    return {
        "historico": {
            "fechas": df[COLUMNA_TIEMPO].dt.strftime('%Y-%m-%d').tolist(),
            "valores": df[COLUMNA_OBJETIVO].tolist(),
            "accumulatedOil": df[COLUMNA_ACUMULADO_OIL].tolist(),
            "rateWater": df[COLUMNA_AGUA].tolist(),
            "accumulatedWater": df[COLUMNA_ACUMULADO_AGUA].tolist(),
            "bsw": df[COLUMNA_BSW].tolist(),
            "accumulatedBSW": df[COLUMNA_BSW_ACUMULADO].tolist(),
        },
        "validacion": {
            "fechas": fechas_validacion,
            "mejor_simulacion": mejor_sim,
            "p10": p10,
            "p50": p50,
            "p90": p90
        },
        "futuro": {
            "fechas": fechas_futuras,
            "p10": p10_f,
            "p50": p50_f,
            "p90": p90_f,
            "simulaciones": sim_futuro.tolist()
        }
    }
