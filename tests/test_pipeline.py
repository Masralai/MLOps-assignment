import pytest
import pandas as pd
import numpy as np
import os
import yaml
from run import process_data, load_config

def test_process_data_signals():
    # Test case where price goes up and down
    data = {'close': [10, 20, 30, 20, 10]}
    df = pd.DataFrame(data)
    window = 3
    
    result_df = process_data(df, window)
    
    # Rolling mean for index 2 (window 3): (10+20+30)/3 = 20. 30 > 20 -> Signal 1
    # Rolling mean for index 3 (window 3): (20+30+20)/3 = 23.33. 20 <= 23.33 -> Signal 0
    # Rolling mean for index 4 (window 3): (30+20+10)/3 = 20. 10 <= 20 -> Signal 0
    
    assert result_df['signal'].iloc[2] == 1
    assert result_df['signal'].iloc[3] == 0
    assert result_df['signal'].iloc[4] == 0
    # First two should be 0 because rolling mean is NaN
    assert result_df['signal'].iloc[0] == 0
    assert result_df['signal'].iloc[1] == 0

def test_process_data_missing_column():
    df = pd.DataFrame({'open': [10, 20]})
    with pytest.raises(ValueError, match="Missing 'close' column"):
        process_data(df, 3)

def test_process_data_empty():
    df = pd.DataFrame({'close': []})
    with pytest.raises(ValueError, match="Input CSV is empty"):
        process_data(df, 3)

def test_load_config_valid(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_data = {'seed': 42, 'window': 5, 'version': 'v1'}
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)
    
    config = load_config(str(config_file))
    assert config['seed'] == 42
    assert config['window'] == 5
    assert config['version'] == 'v1'

def test_load_config_missing_field(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_data = {'seed': 42, 'window': 5} # Missing version
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)
    
    with pytest.raises(KeyError):
        load_config(str(config_file))
