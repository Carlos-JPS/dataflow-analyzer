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
        assert df["Pressure"].dtype.kind in 'fi' # float or int
