Kernverstaendnis

Ziel: Eine deterministische, reproduzierbare "BaZodiac-Engine" zu spezifizieren, die (a) BaZi als diskrete zyklische Algebra (Z10, Z12, Z60) und (b) westliche Astrologie als kontinuierliche Ekliptik-Geometrie (0..360 deg) in einem einheitlich berechenbaren Modellraum verbindet, ohne "mystische" Freitexterfindungen.

Gegebener Kontext: Zwei Vorschlaege (Ansatz_1, Ansatz_2). Ansatz_1 liefert einen brauchbaren, implementierbaren Kern fuer (i) Apex-vs-Ingress Phasenoffset (15 deg), (ii) True Local Solar Time (TLST) und (iii) quadrantenrobuste Winkelarithmetik (atan2). Ansatz_2 enthaelt mehrere Inkonsistenzen (u.a. Branch-Indexierung/Offset) und fuehrt interpretative Konstanten (z.B. feste Planet-Element-Zuordnung, Dignitieskalen) ein, die als "MISSING/Config" behandelt werden muessen.

Arbeitsannahmen (explizit):

Astrologische "Bedeutungen" werden hier als deterministic mapping rules aus Features modelliert, nicht als wissenschaftliche Fakten.

Ephemeriden, Leap-Seconds, DeltaT, DUT1, Praezessionsmodelle sind externe Inputs/Provider: wir spezifizieren Interfaces und Fehlerfortpflanzung, erfinden aber keine Tabellen/Katalogwerte.

Alle Winkeloperationen sind modulo/branch-cut-sicher (wrap360, wrap180, atan2).

Zielgroessen der Engine:

Reproduzierbare Features: BaZi-Pillars/Indices + westliche Positionen/Aspekte + definierte Kopplungsfeatures (Mapping, Harmonik, Interferenz).

Versionierbare Parameter-Sets (engine_version, parameter_set_id, epoch/time_standard flags).

Validierungs-Suite (synthetisch + Randfaelle) und API-Spezifikation.

Reasoning-Pfade
Phase 1 (PS+): Pipeline-Plan als austauschbare Module

Pipeline (Inputs -> Normalisierung -> Transformationskette -> Feature-Extraction -> Fusion -> Interpretation -> Output/Tests)

Inputs

Birth event: local_datetime, geo_lon, geo_lat, tz_id (oder tz_offset), dst_policy

Optional: override time corrections (DUT1, DeltaT, leap_seconds)

Engine config: epoch, precession_model, zodiac_mode, apex_offset, anchors, fusion_mode, thresholds

Normalisierung (Time/Angle Hygiene)

parse + validate input ranges

normalize angles with wrap360/wrap180

normalize times: local -> UTC -> UT1/TT (via provider) -> TLST

Transformationskette

(West) EphemerisProvider: ecliptic longitudes lambda_p(t) fuer bodies

(Coord) optional equatorial <-> ecliptic via explicit atan2 formulas

(BaZi) PillarCalculator: hour branch from TLST; month branch from lambda_sun + apex/anchor (oder jieqi-mode); year/day pillars via ruleset (MISSING constants -> parameterized)

Feature Extraction

West features: signs, degrees-in-sign, aspects (delta angles), houses (optional, MISSING house system), etc.

BaZi features: stems/branches indices, 60-cycle ids, hidden stems (optional)

Bridge features: angle->branch mapping (hard/soft), harmonic metrics, resonance scores

Fusion Operator

Optionally: harmonic/phasor embedding in complex plane; or vector concatenation + deterministic rules

Interpretation Layer

Deterministic rules: feature predicates -> text templates -> explanations referencing features

Output + Tests

/validate invariants, boundary checks, error budget propagation, instability flags near boundaries

Phase 2 (ToT): Drei plausible Fusions-Architekturen (A/B/C)
Thought A: "Koordinaten-Fusion zuerst" (ein gemeinsamer Raum, dann Features)

Idee: Mappe ALLES (auch BaZi) in eine einzige Winkelkoordinate (z.B. ekliptikale Laenge) und leite dann Features ab.

Pros:

Mathematisch "ein Raum", klare Geometrie.

Einfache Aspekt-/Harmonik-Analysen.

Cons/Risiken:

Stems (Z10) sind primaer zeitzyklisch; eine rein raeumliche Zuordnung ist modellhaft und kann willkuerlich wirken.

Gefahr, BaZi-Temporalstruktur zu "ueberschreiben".

