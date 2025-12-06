from abc import ABC, abstractmethod
from typing import Optional, Union, List, Any
import pandas as pd
import polars as pl
import logging
from .data_source import DataSource

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MergeStrategy(ABC):
    """
    Estrategia base para combinar datos de dos fuentes distintas.
    """
    
    @abstractmethod
    def merge(self, left: DataSource, right: DataSource, **kwargs) -> pd.DataFrame:
        """
        Combina los datos de dos fuentes.
        
        Args:
            left: Fuente de datos principal (ej: Dron)
            right: Fuente de datos secundaria (ej: Sonda)
            **kwargs: Argumentos específicos de la estrategia
            
        Returns:
            pd.DataFrame: DataFrame combinado
        """
        pass

class ExactMergeStrategy(MergeStrategy):
    """
    Estrategia de merge exacto (inner, outer, left, right) basada en índices o columnas idénticas.
    """
    def merge(self, left: DataSource, right: DataSource, on: Optional[str] = None, how: str = "inner", **kwargs) -> pd.DataFrame:
        df_left = left.df
        df_right = right.df
        
        logger.info(f"Ejecutando Exact Merge (how={how})")
        
        if on:
            return pd.merge(df_left, df_right, on=on, how=how, **kwargs)
        else:
            # Merge por índice
            return pd.merge(df_left, df_right, left_index=True, right_index=True, how=how, **kwargs)

class ContinuousMergeStrategy(MergeStrategy):
    """
    Estrategia avanzada para alinear datos basados en variables continuas (Tiempo, Presión, Altitud).
    Utiliza 'merge_asof' para encontrar coincidencias cercanas.
    """
    def merge(self, left: DataSource, right: DataSource, on: str, direction: str = "nearest", tolerance: Optional[float] = None, suffixes: tuple = ('_dron', '_sonda'), **kwargs) -> pd.DataFrame:
        """
        Args:
            on: Nombre de la columna continua (ej: 'presion', 'altitude', 'time')
            direction: 'nearest', 'forward', 'backward'
            tolerance: Tolerancia máxima de diferencia para considerar un match.
            suffixes: Sufijos para columnas con mismo nombre.
        """
        df_left = left.df.copy()
        df_right = right.df.copy()
        
        logger.info(f"Ejecutando Continuous Merge en '{on}' (direction={direction}, tolerance={tolerance})")
        
        # 1. Preparar las columnas de cruce
        # Si 'on' es el índice, lo sacamos a columna para poder ordenar
        left_on_col = on
        right_on_col = on
        
        if on == "time" and isinstance(df_left.index, pd.DatetimeIndex):
             df_left = df_left.reset_index()
        if on == "time" and isinstance(df_right.index, pd.DatetimeIndex):
             df_right = df_right.reset_index()
             
        # Verificar que la columna existe
        if on not in df_left.columns:
            raise ValueError(f"Columna '{on}' no encontrada en la fuente izquierda.")
        if on not in df_right.columns:
            raise ValueError(f"Columna '{on}' no encontrada en la fuente derecha.")
            
        # 2. Coercer tipos para evitar errores de int vs float
        # Si la columna es numérica, forzar a float
        try:
            if pd.api.types.is_numeric_dtype(df_left[on]):
                df_left[on] = df_left[on].astype(float)
            if pd.api.types.is_numeric_dtype(df_right[on]):
                df_right[on] = df_right[on].astype(float)
        except Exception as e:
            logger.warning(f"No se pudo coercer tipos numéricos en '{on}': {e}")

        # 3. Ordenar es REQUISITO para merge_asof
        df_left = df_left.sort_values(by=on)
        df_right = df_right.sort_values(by=on)
        
        # 4. Ejecutar Merge AsOf
        try:
            merged_df = pd.merge_asof(
                df_left, 
                df_right, 
                on=on, 
                direction=direction, 
                tolerance=tolerance,
                suffixes=suffixes
            )
            return merged_df
        except Exception as e:
            logger.error(f"Error en merge_asof: {e}")
            raise
