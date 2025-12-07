import pytest
import matplotlib.pyplot as plt
from dataflow_analyzer.visualization import DataVisualizer

class TestDataVisualizer:
    
    def test_plot_vertical_profile_smoke(self, sample_drone_df):
        """Smoke test for plot_vertical_profile."""
        viz = DataVisualizer()
        fig = viz.plot_vertical_profile(
            df=sample_drone_df,
            x_col='presion',
            y1_col='altitude',
            y2_col='temperatura',
            smooth=False
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_plot_compare_profiles_smoke(self, sample_drone_df, sample_sonda_df):
        """Smoke test for compare_profiles."""
        viz = DataVisualizer()
        # Rename Sonda columns to match X
        sample_sonda_df = sample_sonda_df.rename(columns={'Pressure': 'presion', 'Altitude': 'altitude', 'Temperature': 'temperatura'})
        
        fig = viz.compare_profiles(
            df1=sample_drone_df, label1="Dron",
            df2=sample_sonda_df, label2="Sonda",
            x_col='presion',
            y1_col='altitude',
            y2_col='temperatura'
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)
        
    def test_plot_time_series_smoke(self, sample_drone_df):
        """Smoke test for plot_time_series."""
        viz = DataVisualizer()
        fig = viz.plot_time_series(
            df=sample_drone_df,
            y_col='altitude',
            x_col='time'
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)
