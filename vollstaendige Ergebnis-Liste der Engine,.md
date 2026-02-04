vollstaendige Ergebnis-Liste der Engine, ohne Deutungs-/Interpretationsengine. Ich liste sie so, dass ihr daraus direkt das Response-JSON (z.B. /chart oder /features) bauen koennt. Ich trenne in MUST (immer liefern) und MAY (optional, config-abhaengig).

1) Meta und Reproduzierbarkeit (MUST)

engine_version (SemVer)

parameter_set_id (welche Parameter/Defaults)

deterministic=true

timestamp_utc (wann diese Berechnung lief; fuer Debug, nicht fuer Determinismus relevant)

config_fingerprint (sha256 ueber canonical engine_config + ruleset_id/version + refdata ids)

compliance_mode (STRICT|RELAXED|DEV)

1) Provenance / Referenzdaten (MUST)

Block refdata (oder refdata_provenance), mindestens:

refdata_pack_id

refdata_mode (BUNDLED_OFFLINE|LOCAL_MIRROR|PROVIDER_BACKED)

allow_network (bool)

ephemeris_id (z.B. JPL_DE442 oder SwissEph_x.y)

tzdb_version_id

leaps_source_id

eop_source_id (nullable)

Je Artefakt:

present (bool)

verified (bool|null)

hash_sha256 (string|null)

signature_ok (bool|null, tzdb)

expires_utc (string|null, leap seconds)

stale (bool|null)

notes[] (optional)

1) Eingabe-Echo (MUST fuer Audit)

birth_event echo:

local_datetime_input

tz_id oder tz_offset_sec

dst_policy

geo_lon_deg, geo_lat_deg

engine_config echo (oder engine_config_id + diff, je nach API-Design)

1) Zeitmodell / Timescales (MUST als Struktur, einzelne Felder koennen null sein)

Block time_scales:

utc (ISO8601 Z) (MUST wenn tz resolve klappt)

ut1 (ISO8601 Z | null)

tt (ISO8601 Z | null)

jd_utc (float|null)

jd_ut1 (float|null)

jd_tt (float|null)

Lokale Sonnenzeiten:

lmst_hours (0..24 | null)

tlst_hours (0..24 | null)

Korrekturglieder/Provenance:

dut1_sec (float|null) + dut1_source (override|eop|null)

delta_t_sec (float|null) + delta_t_source (override|model|null)

eot_min (float|null) + eot_source (override|approx_method|ephemeris_method|null)

Qualitaet/Flags (MUST):

quality:

utc: ok|missing

ut1: ok|predicted|missing

tt: ok|missing

tlst: ok|degraded|missing

staleness_flags:

tzdb_stale

leaps_expired

eop_missing

eop_stale

eop_predicted_region

1) Westliche Ephemeriden-Ergebnisse (MUST wenn keine overrides)

Array positions[] pro Body (mindestens Sonne; weitere konfigurierbar):
Pro Body:

body (string, z.B. "Sun")

lambda_deg (0..360) ekliptikale Laenge

beta_deg (optional, ekliptikale Breite)

speed_deg_per_day (optional)

retrograde (optional bool)

Provenance:

time_scale_used (TT|TDB etc.)

epoch_id (J2000|ofDate|custom)

zodiac_mode (tropical|sidereal)

ayanamsa_id (wenn sidereal)

ephemeris_id echo (oder nur im refdata-block)

Derived west (MUST wenn ihr es braucht, sonst MAY):

sign_index (0..11)

degree_in_sign (0..30)

half_sign_flag (bool; <15 oder >=15)

1) Koordinaten-Transformationen (MAY, aber stark empfohlen wenn ihr "astronomisch sauber" seid)

Wenn ihr alpha/delta oder eq<->ecl braucht:

obliquity_epsilon_deg (und model id)

alpha_deg, delta_deg (optional pro body)

transform_provenance:

atan2_used=true

model_ids (precession/obliquity)

