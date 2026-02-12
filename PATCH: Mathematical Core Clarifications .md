PATCH: Mathematical Core Clarifications + Extensions

patch_id: PATCH-MATH-002
scope: master_spec.mapping_functions + bazi.ruleset_interfaces + tests
breaking_change: false (adds optional features + clarifies conventions)

1) Spec Text Patch (normativ) fuer spec/bazodiac_spec_master.md

## Mapping Functions (Normative)

### 1. Ingress vs Apex: Definitionen und Konventionen

We distinguish:

- Ingress convention: sector boundaries at multiples of 30 deg (0,30,60,...).
- Apex convention: sector centers at multiples of 30 deg, with boundaries +/- 15 deg.

The engine MUST declare a single branch coordinate convention:

- SHIFT_BOUNDARIES (recommended default): keep longitudes unchanged; shift the branch boundaries.
- SHIFT_LONGITUDES (optional): shift longitudes by phi_apex_offset_deg; boundaries stay at canonical boundaries.

Mixing these conventions in one computation graph is forbidden and MUST trigger
INCONSISTENT_BRANCH_ORIGIN_FOR_SHIFTED_LONGITUDES.

### 2. Month Branch from Solar Longitude (Apex/ZhongQi-consistent)

Parameters:

- zi_apex_deg = 270.0 (tropical, ofDate)  # default
- branch_width_deg = 30.0
- half_width_deg = 15.0
- interval_convention = HALF_OPEN

Definition (SHIFT_BOUNDARIES):
Let the Zi month be centered at zi_apex_deg.
Then Zi month boundaries are:
  [zi_apex_deg - half_width_deg, zi_apex_deg + half_width_deg)
i.e. [255, 285) when zi_apex_deg=270.

Month branch index b_month is:
  b_month = floor( wrap360(lambda_sun_deg - (zi_apex_deg - half_width_deg)) / branch_width_deg )
with b_month in {0..11} and b_month=0 meaning Zi.

This is equivalent to:

- Zi sector: [255, 285)
- Chou: [285, 315)
- ...
and resolves the ingress-vs-apex ambiguity deterministically.

Note:
If month_boundary_mode = JIEQI_CROSSING, the engine MUST use solar-term crossings
as boundaries and MUST still output the implied apex center and distances-to-boundary
for diagnostics (stability).

### 3. Hour Branch as Solar-Time Phase (TLST) and as Solar Hour Angle (H)

Hour branch classification MUST be based on TLST (True Local Solar Time) when available.
We define two equivalent views:

(A) TLST binning (canonical):
  hour_branch = floor( ((TLST_hours + 1) mod 24) / 2 )
with hour_branch=0 meaning Zi (23:00-01:00), HALF_OPEN intervals.

(B) Solar-time phase angle:
Define gamma_deg = wrap360( 15 * TLST_hours )
Interpret TLST midnight as gamma_deg = 0 deg.
Then Zi sector is:
  [345, 15) in circular sense, which is implemented as:
  hour_branch = floor( wrap360(gamma_deg - 345) / 30 )

The engine MUST expose (for explainability and debugging):

- TLST_hours
- gamma_deg
- distance_to_hour_boundary_minutes

Optional: solar hour angle H (astronomy convention):
  H_deg = wrap180( 15 * (TLST_hours - 12) )
This is equivalent information; using H_deg is allowed, but the implementation MUST
remain consistent with HALF_OPEN intervals and the Zi=23-01 bin definition.

### 4. Jupiter / Tai Sui: optional fusion feature channel (NOT a silent Year-Pillar change)

The BaZi Year Pillar remains solar-year ruleset-based (e.g., LiChun boundary).
Separately, the fusion layer MAY expose an additional "annual-cycle" feature channel:

annual_cycle_mode:

- NONE
- PHYSICAL_JUPITER_LONGITUDE
- VIRTUAL_TAI_SUI (requires explicit ruleset definition; may be MISSING)

If PHYSICAL_JUPITER_LONGITUDE:

- compute lambda_jupiter_deg via ephemeris provider
- map to branches using the same branch mapping operator as other bodies
- record provenance: ephemeris_id, time_scale_used, zodiac_mode, epoch_id

If VIRTUAL_TAI_SUI:

- engine MUST require explicit ruleset definition of TaiSui mapping.
- if missing, /validate MUST emit MISSING_TAI_SUI_RULESET and disable this channel.

Rationale:
This preserves BaZi semantics while allowing a mathematically clean, optional
astronomical bridge for fusion experiments.

1) Ruleset Interface Patch (was muss im Ruleset stehen, damit es sauber bleibt?)

Ergaenzung zu rulesets/standard_bazi_2026.json (oder als Schema-Anforderung):

{
  "ruleset_extensions": {
    "month_apex_definition": {
      "zi_apex_deg": 270.0,
      "zodiac_mode": "tropical",
      "epoch_id": "ofDate",
      "interval_convention": "HALF_OPEN"
    },
    "year_boundary_definition": {
      "mode": "solar_longitude_crossing",
      "solar_longitude_deg": 315.0,
      "time_scale": "TT",
      "zodiac_mode": "tropical"
    },
    "optional_annual_cycle": {
      "tai_sui_mapping": "MISSING"
    }
  }
}

Normative Konsequenz:

Wenn month_branch_calc = jieqi_segments, muessen die tatsaechlichen crossing times aus der Ephemeris-/TimeChain berechenbar sein, sonst -> DEGRADED + MISSING_JIEQI_CROSSINGS.

1) /validate: neue Failure Modes und Codes (minimal)
3.1 Neue Error/Warn Codes (nur wenn ihr Tai Sui Channel aktiviert)

MISSING_TAI_SUI_RULESET (ERROR in STRICT, WARNING sonst)

3.2 Neue Evidence Felder (empfohlen)

evidence.time.distance_to_hour_boundary_minutes

evidence.discretization.hour_branch_boundary_distance_min

1) Testvektoren (synthetisch, deterministisch)
TV-MONTH-APEX-001 (SHIFT_BOUNDARIES, zi_apex=270)

lambda_sun=275 -> Zi (0)

lambda_sun=284.9999 -> Zi (0)

lambda_sun=285 -> Chou (1)

lambda_sun=255 -> Zi (0)

lambda_sun=254.9999 -> Hai (11)

TV-HOUR-TLST-001 (HALF_OPEN, Zi=23-01)

TLST=23.0000 -> Zi (0)

TLST=00.9999 -> Zi (0)

TLST=01.0000 -> Chou (1)

TLST=22.9999 -> Hai (11)

TV-HOUR-PHASE-001 (gamma equivalence)

TLST=23 -> gamma=345 -> Zi (0)

TLST=1 -> gamma=15 -> Chou (1)
Assert: hour_branch(TLST-binning) == hour_branch(gamma-mapping)

TV-ANNUAL-JUPITER-001 (optional channel)

if annual_cycle_mode=PHYSICAL_JUPITER_LONGITUDE:

engine returns feature annual_branch_from_jupiter with provenance

if annual_cycle_mode=VIRTUAL_TAI_SUI and mapping missing:

/validate emits MISSING_TAI_SUI_RULESET

1) Was wird dadurch praeziser/besser?

Zi-Sektor Formel ist komplett und implementierbar:

Zi = [255,285) (bei zi_apex=270), HALF_OPEN eindeutig.

Hour-Branch ist wirklich "dieselbe Formel" (nur anderer Winkelraum):

TLST-binning und solar-time phase gamma sind formal gleichwertig.

Optionaler Hour Angle H ist sauber eingebettet (ohne Branch-Def zu veraendern).

Jupiter/Tai Sui wird nicht zum semantischen Stolperdraht:

BaZi Year Pillar bleibt BaZi.

Jupiter/Tai Sui sind definierte, optionale Fusion-Features mit harter Provenance und MISSING-Regeln.
