import pytest
import pandas as pd
import numpy as np
from dataflow_analyzer.processing import DataProcessor

class TestDataProcessor:
    
    def test_bin_data_basic(self, sample_drone_df):
        """Test simple binning of drone data."""
        # Bin by pressure every 10 hPa
        binned = DataProcessor.bin_data(
            sample_drone_df, 
            bin_col='presion', 
            value_cols=['altitude', 'temperatura'], 
            bin_size=10.0
        )
        
        # Original range 1000-900 (100 units). Bin size 10.
        # Max 1000 falls into bin 1005 (1000-1010). Min 900 falls into 905 (900-910).
        # So we expect bins covering [900, 1000], which results in 11 bins.
        assert len(binned) == 11
        assert 'presion' in binned.columns
        assert 'altitude' in binned.columns
        # Check if values are means (approx)
        # Pressure should be centered (e.g., 905, 915...) if my bin logic was centers
        # My bin logic: (val // size) * size + size/2 -> 900//10 * 10 + 5 = 905. Correct.
        assert 905 in binned['presion'].values

    def test_bin_data_empty(self):
        """Test binning an empty DataFrame."""
        empty = pd.DataFrame({'a': [], 'b': []})
        binned = DataProcessor.bin_data(empty, 'a', ['b'], 1.0)
        assert binned.empty

    def test_smooth_curve_basic(self):
        """Test spline smoothing on a perfect sine wave."""
        x = np.linspace(0, 10, 20)
        y = np.sin(x)
        
        x_new, y_new = DataProcessor.smooth_curve(x, y, points=50, k=3)
        
        assert len(x_new) == 50
        assert len(y_new) == 50
        # Spline should match start/end roughly
        assert np.isclose(y_new[0], y[0], atol=0.1)

    def test_smooth_curve_nans(self, df_with_nans):
        """Test that smoothing handles NaNs and Infs by filtering them."""
        x = df_with_nans['x'].values
        y = df_with_nans['y'].values
        
        # Input has 5 points, but 2 are invalid (NaN, Inf). 3 valid points.
        # k=3 needs >3 points usually. My code returns original clean data if len <= k.
        x_new, y_new = DataProcessor.smooth_curve(x, y, k=3)
        
        # Should return the 3 clean points
        assert len(x_new) == 3
        assert np.all(np.isfinite(y_new))
        
    def test_smooth_curve_duplicates(self):
        """Test that smoothing handles duplicate X values."""
        x = np.array([1, 2, 2, 3, 4, 5]) # Duplicate '2'
        y = np.array([10, 20, 21, 30, 40, 50])
        
        x_new, y_new = DataProcessor.smooth_curve(x, y, k=3)
        assert len(x_new) == 500 # Should succeed and generate dense output