Implementierbarkeit: mittel.
Mathematische Sauberkeit: mittel (wenn Stems nur als optionaler Embedding-Kanal).
Score: 0.72

Thought B: "Feature-Fusion zuerst" (je System Features, dann Operator)

Idee: Berechne BaZi-Features und West-Features getrennt; fusioniere als Vektor + rule operator.

Pros:

Robust, modular, minimal invasive.

Kein Zwang, BaZi-Zyklen in Ekliptik zu pressen.

Cons/Risiken:

Kopplung zwischen Systemen kann zu "heuristisch" werden, wenn keine saubere Brueckenfunktion existiert.

Gefahr: Interpretationslayer wird zu frei, wenn Fusion nicht streng formalisiert wird.

Implementierbarkeit: hoch.
Mathematische Sauberkeit: mittel bis hoch (wenn Fusion klar definiert).
Score: 0.84

Thought C: "Hybrid" (gemeinsame Zeitbasis + getrennte Raeume + Kopplungsterm)

Idee: Gemeinsames Zeitmodell (UTC/TT/TLST) als shared backbone. Dann:

BaZi bleibt in (Z10, Z12, Z60) bzw. deren unit-circle embeddings.

West bleibt im Kontinuum (0..360 deg) (Ekliptik) + optional equatorial.

Kopplung uebr harmonic operators (Fourier/phasor) und/oder angle->branch mapping (hard/soft).

Pros:

Respektiert beide Strukturen (diskret vs kontinuierlich).

Kopplung ist explizit und testbar (harmonic alignment, kernel weighting).

Passt direkt zu Ansatz_1 (15 deg offset, TLST, atan2).

Cons/Risiken:

Mehr Parameter (kappa, harmonics, weights).

Muss streng versioniert + validiert werden, sonst Overfitting.

Implementierbarkeit: hoch (mit klaren Interfaces).
Mathematische Sauberkeit: hoch (saubere Brueckenfunktionen).
Score: 0.90

Entscheidung: Architektur C ist beste Basis.

Kurz-CoVe (rueckwaerts) zu Ansatz_1 vs Ansatz_2 (Konsistenzcheck)

15 deg Offset: Ansatz_1 korrekt als modellierbarer Phasenparameter; Ansatz_2 kompatibel, aber seine Branch-Indexierung/Offset ist inkonsistent (Beispielrechnung ordnet "9" faelschlich "Zi" zu, wenn Standardorder gilt). => Wir uebernehmen den Ansatz_1-Anchor-Formalismus.

TLST: Ansatz_1 strukturell ok (LMST + EoT), aber wir machen es explizit modular mit UT1/TT/Provider statt impliziter Annahmen.

Interferenzmodell: Ansatz_1 liefert sauberes phasor framework; Ansatz_2 mischt interpretative Konstanten (Planet=Element, Dignitieskala). => Wir behalten die Mathematik, verschieben semantische Zuordnungen in config (MISSING/Ruleset).

Tool Calls & Evidenz

Action-ID: run_python_calculation
Grund: Verifikation der Kern-Mappingfunktionen (Branch-Sektor aus Sonnenlaenge) und TLST->Stundenbranch, inklusive Randfaelle (0/360, Grenzzeiten).
Parameter: zi_apex_deg=270, width_deg=30, hour formula h=floor(((TLST+1) mod 24)/2)

Ergebnisse (synthetisch, deterministisch):

Branch mapping:

lambda_sun=275.0 deg -> b=0 (Zi) (innerhalb [255,285))

lambda_sun=285.0 deg -> b=1 (Chou) (Grenze geht in naechsten Sektor)

lambda_sun=284.999 deg -> b=0

lambda_sun=255.0 deg -> b=0

lambda_sun=254.999 deg -> b=11 (Hai) (wrap-around korrekt)

Stundenbranch mapping (TLST in Stunden):

22.999 -> h=11 (Hai)

23.000 -> h=0 (Zi)

0.999 -> h=0 (Zi)

1.000 -> h=1 (Chou)

Property checks:

"lambda = center_of_branch(b)" mappt immer zu b.

Halb-offene Intervalle: [center-15, center+15) deterministisch.

Reflexion & Bias-Report

Universal-bias-self-check (kurz):

Anchoring-Bias: starke Anlehnung an Ansatz_1 (weil konsistenter). Mitigation: Architekturvergleich A/B/C + explizite Parametrisierung (zi_apex, offset).

