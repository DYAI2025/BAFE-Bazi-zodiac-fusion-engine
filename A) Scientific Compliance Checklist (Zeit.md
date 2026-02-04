A) Scientific Compliance Checklist (Zeitskalen, Ephemeriden, Referenzsysteme, Grenzfälle, Reproduzierbarkeit)
A0. Grundsatz: “Scientific Compliance” als Gate

Ziel/Definition (MUSS dokumentiert sein):

✅ Compliance bedeutet: Die Engine nutzt etablierte Ephemeriden/Zeitskalen/Frames korrekt, deterministisch, nachvollziehbar (Provenance), offline reproduzierbar.

❌ Nicht bedeutet: Deutungs-Aussagen sind wissenschaftlich bewiesen.

Akzeptanzkriterium: Ein /validate-Report kann “COMPLIANT (astronomisch)” ausweisen, unabhängig davon, was später im Interpretation-Layer passiert.

A1. Referenzdaten & Provenance (RefDataManager)

Pflichtdaten-Packs (MUSS):

 Ephemeris-Paket eindeutig: ephemeris_id (z. B. DE440/DE441 oder SwissEph-Version) + Hash

 tzdb/tzdata Version + (optional) Signaturprüfung

 Leap Seconds Datei + expires_utc geprüft

 EOP / DUT1 Quelle (z. B. IERS finals2000A) oder explizit “nicht vorhanden”

 Manifest (Pack-ID, Build-Infos, Checksummen, Gültigkeitsfenster)

Kontrollen (MUSS):

 Offline-Modus: keinerlei Network I/O (und bei Versuch: harter Fehler)

 Jede /chart-//features-Antwort enthält: engine_version, parameter_set_id, refdata_pack_id, ruleset_id

 Staleness Flags: leap seconds expired, EOP missing/stale, tzdb mismatch etc.

Status v0.2 laut Gap: RefDataManager ❌ / Manifest-Verification ❌ / Offline enforcement ❌ (hohe Priorität P2, aber für “Scientific Compliance”-Label praktisch Pflicht)

A2. Zeitskalen-Kette (Local → UTC → UT1/TT → (L)MST/TLST)

Konversionskette (MUSS exakt festgelegt & testbar sein):

 Local → UTC via tzdb + DST Policy (error|earlier|later)

 UTC → UT1 via DUT1 override oder via EOP-Interpolation; sonst UT1 = missing + Flag

 UTC → TT via Leap Seconds: TT = UTC + (TAI-UTC) + 32.184s

Fallback nur wenn explizit erlaubt: TT = UT1 + ΔT (bei vorhandenem UT1 + DeltaT override)

 LMST/TLST: klare Definition (eure Spec sieht TLST + Equation of Time vor) + Provenance, ob EoT berechnet oder override.

Grenzfälle (MUSS in Tests abgedeckt):

 DST “non-existent local time” (Frühjahrs-Umstellung)

 DST “ambiguous local time” (Herbst-Umstellung)

 Leap second Tag(e) / Übergänge (wenn euer Zeitraum betroffen ist)

 fehlende EOP (UT1 nicht verfügbar) → Verhalten im Strict vs. Relaxed Mode

Akzeptanztests (MUSS):

 Goldene Testvektoren: bekannte (Datum, Ort, tz_id) → UTC/TT/UT1/JD Ergebnisse

 Property Tests: Roundtrip/Monotonie (Zeit steigt, JD steigt), keine Sprünge außer erklärten DST/Leap-Effekten

 Report: pro Stage Unsicherheiten / “MISSING” wenn nicht bekannt (eure Spec fordert Error Budgets)

Status v0.2 laut Gap: TimeModel ⚠️ partiell, EoT provenance ❌, Uncertainty propagation ❌

A3. Referenzsysteme & Koordinaten (Frames, Epoch, Precession/Nutation)