1) BaZi Core Ergebnisse (MUST als Struktur; Teile koennen MISSING/null sein je Ruleset)

Block bazi:

ruleset_id, ruleset_version

pillars (year, month, day, hour):

year: {stem_index, branch_index, sexagenary_index|null}

month: {stem_index, branch_index, sexagenary_index|null}

day: {stem_index, branch_index, sexagenary_index|null}

hour: {stem_index, branch_index, sexagenary_index|null}

Optional: stem_name, branch_name als derived lookup (kein "Deutung", nur Label)

Hidden stems (MUST wenn ruleset enthaelt):

hidden_stems_by_pillar:

pro pillar branch: ordered list ["Ji","Gui","Xin"] etc.

optional gewichtet:

list of {stem_index|stem_name, role, weight}

Boundary Diagnostics (MUST wenn ihr Stabilitaet braucht, sonst MAY):

month_boundary_mode (JIEQI_CROSSING|APEX_SEGMENTS)

month_index_0_definition (z.B. Yin-at-315)

boundary_distance:

month_boundary_distance_deg (float|null)

hour_boundary_distance_min (float|null)

year_boundary_distance_deg (float|null)

classification_unstable_flags:

month_branch_unstable (bool)

hour_branch_unstable (bool)

year_pillar_unstable (bool)

1) Diskret-Kontinuum Bruecken (MUST wenn Fusion aktiv ist; sonst MAY)
7.1 Hard mapping (Segments)

branch_coordinate_convention (SHIFT_BOUNDARIES|SHIFT_LONGITUDES)

phi_apex_offset_deg, zi_apex_deg, branch_width_deg

planet_to_branch:

map body -> branch_index (0..11)

plus branch_center_deg (optional)

plus distance_to_boundary_deg (optional)

7.2 Soft kernel weights (wenn fusion_mode=soft_kernel) (MAY)

planet_branch_weights:

pro body: array[12] weights, sum=1

kernel:

type (von_mises etc.)

kappa (float)

normalization_ok (bool)

1) Harmonic/Phasor Features (wenn fusion_mode=harmonic_phasor) (MAY)

Pro k in harmonics_k:

R_k (BaZi phasor):

re, im, abs

O_k (West phasor):

re, im, abs

Fusion terms:

X_k = Re(conj(R_k)*O_k) (float)

I_k = |R_k + O_k|^2 (float)

A_k = alignment in [-1,1] (float, mit eps norm)

Flags:

harmonic_degenerate (bool)

Und MUST dazu:

harmonic_phase_convention (raw_lambda vs apex_shifted_lambda etc.)

pillar_weights + planet_weights (die verwendeten Gewichte)

1) Fusion Output (ohne Deutung) (MUST wenn fusion requested)

Ein reiner numerischer/strukturierter Block fusion:

fusion_mode (hard_segment|soft_kernel|harmonic_phasor)

fusion_features (key->value Map, strikt definiert und versioniert)

feature_provenance:

welche Eingangsfeatures wurden genutzt (ids/keys)

welche Operatoren/Parameter (kernel/harmonics)

1) Validierungsausgabe (MUST)

Block validation:

ok (bool)

compliance_status (COMPLIANT|DEGRADED|NON_COMPLIANT)

errors[] (mit stable code, message, path, details)

warnings[]

assertions[] (welche Invarianten geprueft wurden)

evidence (wie im /validate schema: refdata/time/discretization/repro etc.)

1) Optional: Debug/Trace (MAY, aber sehr nuetzlich)

Nur wenn debug=true:

intermediate:

lambda_sun_deg_raw

lambda_sun_deg_apex_shifted

month_jieqi_crossing_times[] (timestamps)

atan2_inputs snapshots (optional)

performance:

timings per module

Kurz zusammengefasst: "Welche Ergebnisse liefert die Engine?"

Ohne Deutung liefert sie Zeitmodelle + Koordinaten/Ephemeriden + BaZi-Pillars/HiddenStems + Bruecken-Features (hard/soft/harmonic) + Validierung/Provenance.
