# BaZodiac Engine API

FastAPI-based API server for BaZodiac Engine.

## Installation

```bash
pip install -r requirements.txt
```

## Running

```bash
uvicorn api.main:app --reload --port 8000
```

## Endpoints

- `GET /health` - Health check
- `POST /validate` - Validate request without computation
- `POST /chart` - Compute complete chart
- `POST /features` - Compute features only
- `POST /fusion` - Compute fusion from pillars/positions