Frame/Model-Entscheidungen (MUSS explizit sein, keine impliziten Defaults):

 epoch_id: ofDate|J2000|custom

 precession_model_id + obliquity_model_id (nicht “SwissEph default ohne Kennzeichnung”)

 zodiac_mode: tropical|sidereal

wenn sidereal: [ ] ayanamsa_id MUSS gesetzt sein

Transformations-Hygiene (MUSS):

 konsequent atan2 (quadrant-safe) statt arctan(y/x)

 wrap360, wrap180, delta_deg überall

 Ausgabe eindeutig: ekliptische Länge (λ), ggf. RA/Dec, ob topozentrisch oder geozentrisch

Akzeptanztests (MUSS):

 Vergleich gegen Referenzberechnung (gleiche Ephemeris + gleiche Frame-Settings) mit definierter Toleranz

 Regressionstest bei Modelwechsel (z. B. DE440 → DE441): erwartete Abweichungsbereiche dokumentiert

Status v0.2 laut Gap: Epoch/Precession ⚠️ (implizite SwissEph Defaults), Sidereal ❌

A4. Ephemeriden-Provider (DE440/DE441/SwissEph) – harte Anforderungen

Provider-Vertrag (MUSS):

 Input ist klarer Time Argument (TT/TDB) und Engine dokumentiert, was verwendet wird

 Bodies/IDs eindeutig (Planet, Mond, ggf. Nodes/Apsiden — wenn genutzt, definieren!)

 Output: λ in [0..360), optional lat/RA/Dec; plus Provider-Metadaten (Version, Source)

Integritätskontrollen (MUSS):

 Ephemeris-Datei Hash/Signatur checkt gegen Manifest

 Fehlender Provider → harter Fehler in strict mode

Akzeptanztests (MUSS):

 Vergleich ausgewählter Datumswerte gegen veröffentlichte Referenzen (oder gegen denselben Provider in unabhängiger Umgebung)

 deterministisch identische Ergebnisse bei gleicher refdata_pack_id + config

A5. Diskretisierung & Grenzfälle (BaZi-Branches, Intervalle, Boundary-Instabilität)

Konventionen (MUSS explizit in Config):

 interval_convention = HALF_OPEN (wie in eurer Spec beschrieben)

 branch_coordinate_convention = SHIFT_BOUNDARIES | SHIFT_LONGITUDES

Validator MUSS Fehler werfen, wenn inkonsistent implementiert (ihr habt das in der Spec bereits als Muss-Regel)

Boundary-Risiko (MUSS sichtbar werden):

 boundary_distance_deg pro Klassifikation (wie nah an Grenze)

 classification_unstable Flag, wenn Unsicherheit ≥ Grenzabstand

 Soft-Kernel (von-Mises o. ä.) nur, wenn dokumentiert + reproduzierbar parametriert

Akzeptanztests (MUSS):

 Testpunkte knapp unter/über Branch-Grenze (inkl. exakt Grenzwert)

 numerische Stabilität: gleiche Eingabe → gleiche Branch (oder gleiche Gewichte im Soft Mode)

A6. Reproduzierbarkeit & Determinismus (Engine-Level)

Build-/Run-Determinismus (MUSS):

 Jede Ausgabe enthält vollständige Parameter: EngineConfig + RuleSet + RefData IDs

 Keine “stille Normalisierung” ohne Logging/Provenance

 Floating determinism: definierte Toleranzen, keine zufälligen Seeds, keine systemabhängigen Zeitquellen

Akzeptanztests (MUSS):

 “Same input → byte-identical output JSON” (oder streng definierte tolerante Felder)

 Cross-platform Regression (mindestens Linux/macOS) oder containerisierte Repro-Tests

A7. Validierung / /validate als zentrale Schaltstelle

