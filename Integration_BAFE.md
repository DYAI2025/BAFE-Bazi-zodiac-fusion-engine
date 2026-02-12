# Integration_BAFE.md

## 0) Executive Summary

**Zielbild:** Etablierung einer deterministischen, spezifikationskonformen "Bazodiac-Fusion-Engine" (BAFE), integriert in die bestehende "BC Engine V2".
**Kernphilosophie:** **Contract-First**. Wir definieren erst die Schnittstellen, Validierungsregeln und Datenverträge (Single Source of Truth), bevor Implementierungslogik angefasst wird. Dies verhindert "Feature Creep" und garantiert Reproduzierbarkeit (Scientific Compliance).
**Vorgehen:** Der Plan gliedert sich in 6 Phasen (0–5), beginnend mit der Konsolidierung der Spezifikation (F1–F6) zu einem stabilen Contract, gefolgt von einer datengestützten Gap-Analyse der V2, einer strategischen Architektur-Entscheidung (Umbau vs. Adapter) und der iterativen Umsetzung.

**Wichtigste Deliverables:**

1. **Spec SSOT:** Zentrales Repo-Verzeichnis mit Schemas, Rulesets und Master-Spec.
2. **Gap-Report:** Matrix über den Zustand der V2.
3. **Contract-Pack:** JSON Schemas (Validation) + Ruleset `standard_bazi_2026`.
4. **Integrated Engine:** BAFE-Core laufend in V2 Umgebung.

---

## Phase 0 — Ordnung schaffen (1–2 Iterationen, low risk, doc-only)

**Ziel:** Alle Patches und Dokumente (F1–F6) zu einer "Single Source of Truth" (SSOT) konsolidieren, ohne operativen Code anzufassen.

### 0.1 Spec-Repo Struktur festlegen (einmalig)

Es wird folgende Verzeichnisstruktur im Projekt-Root erzwungen, um alle Artefakte zentral zu verwalten:

```text
spec/
├── bazodiac_spec_master.md       # (F1) Normativer Fließtext (Master)
├── addenda/                      # (F6 Addenda)
│   ├── addendum_scientific_compliance_v1.md
│   └── addendum_interpretation_layer_v1.md
├── changelog.md                  # Versionierung & Patch-Log
├── schemas/                      # (F6 Schemas)
│   ├── ValidateRequest.schema.json
│   ├── ValidateResponse.schema.json
│   ├── refdata_manifest.schema.json
│   └── ...
├── rulesets/                     # (F5 Ruleset)
│   └── standard_bazi_2026.json
├── refdata/                      # Templates für Manifests
│   └── refpack_manifest_template.json
└── tests/                        # (F3/F6 Test Vectors)
    ├── tv_matrix.json            # TV1–TV7 Inputs/Expected
    └── pt_definitions.md         # Property Tests Description
