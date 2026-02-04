# BaZodiac Engine - Gap Analysis & Implementation Plan

**Date:** 2026-02-04  
**Author:** Nexus  
**Spec Version:** 1.0.0-draft  
**Code Version:** 0.2

---

## Executive Summary

The BaZodiac Engine v0.2 implements core BaZi pillar calculation with Swiss Ephemeris and basic Wu-Xing fusion. However, significant gaps exist between the v1.0.0 spec and the current implementation.

**Gap Score:** ~45% of spec requirements implemented

---

## Implemented Features (✅)

### Core BaZi Engine
- [x] Year pillar from LiChun (315°) solar longitude crossing
- [x] Month pillars from exact Jieqi boundaries (24 solar terms)
- [x] Day pillar from JDN-based sexagenary index
- [x] Hour pillars from 2-hour branches
- [x] Zi-hour day boundary option
- [x] Hidden stems with weighting
- [x] Swiss Ephemeris backend
- [x] DST validation (strict mode)

### Basic Fusion
- [x] Planet → Wu-Xing element mapping
- [x] Wu-Xing vector calculation
- [x] Basic harmony index (dot_product, cosine)
- [x] Equation of Time calculation

### Infrastructure
- [x] CLI interface
- [x] Basic API endpoint
- [x] Type safety (dataclasses)
- [x] Configuration inputs

---

## Missing Features (❌)

### 1. Fusion Architecture (Critical)

| Spec Requirement | Status | Priority | Effort |
|------------------|--------|----------|--------|
| Harmonic Phasor Fusion (R_k, O_k, A_k) | ❌ Not implemented | P0 | 4h |
| Soft Kernel Weighting (von Mises) | ❌ Only hard Wu-Xing | P0 | 3h |
| Hard Branch Mapping from Longitude | ❌ Only element mapping | P0 | 2h |
| Fusion Feature Vector | ❌ Partial | P0 | 2h |

**Impact:** Cannot generate the spec's fusion features for interpretation

### 2. Branch Conventions (Critical)

| Spec Requirement | Status | Priority | Effort |
|------------------|--------|----------|--------|
| SHIFT_BOUNDARIES vs SHIFT_LONGITUDES | ❌ Not implemented | P0 | 1h |
| Interval Convention (HALF_OPEN) | ❌ Implicit only | P0 | 1h |
| phi_apex_offset_deg config | ❌ Not configurable | P0 | 1h |
| zi_apex_deg config | ❌ Hardcoded 270° | P0 | 1h |

**Impact:** Spec's offset/anchor formalism not implemented

### 3. Validation Subsystem (High)

| Spec Requirement | Status | Priority | Effort |
|------------------|--------|----------|--------|
| /validate endpoint | ❌ Not implemented | P1 | 3h |
| Invariant checks | ❌ Partial | P1 | 2h |
| Property tests | ❌ Minimal | P1 | 2h |
| Error budget reporting | ❌ Not implemented | P1 | 2h |
| Failure mode enumeration | ❌ Not implemented | P1 | 2h |

**Impact:** Cannot validate inputs/outputs per spec

### 4. Reference Data Subsystem (Medium)

| Spec Requirement | Status | Priority | Effort |
|------------------|--------|----------|--------|
| RefDataManager | ❌ Not implemented | P2 | 4h |
| Manifest verification | ❌ Not implemented | P2 | 2h |
| SHA/GPG verification | ❌ Not implemented | P2 | 2h |
| Offline mode enforcement | ❌ Not implemented | P2 | 1h |

**Impact:** Cannot guarantee reproducibility across environments

### 5. Full Spec Compliance (Medium)

| Spec Requirement | Status | Priority | Effort |
|------------------|--------|----------|--------|
| TimeModel (UT1/TT/TLST) | ⚠️ Partial | P1 | 3h |
| EoT provenance | ❌ Not tracked | P1 | 1h |
| Uncertainty propagation | ❌ Not implemented | P1 | 3h |
| Epoch/precession models | ⚠️ SwissEph defaults | P2 | 2h |
| Sidereal mode | ❌ Not implemented | P2 | 2h |
| House system | ❌ Not implemented | P2 | 3h |
| Dignities | ❌ Not implemented | P2 | 2h |

**Impact:** Cannot achieve spec's determinism guarantees

### 6. Interpretation Layer (Medium)

| Spec Requirement | Status | Priority | Effort |
|------------------|--------|----------|--------|
| Feature-derived statements | ⚠️ Partial | P1 | 3h |
| Provenance tracking | ❌ Not complete | P1 | 2h |
| Threshold parameters | ❌ Hardcoded | P1 | 1h |
| Ruleset versioning | ❌ Not implemented | P2 | 2h |

**Impact:** Interpretation lacks spec's rigor

---

## Gap Analysis Detail

### 3.1 Fusion Module Gaps

**Current Implementation:**
```python
# fusion.py only has:
- planet_to_wuxing()  # Hardcoded mapping
- calculate_wuxing_vector_from_planets()  # Simple accumulation
- calculate_harmony_index()  # dot_product or cosine
```

