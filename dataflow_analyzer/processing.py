import pandas as pd
import numpy as np
import logging
from typing import Any, Optional

try:
    from scipy.interpolate import make_interp_spline
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Encapsula lógica de transformación y limpieza de datos.
    Sigue el Principio de Responsabilidad Única (SRP), separando
    el 'cálculo' de la 'visualización'.
    """

    @staticmethod
    def filter_by_time(
        df: pd.DataFrame, 
        start: Any, 
        end: Any, 
        time_col: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Filtra un DataFrame por rango de tiempo.
        Maneja strings, datetimes y zonas horarias (naive vs aware).
        """
        if df.empty:
            return df
            
        # Determinar series de tiempo
        if time_col:
            if time_col not in df.columns:
                logger.warning(f"Columna de tiempo '{time_col}' no encontrada.")
                return df
            times = pd.to_datetime(df[time_col])
        else:
            times = pd.to_datetime(df.index)
            
        # Normalizar start/end a timestamps pd.Timestamp
        try:
            ts_start = pd.to_datetime(start)
            ts_end = pd.to_datetime(end)
        except Exception as e:
            logger.error(f"Error convirtiendo fechas start/end: {e}")
            return df

        # Manejo de Timezones
        data_tz = getattr(times.dtype, 'tz', None)
        start_tz = getattr(ts_start, 'tz', None)
        end_tz = getattr(ts_end, 'tz', None)
        
        # Lógica de alineación de TZ
        # Si datos tienen TZ y filtro no -> Localizamos el filtro a la TZ de los datos
        if data_tz and not start_tz:
             ts_start = ts_start.tz_localize(data_tz)
        # Si datos no tienen TZ y filtro sí -> Convertimos filtro a UTC y removemos TZ (o convertimos a naive directamente)
        elif not data_tz and start_tz:
             ts_start = ts_start.tz_convert(None)
             
        if data_tz and not end_tz:
            ts_end = ts_end.tz_localize(data_tz)
        elif not data_tz and end_tz:
             ts_end = ts_end.tz_convert(None)

        # Crear máscara
        mask = (times >= ts_start) & (times <= ts_end)
        return df[mask].copy()

    @staticmethod
    def bin_data(
        df: pd.DataFrame, 
        bin_col: str, 
        value_cols: list[str], 
        bin_size: float
    ) -> pd.DataFrame:
        """
        Agrupa y promedia datos en intervalos (bins) de una columna referencia.
        """
        if bin_size <= 0:
            return df
            
        logger.info(f"Procesando: Binning por '{bin_col}' cada {bin_size}")
        df_binned = df.copy()
        
        # Crear bins
        df_binned['bin_idx'] = (df_binned[bin_col] // bin_size) * bin_size + (bin_size / 2)
        
        # Agrupar
        agg_dict = {col: 'mean' for col in value_cols}
        df_binned = df_binned.groupby('bin_idx', as_index=False).agg(agg_dict)
        
        # Renombrar bin_idx a la columna original
        df_binned.rename(columns={'bin_idx': bin_col}, inplace=True)
        
        return df_binned

    @staticmethod
    def smooth_curve(
        x: np.ndarray, 
        y: np.ndarray, 
        points: int = 500, 
        k: int = 3
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Aplica interpolación Spline para generar una curva suave.
        Retorna (x_smooth, y_smooth).
        """
        if not SCIPY_AVAILABLE:
            logger.warning("Scipy no está instalado. No se puede suavizar (Spline).")
            return x, y
            
        # Limpieza previa de NaNs/Infs
        mask = np.isfinite(x) & np.isfinite(y)
        x_clean = x[mask]
        y_clean = y[mask]
        
        if len(x_clean) <= k:
            logger.warning(f"Pocos puntos válidos ({len(x_clean)}) para Spline k={k}. Retornando datos limpios.")
            return x_clean, y_clean

        try:
            # Generar nuevo eje denso
            x_smooth = np.linspace(x_clean.min(), x_clean.max(), points)
            
            # Crear Spline, ordenando primero por X
            idx_sorted = np.argsort(x_clean)
            x_sorted = x_clean[idx_sorted]
            y_sorted = y_clean[idx_sorted]
            
            # Eliminar duplicados en X
            x_unique, idx_unique = np.unique(x_sorted, return_index=True)
            y_unique = y_sorted[idx_unique]
            
            if len(x_unique) <= k:
                 return x_clean, y_clean

            spl = make_interp_spline(x_unique, y_unique, k=k)
            y_smooth = spl(x_smooth)
            
            return x_smooth, y_smooth
        except Exception as e:
            logger.error(f"Error en cálculo Spline: {e}")
            return x_clean, y_clean
