# Simulación comparativa de muestreo por rechazo vs RML-DDHM con archivo CSV
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import Ridge
import os

# Verificación de ruta correcta del archivo
file_path = "pozoSin94.csv"
if not os.path.exists(file_path):
    file_path = "/mnt/data/pozoSin94.csv"
if not os.path.exists(file_path):
    raise FileNotFoundError("El archivo 'pozoSin94.csv' no se encuentra en el directorio actual ni en /mnt/data")

# Leer CSV
df = pd.read_csv(file_path)

# Filtrar datos válidos
df = df[["Tiempo", "RateOil"]].dropna()
df = df[df["RateOil"] > 0]  # Filtrar datos positivos

# Variable objetivo: producción observada
true_production = df["RateOil"].values
N_timesteps = len(true_production)

# Simular modelos previos (100 simulaciones con ruido)
N_models = 100
simulated_models = np.array([
    true_production + np.random.normal(0, 80, N_timesteps)
    for _ in range(N_models)
])

# ----- Monte Carlo por rechazo -----
accepted_models = []
thresh = 2_500_000  # Umbral de error aceptable
for model in simulated_models:
    error = np.sum((model - true_production) ** 2)
    if error < thresh:
        accepted_models.append(model)

accepted_models = np.array(accepted_models)

# ----- RML-DDHM (combinación lineal) -----
X = simulated_models.T  # cada columna es un modelo
y = true_production

ridge = Ridge(alpha=1.0)
ridge.fit(X, y)
weights = ridge.coef_

pred_rml_ddhm = np.dot(X, weights)

# Simulaciones RML con ruido (10 muestras)
rml_predictions = []
for _ in range(10):
    noise = np.random.normal(0, 20, len(y))
    y_noisy = y + noise
    ridge.fit(X, y_noisy)
    rml_predictions.append(np.dot(X, ridge.coef_))

rml_predictions = np.array(rml_predictions)

# ----- Gráficos -----
plt.figure(figsize=(12,6))
plt.plot(true_production, label="Producción Real", linewidth=3, color='black')
if len(accepted_models) > 0:
    plt.plot(np.percentile(accepted_models, 50, axis=0), label="MC-Rechazo P50", linestyle='--', color='blue')
    plt.fill_between(range(N_timesteps),
                     np.percentile(accepted_models, 10, axis=0),
                     np.percentile(accepted_models, 90, axis=0),
                     alpha=0.2, color='blue', label="MC-Rechazo P10-P90")

plt.plot(np.percentile(rml_predictions, 50, axis=0), label="RML-DDHM P50", linestyle='--', color='green')
plt.fill_between(range(N_timesteps),
                 np.percentile(rml_predictions, 10, axis=0),
                 np.percentile(rml_predictions, 90, axis=0),
                 alpha=0.2, color='green', label="RML-DDHM P10-P90")

plt.xlabel("Índice de Tiempo")
plt.ylabel("Tasa de Producción de Petróleo (bls/d)")
plt.title("Comparación Monte Carlo vs RML-DDHM usando datos reales")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