Overconfidence-Risiko: BaZi-Pillar-Offsets/Regelwerke sind kulturhistorisch festgelegt; ohne Referenz darf ich sie nicht "hart codieren". Mitigation: Ruleset-Interfaces + MISSING fuer Epochenkonstanten/Tabellen.

Confirmation bias: Interferenzmodell klingt attraktiv; Mitigation: optionales Modul, klarer Parameterumfang, /validate fuer Overfitting-Warnungen.

Domain-mismatch: Westliche Houses/Dignities nicht spezifiziert. Mitigation: als optionale Features mit Ruleset-ID.

Unsicherheiten:

Exakte BaZi-Standardisierung (Tagwechsel-Regel, Month-by-JieQi vs Segment-Apex) ist konfigurationsabhaengig.

Exakte TT/UT1/DeltaT Datenquellen sind providerabhaengig.

Konfidenz (0..1) pro Hauptmodul:

Winkelarithmetik + Segmentmapping: 0.95

TLST-Formalisierung (modular): 0.85

Equatorial<->Ecliptic Transform (atan2): 0.90

BaZi-Pillar Vollberechnung (Year/Month/Day/Hour stems): 0.55 (wegen MISSING epoch/rules)

Fusion via Harmonik/Phasor: 0.80 (sauber formal, aber Parameterwahl kritisch)

Interpretation layer als deterministische Ableitung: 0.85

Synthese & Empfehlungen
<deliverable>

<executive_summary>
Die BaZodiac-Engine ist ein deterministisches Fusionssystem, das BaZi-Zyklen (Z10/Z12/Z60) und westliche Ekliptik-Geometrie (0..360 deg) ueber eine gemeinsame Zeitbasis (UTC/TT/TLST) und explizite Kopplungsoperatoren verbindet.
Neu ist (1) die formale Loesung des Ingress-vs-Apex Nullpunktproblems als versionierbarer Phasenparameter (typisch 15 deg), (2) ein modulares TLST-Zeitmodell mit separaten Korrekturgliedern (TZ/DST, DUT1, DeltaT, Equation of Time), und (3) eine mathematisch saubere Bruecke diskret<->kontinuierlich via (hard/soft) Segmentierung plus harmonischer Einbettung (phasor/Fourier).
Die Engine erfindet keine Ephemeriden oder historischen Tabellen; stattdessen definiert sie Provider-Interfaces, Fehlerbudgets, Invarianten und Testvektoren, sodass jede Implementierung reproduzierbar und validierbar bleibt.
Der Interpretations-Layer ist strikt regelbasiert: jede Aussage ist auf numerische Features zurueckfuehrbar und optional deaktivierbar.
</executive_summary>

<formal_spec>

<definitions>
  Engine identifiers:
  - engine_version: SemVer string, z.B. "1.0.0"
  - parameter_set_id: string (hash oder name)
  - deterministic: true (keine Zufallsanteile)

  Core domains:

- Angles in degrees unless stated otherwise.
- lambda in [0,360): ecliptic longitude
- beta in [-90,90]: ecliptic latitude
- alpha in [0,360): right ascension (deg)
- delta in [-90,90]: declination (deg)
- TLST in hours in [0,24)

  Safe angle operators:

- wrap360(x) := x mod 360, result in [0,360)
- wrap180(x) := wrap360(x+180) - 180, result in (-180,180]
- delta_deg(a,b) := abs(wrap180(a-b))

  Model parameters (versioned inputs, no implicit constants):

- phi_apex_offset_deg: real, default=15 (Ingress->Apex shift). CONFIG, not assumed.
- zi_apex_deg: real, default=270 (anchor: center of Zi sector). CONFIG.
- branch_width_deg: real, default=30
- branch_halfwidth_deg := branch_width_deg/2
- zodiac_zero_deg: real, default=0 (tropical Aries point) but can be epoch-dependent.
- epoch_id: string, e.g. "J2000", "ofDate", or custom
- precession_model_id: string, e.g. "IAU2006" (input), not implicit.
- obliquity_model_id: string (input)
- time_scale_provider_id: string (input)
- ephemeris_provider_id: string (input)

  Time corrections (modular; each can be input or provider-computed):

