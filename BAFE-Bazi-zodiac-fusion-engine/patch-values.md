1) /validate Endpoint: JSON Schema (Draft-07)
1.1 Request Schema: ValidateRequest.schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "<https://bazodiac.example/schemas/ValidateRequest.schema.json>",
  "title": "ValidateRequest",
  "type": "object",
  "additionalProperties": false,
  "required": ["engine_config"],
  "properties": {
    "engine_config": { "$ref": "#/definitions/EngineConfig" },

    "birth_event": { "$ref": "#/definitions/BirthEvent" },

    "ruleset_inline": { "$ref": "#/definitions/BaZiRuleset" },
    "ruleset_id": { "type": "string" },

    "refdata_manifest_inline": { "$ref": "#/definitions/RefDataManifest" },
    "refdata_pack_id": { "type": "string" },

    "positions_override": {
      "description": "Optional override of western body positions (skips ephemeris).",
      "type": ["object", "null"],
      "additionalProperties": false,
      "properties": {
        "time_scale": { "type": "string", "enum": ["TT", "UTC", "UT1"] },
        "bodies": {
          "type": "array",
          "items": { "$ref": "#/definitions/BodyPosition" }
        }
      }
    },

    "bazi_pillars_override": {
      "description": "Optional override of BaZi pillars (skips anchor dependency).",
      "type": ["object", "null"],
      "additionalProperties": false,
      "properties": {
        "pillars": {
          "type": "array",
          "minItems": 4,
          "maxItems": 4,
          "items": { "$ref": "#/definitions/Pillar" }
        }
      }
    },

    "validate_level": {
      "type": "string",
      "enum": ["BASIC", "FULL"],
      "default": "FULL"
    },

    "now_utc_override": {
      "description": "For deterministic tests: fixed 'now' used for expiry checks.",
      "type": ["string", "null"],
      "format": "date-time"
    }
  },

  "definitions": {
    "EngineConfig": {
      "type": "object",
      "additionalProperties": true,
      "required": ["engine_version", "parameter_set_id", "deterministic", "refdata", "bazi_ruleset_id"],
      "properties": {
        "engine_version": { "type": "string" },
        "parameter_set_id": { "type": "string" },
        "deterministic": { "type": "boolean", "const": true },

        "compliance_mode": { "type": "string", "enum": ["STRICT", "RELAXED", "DEV"], "default": "RELAXED" },

        "epoch_id": { "type": "string" },
        "zodiac_mode": { "type": "string", "enum": ["tropical", "sidereal"] },
        "ayanamsa_id": { "type": ["string", "null"] },

        "time_standard": { "type": "string", "enum": ["CIVIL", "LMT", "TLST"] },
        "dst_policy": { "type": "string", "enum": ["error", "earlier", "later"], "default": "error" },

        "interval_convention": { "type": "string", "enum": ["HALF_OPEN"], "default": "HALF_OPEN" },

        "branch_coordinate_convention": {
          "type": "string",
          "enum": ["SHIFT_BOUNDARIES", "SHIFT_LONGITUDES"],
          "default": "SHIFT_BOUNDARIES"
        },
        "phi_apex_offset_deg": { "type": "number", "default": 15.0 },
        "zi_apex_deg": { "type": "number", "default": 270.0 },
        "branch_width_deg": { "type": "number", "default": 30.0 },

        "month_boundary_mode": { "type": "string", "enum": ["JIEQI_CROSSING", "APEX_SEGMENTS"], "default": "JIEQI_CROSSING" },
        "month_start_solar_longitude_deg": { "type": "number", "default": 315.0 },

        "bazi_ruleset_id": { "type": "string" },

        "json_canonicalization": {
          "type": ["object", "null"],
          "additionalProperties": false,
          "properties": {
            "sorted_keys": { "type": "boolean", "default": true },
            "utf8": { "type": "boolean", "default": true }
          }
        },
        "float_format_policy": {
          "type": ["object", "null"],
          "additionalProperties": false,
          "properties": {
            "mode": { "type": "string", "enum": ["fixed", "shortest_roundtrip"], "default": "shortest_roundtrip" },
            "fixed_decimals": { "type": ["integer", "null"], "minimum": 0, "maximum": 18 }
          }
        },

        "time_fallback_policy": {
          "type": ["object", "null"],
          "additionalProperties": false,
          "properties": {
            "allow_tt_from_ut1_plus_deltat_override": { "type": "boolean", "default": false },
            "allow_compute_tlst_without_ut1": { "type": "boolean", "default": false }
          }
        },

        "refdata": { "$ref": "#/definitions/RefDataConfig" }
      }
    },

    "RefDataConfig": {
      "type": "object",
      "additionalProperties": false,
      "required": ["refdata_pack_id", "refdata_mode", "allow_network", "ephemeris_id", "tzdb_version_id", "leaps_source_id", "verification_policy"],
      "properties": {
        "refdata_pack_id": { "type": "string" },
        "refdata_mode": { "type": "string", "enum": ["BUNDLED_OFFLINE", "LOCAL_MIRROR", "PROVIDER_BACKED"] },
        "refdata_root_path": { "type": ["string", "null"] },
        "allow_network": { "type": "boolean" },

        "ephemeris_id": { "type": "string" },
        "tzdb_version_id": { "type": "string" },
        "leaps_source_id": { "type": "string" },
        "eop_source_id": { "type": ["string", "null"] },

        "verification_policy": {
          "type": "object",
          "additionalProperties": false,
          "required": ["tzdb_gpg_required", "ephemeris_hash_required", "eop_redundancy_required", "leaps_expiry_enforced"],
          "properties": {
            "tzdb_gpg_required": { "type": "boolean" },
            "ephemeris_hash_required": { "type": "boolean" },
            "eop_redundancy_required": { "type": "boolean" },
            "leaps_expiry_enforced": { "type": "boolean" }
          }
        }
      }
    },

    "BirthEvent": {
      "type": "object",
      "additionalProperties": false,
      "required": ["local_datetime", "geo_lon_deg", "geo_lat_deg"],
      "properties": {
        "local_datetime": { "type": "string", "format": "date-time" },
        "tz_id": { "type": ["string", "null"] },
        "tz_offset_sec": { "type": ["integer", "null"] },
        "dst_policy": { "type": ["string", "null"], "enum": ["error", "earlier", "later", null] },
        "geo_lon_deg": { "type": "number", "minimum": -180, "maximum": 180 },
        "geo_lat_deg": { "type": "number", "minimum": -90, "maximum": 90 }
      }
    },

    "BodyPosition": {
      "type": "object",
      "additionalProperties": false,
      "required": ["body", "lambda_deg"],
      "properties": {
        "body": { "type": "string" },
        "lambda_deg": { "type": "number", "minimum": 0, "exclusiveMaximum": 360 },
        "beta_deg": { "type": ["number", "null"], "minimum": -90, "maximum": 90 },
        "speed_deg_per_day": { "type": ["number", "null"] },
        "retrograde": { "type": ["boolean", "null"] }
      }
    },

    "Pillar": {
      "type": "object",
      "additionalProperties": false,
      "required": ["stem_index", "branch_index"],
      "properties": {
        "stem_index": { "type": "integer", "minimum": 0, "maximum": 9 },
        "branch_index": { "type": "integer", "minimum": 0, "maximum": 11 }
      }
    },

    "BaZiRuleset": {
      "type": "object",
      "additionalProperties": true,
      "required": ["ruleset_id"],
      "properties": {
        "ruleset_id": { "type": "string" }
      }
    },

    "RefDataManifest": {
      "type": "object",
      "additionalProperties": true,
      "required": ["pack_id", "artifacts"],
      "properties": {
        "pack_id": { "type": "string" },
        "artifacts": { "type": "array" }
      }
    }
  }
}

