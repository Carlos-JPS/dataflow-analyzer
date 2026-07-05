# DataFlow Analyzer 🌦️🛸

**DataFlow Analyzer** es una librería en Python diseñada para el procesamiento, análisis y visualización de perfiles atmosféricos. Su objetivo principal es facilitar la comparación de datos obtenidos por **Drones (UAVs)** frente a **Radiosondas** meteorológicas.

## 🚀 Características Principales

- **Ingesta de Datos Robusta**:
  - Soporte para CSVs de Drones (con limpieza automática de duplicados y metadatos).
  - Soporte para XMLs de Radiosondas (con aplanado automático de estructuras anidadas).
  - Manejo inteligente de zonas horarias y formatos de fecha.
- **Procesamiento Científico (`DataProcessor`)**:
  - **Filtrado de Tiempo**: Selección precisa de rangos con soporte timezone-aware.
  - **Binning Vertical**: Agrupación de datos por intervalos de altitud o presión.
  - **Suavizado (Splines)**: Interpolación suave para eliminar el ruido de alta frecuencia del dron.
- **Visualización Profesional (`DataVisualizer`)**:
  - **Perfiles Verticales**: Gráficos de Temperatura/Humedad vs Altitud.
  - **Comparativas**: Estilos visuales distintos para superponer Dron vs Sonda.
  - **Análisis de Viento**: Perfil vertical con barbas meteorológicas (Wind Barbs) indicando velocidad y dirección.
  - **Series de Tiempo**: Análisis de variables a lo largo de la misión.
- **Testeo Riguroso**: Batería completa de tests unitarios con `pytest`.

## 📦 Instalación

El proyecto utiliza `uv` o `pip` estándar. Se recomienda instalar en modo editable:

```bash
# Crear entorno virtual (opcional pero recomendado)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instalar dependencias y la librería
pip install -e .[test]
```

## 📓 Uso en Google Colab / DataSpell

Para usar la librería en notebooks sin necesidad de subir archivos manualmente, puedes instalarla directamente desde el repositorio:

### Google Colab

En una celda de código, ejecuta:

```python
!pip install git+https://github.com/Carlos-JPS/dataflow-analyzer.git@main
```

### DataSpell / Jupyter Lab Local

Simplemente instala la librería en tu entorno activo (terminal):

```bash
pip install git+https://github.com/Carlos-JPS/dataflow-analyzer.git@main
```

Una vez instalada, puedes importar los módulos y usar los datos de muestra incluidos:

```python
from dataflow_analyzer.data_source import CSVSource
import importlib.resources

# Usar datos de ejemplo
with importlib.resources.path("dataflow_analyzer.sample_data", "dron_sample.csv") as p:
    dron = CSVSource(str(p)).load(pivot=True)
    dron.df.head()
```

### Opción C: Instalación Offline (Wheel)

Si prefieres compartir el archivo `.whl` directamente:

1.  Generar el instalador `.whl`:

    ```bash
    pip install build
    python -m build
    ```

    Esto creará una carpeta `dist/` con el archivo `dataflow_analyzer-0.1.0-py3-none-any.whl`.

2.  Instalar en Colab/DataSpell:
    (Sube el archivo `.whl` a tus archivos del notebook y ejecuta):
    ```bash
    pip install dataflow_analyzer-0.1.0-py3-none-any.whl
    ```

## 🛠️ Uso Básico

### 1. Cargar Datos

```python
from dataflow_analyzer.data_source import CSVSource, XMLSource

# Cargar datos de Dron (CSV)
# pivot=True si los datos vienen en formato 'long' (ej. exportación de InfluxDB)
dron_loader = CSVSource("ruta/al/dron.csv")
dron_loader.load(pivot=True)
df_dron = dron_loader.df

# Cargar datos de Sonda (XML)
sonda_loader = XMLSource("ruta/a/sonda.xml")
sonda_loader.load() # Infiere raíz automáticamente
df_sonda = sonda_loader.df
```

### 2. Generar Gráficos

#### Comparación de Perfiles

```python
from dataflow_analyzer.visualization import DataVisualizer

viz = DataVisualizer()
viz.compare_profiles(
    df1=df_dron, label1="Dron",
    df2=df_sonda, label2="Sonda",
    x_col='presion',       # Eje Común (Vertical en Meteorología)
    y1_col='altitude',     # Eje Izquierdo
    y2_col='temperatura',  # Eje Derecho
    title="Comparativa Dron vs Sonda",
    smooth=True            # Activar suavizado Spline
)
```

#### Perfil de Viento

```python
viz.plot_wind_profile(
    df=df_dron,
    alt_col='altitude',
    speed_col='velocidadViento',
    dir_col='direccionViento',
    BarbInterval=50 # Una barba cada 50m
)
```

## 🧪 Ejecutar Tests

El proyecto cuenta con una suite de tests robusta. Para ejecutarla:

```bash
pytest
```

## 📂 Demos

Puedes ver ejemplos funcionales en la carpeta `demos/`:

- `demo_comparison.py`: Comparativa completa y ajustada entre datos de Dron y Sonda.
- `demo_wind.py`: Generación del perfil de viento con barbas meteorológicas.
