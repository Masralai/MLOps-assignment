import argparse
import yaml
import pandas as pd
import numpy as np
import time
import json
import logging
import sys
import os

def setup_logging(log_file):
    """
    Configures a dual-stream logger to capture stdout and file persistence.
    Using a standard ISO-ish format for easier grepping in production logs.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_config(config_path):
    """
    Parses the YAML orchestration config. 
    strictly enforces schema presence before 
    downstream processing starts.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    required_fields = ['seed', 'window', 'version']
    for field in required_fields:
        if field not in config:
            raise KeyError(f"Missing required config field: {field}")
    return config

def process_data(df, window):
    """
    Vectorized signal generation logic.
    Calculates simple moving average crossover. First (window-1) rows 
    will result in NaN for rolling_mean, producing a 0 signal by default.
    """
    if 'close' not in df.columns:
        raise ValueError("Missing 'close' column in input CSV")
    
    if df.empty:
        raise ValueError("Input CSV is empty")

    df['rolling_mean'] = df['close'].rolling(window=window).mean()
    df['signal'] = np.where(df['close'] > df['rolling_mean'], 1, 0)
    return df

def main():
    """
    Handles CLI parsing, orchestration, and ensures a JSON-serializable 
    metric state is persisted even on failure.
    """
    start_time_ns = time.time_ns()
    
    parser = argparse.ArgumentParser(description="Cryptocurrency Signal Generation Pipeline")
    parser.add_argument("--input", required=True, help="Path to input CSV data")
    parser.add_argument("--config", required=True, help="Path to YAML config file")
    parser.add_argument("--output", required=True, help="Path to output metrics JSON")
    parser.add_argument("--log-file", required=True, help="Path to log file")
    
    args = parser.parse_args()
    
    setup_logging(args.log_file)
    logging.info("Job started")

    version = "unknown"
    try:
        # Load Config
        config = load_config(args.config)
        version = config['version']
        seed = config['seed']
        window = config['window']

        # Set Seed
        np.random.seed(seed)
        logging.info(f"Config loaded: seed={seed}, window={window}, version={version}")

        # Load Data
        if not os.path.exists(args.input):
            raise FileNotFoundError(f"Input file not found: {args.input}")
        
        df = pd.read_csv(args.input)
        rows_processed = len(df)
        logging.info(f"Data loaded: {rows_processed} rows")

        # Processing Steps
        df = process_data(df, window)
        logging.info(f"Rolling mean calculated with window={window}")
        logging.info("Signals generated")

        # Metrics
        signal_rate = float(df['signal'].mean())
        
        end_time_ns = time.time_ns()
        latency_ms = int((end_time_ns - start_time_ns) / 1_000_000)
        
        metrics = {
            "version": version,
            "rows_processed": rows_processed,
            "metric": "signal_rate",
            "value": round(signal_rate, 4),
            "latency_ms": latency_ms,
            "seed": seed,
            "status": "success"
        }
        
        logging.info(f"Metrics: signal_rate={signal_rate:.4f}, rows_processed={rows_processed}")
        
        with open(args.output, 'w') as f:
            json.dump(metrics, f, indent=4)
        
        print(json.dumps(metrics, indent=4))
        logging.info(f"Job completed successfully in {latency_ms}ms")
        sys.exit(0)

    except Exception as e:
        error_msg = str(e)
        logging.error(f"Job failed: {error_msg}")
        
        error_metrics = {
            "version": version,
            "status": "error",
            "error_message": error_msg
        }
        
        with open(args.output, 'w') as f:
            json.dump(error_metrics, f, indent=4)
        
        print(json.dumps(error_metrics, indent=4))
        sys.exit(1)

if __name__ == "__main__":
    main()
