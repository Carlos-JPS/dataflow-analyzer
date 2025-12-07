import logging
import pandas as pd
import numpy as np
import os
import importlib.resources

from dataflow_analyzer.data_source import CSVSource, XMLSource
from dataflow_analyzer.visualization import DataVisualizer
from dataflow_analyzer.processing import DataProcessor

# Configurar logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("--- Demo Comparacion: Dron vs Sonda ---")

    # --- 2. Encontrar la ruta a los datos de forma robusta ---
    with importlib.resources.path("dataflow_analyzer.sample_data", "dron_sample.csv") as p:
        csv_path = str(p)
    with importlib.resources.path("dataflow_analyzer.sample_data", "sonda_sample.xml") as p:
        xml_path = str(p)
    
    # 1. Cargar Dron
    print(f"\n1. Cargando Dron ({csv_path})...")
    dron = CSVSource(csv_path).load(pivot=True)
    df_dron = dron.df.copy()
    
    # Limpieza Dron (Idéntica a otros demos)
    # Filtrar altitud valida
    df_dron = df_dron[(df_dron['altitude'] > 0) & (df_dron['altitude'] < 1500)]
    # Filtrar Fase de Descenso
    # NOTA: Con datos de muestra podria no haber un pico si es solo el inicio.
    # Ajustamos la logica para usar lo que tengamos si es pequeno.
    if len(df_dron) > 100:
        idx_peak = df_dron['altitude'].idxmax()
        df_dron = df_dron.loc[idx_peak:]
    else:
        print("   Nota: Dataset pequeño, omitiendo deteccion de fase de descenso.")
    
    print(f"   Dron (Procesado): {len(df_dron)} filas. Rango Presion: {df_dron['presion'].min():.1f} - {df_dron['presion'].max():.1f} hPa")

    # 2. Cargar Sonda
    print(f"\n2. Cargando Sonda ({xml_path})...")
    sonda = XMLSource(xml_path).load()
    df_sonda = sonda.df.copy()
    
    # Limpieza Sonda
    # Kelvin -> Celsius
    if 'Temperature' in df_sonda.columns:
        df_sonda['Temperature_C'] = df_sonda['Temperature'] - 273.15
    else:
        df_sonda['Temperature_C'] = np.nan
        
    print(f"   Sonda (Total): {len(df_sonda)} filas. Rango Presion: {df_sonda['Pressure'].min():.1f} - {df_sonda['Pressure'].max():.1f} hPa")

    # 3. Recortar Sonda al rango del Dron (Comparacion justa)
    # Renombrar columnas para coincidir con Dron
    df_sonda.rename(columns={
        'Pressure': 'presion',
        'Altitude': 'altitude',
        'Temperature_C': 'temperatura'
    }, inplace=True)
    
    # Usamos el rango de presion del Dron con un margen de 5 hPa
    min_p = df_dron['presion'].min() - 5
    max_p = df_dron['presion'].max() + 5
    
    df_sonda_crop = df_sonda[
        (df_sonda['presion'] >= min_p) & 
        (df_sonda['presion'] <= max_p)
    ].copy()
    
    print(f"   Sonda (Recortada al Dron): {len(df_sonda_crop)} filas")

    # 4. Generar Grafico Comparativo
    print("\n3. Generando Grafico Comparativo...")
    viz = DataVisualizer()
    output_file = "comparacion_sonda_dron.png"
    
    viz.compare_profiles(
        df1=df_sonda_crop, label1="Sonda",
        df2=df_dron, label2="Dron",
        x_col='presion', 
        y1_col='altitude',
        y2_col='temperatura',
        title="Comparacion Sonda vs Dron (Fase Descenso)",
        save_path=output_file,
        bin_size=1.0,
        smooth=True,
        xlabel='Presion (hPa)',
        y1_label='Altitud (m)',
        y2_label='Temperatura (degC)'
    )

    if os.path.exists(output_file):
        print(f"\nGrafico guardado en: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    main()
