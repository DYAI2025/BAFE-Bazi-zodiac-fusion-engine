PATCH BUNDLE

patch_bundle_id: PATCH-BUNDLE-SCI-INT-001
includes: PATCH-SCI-001, PATCH-INT-001
breaking_change: false (but introduces new error codes)

1) Datei: spec/addenda/addendum_scientific_compliance_v1.md

# Addendum: Scientific Compliance v1

addendum_id: ADD-SCI-001
status: PROPOSED
applies_to_spec_version: ">=1.0.0-rc0"
patch_id: PATCH-SCI-001
breaking_change: false

## 0. Purpose

This addendum formalizes the "Scientific Compliance" gate for the BaZodiac Engine.
It operationalizes requirements stated in the master spec:

- deterministic operation
- no implicit downloads in offline modes
- explicit conventions (time/angles/frames)
- verifiable reference data packs
- /validate invariants + failure modes + error budget reporting

Non-goal:
This addendum does not assert metaphysical truth. It enforces technical reproducibility.

## 1. Placement in Implementation Plan (Phase mapping)

### Phase 0 (Single Source of Truth)

MUST:

- Create `spec/bazodiac_spec_master.md` as canonical.
- Register this addendum in the Addenda Registry.
SHOULD:
- Move policy-heavy compliance text into this file (keep contracts in JSON schemas).

### Phase 1 (Gap Analysis vs BC Engine V2)

MUST:

- Inventory matrix includes these compliance rows:
  - TimeModel chain and DST fold/gap behavior
  - RefData allow_network guard and manifest verification
  - /validate invariants + failure modes + error budget reporting
Deliverable:
- `gap_report.md` tags each row as DONE/PARTIAL/MISSING/CONFLICTS_SPEC.

### Phase 3 (Contract-first implementation order)

This addendum aligns with epics:

- E0: /validate skeleton + invariant framework
- E1: RefData subsystem (offline packs)
- E2: TimeModel + TLST, DST fold/gap, EoT provenance

## 2. Normative Requirements

### 2.1 RefData Integrity & Offline Reproducibility (RefDataManager)

MUST:

- If `refdata_mode in {BUNDLED_OFFLINE, LOCAL_MIRROR}` then:
  - `allow_network` MUST be false
  - any network access attempt MUST fail with error code `REFDATA_NETWORK_FORBIDDEN`
- In offline modes:
  - `refdata_root_path/live/manifest.json` MUST exist
- Verification rules (policy-driven):
  - tzdb: GPG signature MUST verify if `tzdb_gpg_required=true`
  - ephemeris: sha256 MUST match manifest if `ephemeris_hash_required=true`
  - leap seconds: expires_utc MUST be in the future if `leaps_expiry_enforced=true`
  - EOP: MUST run sanity-range checks
    - redundancy comparison SHOULD happen during pack build (sidecar), not at runtime

SHOULD:

- LOCAL_MIRROR uses sidecar pattern:
  - staging download -> verify -> atomic swap to live/
  - runtime reads only live/

MUST (provenance):

- All computational endpoints MUST echo:
  - engine_version, parameter_set_id, ruleset_id, refdata_pack_id
- All computational endpoints MUST include:
  - artifact presence + verification flags (ephemeris/tzdb/leaps/eop)

### 2.2 Time Scales Chain (f_time)

MUST:

- Implement Local -> UTC -> UT1/TT -> LMST/TLST as specified, including:
  - overrides
  - missing/degraded flags
  - provenance of correction terms

UT1 (MUST):

- If DUT1 override provided: UT1 = UTC + DUT1
- Else if EOP available: interpolate DUT1
- Else UT1 missing (flag ut1_quality=missing)

TT (MUST):

- If leap seconds valid: TT = UTC + (TAI-UTC) + 32.184s
- Else if DeltaT override + UT1 exists: TT = UT1 + DeltaT
- Else TT missing:
  - STRICT: error `MISSING_TT`
  - RELAXED/DEV: tt_quality=missing + degrade status

TLST (MUST):

- If EoT override: use it
- Else compute by chosen method and mark provenance
- If EoT missing and TLST requested: tlst_quality MUST be degraded

Diagnostics (MUST):