- tz_offset_sec: from tz database or input
- dst_applied: boolean + policy for ambiguous local times
- DUT1_sec: UT1-UTC (input or provider)
- leap_seconds: TAI-UTC (input or provider)
- DeltaT_sec: TT-UT1 (optional output/diagnostic; or input if provider uses it)
- EoT_min: equation of time in minutes (input or computed from ephemeris)
</definitions>

<mapping_functions>

  f_time (local civil -> UTC/UT1/TT/TLST):
  Inputs:

- local_datetime (ISO 8601)
- tz_id OR tz_offset_sec
- geo_lon_deg (east positive)
- optional: DUT1_sec, leap_seconds, EoT_min, DeltaT_sec
  Outputs:
- UTC datetime
- UT1 datetime
- TT datetime
- TLST_hours (true local solar time, apparent)

  Deterministic structure:

  1) UTC = LocalToUTC(local_datetime, tz_id, dst_policy)
     - if tz_id given, tz_offset_sec is derived deterministically
     - ambiguous local time -> dst_policy selects earlier/later/error
  2) UT1 = UTC + DUT1_sec
     - DUT1_sec is input or provider lookup; if missing => MISSING
  3) TT pathway options:
     - Preferred: TT = UTC + (TAI-UTC) + 32.184 sec
       where (TAI-UTC) is from leap_seconds provider.
     - Alternative: TT = UT1 + DeltaT_sec
       where DeltaT_sec is input/provider; requires UT1.
  4) TLST:
     - LMST_hours = (UT1_hours + geo_lon_deg/15.0) mod 24
     - TLST_hours = (LMST_hours + EoT_min/60.0) mod 24
     Notes:
     - EoT_min should be derived from solar ephemeris at (TT, epoch) if not provided.
     - If EoT_min missing => TLST falls back to LMST (flagged degraded).

  f_coord (equatorial <-> ecliptic; quadrant safe):
  Given obliquity epsilon_deg at chosen epoch.

  Equatorial -> Ecliptic:

- beta = asin( sin(delta)*cos(eps) - cos(delta)*sin(eps)*sin(alpha) )
- lambda = atan2( sin(alpha)*cos(eps) + tan(delta)*sin(eps), cos(alpha) )
- lambda = wrap360(rad2deg(lambda))

  Ecliptic -> Equatorial:

- delta = asin( sin(beta)*cos(eps) + cos(beta)*sin(eps)*sin(lambda) )
- alpha = atan2( sin(lambda)*cos(eps) - tan(beta)*sin(eps), cos(lambda) )
- alpha = wrap360(rad2deg(alpha))

  Implementation rule: always use atan2(y,x); never arctan(y/x).

  f_bazi (diskrete Zyklen; modular ruleset):
  Outputs at minimum:

- hour_branch_index in Z12 computed from TLST_hours:
    h = floor( ((TLST_hours + 1) mod 24) / 2 )  in {0..11}
    where 0=Zi, 1=Chou, ..., 11=Hai (index mapping is config, but must be fixed).
- month_branch_index from solar ecliptic longitude lambda_sun_deg:
    b = floor( wrap360(lambda_sun_deg - (zi_apex_deg - branch_halfwidth_deg)) / branch_width_deg )
  Optional (requires ruleset constants -> MISSING unless provided):
- year/day/month/hour stem indices (Z10) and 60-cycle ids (Z60)
  Approach:
- Provide bazi_ruleset_id and (sexagenary_epoch_reference) as input.
- Without those, engine can accept precomputed pillars as input (bazi_pillars_override).

  f_west (continuous ecliptic geometry):
  Inputs:

- TT datetime, epoch_id, zodiac_mode (tropical/sidereal), ephemeris_provider_id
  Outputs:
- For each body p: lambda_p_deg, beta_p_deg (optional), speed, flags (retrograde etc if provider supplies)
- Derived: sign_index = floor(wrap360(lambda_p_deg - zodiac_zero_deg)/30)
            degree_in_sign = wrap360(lambda_p_deg - zodiac_zero_deg) mod 30
            half_sign = 0 if degree_in_sign < 15 else 1

  f_fusion (bridge + coupling operator):
  Core bridge (Ingress vs Apex) as parameterized phase shift:

- lambda_apex_p = wrap360(lambda_p_deg - phi_apex_offset_deg)
- lambda_apex_sun = wrap360(lambda_sun_deg - phi_apex_offset_deg)

  Bridge option 1: Hard segment mapping (piecewise):

- planet_branch_p = floor( wrap360(lambda_p_deg - (zi_apex_deg - 15)) / 30 )
    (generalized by branch_halfwidth_deg)

  Bridge option 2: Soft kernel weighting over branch centers:

