import logging
import pandas as pd
import os
import importlib.resources

from dataflow_analyzer.data_source import CSVSource
from dataflow_analyzer.visualization import DataVisualizer
from dataflow_analyzer.processing import DataProcessor

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("--- Demo: Perfil de Viento ---")
    
    # --- 2. Encontrar la ruta a los datos de forma robusta ---
    with importlib.resources.path("dataflow_analyzer.sample_data", "dron_sample.csv") as p:
        csv_path = str(p)

    # 1. Cargar Dron
    print(f"\n1. Cargando Datos ({csv_path})...")
    dron = CSVSource(csv_path).load(pivot=True)
    df = dron.df.copy()

    # 2. Limpieza y Filtrado de Datos
    print("\n2. Limpiando y filtrando datos para un perfil coherente...")

    # Filtrar outliers de altitud
    df_clean = df[(df['altitude'] > 0) & (df['altitude'] < 1200)].copy()

    # Aislar fase de descenso
    if len(df_clean) > 100:
        idx_max_alt = df_clean['altitude'].idxmax()
        df_descent = df_clean.loc[idx_max_alt:].copy()
    else:
        df_descent = df_clean
    print(f"   Datos listos para graficar (fase de descenso): {len(df_descent)} registros.")

    # 3. Graficar perfil de viento
    print("\n3. Generando Perfil de Viento con datos limpios...")
    viz = DataVisualizer()

    viz.plot_wind_profile(
        df=df_descent,
        alt_col='altitude',
        speed_col='velocidadViento',
        dir_col='direccionViento',
        title="Perfil de Viento - Fase de Descenso",
        save_path="perfil_viento.png",
        BarbInterval=50
    )

    print("\nGrafico guardado en: perfil_viento.png")

if __name__ == "__main__":
    main()
