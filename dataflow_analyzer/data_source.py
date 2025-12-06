from abc import ABC, abstractmethod
from typing import Optional, Union, List, Any, Dict
import pandas as pd
import polars as pl
from pathlib import Path
import logging
from lxml import etree

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataSource(ABC):
    """
    Clase base abstracta para todas las fuentes de datos.
    Define la interfaz que deben implementar CSVSource, XMLSource, InfluxSource, etc.
    """
    
    def __init__(self, name: str):
        self.name = name
        self._df: Optional[Union[pd.DataFrame, pl.DataFrame]] = None
        self._engine: str = "pandas" # default engine

    @property
    def df(self) -> Union[pd.DataFrame, pl.DataFrame]:
        if self._df is None:
            raise ValueError(f"Los datos no han sido cargados para la fuente {self.name}. Ejecute load() primero.")
        return self._df

    @abstractmethod
    def load(self, engine: str = "pandas", **kwargs) -> 'DataSource':
        """
        Carga los datos desde la fuente.
        Returns: self
        """
        pass

    def get_time_range(self) -> tuple[Any, Any]:
        """Retorna (min_time, max_time) de los datos cargados."""
        if self._df is None:
            return (None, None)
        
        if isinstance(self._df, pd.DataFrame):
            if isinstance(self._df.index, pd.DatetimeIndex):
                return (self._df.index.min(), self._df.index.max())
            elif "time" in self._df.columns:
                 return (self._df["time"].min(), self._df["time"].max())
            return (None, None)
        return (None, None)


class CSVSource(DataSource):
    """
    Manejador de fuentes CSV, con soporte especializado para exportaciones de InfluxDB.
    """
    def __init__(self, path: str, name: Optional[str] = None):
        self.path = Path(path)
        name = name or self.path.stem
        super().__init__(name)
    
    def load(self, engine: str = "pandas", time_col: str = "_time", field_col: str = "_field", value_col: str = "_value", pivot: bool = True, aggregation: str = "mean", **kwargs) -> 'CSVSource':
        self._engine = engine
        
        # 1. Detectar líneas de metadatos de InfluxDB (empiezan con #)
        skiprows = 0
        try:
            with open(self.path, 'r') as f:
                for i, line in enumerate(f):
                    if line.strip().startswith('#'):
                        skiprows += 1
                    else:
                        break
        except Exception as e:
            logger.error(f"Error leyendo archivo {self.path}: {e}")
            raise

        logger.info(f"Cargando CSV: {self.path} (skiprows={skiprows})")

        # 2. Cargar Datos
        if engine == "pandas":
            df = pd.read_csv(self.path, skiprows=skiprows, **kwargs)
            df.columns = df.columns.str.strip()
            
            # 3. Procesar Tiempo
            if time_col in df.columns:
                df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
                df = df.dropna(subset=[time_col])
                df.set_index(time_col, inplace=True)
                df.index.name = "time"
            
            # 4. Formato Largo -> Ancho (Pivoting)
            if pivot and field_col in df.columns and value_col in df.columns:
                logger.info(f"Pivoteando datos usando '{field_col}'...")
                if df.index.duplicated().any():
                    logger.info(f"Timestamps duplicados detectados. Agregando con: {aggregation}")
                    df = df.pivot_table(index="time", columns=field_col, values=value_col, aggfunc=aggregation)
                else:
                    df = df.pivot(columns=field_col, values=value_col)
                df.columns.name = None
            
            self._df = df
            
        elif engine == "polars":
            df = pl.read_csv(self.path, skip_rows=skiprows)
            self._df = df
            
        return self

class XMLSource(DataSource):
    """
    Fuente de datos para archivos XML (Sonda).
    """
    def __init__(self, path: str, name: Optional[str] = None):
        self.path = Path(path)
        name = name or self.path.stem
        super().__init__(name)

    def load(self, engine: str = "pandas", xpath_root: str = "Row", time_col: str = "DataSrvTime", **kwargs) -> 'XMLSource':
        """
        Carga datos desde XML.
        Soporta estructuras donde los datos están en atributos (<Row Attr="Val"/>) o en sub-tags.
        
        Args:
            xpath_root: Tag nombre de los elementos fila (ej: 'Row').
            time_col: Nombre del atributo/tag que contiene la fecha/hora.
        """
        self._engine = engine
        logger.info(f"Cargando XML: {self.path}")
        
        try:
            tree = etree.parse(str(self.path))
            root = tree.getroot()
        except Exception as e:
            raise ValueError(f"Error parseando XML: {e}")

        data = []
        # Buscar elementos usando xpath relativo
        elements = root.findall(f".//{xpath_root}") if xpath_root else list(root)
        
        if not elements:
            logger.warning(f"No se encontraron elementos con tag '{xpath_root}'. Intentando iterar hijos directos.")
            elements = list(root)

        for elem in elements:
            # Primero intentar obtener atributos
            row = dict(elem.attrib)
            
            # Si no hay atributos, buscar en hijos directos (estructura anidada)
            if not row:
                for child in elem:
                    if child.text:
                        row[child.tag] = child.text
            
            data.append(row)

        if not data:
            logger.warning("El archivo XML no generó filas. Verifique el xpath_root.")
        
        if engine == "pandas":
            df = pd.DataFrame(data)
            
            # Auto-detectar columnas numéricas (optimizado)
            for col in df.columns:
                # Intentar convertir a numero, ignorando errores para columnas de texto
                df[col] = pd.to_numeric(df[col], errors='ignore')
            
            # Procesar Tiempo
            if time_col in df.columns:
                df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
                df = df.dropna(subset=[time_col])
                df.set_index(time_col, inplace=True)
                df.index.name = "time"
            else:
                logger.warning(f"Columna de tiempo '{time_col}' no encontrada en el XML. Columnas: {df.columns.tolist()}")

            self._df = df
            
        return self