- centers_b = wrap360(zi_apex_deg + 30*b) for b=0..11
- weights_b(lambda) proportional to K(delta_deg(lambda, centers_b))
    Example kernel family (von Mises, circular Gaussian):
    K(delta) = exp(kappa * cos(delta_rad))
- normalize: sum_b weights_b = 1

  Bridge option 3: Harmonic/phasor embedding (recommended coupling term):
  Choose harmonics H = {k1,k2,...} (e.g., {2,3,4,6,12})

- Represent BaZi reference phases theta_i (e.g., pillar branches as centers in degrees):
    theta_branch(b) = wrap360(zi_apex_deg + 30*b)
- Build BaZi harmonic phasor:
    R_k = sum_{i in pillars} w_i *exp(i* k * deg2rad(theta_i))
- Build West harmonic phasor:
    O_k = sum_{p in bodies} v_p *exp(i* k * deg2rad(lambda_apex_p))
- Fusion features:
    I_k = |R_k + O_k|^2
    X_k = Re(conj(R_k) *O_k)   (pure cross-term / alignment)
    A_k = X_k / (|R_k|*|O_k| + eps)  in [-1,1] (normalized alignment)

  Gudu scaling (optional, strictly defined as parameter):

- gudu_circle_deg: real (e.g., 365.25) CONFIG
- theta_360 = theta_gudu * (360 / gudu_circle_deg)
- theta_gudu = theta_360 * (gudu_circle_deg / 360)
</mapping_functions>

<invariants_and_assertions>
  Angle hygiene:

- assert 0 <= wrap360(x) < 360
- assert -180 < wrap180(x) <= 180
- assert delta_deg(a,b) in [0,180]

  Time hygiene:

- TLST_hours in [0,24)
- If EoT_min missing and TLST requested, set flag tlst_quality="degraded"

  Discrete mapping:

- month_branch_index and hour_branch_index must be integers in [0,11]
- For any integer n: branch(lambda+360*n) == branch(lambda)

  Soft mapping:

- sum(weights_b) == 1 (within float tolerance)
- weights_b >= 0

  Boundary stability diagnostics:

- let d = min distance to nearest branch boundary (in deg)
- if estimated sigma_lambda_deg > d, set flag "branch_unstable=true"

  Harmonic fusion:

- if |R_k|==0 or |O_k|==0, define A_k=0 and flag "harmonic_degenerate"
</invariants_and_assertions>

<error_budget>
  Policy: Budgets are either (a) provider-supplied uncertainties or (b) explicit config. No hidden constants.

  Stage budgets (min/typ/max fields are required; values may be MISSING until provider chosen):

  1) CivilTime -> UTC
     - err_sec: {min:0, typ:MISSING, max:3600}  (max captures DST ambiguity if unresolved)
     - failure mode: ambiguous local time without dst_policy
  2) UTC -> UT1 (DUT1)
     - err_sec: {min:MISSING, typ:MISSING, max:MISSING} depends on DUT1 source
  3) UTC/UT1 -> TT (leap_seconds or DeltaT)
     - err_sec: {min:MISSING, typ:MISSING, max:MISSING} depends on provider/model
  4) Ephemeris positions (lambda)
     - err_deg: {min:MISSING, typ:MISSING, max:MISSING} provider-dependent
  5) Equation of Time (EoT)
     - err_min: {min:MISSING, typ:MISSING, max:MISSING} provider-dependent
  6) TLST
     - err_sec approx = sqrt(err_UT1^2 + (err_EoT*60)^2)
  7) Discretization into branches/signs
     - classification risk if sigma_lambda_deg >= distance_to_boundary_deg
     - engine must output distance_to_boundary_deg for each discrete assignment

  Required failure modes list (non-exhaustive):

- wrap boundary at 0/360 deg
- exactly on boundary (e.g., 285.000 deg): defined as half-open interval
- DST gaps/repeats (spring forward / fall back)
- timezone id missing/invalid
- date line / extreme longitudes (lon near +/-180)
- UT1/DUT1 missing for high-precision TLST
- ephemeris provider mismatch of epoch/zodiac_mode
</error_budget>

</formal_spec>

<engine_architecture>