/validate MUSS:

 RefData-Checks (Hashes, expiry, allow_network)

 Pflichtfelder (day_cycle_anchor etc.) und harte Fehlercodes (wie in Spec)

 Invarianten: wrap360 ranges, delta ranges, interval convention, branch mapping consistency

 Fehlermoden-Katalog + Error Budgets (oder “MISSING”)

Status v0.2 laut Gap: /validate ❌, Invariant checks ❌, Error budgets ❌ (Priorität P1)

B) Interpretation-Layer Checklist (Fakt vs. Narrativ sauber trennen & kennzeichnen)
B0. Output-Typen: 3-Schichten-Modell (MUSS)

Definiert und enforced im Schema:

Fakt (Astronomie/Geodäsie/Zeitskalen)

Planetpositionen, Zeitumrechnungen, Koordinatensysteme, Provenance.

Regel-/Konventionsoutput (Systemintern)

BaZi Pillars, Branch/Stem Indizes, Aspektklassen, Harmonic Scores, Soft-Weights.

Narrativ/Interpretation (Deutungstexte)

sprachliche Aussagen, Metaphern, “Tendenzen”, keine naturwissenschaftliche Behauptung.

Akzeptanzkriterium: Jede Textaussage MUSS maschinenlesbar taggen, aus welcher Schicht sie stammt.

B1. Jede Interpretation MUSS “Feature-Provenance” haben

Pflichtfelder pro Aussage:

 statement_id, layer = NARRATIVE

 derived_from_features: Liste von Feature-IDs + deren Werte/Schwellen

 config_fingerprint + ruleset_id + refdata_pack_id

 stability_flags: boundary_unstable, time_ambiguous, missing_eop etc.

 optional: confidence = nur technische Stabilität (z. B. “weit weg von Boundary”), nicht “Wahrheit”

Akzeptanztest: Wenn derived_from_features leer → harte Ablehnung (kein Text darf “aus dem Bauch” entstehen).

B2. Harte Claim-Grenzen (MUSS, als Linter/Policy)

 Keine medizinischen/psychologischen Diagnosen, keine rechtlichen/finanziellen Anweisungen

 Keine physikalisch-kausalen Behauptungen (“Planeten verursachen X”) als Fakt

 Bei jedem Export/Report: kurzer Disclaimer “Symbolisches Regelwerk, nicht wissenschaftliche Faktbehauptung”

Akzeptanztest: “Claim-Linter” über alle Texte (Blocklist + Pattern + Reviewliste).

B3. Transparenz: “Wie kam das zustande?”

 UI/Report zeigt: zugrunde liegende Features (z. B. λ, Aspekte, Branch, Harmonic A_k)

 zeigt Konventionen (tropical/sidereal, ayanamsa, interval_convention, DST policy)

 zeigt Warnungen (Zeit ambig, EOP missing, boundary unstable)

Akzeptanztest: Nutzer kann aus Report rekonstruiert nachvollziehen, warum ein Satz erscheint.

B4. Umgang mit Ambiguität (Narrativ muss “vorsichtig” werden)

Wenn Instabilität vorliegt (Boundary, DST, fehlende EOP):

 Texte wechseln in “unsicher/nahe Grenze”-Variante oder werden unterdrückt

 optional: mehrere Varianten mit Kennzeichnung (“wenn Branch A”, “wenn Branch B”)

Akzeptanztest: Grenzfälle erzeugen nie fälschlich “sicher klingende” Statements.

B5. Versionierung & Änderungsmanagement (Interpretationen sind Ruleset-gebunden)

 Interpretations-Templates sind versioniert und referenzieren Feature-Schema-Version

 Breaking changes: Migration oder Block

 Tests: Golden outputs für Interpretationslayer (bei unveränderten Inputs)

B6. Optional: “Research Mode” (nur wenn ihr Aussagen empirisch prüfen wollt)

Wenn ihr jemals behaupten wollt “das korreliert mit X”, braucht ihr:

 Prä-registrierte Hypothesen, klare Metriken, Baselines, Blind/Randomisierung wo möglich

 strikte Trennung: Engine erzeugt Features; ein separater Evaluator testet Hypothesen

 Ergebnisbericht: Effektgrößen + Unsicherheiten, nicht nur Trefferquote