- Provide `distance_to_hour_boundary_minutes` for hour classification

Edge cases (MUST enumerate as failure modes):

- DST fold (ambiguous local time)
- DST gap (non-existent local time)
- tz invalid
- leap seconds expired
- EOP missing/stale/predicted region used

### 2.3 Angle/Frame Hygiene & Coordinate Transforms

MUST:

- atan2 MUST be used; arctan(y/x) MUST NOT be used
- Interval convention default is half-open [a,b) for segmentation
- wrap360/wrap180 MUST be used consistently, with tested invariants

### 2.4 Validation Contract (/validate)

MUST:

- /validate exists and runs invariants + failure modes (E0 acceptance)
- Invariants MUST include at minimum:
  - angle hygiene (wrap ranges, atan2 usage)
  - TLST hours range + degraded rule if EoT missing
  - branch convention mixing forbidden (SHIFT_LONGITUDES consistency)
  - refdata invariants (network forbidden, signature/hash/expiry)
- Failure modes MUST include at minimum:
  - DST fold/gap
  - tz invalid
  - leaps expired
  - EOP missing/stale/predicted region
  - ephemeris hash mismatch/missing
  - boundary instability for discretization
- Error budget policy MUST be reported per stage; unknown values MUST be MISSING

## 3. Required Repo Artifacts

### 3.1 Schemas (spec/schemas/)

MUST:

- ValidateRequest.schema.json
- ValidateResponse.schema.json
SHOULD:
- ChartResponse.schema.json (once /chart stabilized)

### 3.2 RefData schemas/templates (spec/refdata/)

MUST:

- manifest.schema.json
- refpack_manifest_template.json

### 3.3 Tests (spec/tests/)

MUST:

- tv1_branch_boundary.json
- tv4_tlst_boundary.json
- tv7_refdata_policy_guard.json
SHOULD:
- property tests:
  - wrap invariants, periodicity lambda+360n
  - kernel normalization
  - harmonic degeneracy
  - leap expiry enforcement

## 4. Definition of Done (DoD) for Iterations (E0-E2)

Iteration DoD:

- /validate returns:
  - invariants status
  - failure modes triggered/not triggered
  - error budget fields (typ/max or MISSING)
- offline modes never perform network I/O (guarded)
- output echoes engine_version, parameter_set_id, refdata_pack_id, ruleset_id

1) Datei: spec/addenda/addendum_interpretation_layer_v1.md

# Addendum: Interpretation Layer v1 (Fact / Rules / Narrative)

addendum_id: ADD-INT-001
status: PROPOSED
applies_to_spec_version: ">=1.0.0-rc0"
patch_id: PATCH-INT-001
breaking_change: false

## 0. Purpose

This addendum enforces that interpretation output is:

- optional
- deterministic
- strictly derived from numeric features
- explicitly separated from astronomical facts and symbolic rule outputs

It also enforces "claim boundaries":

- no statement is presented as scientific proof of metaphysical assertions

## 1. Layer Model (Schema-level)

MUST:

- Any response that includes interpretation MUST separate three layers:
  1) facts: astronomical/time outputs (UTC/UT1/TT, TLST, ephemeris positions, provenance)
  2) rules: discrete mappings (BaZi pillars, branch mapping, weights, harmonics features)
  3) interpretations: text statements

SHOULD:

- If include_interpretation=false, engine still returns valid facts/rules.

## 2. Statement Provenance

MUST:

- Each interpretation statement MUST contain:
  - statement_id (stable)
  - template_id (optional)
  - feature_refs: array of concrete feature keys (non-empty)
  - interpretation_ruleset_id + version
  - bazi_ruleset_id + version
  - provenance echo: engine_version, parameter_set_id, refdata_pack_id, config_fingerprint
  - stability_flags snapshot (boundary/time/refdata warnings)

If feature_refs is empty or missing:

- /validate MUST fail with error `INTERP_MISSING_FEATURE_REFS`

If include_interpretation=true but interpretation_ruleset_id missing:

- /validate MUST fail with error `INTERP_RULESET_ID_MISSING`

## 3. Claim Boundaries (Safety / Honesty Policy)

MUST NOT:

- Output any claim as scientific fact that the engine "proves" metaphysical assertions.

MUST:

- Include a short disclaimer (configurable string) when interpretation is enabled, e.g.:
  - "Symbolische, regelbasierte Ableitung; keine wissenschaftliche Faktbehauptung."
- Provide "why this statement" explainability:
  - feature_refs is the minimum requirement
  - optional: include threshold/logic references

## 4. Ambiguity Handling (Boundary + Time uncertainty)

MUST:

- If validation flags include any of:
  - DST fold/gap
  - tlst_quality=degraded/missing
  - classification_unstable near boundary
then InterpretationEngine MUST either:
  - produce a cautious variant, or
  - suppress the statement, or
  - present multiple conditional variants labeled A/B

## 5. Required Repo Artifacts

### 5.1 Rulesets (spec/rulesets/)

MUST (only if interpretation is shipped):

- interp_core_v1.json
  - versioned
  - thresholds/templates live here, not in code

### 5.2 Schemas (spec/schemas/)

SHOULD:

- InterpretationResponse.schema.json (once endpoint is live)
- Extend ValidateResponse.schema.json with:
  - INTERP_MISSING_FEATURE_REFS
  - INTERP_RULESET_ID_MISSING

## 6. Definition of Done (DoD)

- For any statement returned:
  - feature_refs is non-empty
  - statement is reproducible with same feature vector + ruleset
- Disabling interpretation does not change facts/rules
- /validate catches missing feature_refs and missing ruleset id as errors

1) Master spec: Addenda Registry Snippet

Datei: spec/bazodiac_spec_master.md (Snippet zum Einfuegen)

## Addenda Registry (normative)

This master spec is normative. The following addenda are normative unless stated otherwise:

- ADD-SCI-001: Scientific Compliance (time scales, refdata integrity, frames, edge cases, reproducibility)
  - File: addenda/addendum_scientific_compliance_v1.md
  - Applies to: spec_version 1.0.0-rc0+

- ADD-INT-001: Interpretation Layer (fact/rules/narrative separation, feature_refs, claim boundaries)
  - File: addenda/addendum_interpretation_layer_v1.md
  - Applies to: spec_version 1.0.0-rc0+

1) Changelog Snippet

Datei: spec/changelog.md (Snippet)

## [1.0.0-rc0] - YYYY-MM-DD

### Added

- ADD-SCI-001 Scientific Compliance Addendum v1
- ADD-INT-001 Interpretation Layer Addendum v1

1) Schema-Patch: Error Codes erweitern (ValidateResponse)

Ihr habt aktuell schon Codes wie INTERP_DERIVATION_EMPTY und INTERP_LINT_FAIL. Das neue Addendum verlangt zusaetzlich:

INTERP_MISSING_FEATURE_REFS

INTERP_RULESET_ID_MISSING

Empfehlung (praezise, stabil):

Behalten: INTERP_LINT_FAIL

Deprecate/alias: INTERP_DERIVATION_EMPTY -> ersetzt durch INTERP_MISSING_FEATURE_REFS

Validator darf intern beide erkennen, soll aber nach aussen bevorzugt INTERP_MISSING_FEATURE_REFS ausgeben.

Patch-Snippet fuer schemas/ValidateResponse.schema.json

(Ergaenzung der ErrorCode.enum Liste)

{
  "definitions": {
    "ErrorCode": {
      "type": "string",
      "enum": [
        "... existing codes ...",
        "INTERP_MISSING_FEATURE_REFS",
        "INTERP_RULESET_ID_MISSING"
      ]
    }
  }
}

Und in /validate Logik:

Wenn statement feature_refs missing/empty -> INTERP_MISSING_FEATURE_REFS

Wenn include_interpretation=true und ruleset id missing -> INTERP_RULESET_ID_MISSING

Wenn claim-linter fail -> INTERP_LINT_FAIL

Was sich dadurch verbessert (kurz, konkret)

Eure Addenda sind jetzt repo-faehig, normativ, phase-mapped.

/validate bekommt eindeutige neue Errors fuer Interpretation-Contracts.

Interpretation bleibt sauber pluginfaehig, ohne Fakten/Regeln zu beeinflussen.

Keine "versteckten" Netz-Zugriffe: RefData Guard ist jetzt als MUST festgenagelt.