<modules>
  1) InputValidator
     In: raw request JSON
     Out: normalized input, warnings/errors

  1) TimeModel
     In: local time, tz, lon/lat, time corrections
     Out: UTC, UT1, TT, TLST_hours, quality flags, uncertainty estimates

  2) EphemerisProvider (interface)
     In: TT, epoch_id, bodies list, mode flags
     Out: positions {lambda,beta,alpha,delta} + uncertainty metadata

  3) CoordTransform
     In: alpha/delta or lambda/beta, epsilon(epoch), precession_model
     Out: transformed coordinates + flags

  4) BaZiCalculator (ruleset-driven)
     In: TLST_hours, lambda_sun_deg, ruleset params OR pillars_override
     Out: pillars (stem/branch indices), plus diagnostics

  5) WestCalculator
     In: positions from provider
     Out: signs, degree_in_sign, aspects (optional), other derived features

  6) FeatureExtractor
     In: BaZi + West outputs
     Out: feature vector (flat, typed), plus boundary distances

  7) FusionOperator
     In: feature vector + fusion config
     Out: fusion features (mapping, kernels, harmonics), plus provenance

  8) InterpretationEngine
     In: (BaZi, West, Fusion) feature sets + interpretation ruleset
     Out: deterministic statements + explanations + references to features

  9) Validator
     In: any intermediate/result object
     Out: invariant checks, property-test results, error budgets, failure-mode flags
</modules>

<data_model>
  Types are JSON-like; all IDs must be explicit for reproducibility.

  EngineConfig:

- engine_version: string
- parameter_set_id: string
- epoch_id: string
- zodiac_mode: "tropical"|"sidereal" (sidereal requires ayanamsa_id -> MISSING if used)
- precession_model_id: string
- obliquity_model_id: string
- phi_apex_offset_deg: number
- zi_apex_deg: number
- branch_width_deg: number
- bazi_ruleset_id: string
- fusion_mode: "hard_segment"|"soft_kernel"|"harmonic_phasor"
- harmonics: array<int>
- kernel: {type:"von_mises", kappa:number} | ...
- interpretation_ruleset_id: string

  BirthEvent:

- local_datetime: string (ISO 8601)
- tz_id: string | null
- tz_offset_sec: int | null
- dst_policy: "error"|"earlier"|"later"
- geo_lon_deg: number
- geo_lat_deg: number

  TimeScales:

- utc: string
- ut1: string | null
- tt: string | null
- tlst_hours: number | null
- quality: {tlst:"ok"|"degraded"|"missing", tt:"ok"|"missing", ut1:"ok"|"missing"}
- corrections_used: {DUT1_sec, leap_seconds, DeltaT_sec, EoT_min}
- uncertainty: {utc_sec, ut1_sec, tt_sec, tlst_sec}

  BodyPosition:

- body_id: string (e.g., "Sun","Moon","Mars",...)
- lambda_deg: number
- beta_deg: number | null
- alpha_deg: number | null
- delta_deg: number | null
- speed_deg_per_day: number | null
- flags: {retrograde:boolean|null}
- uncertainty: {lambda_deg:number|null}

  BaZiPillar:

- pillar: "year"|"month"|"day"|"hour"
- stem_index: int|null  (0..9)
- branch_index: int     (0..11)
- sexagenary_index: int|null (0..59)
- method: "ruleset"|"override"
- diagnostics: {boundary_distance_deg:number|null}

  FeatureVector:

- engine_version
- parameter_set_id
- features: map<string, number|string|boolean|array>
- provenance: map<string, string> (which module computed what)

  Interpretation:

- statements: array<{id:string, text:string, confidence:number, feature_refs:array<string>}>
- explain: map<string, any> (feature values per statement)
</data_model>

<pseudocode>
  function compute_chart(request):
    cfg = request.engine_config
    evt = request.birth_event

    validate(evt, cfg)

    times = TimeModel.compute(evt, cfg)
    positions = EphemerisProvider.compute(times.tt, cfg.epoch_id, request.bodies)

    # West derived features
    west = WestCalculator.derive(positions, cfg)

    # BaZi core (minimal deterministic subset)
    sun_lambda = positions["Sun"].lambda_deg
    bazi = BaZiCalculator.compute_minimal(
      tlst_hours=times.tlst_hours,
      lambda_sun_deg=sun_lambda,
      cfg=cfg,
      pillars_override=request.bazi_override
    )

    # Extract features
    feats = FeatureExtractor.build(times, west, bazi, cfg)

    # Fuse
    fused = FusionOperator.apply(feats, cfg)

    # Interpret (optional)
    interp = null
    if request.include_interpretation:
      interp = InterpretationEngine.apply(feats, fused, cfg)

    # Validate invariants
    report = Validator.run(times, positions, bazi, feats, fused, cfg)

    return {times, positions, bazi, feats, fused, interp, report}
