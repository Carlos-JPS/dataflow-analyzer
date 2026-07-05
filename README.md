# DataFlow Analyzer

DataFlow Analyzer es una librería de Python para procesar y visualizar perfiles
atmosféricos obtenidos mediante drones y radiosondas.

El proyecto permite leer mediciones desde archivos CSV y XML, aplicar
transformaciones comunes sobre series meteorológicas y comparar perfiles de
altitud, presión, temperatura y viento.

## Funcionalidades

- Lectura de archivos CSV estándar y exportaciones CSV de InfluxDB.
- Conversión de datos desde formato largo a formato ancho.
- Agregación de registros con marcas de tiempo duplicadas.
- Lectura de radiosondas desde XML con datos en atributos o elementos hijos.
- Filtrado por intervalos de tiempo, incluyendo datos con zona horaria.
- Agrupación por intervalos de altitud, presión u otra variable continua.
- Interpolación mediante splines para suavizar perfiles.
- Combinación exacta o aproximada de fuentes mediante `merge` y `merge_asof`.
- Gráficos de perfiles verticales, series de tiempo y perfiles de viento.

## Componentes

| Módulo | Responsabilidad |
| --- | --- |
| `data_source.py` | Carga de fuentes CSV y XML. |
| `processing.py` | Filtrado, agrupación e interpolación de datos. |
| `strategies.py` | Alineación exacta o aproximada entre fuentes. |
| `visualization.py` | Creación de perfiles, comparaciones y series de tiempo. |

## Requisitos

- Python 3.9 o superior.
- pandas, Polars, lxml, SciPy, Matplotlib y Seaborn.

## Instalación

Para trabajar con una copia local del proyecto:

```bash
git clone https://github.com/Carlos-JPS/dataflow-analyzer.git
cd dataflow-analyzer
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
```

En Windows, la activación del entorno virtual se realiza con:

```powershell
.venv\Scripts\activate
```

La librería también se puede instalar directamente desde GitHub:

```bash
pip install "git+https://github.com/Carlos-JPS/dataflow-analyzer.git@main"
```

En Google Colab, anteponer `!` al mismo comando:

```python
!pip install git+https://github.com/Carlos-JPS/dataflow-analyzer.git@main
```

## Uso básico

### Cargar datos

```python
from dataflow_analyzer.data_source import CSVSource, XMLSource

# CSV de un dron. pivot=True convierte una exportación de InfluxDB
# desde formato largo a formato ancho.
dron = CSVSource("datos/dron.csv").load(pivot=True)
df_dron = dron.df

# XML de una radiosonda.
sonda = XMLSource("datos/sonda.xml").load()
df_sonda = sonda.df
```

Los nombres predeterminados para un CSV en formato largo son `_time`, `_field`
y `_value`. Se pueden cambiar mediante los argumentos de `CSVSource.load()`.
Para XML, los valores predeterminados son `Row` como elemento de cada registro y
`DataSrvTime` como campo temporal.

### Procesar datos

```python
from dataflow_analyzer.processing import DataProcessor

df_filtrado = DataProcessor.filter_by_time(
    df_dron,
    start="2025-01-01 10:00:00",
    end="2025-01-01 11:00:00",
)

df_agrupado = DataProcessor.bin_data(
    df_filtrado,
    bin_col="altitude",
    value_cols=["presion", "temperatura"],
    bin_size=10,
)
```

### Generar un perfil de viento

```python
from dataflow_analyzer.visualization import DataVisualizer

visualizer = DataVisualizer()
visualizer.plot_wind_profile(
    df=df_dron,
    alt_col="altitude",
    speed_col="velocidadViento",
    dir_col="direccionViento",
    BarbInterval=50,
    save_path="perfil_viento.png",
)
```

Los gráficos pueden guardarse en los formatos admitidos por Matplotlib, como
PNG, PDF o SVG, utilizando el argumento `save_path`.

## Ejemplos

El repositorio incluye datos de muestra y dos programas ejecutables:

```bash
python demos/demo_comparison.py
python demos/demo_wind.py
```

- `demo_comparison.py` compara perfiles de presión, altitud y temperatura de
  un dron y una radiosonda.
- `demo_wind.py` genera un perfil vertical de velocidad y dirección del viento.

## Pruebas

Las pruebas unitarias cubren la carga de fuentes, las transformaciones y la
creación de visualizaciones.

```bash
pytest
```

## Alcance actual

La librería carga archivos locales, pero no consulta directamente una instancia
de InfluxDB. Tampoco incluye una capa propia para exportar datos tabulares. Los
resultados son objetos `DataFrame`, por lo que pueden exportarse mediante los
métodos de pandas, por ejemplo `to_csv()` o `to_json()`. La exportación a Excel
con `to_excel()` requiere instalar un motor compatible, como `openpyxl`.

## Autor

[Carlos Pradenas Sepúlveda](https://github.com/Carlos-JPS)
