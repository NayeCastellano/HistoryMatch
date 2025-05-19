import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def parse_spanish_dates(series):
    traducciones = {
        "ene": "jan", "feb": "feb", "mar": "mar", "abr": "apr",
        "may": "may", "jun": "jun", "jul": "jul", "ago": "aug",
        "sep": "sep", "oct": "oct", "nov": "nov", "dic": "dec"
    }
    series = series.str.lower()
    for esp, eng in traducciones.items():
        series = series.str.lowercase().replace(f"-{esp}-", f"-{eng}-", regex=False)
    return pd.to_datetime(series, format="%d-%b-%y")

# === CONFIGURACIÓN ===
#archivo_csv = "data.csv"  # POZO1 ECUADOR
archivo_csv = "pozoSin94.csv"  #POZO 2 VENEZUELA

columna_objetivo = "RateOil"
n_simulaciones = 1000
n_meses = 60
simulaciones_visibles = 20

timeColumnName = "Tiempo"
inputDateFormatVEN = "%d-%b-%y" # formato dateset EC
inputDateFormatEC = "%d/%m/%Y" # formateo dataset VEN

# === CARGA DE DATOS ===
fullDf = pd.read_csv(archivo_csv, sep=";")
targetColumns = ["Tiempo", "RateOil"]
df = fullDf[targetColumns].copy()
df[timeColumnName] = pd.to_datetime(df[timeColumnName], dayfirst=True ) #Se transforma fecha
df[columna_objetivo] = df[columna_objetivo].astype(str).str.replace(",", ".", regex=False) # se convierte valores de rateoil a string y luego a número
df[columna_objetivo] = pd.to_numeric(df[columna_objetivo], errors='coerce')
df = df.dropna(subset=[columna_objetivo])

# === DIVISIÓN EN ENTRENAMIENTO Y VALIDACIÓN ===
df = df.sort_values(timeColumnName).reset_index(drop=True)
midpoint = len(df) // 2
df_train = df.iloc[:midpoint].copy()
df_valid = df.iloc[midpoint:].copy()

# === CÁLCULO DE INCREMENTOS MENSUALES ===
df_train["Delta"] = df_train[columna_objetivo].diff()
delta_mean = df_train["Delta"].mean()
delta_std = df_train["Delta"].std()

# === TIEMPO FUTURO ===
fecha_inicial_sim = df_train[timeColumnName].iloc[-1]
n_meses = len(df_valid)  # ajustamos al largo de la validación
fechas_futuras = pd.date_range(start=fecha_inicial_sim + pd.DateOffset(months=1), periods=n_meses, freq='MS')


# === SIMULACIONES MONTE CARLO SOBRE INCREMENTOS ===
simulaciones = np.zeros((n_simulaciones, n_meses))
valor_inicial = df_train[columna_objetivo].iloc[-1]

for i in range(n_simulaciones):
    valores = [valor_inicial]
    for _ in range(n_meses - 1):
        incremento = np.random.normal(delta_mean, delta_std)
        siguiente = max(valores[-1] + incremento, 0)  # evitar valores negativos
        valores.append(siguiente)
    simulaciones[i] = valores

# === COMPARACIÓN CON VALIDACIÓN ===
valid_real = df_valid[columna_objetivo].values
errors = np.linalg.norm(simulaciones - valid_real, axis=1) # cálculo del error cuadrático total entre cada simulación y la curva real
idx_mejor = np.argmin(errors) # simulación con menor error, la más cercana a la curva real
mejor_simulacion = simulaciones[idx_mejor]

# === PERCENTILES ===
p10 = np.percentile(simulaciones, 10, axis=0)
p50 = np.percentile(simulaciones, 50, axis=0)
p90 = np.percentile(simulaciones, 90, axis=0)


#========== SIMULACIÓN HACIA EL FUTURO =================
valor_inicial_futuro = df[columna_objetivo].iloc[-1]
n_meses_futuro = 60  # o cualquier número de meses a futuro
fechas_futuras_futuro = pd.date_range(start=df[timeColumnName].iloc[-1] + pd.DateOffset(months=1), periods=n_meses_futuro, freq='MS')
simulaciones_futuro = np.zeros((n_simulaciones, n_meses_futuro))
for i in range(n_simulaciones):
    valores = [valor_inicial_futuro]
    for _ in range(n_meses_futuro - 1):
        incremento = np.random.normal(delta_mean, delta_std)
        siguiente = max(valores[-1] + incremento, 0)
        valores.append(siguiente)
    simulaciones_futuro[i] = valores

p10_futuro = np.percentile(simulaciones_futuro, 10, axis=0)
p50_futuro = np.percentile(simulaciones_futuro, 50, axis=0)
p90_futuro = np.percentile(simulaciones_futuro, 90, axis=0)

    


# === GRAFICA 1: Curvas + Percentiles + Mejor ajuste ===
plt.figure(figsize=(14, 7))
plt.plot(df[timeColumnName], df[columna_objetivo], label="Histórico completo", color='black', linewidth=2)
colors = plt.cm.viridis(np.linspace(0, 1, simulaciones_visibles))
for i, color in zip(range(simulaciones_visibles), colors):
    plt.plot(fechas_futuras, simulaciones[i], color=color, alpha=0.3)

plt.plot(fechas_futuras, mejor_simulacion, label="Simulación más cercana", color='red', linewidth=2)
plt.plot(fechas_futuras, p10, label="P10", color='blue', linestyle="--", linewidth=2)
plt.plot(fechas_futuras, p50, label="P50 (Mediana)", color='green', linestyle="-", linewidth=2)
plt.plot(fechas_futuras, p90, label="P90", color='purple', linestyle="--", linewidth=2)
plt.title("Simulación Monte Carlo vs Validación histórica")
plt.xlabel("Fecha")
plt.ylabel("RateOil (bpd)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()


# ===== PREDICCIÓN AL FUTURO ==========
plt.figure(figsize=(14, 7))
plt.plot(df[timeColumnName], df[columna_objetivo], label="Histórico", color='black', linewidth=2)
for i in range(simulaciones_visibles):
    plt.plot(fechas_futuras_futuro, simulaciones_futuro[i], alpha=0.3)

plt.plot(fechas_futuras_futuro, p10_futuro, label="P10", linestyle="--", color='blue')
plt.plot(fechas_futuras_futuro, p50_futuro, label="P50", color='green')
plt.plot(fechas_futuras_futuro, p90_futuro, label="P90", linestyle="--", color='red')
plt.title("Proyección Monte Carlo hacia el futuro")
plt.xlabel("Fecha")
plt.ylabel("RateOil (bpd)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()


# === GRAFICA 2: EUR ===

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