(Ohne das bleibt Interpretation sauber als Narrativ/Heuristik – was völlig ok ist.)

Mini-Beispiel: JSON-Tagging für Fakt vs. Regel vs. Narrativ
{
  "facts": {
    "utc": "1992-03-29T01:30:00Z",
    "tt": "1992-03-29T01:31:...Z",
    "ephemeris_id": "JPL_DE441",
    "sun_lambda_deg": 8.1234
  },
  "rules": {
    "bazi": { "day_branch": 3, "hour_branch": 0 },
    "branch_mapping": { "interval_convention": "HALF_OPEN", "branch": 9, "boundary_distance_deg": 0.12, "unstable": true },
    "harmonics": { "k": 3, "A_k": 0.41 }
  },
  "interpretations": [
    {
      "statement_id": "NAR_1029",
      "layer": "NARRATIVE",
      "text": "Du stehst aktuell an einer Schwelle – kleine Unterschiede in Zeit/Ort können die Zuordnung verändern.",
      "derived_from_features": ["branch_mapping.unstable", "branch_mapping.boundary_distance_deg"],
      "stability_flags": ["BOUNDARY_UNSTABLE"],
      "refdata_pack_id": "ref_2026_02_01",
      "ruleset_id": "bazi_rules_v3",
      "config_fingerprint": "sha256:..."
    }
  ]
}

Quellen (für eure Compliance-Dokumentation)

Park, R. S., Folkner, W. M., & Williams, J. G. (2021). The JPL planetary and lunar ephemerides DE440 and DE441. The Astronomical Journal. <https://doi.org/10.3847/1538-3881/abd414>

Petit, G., & Luzum, B. (Eds.). (2010). IERS Conventions (2010). IERS Technical Note 36. <https://www.iers.org/IERS/EN/Publications/TechnicalNotes/tn36.html>

Plate, T. A. (1995). Holographic reduced representations. IEEE Transactions on Neural Networks, 6(3). <https://doi.org/10.1109/72.377968>

McCarthy, D. D. (2011). Evolution of timescales from astronomy to physical metrology. Metrologia, 48(4). <https://doi.org/10.1088/0026-1394/48/4/S03>

Dirkx, D., Kopeikin, S. M., Lion, G., Panet, I., & Petit, G. (2018). High performance clocks and gravity field determination. Space Science Reviews. <https://doi.org/10.1007/s11214-017-0431-z>

Susskind, L. (1995). The World as a Hologram. Journal of Mathematical Physics, 36. <https://doi.org/10.1063/1.531249>

Bousso, R. (2002). The holographic principle. Reviews of Modern Physics, 74, 825–874. <https://doi.org/10.1103/RevModPhys.74.825>

Banerjee, P., & Matsakis, D. (2023). Time and Its Definition. In Introduction to Modern Timekeeping and Time Transfer. (Springer). <https://link.springer.com/chapter/10.1007/978-3-031-30780-5_1>

Wyman, A. J., & Vyse, S. (2008). Science versus the stars… computer-generated astrological natal charts. The Journal of General Psychology, 135(3), 287–300. <https://doi.org/10.3200/GENP.135.3.287-300>

McGrew, J. H., & McFall, R. M. (1990). A scientific inquiry into the validity of astrology. Journal of Scientific Exploration (PDF). <http://www.skepticalmedia.com/astrology/Scientific%20Inquiry%20into%20Astrology.pdf>

Wenn du magst, kann ich als nächsten Schritt diese Checklisten direkt als “Spec Addendum” in eure Markdown-Struktur gießen (mit eindeutigen MUST/SHOULDs + Testvektoren + Failure Codes), sodass es 1:1 in eure /validate-Roadmap passt.
