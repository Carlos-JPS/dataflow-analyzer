import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
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
        colors: Optional[List[str]] = None
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
        
        # Si es Presión, invertir eje Y (mayor presión = menor altura)
        if "presion" in y_left_col.lower() or "pressure" in y_left_col.lower():
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
            
            # Invertir también si es presión
            if "presion" in y_right_col.lower() or "pressure" in y_right_col.lower():
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
