import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def sample_drone_df():
    """Generates a sample DataFrame mimicking Drone data."""
    data = {
        'presion': np.linspace(1000, 900, 100),
        'altitude': np.linspace(0, 1000, 100),
        'temperatura': np.linspace(20, 10, 100),
        'time': pd.date_range(start='2025-01-01', periods=100, freq='s')
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_sonda_df():
    """Generates a sample DataFrame mimicking Sonda data."""
    data = {
        'Pressure': np.linspace(1000, 100, 100),
        'Altitude': np.linspace(0, 10000, 100),
        'Temperature': np.linspace(293.15, 233.15, 100), # Kelvin
    }
    return pd.DataFrame(data)

@pytest.fixture
def df_with_nans():
    """Generates a DataFrame with some NaNs for testing Robustness."""
    df = pd.DataFrame({
        'x': [1, 2, 3, 4, 5],
        'y': [10, np.nan, 30, 40, np.inf]
    })
    return df
