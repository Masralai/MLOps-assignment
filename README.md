# MetaStackerBandit MLOps Pipeline

## Overview

This project implements a deterministic, containerized MLOps pipeline for cryptocurrency signal generation. It calculates a rolling mean on price data and generates buy/sell signals based on price momentum.

## Features

- **Deterministic**: Uses fixed random seeds for reproducibility.
- **Configurable**: Externalized configuration via `config.yaml`.
- **Containerized**: Fully portable via Docker.
- **Robust**: Includes comprehensive error handling and logging.
- **Observable**: Outputs detailed metrics in JSON format.

## Setup & Usage

### Local Execution

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the pipeline:

   ```bash
   python run.py --input data.csv --config config.yaml --output metrics.json --log-file run.log
   ```

### Docker Execution

1. Build the image:

   ```bash
   docker build -t mlops-task .
   ```

2. Run the container:

   ```bash
   docker run --rm mlops-task
   ```

## Expected Output

The `metrics.json` will have the following structure:

```json
{
    "version": "v1",
    "rows_processed": 10000,
    "metric": "signal_rate",
    "value": 0.4990,
    "latency_ms": 127,
    "seed": 42,
    "status": "success"
}
```

## Technical Specifications

- **Rolling Window**: Configured in `config.yaml`.
- **Signal Logic**: `Signal = 1` if `close > rolling_mean`, else `0`.
- **Latency**: Measured in milliseconds (ms).
