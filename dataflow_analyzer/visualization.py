import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from .processing import DataProcessor
import logging

# Configurar estilo visual profesional
sns.set_theme(style="whitegrid", rc={"grid.linestyle": "--"})
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataVisualizer:
    """
    Clase encargada de generar visualizaciones comparativas.
    """
    
    def __init__(self, figsize=(10, 8)):
        self.figsize = figsize

    def plot_profile_comparison(
        self,
        df: pd.DataFrame,
        x_col: str,
        y_left_col: str,
        y_right_col: Optional[str] = None,
        title: str = "Comparación de Perfiles Atmosféricos",
        labels: Optional[Dict[str, str]] = None,
        save_path: Optional[str] = None,
        marker: str = '.',
        linestyle: str = '-',
        alpha: float = 0.6,
        colors: Optional[List[str]] = None,
        invert_yaxis_left: bool = False,
        invert_yaxis_right: bool = False
    ):
        """
        Genera un gráfico de perfil vertical.
        
        Args:
            df: DataFrame con los datos combinados.
            x_col: Variable eje X (ej: 'Temperature').
            y_left_col: Variable eje Y primario (ej: 'Altitude' o 'Pressure').
            y_right_col: Variable eje Y secundario (opcional, ej: 'Pressure' si Y1 es Altura).
            labels: Diccionario para renombrar ejes. ej: {'x': 'Temperatura (°C)', 'y_left': 'Altitud (m)'}
            save_path: Si se provee, guarda el gráfico en disco.
            marker: Estilo de marcador (ej: '.', 'o', '+').
            linestyle: Estilo de línea (ej: '-', '--').
            alpha: Transparencia (0.0 a 1.0).
            colors: Lista opcional de colores para sobreescribir los defaults.
        """
        fig, ax1 = plt.subplots(figsize=self.figsize)
        
        # Mapa de etiquetas por defecto
        lbl = labels or {}
        xlabel = lbl.get(x_col, x_col)
        yleft_label = lbl.get(y_left_col, y_left_col)
        
        # --- Plot Eje Izquierdo ---
        # Detectar columnas relevantes
        cols_to_plot = [c for c in df.columns if x_col in c] # ej: temp_dron, temp_sonda
        
        # Colores
        if colors:
            plot_colors = colors
        else:
            plot_colors = sns.color_palette("husl", max(len(cols_to_plot), 2))
        
        for i, col in enumerate(cols_to_plot):
            label_text = col.replace("_", " ").title()
            color = plot_colors[i % len(plot_colors)]
            
            # Plot X vs Y usando estilo configurable
            ax1.plot(
                df[col], 
                df[y_left_col], 
                label=label_text, 
                color=color, 
                alpha=alpha, 
                marker=marker, 
                linestyle=linestyle
            )

        ax1.set_xlabel(xlabel, fontsize=12)
        ax1.set_ylabel(yleft_label, fontsize=12, color='black')
        ax1.tick_params(axis='y', labelcolor='black')
        ax1.legend(loc="upper left")
        ax1.grid(True, linestyle="--", alpha=alpha)
        
        if invert_yaxis_left:
            ax1.invert_yaxis()
            
        # --- Plot Eje Derecho (Twinx) ---
        if y_right_col and y_right_col in df.columns:
            ax2 = ax1.twinx()
            yright_label = lbl.get(y_right_col, y_right_col)
            
            # Color distintivo para el eje secundario si no se proveyó uno específico
            # Usaremos el último color de la lista o azul por defecto si no alcanza
            color_y2 = 'tab:blue' 
            
            ax2.plot(
                df[x_col] if x_col in df.columns else df[df.columns[0]], 
                df[y_right_col], 
                color=color_y2, 
                label=yright_label, 
                alpha=alpha, 
                marker=marker, 
                linestyle=linestyle
            )
            
            ax2.set_ylabel(yright_label, fontsize=12, color=color_y2)
            ax2.tick_params(axis='y', labelcolor=color_y2)
            
            if invert_yaxis_right:
                ax2.invert_yaxis()
                
            # Mover la leyenda del eje derecho para que no tape
            ax2.legend(loc="upper right")

        plt.title(title, fontsize=14, pad=20)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300)
            logger.info(f"Gráfico guardado en: {save_path}")
            
        return fig

    def plot_vertical_profile(
        self,
        df: pd.DataFrame,
        x_col: str,
        y1_col: str,
        y2_col: str,
        title: str = "Perfil Vertical",
        xlabel: Optional[str] = None,
        y1_label: Optional[str] = None,
        y2_label: Optional[str] = None,
        save_path: Optional[str] = None,
        bin_size: Optional[float] = None,
        smooth: bool = False,
        **kwargs
    ):
        """
        Genera un gráfico genérico con Doble Eje Y.
        Permite seleccionar libremente qué variable va en cada eje.
        
        Args:
            df: DataFrame con los datos.
            x_col: Columna para el Eje X (Variable Independiente).
            y1_col: Columna para el Eje Y Izquierdo.
            y2_col: Columna para el Eje Y Derecho.
            title: Título del gráfico.
            xlabel: Etiqueta personalizada para X.
            y1_label: Etiqueta personalizada para Y1.
            y2_label: Etiqueta personalizada para Y2.
            save_path: Ruta guardar archivo.
            bin_size: Tamaño de bin para suavizar usando la variable X.
            smooth: Si True, aplica interpolación Spline (y=f(x)).
        """
        fig, ax1 = plt.subplots(figsize=self.figsize)
        
        # 1. Copia Segura
        plot_df = df[[x_col, y1_col, y2_col]].dropna().copy()
        
        # 2. Procesamiento: Binning (Generic via DataProcessor)
        if bin_size and bin_size > 0:
            plot_df = DataProcessor.bin_data(
                plot_df, 
                bin_col=x_col, 
                value_cols=[y1_col, y2_col], 
                bin_size=bin_size
            )
            
        # 3. Ordenamiento (Crítico para gráficos de línea y spline)
        plot_df.sort_values(by=x_col, inplace=True)

        # 4. Datos Base
        x_vals = plot_df[x_col].values
        y1_vals = plot_df[y1_col].values
        y2_vals = plot_df[y2_col].values
        
        # 5. Procesamiento: Spline (Generic y=f(x))
        if smooth and len(plot_df) > 3:
            logger.info(f"Aplicando suavizado Spline (X={x_col})...")
            # Interpolamos Y1 = f(X) y Y2 = f(X)
            x_plot, y1_plot = DataProcessor.smooth_curve(x_vals, y1_vals)
            _, y2_plot = DataProcessor.smooth_curve(x_vals, y2_vals)
        else:
            x_plot, y1_plot, y2_plot = x_vals, y1_vals, y2_vals


        # --- PLOTTING ---
        
        # Labels Defaults
        lbl_x = xlabel if xlabel else x_col.replace("_", " ").title()
        lbl_y1 = y1_label if y1_label else y1_col.replace("_", " ").title()
        lbl_y2 = y2_label if y2_label else y2_col.replace("_", " ").title()
        
        # Eje Y1 (Izquierdo)
        color_y1 = 'tab:blue'
        ax1.set_xlabel(lbl_x, fontsize=12)
        ax1.set_ylabel(lbl_y1, fontsize=12, color=color_y1)
        ax1.tick_params(axis='y', labelcolor=color_y1)
        
        ax1.plot(
            x_plot, 
            y1_plot, 
            color=color_y1, 
            label=lbl_y1,
            marker=None if smooth else kwargs.get('marker', '.'),
            linestyle=kwargs.get('linestyle', '-'),
            alpha=kwargs.get('alpha', 0.6)
        )
        
        ax1.grid(True, linestyle="--", alpha=0.5)

        # Eje Y2 (Derecho)
        ax2 = ax1.twinx()
        color_y2 = 'tab:red'
        ax2.set_ylabel(lbl_y2, fontsize=12, color=color_y2)
        ax2.tick_params(axis='y', labelcolor=color_y2)
        
        ax2.plot(
            x_plot,
            y2_plot, 
            color=color_y2, 
            label=lbl_y2, 
            marker=None if smooth else kwargs.get('marker', '.'),
            linestyle=kwargs.get('linestyle', '-'),
            alpha=kwargs.get('alpha', 0.6)
        )

        plt.title(title, fontsize=14, pad=20)
        
        lines_1, labels_1 = ax1.get_legend_handles_labels()
        lines_2, labels_2 = ax2.get_legend_handles_labels()
        ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='best')

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Gráfico guardado en: {save_path}")
            
        return fig
    def compare_profiles(
        self,
        df1: pd.DataFrame,
        label1: str,
        df2: pd.DataFrame,
        label2: str,
        x_col: str,
        y1_col: str,
        y2_col: str,
        title: str = "Comparación de Perfiles",
        save_path: Optional[str] = None,
        bin_size: Optional[float] = None,
        smooth: bool = False,
        xlabel: Optional[str] = None,
        y1_label: Optional[str] = None,
        y2_label: Optional[str] = None,
        style1: Optional[Dict[str, Any]] = None,
        style2: Optional[Dict[str, Any]] = None,
        color_y1: str = 'tab:blue',
        color_y2: str = 'tab:red',
        invert_x: bool = False,
        invert_y1: bool = False,
        invert_y2: bool = False
    ):
        """
        Compara dos perfiles (ej: Dron vs Sonda) en el mismo gráfico.
        """
        fig, ax1 = plt.subplots(figsize=self.figsize)
        
        # Styles defaults
        s1 = style1 or {'color': color_y1, 'linestyle': '-'} # Use color_y1 if not in style? No, style overrides? 
        # Actually s1/s2 are for DF1/DF2 datasets. 
        # But we align colors by VARIABLE (Y1 vs Y2).
        # So we should use color_y1 for Y1 plots (both dashed and solid)
        # And color_y2 for Y2 plots.
        
        s1 = style1 or {}
        s2 = style2 or {'linestyle': '--', 'alpha': 0.7}
        
        # Logic: Plot Y1 with color_y1, varying linestyle by dataset.
        
        # Procesar ambos DataFrames

        data_1 = self._process_data(df1, x_col, y1_col, y2_col, bin_size, smooth)
        data_2 = self._process_data(df2, x_col, y1_col, y2_col, bin_size, smooth)
        
        # Labels
        lbl_x = xlabel if xlabel else x_col.replace("_", " ").title()
        lbl_y1 = y1_label if y1_label else y1_col.replace("_", " ").title()
        lbl_y2 = y2_label if y2_label else y2_col.replace("_", " ").title()

        # --- Eje Y1 (Izquierdo) ---
        ax1.set_xlabel(lbl_x, fontsize=12)
        ax1.set_ylabel(lbl_y1, fontsize=12, color=color_y1)
        ax1.tick_params(axis='y', labelcolor=color_y1)
        
        # Plot DF1 (Sólido default)
        ax1.plot(data_1['x'], data_1['y1'], color=color_y1, linestyle=s1.get('linestyle', '-'), label=f'{label1} ({lbl_y1})')
        # Plot DF2 (Punteado default)
        ax1.plot(data_2['x'], data_2['y1'], color=color_y1, linestyle=s2.get('linestyle', '--'), alpha=s2.get('alpha', 0.7), label=f'{label2} ({lbl_y1})')

        ax1.grid(True, linestyle="--", alpha=0.5)
        
        if invert_y1:
            ax1.invert_yaxis()
        if invert_x:
            ax1.invert_xaxis()

        # --- Eje Y2 (Derecho) ---
        ax2 = ax1.twinx()
        ax2.set_ylabel(lbl_y2, fontsize=12, color=color_y2)
        ax2.tick_params(axis='y', labelcolor=color_y2)
        
        # Plot DF1 (Sólido)
        ax2.plot(data_1['x'], data_1['y2'], color=color_y2, linestyle=s1.get('linestyle', '-'), label=f'{label1} ({lbl_y2})')
        # Plot DF2 (Punteado)
        ax2.plot(data_2['x'], data_2['y2'], color=color_y2, linestyle=s2.get('linestyle', '--'), alpha=s2.get('alpha', 0.7), label=f'{label2} ({lbl_y2})')
        
        if invert_y2:
            ax2.invert_yaxis()
        
        plt.title(title, fontsize=14, pad=20)
        
        # Leyenda Unificada
        lines_1, labels_1 = ax1.get_legend_handles_labels()
        lines_2, labels_2 = ax2.get_legend_handles_labels()
        ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='best')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Gráfico guardado en: {save_path}")
            
        return fig

    def _process_data(self, df, x_col, y1_col, y2_col, bin_size, smooth):
        """Helper para limpiar, binning y smoothing."""
        sub = df[[x_col, y1_col, y2_col]].dropna().copy()
        
        if bin_size and bin_size > 0:
            sub = DataProcessor.bin_data(sub, x_col, [y1_col, y2_col], bin_size)
            
        sub.sort_values(by=x_col, inplace=True)
        
        x_vals = sub[x_col].values
        y1_vals = sub[y1_col].values
        y2_vals = sub[y2_col].values
        
        if smooth and len(sub) > 3:
            x_plot, y1_plot = DataProcessor.smooth_curve(x_vals, y1_vals)
            _, y2_plot = DataProcessor.smooth_curve(x_vals, y2_vals)
            return {'x': x_plot, 'y1': y1_plot, 'y2': y2_plot}
        
        return {'x': x_vals, 'y1': y1_vals, 'y2': y2_vals}

    def plot_time_series(
        self,
        df: pd.DataFrame,
        y_col: str,
        x_col: Optional[str] = None,
        title: str = "Serie de Tiempo",
        xlabel: str = "Tiempo",
        ylabel: str = "Valor",
        label: str = "Datos",
        color: str = "tab:blue",
        kind: str = "line", # 'line' or 'scatter'
        smooth: bool = False,
        save_path: Optional[str] = None
    ):
        """
        Genera un gráfico simple de serie de tiempo (o X vs Y).
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # Preparar X e Y
        if x_col:
            x_vals = df[x_col].values
        else:
            x_vals = df.index.values
            
        y_vals = df[y_col].values
        
        # Manejo de suavizado
        is_datetime = pd.api.types.is_datetime64_any_dtype(x_vals) or (len(x_vals)>0 and isinstance(x_vals[0], pd.Timestamp))
        
        if smooth and len(x_vals) > 3:
            # Convertir datetime a float para cálculo
            if is_datetime:
                # Convertir a timestamps (floats)
                x_float = np.array([t.timestamp() for t in pd.to_datetime(x_vals)])
                # Spline
                x_plot_f, y_plot = DataProcessor.smooth_curve(x_float, y_vals)
                # Reconversión a datetime para plot
                x_plot = pd.to_datetime(x_plot_f, unit='s')
            else:
                x_plot, y_plot = DataProcessor.smooth_curve(x_vals, y_vals)
        else:
            x_plot, y_plot = x_vals, y_vals

        # Plot
        if kind == "scatter":
            ax.scatter(x_plot, y_plot, color=color, alpha=0.6, label=label, s=5)
        else:
            ax.plot(x_plot, y_plot, color=color, alpha=0.8, label=label, linewidth=2)
            
        ax.set_title(title, fontsize=14, pad=15)
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(loc="best")
        
        # Formato de fecha rotado si es serie de tiempo
        if is_datetime:
            fig.autofmt_xdate()
            
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Gráfico guardado en: {save_path}")
            
        return fig

    def plot_wind_profile(
        self,
        df: pd.DataFrame,
        alt_col: str,
        speed_col: str,
        dir_col: str,
        title: str = "Perfil de Viento",
        xlabel: str = "Velocidad de Viento (m/s)",
        ylabel: str = "Altitud (m)",
        save_path: Optional[str] = None,
        BarbInterval: int = 30, # Plot barb every N meters roughly
        line_color: str = "tab:blue",
        barb_color: str = "black"
    ):
        """
        Genera un perfil vertical de viento con barbas.
        Muestra la velocidad como línea y la dirección como barbas.
        """
        fig, ax = plt.subplots(figsize=(6, 10)) # Vertical layout
        
        # 1. Clean Data
        sub = df[[alt_col, speed_col, dir_col]].dropna().sort_values(by=alt_col)
        
        # 2. Bin data FIRST for clear barbs AND a clean profile line
        bins = np.arange(sub[alt_col].min(), sub[alt_col].max(), BarbInterval)
        # Handle cases where bins might be empty or single point
        if len(bins) < 2:
            bins = 5 # Default to 5 bins if range is small
            
        sub['bin'] = pd.cut(sub[alt_col], bins=bins)
        binned = sub.groupby('bin', observed=True).mean().dropna()
        
        # 3. Main Line (Speed) - USING BINNED DATA
        ax.plot(binned[speed_col], binned[alt_col], label="Velocidad (Promedio)", color=line_color, alpha=0.8, marker='o', markersize=4)
        
        # 4. Calculate U/V (Meteorological Convention: Direction FROM)
        rads = np.deg2rad(binned[dir_col].values)
        vals_speed = binned[speed_col].values
        
        # Met convention to U/V
        u = -vals_speed * np.sin(rads)
        v = -vals_speed * np.cos(rads)
        
        y_locs = binned[alt_col].values # Altitude positions
        # Place barbs slightly to the right of the max speed or fixed position?
        # Fixed position prevents overlapping data lines.
        x_max = sub[speed_col].max()
        x_locs = np.ones_like(y_locs) * (x_max * 1.1 if x_max > 0 else 1) 
        
        # Plot Barbs
        ax.barbs(x_locs, y_locs, u, v, length=6, pivot='middle', color=barb_color)
        
        ax.set_title(title, fontsize=14)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, linestyle="--", alpha=0.5)
        
        # Adjust X limit to fit barbs
        ax.set_xlim(0, (x_max * 1.3) if x_max > 0 else 10)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Gráfico de viento guardado en: {save_path}")
            
        return fig
