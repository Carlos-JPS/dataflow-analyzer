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

    def test_smooth_curve_all_nans(self):
        """Test smoothing when all data is NaN."""
        x = np.array([np.nan, np.nan])
        y = np.array([1, 2])
        x_new, y_new = DataProcessor.smooth_curve(x, y)
        # Should return emtpy or original (filtered) which is empty
        assert len(x_new) == 0
        
    def test_smooth_curve_single_point(self):
        """Test smoothing with a single valid point."""
        x = np.array([1.0])
        y = np.array([10.0])
        x_new, y_new = DataProcessor.smooth_curve(x, y)
        assert len(x_new) == 1
        assert x_new[0] == 1.0

    def test_bin_data_invalid_size(self, sample_drone_df):
        """Test binning with zero or negative bin size."""
        # Zero bin size -> Return original
        binned = DataProcessor.bin_data(sample_drone_df, 'presion', ['altitude'], 0)
        assert len(binned) == len(sample_drone_df)
        
    def test_filter_by_time_basic(self):
        """Test basic time filtering on index."""
        # Create timestamps
        rng = pd.date_range('2025-01-01 10:00', periods=5, freq='h') # 10, 11, 12, 13, 14
        df = pd.DataFrame({'val': range(5)}, index=rng)
        
        # Filter from 11 to 13
        filtered = DataProcessor.filter_by_time(df, '2025-01-01 11:00', '2025-01-01 13:00')
        assert len(filtered) == 3 # 11, 12, 13
        assert filtered.index[0] == pd.Timestamp('2025-01-01 11:00')

    def test_filter_by_time_tz_aware_naive_mix(self):
        """Test filtering where data is TZ-aware (UTC) and filter is naive string."""
        # Data is UTC
        rng = pd.date_range('2025-01-01 10:00', periods=5, freq='h', tz='UTC') 
        df = pd.DataFrame({'val': range(5)}, index=rng)
        
        # Filter is naive "11:00" -> Should be treated as 11:00 UTC
        filtered = DataProcessor.filter_by_time(df, '2025-01-01 11:00', '2025-01-01 12:00')
        assert len(filtered) == 2
        assert filtered.index.tz is not None # Should preserve TZ

    def test_filter_by_time_naive_data_aware_filter(self):
        """Test filtering where data is naive and filter is TZ-aware."""
        rng = pd.date_range('2025-01-01 10:00', periods=5, freq='h') # Naive
        df = pd.DataFrame({'val': range(5)}, index=rng)
        
        # Filter is 11:00 UTC. Logic should convert it to naive 11:00.
        ts_start = pd.Timestamp('2025-01-01 11:00').tz_localize('UTC')
        ts_end = pd.Timestamp('2025-01-01 12:00').tz_localize('UTC')
        
        filtered = DataProcessor.filter_by_time(df, ts_start, ts_end)
        assert len(filtered) == 2
        assert filtered.index[0] == pd.Timestamp('2025-01-01 11:00')
