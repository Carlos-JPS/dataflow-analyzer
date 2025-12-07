import pytest
import pandas as pd
import os
from dataflow_analyzer.data_source import CSVSource, XMLSource

class TestCSVSource:
    
    def test_load_basic_csv(self, tmp_path):
        """Test loading a standard CSV file."""
        # Create dummy CSV
        d = tmp_path / "data"
        d.mkdir()
        p = d / "test.csv"
        p.write_text("time, value,  meta \n2025-01-01, 10, A\n2025-01-02, 20, B")
        
        source = CSVSource(str(p))
        source.load(pivot=False, time_col='time')
        
        df = source.df
        assert len(df) == 2
        # Check column stripping
        assert "meta" in df.columns
        assert "meta " not in df.columns 
        # Check time index
        assert isinstance(df.index, pd.DatetimeIndex)

    def test_load_influx_csv(self, tmp_path):
        """Test loading an InfluxDB style CSV with skip rows."""
        p = tmp_path / "influx.csv"
        content = """#group,false,false,true
#datatype,string,long,dateTime
#default,mean,,
,result,table,_time,_value,_field
,,0,2025-01-01T00:00:00Z,15.5,temperature
,,0,2025-01-01T00:01:00Z,16.0,temperature
"""
        p.write_text(content)
        
        # Influx usually needs pivoting
        source = CSVSource(str(p))
        source.load(pivot=True, time_col='_time', field_col='_field', value_col='_value')
        
        df = source.df
        assert 'temperature' in df.columns
        assert len(df) == 2
        
class TestXMLSource:
    
    def test_load_basic_xml(self, tmp_path):
        """Test loading a generic Sonda XML."""
        p = tmp_path / "sonda.xml"
        content = """<Data>
  <Row time="2025-01-01T12:00:00" Pressure="1000" Temperature="20" />
  <Row time="2025-01-01T12:01:00" Pressure="990" Temperature="19" />
</Data>
"""
        p.write_text(content)
        
        source = XMLSource(str(p))
        # Default xpath_root="Row", time_col="DataSrvTime" (default) mismatch.
        # Need to specify time_col matching XML attribute
        source.load(time_col="time")
        
        df = source.df
        assert len(df) == 2
        assert "Pressure" in df.columns
    def test_load_empty_file(self, tmp_path):
        """Test loading an empty file."""
        p = tmp_path / "empty.csv"
        p.touch()
        source = CSVSource(str(p))
        # Pandas empty csv raises EmptyDataError usually, or returns empty df depending on version/args.
        # Our implementation might raise custom error or propagate pandas error.
        with pytest.raises(Exception): # We expect some failure
            source.load()

    def test_load_corrupt_csv(self, tmp_path):
        """Test loading a malformed CSV."""
        p = tmp_path / "corrupt.csv"
        p.write_text("a,b,c\n1,2") # Missing column
        source = CSVSource(str(p))
        source.load(pivot=False)
        assert len(source.df) == 1 # Pandas is lenient, strict checks might be needed if we care.

    def test_load_unicode_headers(self, tmp_path):
        """Test CSV with special characters in headers."""
        p = tmp_path / "unicode.csv"
        p.write_text("time,presión,temperatura\n2025-01-01,1000,20")
        source = CSVSource(str(p))
        source.load(pivot=False, time_col='time')
        assert 'presión' in source.df.columns

    def test_load_missing_columns_xml(self, tmp_path):
        """Test XML missing expected attributes."""
        p = tmp_path / "bad.xml"
        p.write_text("<Root><Row time='2025'/></Root>") # No pressure
        
        source = XMLSource(str(p))
        source.load(time_col='time')
        df = source.df
        assert 'Pressure' not in df.columns # Should load but just lack the column
