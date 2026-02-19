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
    Standardizes log format across the stack. 
    Outputs to both file (for persistence) and stdout (for container log capture).
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

def main():
    """
    Execution is wrapped in a global try-except to ensure metrics are 
    emitted even on catastrophic failure (important for downstream monitoring).
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
        """
        Ensures we have the required hyper-parameters before touching the data.
        If 'version' is missing, we fail early to prevent untracked experimental runs.
        """
        if not os.path.exists(args.config):
            raise FileNotFoundError(f"Config file not found: {args.config}")
        
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
        
        # Mandatory fields check
        required_fields = ['seed', 'window', 'version']
        for field in required_fields:
            if field not in config:
                raise KeyError(f"Missing required config field: {field}")

        version = config['version']
        seed = config['seed']
        window = config['window']

        np.random.seed(seed)
        logging.info(f"Config loaded: seed={seed}, window={window}, version={version}")

        """
        We validate the 'close' price column exists. We don't perform 
        outlier detection here; that should happen in the upstream ETL.
        """
        if not os.path.exists(args.input):
            raise FileNotFoundError(f"Input file not found: {args.input}")
        
        df = pd.read_csv(args.input)
        rows_processed = len(df)
        logging.info(f"Data loaded: {rows_processed} rows")

        if 'close' not in df.columns:
            raise ValueError("Missing 'close' column in input CSV")
        
        if df.empty:
            raise ValueError("Input CSV is empty")

        """
        Using a standard rolling SMA. 
        The first 'window-1' rows will result in NaNs for 'rolling_mean'.
        This effectively nullifies signal generation for the start of the series.
        """
        df['rolling_mean'] = df['close'].rolling(window=window).mean()
        logging.info(f"Rolling mean calculated with window={window}")
        

        df['signal'] = np.where(df['close'] > df['rolling_mean'], 1, 0)
        logging.info("Signals generated")

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
