import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# === CONFIGURACIÓN ===
ARCHIVO_CSV = "pozoSin94.csv"  # POZO 2 VENEZUELA
COLUMNA_OBJETIVO = "RateOil"
COLUMNA_TIEMPO = "Tiempo"
N_SIMULACIONES = 1000
N_MESES_FUTURO = 60
SIMULACIONES_VISIBLES = 20


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


def cargar_y_preparar_datos(archivo, columnas, columna_objetivo, columna_tiempo):
    df = pd.read_csv(archivo, sep=";")[columnas].copy()
    df[columna_tiempo] = pd.to_datetime(df[columna_tiempo], dayfirst=True)
    df[columna_objetivo] = df[columna_objetivo].astype(str).str.replace(",", ".", regex=False)
    df[columna_objetivo] = pd.to_numeric(df[columna_objetivo], errors='coerce')
    df = df.dropna(subset=[columna_objetivo])
    return df.sort_values(columna_tiempo).reset_index(drop=True)


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
        np.percentile(simulaciones, 10, axis=0),
        np.percentile(simulaciones, 50, axis=0),
        np.percentile(simulaciones, 90, axis=0)
    )


def graficar_simulaciones(tiempo_historico, datos_historicos, fechas_sim, simulaciones, mejor_sim, p10, p50, p90):
    plt.figure(figsize=(14, 7))
    plt.plot(tiempo_historico, datos_historicos, label="Histórico completo", color='black', linewidth=2)
    colores = plt.cm.viridis(np.linspace(0, 1, SIMULACIONES_VISIBLES))
    for i, color in zip(range(SIMULACIONES_VISIBLES), colores):
        plt.plot(fechas_sim, simulaciones[i], color=color, alpha=0.3)
    plt.plot(fechas_sim, mejor_sim, label="Simulación más cercana", color='red', linewidth=2)
    plt.plot(fechas_sim, p10, label="P10", color='blue', linestyle="--")
    plt.plot(fechas_sim, p50, label="P50", color='green')
    plt.plot(fechas_sim, p90, label="P90", color='purple', linestyle="--")
    plt.title("Simulación Monte Carlo vs Validación histórica")
    plt.xlabel("Fecha")
    plt.ylabel("RateOil (bpd)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def graficar_prediccion_futura(tiempo_historico, datos_historicos, fechas_fut, simulaciones_fut, p10, p50, p90):
    plt.figure(figsize=(14, 7))
    plt.plot(tiempo_historico, datos_historicos, label="Histórico", color='black', linewidth=2)
    for i in range(SIMULACIONES_VISIBLES):
        plt.plot(fechas_fut, simulaciones_fut[i], alpha=0.3)
    plt.plot(fechas_fut, p10, label="P10", linestyle="--", color='blue')
    plt.plot(fechas_fut, p50, label="P50", color='green')
    plt.plot(fechas_fut, p90, label="P90", linestyle="--", color='red')
    plt.title("Proyección Monte Carlo hacia el futuro")
    plt.xlabel("Fecha")
    plt.ylabel("RateOil (bpd)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def graficar_eur(simulaciones):
    eur_sim = simulaciones.sum(axis=1)
    plt.figure(figsize=(10, 5))
    plt.hist(eur_sim, bins=30, color='skyblue', edgecolor='black')
    plt.axvline(np.percentile(eur_sim, 10), color='blue', linestyle='--', label='P10')
    plt.axvline(np.percentile(eur_sim, 50), color='green', linestyle='-', label='P50 (Mediana)')
    plt.axvline(np.percentile(eur_sim, 90), color='red', linestyle='--', label='P90')
    plt.title("Distribución del EUR (Estimated Ultimate Recovery)")
    plt.xlabel("EUR acumulado (bbl)")
    plt.ylabel("Frecuencia")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


# === PROCESAMIENTO ===
df = cargar_y_preparar_datos(ARCHIVO_CSV, [COLUMNA_TIEMPO, COLUMNA_OBJETIVO], COLUMNA_OBJETIVO, COLUMNA_TIEMPO)
midpoint = len(df) // 2
train, valid = df.iloc[:midpoint].copy(), df.iloc[midpoint:].copy()
train["Delta"] = train[COLUMNA_OBJETIVO].diff()
delta_mean, delta_std = train["Delta"].mean(), train["Delta"].std()

fecha_ini = train[COLUMNA_TIEMPO].iloc[-1]
fechas_validacion = pd.date_range(start=fecha_ini + pd.DateOffset(months=1), periods=len(valid), freq='MS')
sim_valid = simular_monte_carlo(train[COLUMNA_OBJETIVO].iloc[-1], delta_mean, delta_std, N_SIMULACIONES, len(valid))

errores = np.linalg.norm(sim_valid - valid[COLUMNA_OBJETIVO].values, axis=1)
mejor_idx = np.argmin(errores)
mejor_sim = sim_valid[mejor_idx]
p10, p50, p90 = calcular_percentiles(sim_valid)

#graficar_simulaciones(df[COLUMNA_TIEMPO], df[COLUMNA_OBJETIVO], fechas_validacion, sim_valid, mejor_sim, p10, p50, p90)

fechas_futuras = pd.date_range(start=df[COLUMNA_TIEMPO].iloc[-1] + pd.DateOffset(months=1), periods=N_MESES_FUTURO, freq='MS')
sim_futuro = simular_monte_carlo(df[COLUMNA_OBJETIVO].iloc[-1], delta_mean, delta_std, N_SIMULACIONES, N_MESES_FUTURO)
p10_f, p50_f, p90_f = calcular_percentiles(sim_futuro)

graficar_prediccion_futura(df[COLUMNA_TIEMPO], df[COLUMNA_OBJETIVO], fechas_futuras, sim_futuro, p10_f, p50_f, p90_f)
#graficar_eur(sim_valid)