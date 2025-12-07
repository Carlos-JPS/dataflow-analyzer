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

    def test_plot_wind_profile_smoke(self, sample_drone_df):
        """Smoke test for plot_wind_profile."""
        viz = DataVisualizer()
        # Ensure columns exist in sample (add dummy if needed)
        df = sample_drone_df.copy()
        df['speed'] = 5.0
        df['direction'] = 180.0
        
        fig = viz.plot_wind_profile(
            df=df,
            alt_col='altitude',
            speed_col='speed',
            dir_col='direction'
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)