**Missing per Spec:**
```python
# Harmonic Phasor (not implemented):
def harmonic_phasor_fusion(features, harmonics_k):
    R_k = sum(w_i * exp(i * k * theta_i))  # BaZi reference phases
    O_k = sum(v_p * exp(i * k * lambda_p))  # West positions
    I_k = |R_k + O_k|^2
    X_k = Re(conj(R_k) * O_k)
    A_k = X_k / (|R_k|*|O_k| + eps)  # Alignment score
```

**Missing:**
- Harmonic embedding for both systems
- Phase center calculations
- Normalized alignment metrics
- Degeneracy detection

### 3.2 Branch Convention Gaps

**Current Implementation:**
```python
# bazi.py - implicit conventions:
month_p = month_pillar_from_year_stem(year_p.stem_index, month_index)
# month_index from Jieqi crossing
```

**Missing per Spec:**
```python
# Configurable conventions not present:
phi_apex_offset_deg: float = 15.0  # Configurable?
zi_apex_deg: float = 270.0  # Hardcoded
branch_width_deg: float = 30.0  # Implicit

# Two conventions not distinguished:
# K1 SHIFT_BOUNDARIES: branch(lambda) = floor(wrap360(lambda - B0) / width)
# K2 SHIFT_LONGITUDES:  branch(lambda_apex) where lambda_apex = lambda - offset
```

### 3.3 Validation Gaps

**Current Tests:**
- `test_golden_vectors.py` - some golden tests
- `test_invariants.py` - minimal invariant checks

**Missing per Spec:**
```python
# Full validation not implemented:
POST /validate
{
  "assertions": [...],
  "warnings": [...],
  "errors": [...],
  "failure_modes": [...]
}

# Required checks:
- wrap360 in [0,360)
- wrap180 in (-180,180]
- delta in [0,180]
- TLST in [0,24)
- hidden stems 1-3 per branch
- kernel normalization sum(weights)=1
- mixing detector for conventions
```

---

## Recommendations

### Phase 1: Core Fusion (Priority P0)

1. **Implement Harmonic Phasor Fusion**
   - Add `fusion/harmonics.py` module
   - Implement R_k, O_k, A_k calculations
   - Add degeneracy detection

2. **Implement Branch Conventions**
   - Add `fusion/branch_mapping.py` module
   - Implement SHIFT_BOUNDARIES vs SHIFT_LONGITUDES
   - Make phi_apex_offset_deg configurable

### Phase 2: Validation (Priority P1)

1. **Implement /validate endpoint**
   - Add `validation/validator.py` module
   - Implement invariant checks
   - Add failure mode enumeration

2. **Add Error Budgets**
   - Track uncertainty through pipeline
   - Report typical/max per stage

### Phase 3: Reference Data (Priority P2)

1. **Implement RefDataManager**
   - Add `refdata/manager.py` module
   - Implement manifest parsing
   - Add SHA/GPG verification

---

## Test Vectors Status

| Test Vector | Spec | Implementation | Status |
|-------------|------|----------------|--------|
| TV1: Branch boundary (Zi/Chou) | ✅ | ✅ | PASS |
| TV2: Wrap-around (254.999/255) | ✅ | ❌ | FAIL |
| TV3: Convention mixing | ✅ | ❌ | FAIL |
| TV4: TLST hour branch | ✅ | ❌ | FAIL |
| TV5: Soft kernel symmetry | ✅ | ❌ | FAIL |
| TV6: Hidden stems | ✅ | ✅ | PASS |
| TV7: RefData policy | ✅ | ❌ | FAIL |

**Test Coverage:** 4/7 test vectors implemented (57%)

---

## Files to Create/Modify

### New Files
- `bazi_engine/fusion/harmonics.py` - Phasor fusion
- `bazi_engine/fusion/branch_mapping.py` - Branch conventions
- `bazi_engine/validation/validator.py` - Validation engine
- `bazi_engine/refdata/manager.py` - Reference data subsystem
- `bazi_engine/validation/test_vectors.py` - Spec test vectors

### Modified Files
- `bazi_engine/types.py` - Add fusion types, conventions
- `bazi_engine/fusion.py` - Integrate new fusion modules
- `bazi_engine/api/index.py` - Add /validate endpoint
- `bazi_engine/cli.py` - Add --convention flags
- `tests/test_golden_vectors.py` - Add missing TVs

---

## Estimated Effort

| Phase | Features | Hours |
|-------|----------|-------|
| P0 | Harmonic Fusion + Branch Conventions | 10h |
| P1 | Validation + Error Budgets | 10h |
| P2 | Reference Data | 8h |
| P2 | Spec Compliance (TimeModel, etc.) | 10h |
| **Total** | | **38h** |

---

## Conclusion

The BaZodiac Engine v0.2 provides a solid foundation for BaZi pillar calculation with Swiss Ephemeris. However, the fusion architecture, validation subsystem, and reference data integrity features specified in v1.0.0 are largely unimplemented.

**Recommendation:** Implement Phase P0 (Core Fusion) first, as it enables the unique value proposition of the spec (harmonic/phasor fusion). Phase P1 (Validation) should follow to achieve spec compliance. Reference data (P2) can be deferred for initial launch.

**Risk:** Without validation and reference data, the engine cannot guarantee the reproducibility and determinism promised in the spec.