1.2 Response Schema: ValidateResponse.schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "<https://bazodiac.example/schemas/ValidateResponse.schema.json>",
  "title": "ValidateResponse",
  "type": "object",
  "additionalProperties": false,
  "required": ["compliance_status", "compliance_components", "errors", "warnings", "evidence"],
  "properties": {
    "compliance_status": {
      "type": "string",
      "enum": ["COMPLIANT", "DEGRADED", "NON_COMPLIANT"]
    },

    "compliance_components": {
      "type": "object",
      "additionalProperties": false,
      "required": ["REFDATA", "TIME", "FRAMES", "EPHEMERIS", "DISCRETIZATION", "REPRODUCIBILITY", "INTERPRETATION_POLICY"],
      "properties": {
        "REFDATA": { "$ref": "#/definitions/ComponentStatus" },
        "TIME": { "$ref": "#/definitions/ComponentStatus" },
        "FRAMES": { "$ref": "#/definitions/ComponentStatus" },
        "EPHEMERIS": { "$ref": "#/definitions/ComponentStatus" },
        "DISCRETIZATION": { "$ref": "#/definitions/ComponentStatus" },
        "REPRODUCIBILITY": { "$ref": "#/definitions/ComponentStatus" },
        "INTERPRETATION_POLICY": { "$ref": "#/definitions/ComponentStatus" }
      }
    },

    "errors": {
      "type": "array",
      "items": { "$ref": "#/definitions/Issue" }
    },

    "warnings": {
      "type": "array",
      "items": { "$ref": "#/definitions/Issue" }
    },

    "evidence": {
      "type": "object",
      "additionalProperties": false,
      "required": ["refdata", "time", "discretization", "reproducibility"],
      "properties": {
        "refdata": { "$ref": "#/definitions/RefDataEvidence" },
        "time": { "$ref": "#/definitions/TimeEvidence" },
        "frames": { "$ref": "#/definitions/FramesEvidence" },
        "ephemeris": { "$ref": "#/definitions/EphemerisEvidence" },
        "discretization": { "$ref": "#/definitions/DiscretizationEvidence" },
        "reproducibility": { "$ref": "#/definitions/ReproEvidence" },
        "interpretation": { "$ref": "#/definitions/InterpEvidence" }
      }
    }
  },

  "definitions": {
    "ComponentStatus": {
      "type": "object",
      "additionalProperties": false,
      "required": ["status"],
      "properties": {
        "status": { "type": "string", "enum": ["OK", "DEGRADED", "FAIL"] },
        "notes": { "type": "array", "items": { "type": "string" } }
      }
    },

    "Issue": {
      "type": "object",
      "additionalProperties": false,
      "required": ["code", "message"],
      "properties": {
        "code": { "$ref": "#/definitions/ErrorCode" },
        "message": { "type": "string" },
        "severity": { "type": "string", "enum": ["ERROR", "WARNING"], "default": "ERROR" },
        "path": { "type": ["string", "null"], "description": "JSON pointer-like location, if applicable." },
        "details": { "type": ["object", "null"] }
      }
    },

    "ErrorCode": {
      "type": "string",
      "enum": [
        "REFDATA_NETWORK_FORBIDDEN",
        "REFDATA_MANIFEST_MISSING",
        "EPHEMERIS_HASH_MISMATCH",
        "EPHEMERIS_MISSING",
        "TZDB_SIGNATURE_INVALID",
        "LEAP_SECONDS_FILE_EXPIRED",
        "MISSING_TT",
        "EOP_MISSING",
        "EOP_STALE",
        "EOP_PREDICTED_REGION_USED",
        "DST_AMBIGUOUS_LOCAL_TIME",
        "DST_NONEXISTENT_LOCAL_TIME",
        "INCONSISTENT_BRANCH_ORIGIN_FOR_SHIFTED_LONGITUDES",
        "MISSING_DAY_CYCLE_ANCHOR",
        "MISSING_AYANAMSA_ID",
        "INTERP_DERIVATION_EMPTY",
        "INTERP_LINT_FAIL"
      ]
    },

    "RefDataEvidence": {
      "type": "object",
      "additionalProperties": false,
      "required": ["refdata_pack_id", "allow_network", "mode", "artifacts"],
      "properties": {
        "refdata_pack_id": { "type": "string" },
        "allow_network": { "type": "boolean" },
        "mode": { "type": "string", "enum": ["BUNDLED_OFFLINE", "LOCAL_MIRROR", "PROVIDER_BACKED"] },
        "artifacts": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "ephemeris": { "$ref": "#/definitions/ArtifactEvidence" },
            "tzdb": { "$ref": "#/definitions/ArtifactEvidence" },
            "leaps": { "$ref": "#/definitions/ArtifactEvidence" },
            "eop": { "$ref": "#/definitions/ArtifactEvidence" }
          }
        }
      }
    },

    "ArtifactEvidence": {
      "type": "object",
      "additionalProperties": false,
      "required": ["logical_id", "present"],
      "properties": {
        "logical_id": { "type": "string" },
        "present": { "type": "boolean" },
        "verified": { "type": ["boolean", "null"] },
        "hash_sha256": { "type": ["string", "null"] },
        "signature_ok": { "type": ["boolean", "null"] },
        "expires_utc": { "type": ["string", "null"], "format": "date-time" },
        "stale": { "type": ["boolean", "null"] },
        "notes": { "type": "array", "items": { "type": "string" } }
      }
    },

    "TimeEvidence": {
      "type": "object",
      "additionalProperties": false,
      "required": ["time_standard", "dst_policy", "ut1_quality", "tt_quality", "tlst_quality"],
      "properties": {
        "time_standard": { "type": "string", "enum": ["CIVIL", "LMT", "TLST"] },
        "dst_policy": { "type": "string", "enum": ["error", "earlier", "later"] },
        "ut1_quality": { "type": "string", "enum": ["ok", "predicted", "missing"] },
        "tt_quality": { "type": "string", "enum": ["ok", "missing"] },
        "tlst_quality": { "type": "string", "enum": ["ok", "degraded", "missing"] },
        "eot_provenance": { "type": ["string", "null"] },
        "uncertainty_budget_sec": { "type": ["number", "null"] }
      }
    },

    "FramesEvidence": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "epoch_id": { "type": ["string", "null"] },
        "precession_model_id": { "type": ["string", "null"] },
        "obliquity_model_id": { "type": ["string", "null"] },
        "zodiac_mode": { "type": ["string", "null"] },
        "ayanamsa_id": { "type": ["string", "null"] }
      }
    },

    "EphemerisEvidence": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "ephemeris_id": { "type": ["string", "null"] },
        "time_scale": { "type": ["string", "null"], "enum": ["TT", "TDB", "UTC", "UT1", null] },
        "bodies": { "type": "array", "items": { "type": "string" } }
      }
    },

    "DiscretizationEvidence": {
      "type": "object",
      "additionalProperties": false,
      "required": ["interval_convention", "branch_coordinate_convention"],
      "properties": {
        "interval_convention": { "type": "string", "enum": ["HALF_OPEN"] },
        "branch_coordinate_convention": { "type": "string", "enum": ["SHIFT_BOUNDARIES", "SHIFT_LONGITUDES"] },
        "boundary_distance_deg": { "type": ["number", "null"] },
        "classification_unstable": { "type": ["boolean", "null"] }
      }
    },

    "ReproEvidence": {
      "type": "object",
      "additionalProperties": false,
      "required": ["config_fingerprint", "float_format_policy", "json_canonicalization"],
      "properties": {
        "config_fingerprint": { "type": "string" },
        "float_format_policy": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "mode": { "type": "string", "enum": ["fixed", "shortest_roundtrip"] },
            "fixed_decimals": { "type": ["integer", "null"] }
          }
        },
        "json_canonicalization": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "sorted_keys": { "type": "boolean" },
            "utf8": { "type": "boolean" }
          }
        }
      }
    },

    "InterpEvidence": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "lint_status": { "type": ["string", "null"], "enum": ["PASS", "FAIL", null] },
        "statements_returned": { "type": ["integer", "null"], "minimum": 0 }
      }
    }
  }
}