</pseudocode>

</engine_architecture>

<api_spec>

<endpoints>
  POST /chart
  - Computes timescales, positions, BaZi minimal pillars, features, fusion, optional interpretation, validation report.

  POST /features

- Computes features only (optionally from provided positions/pillars to avoid ephemeris).

  POST /fusion

- Computes fusion features from a FeatureVector (or from west+bazi feature blocks).

  POST /interpretation

- Applies deterministic interpretation rules to (features + fusion), returns explanations.

  POST /validate

- Runs invariant checks and boundary/failure-mode diagnostics on provided objects.
</endpoints>

<schemas>
  Request schema (common):
  {
    "engine_config": EngineConfig,
    "birth_event": BirthEvent,
    "bodies": ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn"],
    "bazi_override": { "pillars": [BaZiPillar,...] } | null,
    "positions_override": [BodyPosition,...] | null,
    "include_interpretation": true|false,
    "include_validation": true|false
  }

  Response schema (/chart):
  {
    "engine_version": "1.0.0",
    "parameter_set_id": "pz_2026_02_core",
    "time_scales": TimeScales,
    "positions": [BodyPosition,...],
    "bazi": { "pillars": [BaZiPillar,...] },
    "features": FeatureVector,
    "fusion": { "features": map<string, any>, "mode": string },
    "interpretation": Interpretation | null,
    "validation": { "ok": boolean, "assertions": [...], "warnings": [...], "errors": [...] }
  }

  Notes:

- If positions_override is provided, ephemeris_provider is not called.
- If bazi_override is provided, BaZiCalculator ruleset is bypassed.
</schemas>

<versioning>
  - SemVer: MAJOR.MINOR.PATCH
  - Breaking changes (MAJOR): feature names/types, default anchors/offset semantics, interval-closure conventions.
  - MINOR: new optional fields/features/modules.
  - PATCH: bugfixes, stricter validation, additional diagnostics.
  - Every response echoes engine_version + parameter_set_id + epoch_id + time standards used.
</versioning>

</api_spec>

<validation_suite>

<test_vectors>
  All test vectors are synthetic: they inject known lambda/TLST values, so no ephemerides needed.

  TV1 (Ingress vs Apex split in Capricorn example):

- cfg: zi_apex_deg=270, branch_width_deg=30, phi_apex_offset_deg=15
- sun_lambda_deg=275.0
    expect month_branch_index=0 (Zi)
- sun_lambda_deg=285.0
    expect month_branch_index=1 (Chou)

  TV2 (wrap-around at sector start):

- sun_lambda_deg=254.999
    expect month_branch_index=11 (Hai)
- sun_lambda_deg=255.000
    expect month_branch_index=0 (Zi)

  TV3 (hour branch boundaries, TLST):

- TLST_hours=22.999 -> hour_branch=11 (Hai)
- TLST_hours=23.000 -> hour_branch=0  (Zi)
- TLST_hours=0.999  -> hour_branch=0  (Zi)
- TLST_hours=1.000  -> hour_branch=1  (Chou)

  TV4 (soft kernel symmetry at exact boundary):

- lambda=285.0, centers Zi=270, Chou=300
    expect weights[Zi] == weights[Chou] (for symmetric kernel)

  TV5 (atan2 quadrants):

- Provide a set of (alpha,delta,eps) where cos(alpha)<0 to ensure atan2 returns correct quadrant.
    expect wrap360(lambda) in [0,360) and continuity under small perturbations.
</test_vectors>

<property_tests>
  P1: wrap invariants:

- for random x: 0<=wrap360(x)<360
- for random x: -180<wrap180(x)<=180

  P2: branch center mapping:

- for b in 0..11: branch(theta_branch(b)) == b

  P3: periodicity:

- for random lambda, integer n: branch(lambda+360*n)==branch(lambda)

  P4: boundary half-open convention:

- branch(center+15-eps)==b AND branch(center+15)==(b+1 mod 12)

  P5: kernel normalization:

- sum(weights)==1 within tolerance, all weights>=0
</property_tests>

</validation_suite>

<interpretation_layer>

