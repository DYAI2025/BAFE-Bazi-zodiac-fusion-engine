# BaZodiac Engine - Complete Specification v1.0.0

**Spec ID:** bazodiac-engine-v1-full  
**Version:** 1.0.0-draft  
**Date:** 2026-02-04  
**Status:** READY FOR IMPLEMENTATION

---

## 1. Executive Summary

The BaZodiac Engine is a **deterministic, reproducible fusion system** that combines:

- **BaZi**: Discrete cyclic algebra (Z10 stems, Z12 branches, Z60 sexagenary)
- **Western Astrology**: Continuous ecliptic geometry (0..360°)

### Key Design Principles

1. **Scientific Compliance**: Explicit time scales, ephemeris sources, coordinate frames
2. **Determinism**: Same input → same output (byte-identical JSON)
3. **Validation-First**: `/validate` runs invariant checks before computation
4. **Provenance**: Every output includes metadata about sources and methods
5. **No Hidden Constants**: All parameters explicit in config or ruleset

---

## 2. Core Definitions

### 2.1 Data Types

```typescript
type Angle360 = number;   // [0, 360)
type Angle180 = number;   // (-180, 180]
type Longitude = Angle360;
type Latitude = number;   // [-90, 90]
type StemIndex = 0..9;    // Z10
type BranchIndex = 0..11; // Z12
type SexagenaryIndex = 0..59; // Z60

const STEMS = ["Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui"];
const BRANCHES = ["Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai"];
```

### 2.2 Safe Angle Operators

```python
def wrap360(x): return x % 360.0
def wrap180(x): return wrap360(x + 180.0) - 180.0
def delta_deg(a, b):
    d = abs(wrap360(a) - wrap360(b))
    return d if d <= 180.0 else 360.0 - d
```

### 2.3 Interval Convention

**Default: HALF_OPEN [a, b)**

Example: Zi sector [255°, 285°):
- 284.999 → Zi
- 285.000 → Chou (next branch)

---

## 3. Configuration Schema

```typescript
interface EngineConfig {
  engine_version: string;           // "1.0.0"
  parameter_set_id: string;          // "pz_2026_02_core"
  deterministic: boolean;            // true
  epoch_id: "J2000" | "ofDate";
  time_standard: "CIVIL" | "LMT" | "TLST";
  dst_policy: "error" | "earlier" | "later";
  zodiac_mode: "tropical" | "sidereal";
  bazi_ruleset_id: string;
  fusion_mode: "hard_segment" | "soft_kernel" | "harmonic_phasor";
  harmonics_k?: number[];           // e.g., [2, 3, 4, 6, 12]
  kernel?: { type: "von_mises"; kappa: number };
  interval_convention: "HALF_OPEN";
  branch_coordinate_convention: "SHIFT_BOUNDARIES" | "SHIFT_LONGITUDES";
  phi_apex_offset_deg: number;       // 15.0
  zi_apex_deg: number;              // 270.0
  branch_width_deg: number;         // 30.0
  refdata: RefDataConfig;
  compliance_mode: "STRICT" | "RELAXED" | "DEV";
}
```

---

## 4. BaZi Ruleset

### 4.1 Standard Ruleset

```json
{
  "ruleset_id": "standard_bazi_v1",
  "ruleset_version": "1.0.0",
  "stem_order": ["Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui"],
  "branch_order": ["Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai"],
  "day_cycle_anchor": {
    "anchor_type": "JDN",
    "anchor_jdn": 2419451,
    "anchor_sexagenary_index": 0,
    "anchor_verification": "unverified"
  },
  "day_change_policy": { "mode": "zi_hour_start", "time_standard": "TLST", "zi_start_hour": 23.0 },
  "year_boundary": { "mode": "solar_longitude_crossing", "solar_longitude_deg": 315.0 },
  "month_boundary": { "mode": "JIEQI_CROSSING", "month_start_solar_longitude_deg": 315.0, "step_deg": 30.0 },
  "month_stem_rule": { "mode": "five_tigers_formula" },
  "hour_stem_rule": { "mode": "five_rats_formula" },
  "hidden_stems": {
    "mode": "table",
    "ordering": "principal_central_residual",
    "branch_to_hidden": {
      "Zi": ["Gui"], "Chou": ["Ji", "Gui", "Xin"], "Yin": ["Jia", "Bing", "Wu"],
      "Mao": ["Yi"], "Chen": ["Wu", "Yi", "Gui"], "Si": ["Bing", "Geng", "Wu"],
      "Wu": ["Ding", "Ji"], "Wei": ["Ji", "Yi", "Ding"], "Shen": ["Geng", "Ren", "Wu"],
      "You": ["Xin"], "Xu": ["Wu", "Xin", "Ding"], "Hai": ["Ren", "Jia"]
    },
    "weighting": { "mode": "role_weights", "role_weights": { "principal": 1.0, "central": 0.5, "residual": 0.3 } }
  }
}
```

---

## 5. Time Model

### 5.1 Time Scale Chain

```
Civil Time → UTC → UT1 → TT → LMST → TLST
```

### 5.2 TLST Computation