1) Acceptance Test Matrix (Epic -> Tests -> Checks/Codes)

Die Matrix ist so geschrieben, dass du sie direkt in Jira/Linear als Acceptance Criteria pro Epic uebernehmen kannst.

2.1 Gemeinsame Test-IDs (TV = test vector, PT = property test)

TV1 Branch boundary (HALF_OPEN)

TV2 Convention equivalence (K1 == K2)

TV3 Forbidden mixing detector (SHIFT_LONGITUDES misuse)

TV4 TLST hour boundary

TV5 Soft kernel symmetry + normalization

TV6 Hidden stems mapping correctness

TV7 Refdata policy checks (network guard, signature/hash)

PT1 wrap360/wrap180 periodicity

PT2 kernel sum(weights)=1

PT3 harmonic degeneracy/periodicity

PT4 canonical JSON determinism (fingerprint stable)

2.2 Epic-level Acceptance Criteria
Epic E0: Spec compliance harness (/validate skeleton)

Must pass:

TV1, TV3, PT1, PT4 (at least on mocked data paths)
Must output:

compliance_status, compliance_components, errors[], warnings[], evidence{...}
Failure codes expected:

if missing required fields: REFDATA_MANIFEST_MISSING or schema-level validation fail (pre-validate)

Epic E1-mini: RefData contract (provenance + network guard)