<principle>
  Jede Ausgabeaussage ist eine deterministische Funktion der berechneten Features.
  Keine Aussage darf ohne feature_refs (Provenance) ausgegeben werden.
  Keine Behauptung ueber physikalische/medizinische/psychologische Faktizitaet.
</principle>

<mapping_table>
  Deterministische Regeln (Beispiele; alle Schwellenwerte sind Parameter im ruleset):

- Feature: "sun_month_branch_index"
    Output: "Month-Branch (geometric) = {branch_name}"
    Explain: source = f_bazi.month_branch_index from sun_lambda_deg

- Feature: "planet_branch_index[planet]"
    Output: "{planet} maps to branch {branch_name} under apex_offset={phi_apex_offset_deg} deg"
    Explain: uses hard_segment mapping and reports boundary_distance_deg

- Feature: "branch_unstable[object]=true"
    Output: "Discrete assignment unstable (near boundary); prefer soft weights or report both candidates."
    Explain: shows sigma_lambda_deg and distance_to_boundary_deg

- Feature: "harmonic_alignment_A_k[k]"
    Output (template):
      if A_k >= +T_pos: "Strong constructive coupling at harmonic k={k}"
      if A_k <= -T_neg: "Strong destructive coupling at harmonic k={k}"
      else: "Neutral coupling at harmonic k={k}"
    Explain: references R_k, O_k, X_k, A_k

- Feature: "delta_deg(planet_lambda, pillar_branch_center) approx 180"
    Output: "Opposition-like geometry (k=2 dominant) between {planet} and {pillar}"
    Explain: delta_deg computed via wrap180, not via naive subtraction
</mapping_table>

<explainability>
  - Jede Statement-Instanz enthaelt feature_refs: Liste der Feature Keys + deren Werte.
  - Die Engine liefert zusaetzlich einen "provenance" Block (welches Modul welche Werte erzeugt hat).
  - Validator annotiert jede diskrete Zuordnung mit boundary distances und ggf. instability flags.
</explainability>

</interpretation_layer>

<limitations_and_open_questions>
MISSING (muss fuer vollstaendige BaZi-Pillarberechnung festgelegt werden, statt zu improvisieren):

1) bazi_ruleset_id Details:

- Referenz-Epoche fuer sexagenary day cycle (welcher JDN ist JiaZi-Tag?)
- Regel fuer Tageswechsel (Mitternacht vs Zi-hour boundary)
- Monatssauele: "jieqi boundaries" vs "apex segments" (beides implementierbar, aber muss entschieden werden)
- Tabellen/Regeln fuer month/hour stems aus year/day stem

1) time_scale_provider:
   - Quelle fuer leap_seconds, DUT1, optional DeltaT
   - Policy, wenn UT1/TT nicht verfuegbar (degraded precision flags)

2) ephemeris_provider:
   - Welche bodies, welcher Referenzrahmen (geocentric/apparent), welche Genauigkeitsmetadaten
   - zodiac_mode sidereal braucht ayanamsa_id (sonst nicht aktivieren)

3) Interpretation ruleset:
   - Thresholds (T_pos, T_neg) und Gewichtungen (w_i, v_p) sind Modellparameter und muessen versioniert werden.

Grenzen:

- Die Engine ist formal/mathematisch reproduzierbar, macht aber keine wissenschaftlichen Wahrheitsansprueche zu "Wirkungen".
- Ohne provider uncertainties kann das error_budget nur als Struktur geliefert werden (nicht als numerische Garantie).

</limitations_and_open_questions>

<self_critique_summary>
Wichtigste Annahmen:

- Zi_apex_deg=270 und phi_apex_offset_deg=15 sind Default-Parameter, keine Naturkonstanten.
- BaZi-Stems/Year/Day-Pillars sind ohne ruleset/epoch nicht sicher ableitbar; deshalb modularisiert.

Fragilste Stellen:

- Vollstaendige BaZi-Standardisierung (Epochen/Tabellen/Tagwechsel) -> hoechster "MISSING"-Anteil.
- TLST Genauigkeit, wenn DUT1/EoT nur approximiert werden -> kann Stundenbranch an Grenzen kippen.

Konfidenzen (0..1):

- Mapping/Angle hygiene: 0.95
- TLST modular spec: 0.85
- Coord transform formulas: 0.90
- Full BaZi pillars without external ruleset: 0.55
- Fusion harmonic operator: 0.80

</self_critique_summary>

 </deliverable>
