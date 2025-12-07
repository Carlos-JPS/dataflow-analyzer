import pandas as pd
import numpy as np
import logging

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
            
        if len(x) <= k:
            logger.warning(f"Pocos puntos ({len(x)}) para Spline k={k}. Retornando original.")
            return x, y

        try:
            # Generar nuevo eje denso
            x_smooth = np.linspace(x.min(), x.max(), points)
            
            # Crear Spline
            spl = make_interp_spline(x, y, k=k)
            y_smooth = spl(x_smooth)
            
            return x_smooth, y_smooth
        except Exception as e:
            logger.error(f"Error en cálculo Spline: {e}")
            return x, y