Must pass:

TV7 (network guard)

Response includes evidence.refdata + artifact presence flags
Expected codes:

Offline mode + allow_network=true or any attempted network: REFDATA_NETWORK_FORBIDDEN

Missing manifest in offline modes: REFDATA_MANIFEST_MISSING

Epic E2: TimeModel + TLST

Must pass:

TV4

DST fold/gap tests:

ambiguous local time + dst_policy=error -> DST_AMBIGUOUS_LOCAL_TIME

nonexistent local time + dst_policy=error -> DST_NONEXISTENT_LOCAL_TIME
Quality flags:

evidence.time.ut1_quality in {ok,predicted,missing}

evidence.time.tlst_quality in {ok,degraded,missing}
Expected codes:

Leap seconds expired in STRICT: LEAP_SECONDS_FILE_EXPIRED

Missing TT when required in STRICT: MISSING_TT

Epic E4: Branch mapping (SHIFT_BOUNDARIES canonical + K2 optional)

Must pass:

TV1 always

TV2 if SHIFT_LONGITUDES implemented

TV3 always
Expected codes:

mixing error: INCONSISTENT_BRANCH_ORIGIN_FOR_SHIFTED_LONGITUDES

Epic E3-lite: Ruleset loader + Hidden Stems + Stem rules