```python
def compute_tlst(utc_dt, geo_lon_deg, eot_min=0):
    """True Local Solar Time = LMST + Equation of Time"""
    ut1_hours = hour_of_day(utc_dt) + utc_dt.minute/60
    lmst = (ut1_hours + geo_lon_deg / 15.0) % 24.0
    return (lmst + eot_min / 60.0) % 24.0
```

### 5.3 Hour Branch from TLST

```python
def hour_branch_from_tlst(tlst_hours):
    """floor(((TLST + 1) % 24) / 2)"""
    return int(((tlst_hours + 1.0) % 24.0) / 2.0) % 12
```

---

## 6. Fusion Operators

### 6.1 Hard Segment Mapping

```python
def hard_branch_mapping(longitude_deg, zi_apex_deg=270.0, width_deg=30.0, convention="SHIFT_BOUNDARIES"):
    half = width_deg / 2.0
    b0 = zi_apex_deg - half
    if convention == "SHIFT_BOUNDARIES":
        shifted = wrap360(longitude_deg - b0)
    else:
        lambda_apex = wrap360(longitude_deg - 15.0)  # phi_offset
        b0_apex = wrap360(b0 - 15.0)
        shifted = wrap360(lambda_apex - b0_apex)
    return int(floor(shifted / width_deg)) % 12
```

### 6.2 Soft Kernel Weighting

```python
def soft_branch_weights(longitude_deg, zi_apex_deg=270.0, width_deg=30.0, kappa=4.0):
    centers = [wrap360(zi_apex_deg + width_deg * i) for i in range(12)]
    raw_weights = [exp(kappa * cos(radians(delta_deg(longitude_deg, c)))) for c in centers]
    total = sum(raw_weights)
    return {i: w/total for i, w in enumerate(raw_weights)}
```

### 6.3 Harmonic Phasor Fusion

```python
def harmonic_phasor_fusion(pillars, positions, zi_apex_deg=270.0, width_deg=30.0, harmonics=[2,3,4,6,12]):
    """R_k (BaZi) + O_k (West) → I_k, X_k, A_k"""
    results = {}
    for k in harmonics:
        r_k = sum(exp(1j * k * radians(zi_apex_deg + width_deg * idx)) for idx in pillars.values())
        o_k = sum(exp(1j * radians(lon)) for lon in positions.values())
        magnitude_r, magnitude_o = abs(r_k), abs(o_k)
        degenerate = magnitude_r < 1e-10 or magnitude_o < 1e-10
        a_k = 0.0 if degenerate else ((r_k.conjugate() * o_k).real / (magnitude_r * magnitude_o))
        i_k = abs(r_k + o_k) ** 2
        results[k] = {"k": k, "a_k": a_k, "i_k": i_k, "degenerate": degenerate}
    return results
```

---

## 7. Validation

### 7.1 Error Codes

| Code | Meaning |
|------|---------|
| `REFDATA_NETWORK_FORBIDDEN` | Network access in offline mode |
| `MISSING_DAY_CYCLE_ANCHOR` | No anchor for sexagenary day |
| `INCONSISTENT_BRANCH_ORIGIN` | SHIFT_LONGITUDES without B0_apex |
| `DST_AMBIGUOUS_LOCAL_TIME` | DST fallback/forward overlap |
| `LEAP_SECONDS_FILE_EXPIRED` | Leap seconds file expired |
| `INVALID_LAMBDA` | Longitude not in [0, 360) |

### 7.2 Validation Response

```json
{
  "compliance_status": "COMPLIANT|DEGRADED|NON_COMPLIANT",
  "errors": [{"code": "...", "message": "..."}],
  "warnings": [{"code": "...", "message": "..."}],
  "evidence": {
    "refdata": {"refdata_pack_id": "..."},
    "time": {"tlst_quality": "ok"},
    "discretization": {"interval_convention": "HALF_OPEN"}
  }
}
```

---

## 8. Test Vectors

### 8.1 Branch Boundaries

| Longitude | Expected Branch | Description |
|-----------|-----------------|------------|
| 275.0° | 0 (Zi) | Middle of Zi |
| 285.0° | 1 (Chou) | Boundary |
| 284.999° | 0 (Zi) | Just below |
| 254.999° | 11 (Hai) | Wrap-around |

### 8.2 TLST Hour Branches

| TLST Hours | Branch | Description |
|------------|--------|-------------|
| 22.999 | 11 (Hai) | Before Zi |
| 23.000 | 0 (Zi) | Start Zi |
| 0.999 | 0 (Zi) | Before Chou |
| 1.000 | 1 (Chou) | Start Chou |

---

## 9. API Endpoints

```
POST /chart         Full computation
POST /validate      Validation only
GET  /health       Health check
```

---

## 10. 3-Layer Interpretation Model

| Layer | Content | Example |
|-------|---------|---------|
| **Facts** | Astronomy/Geodesy | "Sun at λ=8.12°" |
| **Rules** | System conventions | "Hour branch = Chou" |
| **Narrative** | Interpretation | "You stand at a threshold..." |

Every narrative MUST reference `derived_from_features`.

---

**Status:** ✅ COMPLETE - Ready for implementation
