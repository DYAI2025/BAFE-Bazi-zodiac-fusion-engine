# BaZodiac Engine

**Deterministic BaZi + Western Astrology Fusion Engine**

A scientific, reproducible fusion system that combines Chinese BaZi (Z10/Z12/Z60) with Western astrological geometry.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    BaZodiac Engine                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   TimeModel │  │  Ephemeris  │  │BaZiCalculator│ │
│  │ (TLST/TT)   │  │ (SwissEph)  │  │  (Ruleset)  │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
│         │                │                 │         │
│         └────────────────┼─────────────────┘         │
│                          ▼                          │
│              ┌─────────────────────┐                │
│              │  FeatureExtractor   │                │
│              └──────────┬──────────┘                │
│                         │                           │
│         ┌───────────────┼───────────────┐           │
│         ▼               ▼               ▼           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │Hard Segment│ │Soft Kernel │ │HarmonicPhasor│   │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘   │
│         │               │               │           │
│         └───────────────┼───────────────┘           │
│                         ▼                           │
│              ┌─────────────────────┐                │
│              │  Interpretation     │                │
│              │  (Feature-based)    │                │
│              └─────────────────────┘                │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Features

- ✅ **Deterministic**: Same input → same output (byte-identical JSON)
- ✅ **Validated**: `/validate` endpoint runs invariant checks
- ✅ **Provenance**: Every output includes metadata about sources
- ✅ **Scientific Compliance**: Explicit time scales, ephemeris sources
- ✅ **3-Layer Interpretation**: Facts / Rules / Narrative separation

## Installation

```bash
git clone https://github.com/DYAI2025/BAFE-Bazi-zodiac-fusion-engine.git
cd BAFE-Bazi-zodiac-fusion-engine
```

## API Server

FastAPI-based REST API:

```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `POST /validate` | Validate request without computation |
| `POST /chart` | Compute complete chart |
| `POST /features` | Compute features only |
| `POST /fusion` | Compute fusion from pillars/positions |

### Example Request

```json
POST /chart
{
  "engine_config": {
    "engine_version": "1.0.0",
    "parameter_set_id": "pz_2026_02_test",
    "deterministic": true,
    "fusion_mode": "harmonic_phasor",
    "harmonics_k": [2, 3, 4, 6, 12],
    "bazi_ruleset_id": "standard_bazi_v1",
    "refdata": {
      "refdata_pack_id": "test_pack",
      "refdata_mode": "BUNDLED_OFFLINE",
      "allow_network": false
    }
  },
  "birth_event": {
    "local_datetime": "1992-03-29T01:30:00",
    "tz_id": "Europe/Berlin",
    "geo_lon_deg": 13.405,
    "geo_lat_deg": 52.52
  },
  "bodies": ["Sun", "Moon", "Mercury", "Venus", "Mars"]
}
```

## Core Modules

| Module | File | Description |
|--------|------|-------------|
| Angles | `api/utils/core.py` | wrap360, wrap180, delta_deg |
| Time | `api/services/time_model.py` | UTC→TT→TLST chain |
| BaZi | `api/services/bazi_calculator.py` | Pillars, hidden stems |
| Fusion | `api/services/fusion.py` | Hard/Soft/Harmonic operators |
| Validation | `api/services/validation.py` | Error codes, invariants |

## Test Vectors

```bash
cd api
python -m pytest tests/ -v
python tests/test_core.py  # Run core function tests
```

### TV1: Branch Boundaries

| Longitude | Branch | Description |
|-----------|--------|-------------|
| 275.0° | Zi (0) | Middle of Zi |
| 285.0° | Chou (1) | Exact boundary |
| 284.999° | Zi (0) | Just below |
| 254.999° | Hai (11) | Wrap-around |

### TV4: TLST Hour Branches

| TLST Hours | Branch | Description |
|------------|--------|-------------|
| 22.999 | Hai (11) | Before Zi |
| 23.000 | Zi (0) | Start Zi |
| 1.000 | Chou (1) | Start Chou |

## Spec Documentation

- `specs/ENGINE_SPEC_v1.md` - Complete specification v1.0.0
- `GAP_ANALYSIS.md` - Implementation gap analysis
- `IMPLEMENTATION_PLAN.md` - Roadmap

## License

MIT

## References

- Park et al. (2021) JPL DE440/DE441 Ephemerides
- IERS Conventions (2010)
- Meeus Astronomical Algorithms