Must pass:

TV6

day anchor enforcement:

if no anchor and no override: MISSING_DAY_CYCLE_ANCHOR
Must output:

hidden stems per branch/pillar in deterministic order
Optional:

weighting validation if enabled (sum/positivity)

Epic E5a: FeatureExtractor + BridgeOperators

Must pass:

TV5, PT2
Must output:

hard mapped branch per body (if enabled)

soft weights with sum=1, symmetric cases correct
Failure behaviors:

if kernel params missing: mark as error or disable feature channel per policy (but never silently)

Epic E5b: Harmonics/Phasors

Must pass:

PT3
Must output:

R_k, O_k, A_k, I_k

degeneracy flags when norms are zero
Must declare:

harmonic_phase_convention in config/evidence

Epic E1-full: Offline packs + verification

Must pass:

TV7 expanded:

tzdb signature required -> invalid signature: TZDB_SIGNATURE_INVALID

ephemeris hash required -> mismatch: EPHEMERIS_HASH_MISMATCH

missing ephemeris: EPHEMERIS_MISSING

leaps expiry enforced: LEAP_SECONDS_FILE_EXPIRED
Optional:

eop sanity flags: EOP_STALE, EOP_MISSING, EOP_PREDICTED_REGION_USED (warn)

Epic E6: Interpretation ruleset + claim-linter

Must pass:

Lint gating:

empty derived_from_features -> INTERP_DERIVATION_EMPTY

lint fail -> INTERP_LINT_FAIL
Strict behavior:

If compliance_mode=STRICT and lint fails: return no narrative statements + error

1) Minimal "definition of done" for /validate itself

The endpoint MUST validate inputs, config, refdata policy, time chain feasibility, and mapping conventions even if actual chart computation is not fully implemented yet.

The endpoint MUST be stable for CI: allow now_utc_override for deterministic expiry tests.
