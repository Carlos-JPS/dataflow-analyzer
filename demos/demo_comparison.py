import logging
import pandas as pd
import numpy as np
import os
from dataflow_analyzer.data_source import CSVSource, XMLSource
from dataflow_analyzer.visualization import DataVisualizer

# Configurar logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("--- 🚀 Demo Comparación: Dron vs Sonda ---")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Cargar Dron
    csv_path = os.path.join(base_dir, "../../drone", "drone-data-27-11-2025.csv")
    print(f"\n1. Cargando Dron ({csv_path})...")
    dron = CSVSource(csv_path).load(pivot=True)
    df_dron = dron.df.copy()
    
    # Limpieza Dron (Idéntica a demo_plot.py)
    # Filter valid altitude
    df_dron = df_dron[(df_dron['altitude'] > 0) & (df_dron['altitude'] < 1500)]
    # Filter Descent Phase
    idx_peak = df_dron['altitude'].idxmax()
    df_dron = df_dron.loc[idx_peak:]
    print(f"   Dron (Descenso): {len(df_dron)} filas. Rango Presión: {df_dron['presion'].min():.1f} - {df_dron['presion'].max():.1f} hPa")

    # 2. Cargar Sonda
    xml_path = os.path.join(base_dir, "../../temp_sonda_data", "SynchronizedSoundingData.xml")
    print(f"\n2. Cargando Sonda ({xml_path})...")
    sonda = XMLSource(xml_path).load()
    df_sonda = sonda.df.copy()
    
    # Limpieza Sonda
    # Kelvin -> Celsius
    if 'Temperature' in df_sonda.columns:
        df_sonda['Temperature_C'] = df_sonda['Temperature'] - 273.15
    else:
        df_sonda['Temperature_C'] = np.nan
        
    print(f"   Sonda (Total): {len(df_sonda)} filas. Rango Presión: {df_sonda['Pressure'].min():.1f} - {df_sonda['Pressure'].max():.1f} hPa")

    # 3. Recortar Sonda al rango del Dron (Comparación justa)
    # Renombrar columnas para coincidir con Dron
    df_sonda.rename(columns={
        'Pressure': 'presion',
        'Altitude': 'altitude',
        'Temperature_C': 'temperatura'
    }, inplace=True)
    
    # Usamos el rango de presión del Dron con un margen de 5 hPa
    min_p = df_dron['presion'].min() - 5
    max_p = df_dron['presion'].max() + 5
    
    df_sonda_crop = df_sonda[
        (df_sonda['presion'] >= min_p) & 
        (df_sonda['presion'] <= max_p)
    ].copy()
    
    print(f"   Sonda (Recortada al Dron): {len(df_sonda_crop)} filas")

    # 4. Generar Gráfico Comparativo
    print("\n3. Generando Gráfico Comparativo...")
    viz = DataVisualizer()
    output_file = "comparacion_dron_sonda.png"
    
    viz.compare_profiles(
        df1=df_dron, label1="Dron",
        df2=df_sonda_crop, label2="Sonda",
        x_col='presion', 
        y1_col='altitude',
        y2_col='temperatura',
        title="Comparación Dron vs Sonda (Fase Descenso)",
        save_path=output_file,
        bin_size=1.0,
        smooth=True,
        xlabel='Presión (hPa)',
        y1_label='Altitud (m)',
        y2_label='Temperatura (°C)'
    )
    # NOTE: El código fallará si las columnas no se llaman igual.
    # Voy a ajustar los nombres del DF Sonda aquí mismo.

    if os.path.exists(output_file):
        print(f"\n✅ Gráfico guardado en: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    main()
