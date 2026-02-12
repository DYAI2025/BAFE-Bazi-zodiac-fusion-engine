Patch: Spec-kompatibles Ruleset (Ready for Implementation)

Unten ist eine normalisierte Version, die in die BaZodiac-Spezifikation passt (explizite Month/Year-Boundaries, Month-Index-Definition, Hour-Time-Standard, Hidden-Stems-Ordering/Weights). Ich gebe sie als “recommended” aus; wenn ihr den Anchor noch nicht verifizieren wollt, setzt anchor_jdn auf "MISSING" und erzwingt /validate -> Error.

{
  "ruleset_id": "standard_bazi_2026",
  "ruleset_version": "1.0.0",
  "source_provenance": {
    "notes": [
      "Month/Hour stem group tables provided by project.",
      "Hidden stems table matches common published tables.",
      "Day-cycle anchor MUST be verified and pinned."
    ]
  },

  "stem_order": ["Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui"],
  "branch_order": ["Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai"],

  "day_cycle_anchor": {
    "anchor_type": "JDN",
    "anchor_jdn": 2419451,
    "anchor_sexagenary_index_0based": 0,
    "anchor_label": "Assumed JiaZi day (verify!)",
    "anchor_verification": "unverified"
  },

  "day_change_policy": {
    "mode": "zi_hour_start",
    "time_standard_for_day_rollover": "TLST",
    "zi_start_hour": 23.0,
    "interval_convention": "HALF_OPEN"
  },

  "year_boundary": {
    "mode": "solar_longitude_crossing",
    "zodiac_mode": "tropical",
    "time_scale": "TT",
    "solar_longitude_deg": 315.0,
    "label": "LiChun-based year boundary"
  },

  "month_boundary": {
    "mode": "JIEQI_CROSSING",
    "zodiac_mode": "tropical",
    "time_scale": "TT",
    "month_start_solar_longitude_deg": 315.0,
    "step_deg": 30.0,
    "month_index_0_definition": "Yin_month_at_start_longitude",
    "month_order_by_index": ["Yin","Mao","Chen","Si","Wu","Wei","Shen","You","Xu","Hai","Zi","Chou"]
  },

  "month_stem_rule": {
    "mode": "table_groups",
    "groups": [
      { "year_stems": [0, 5], "month_stems_by_month_index": [2,3,4,5,6,7,8,9,0,1,2,3] },
      { "year_stems": [1, 6], "month_stems_by_month_index": [4,5,6,7,8,9,0,1,2,3,4,5] },
      { "year_stems": [2, 7], "month_stems_by_month_index": [6,7,8,9,0,1,2,3,4,5,6,7] },
      { "year_stems": [3, 8], "month_stems_by_month_index": [8,9,0,1,2,3,4,5,6,7,8,9] },
      { "year_stems": [4, 9], "month_stems_by_month_index": [0,1,2,3,4,5,6,7,8,9,0,1] }
    ],
    "validation": {
      "require_length_12": true,
      "month_index_range": [0, 11]
    }
  },

  "hour_branch_rule": {
    "mode": "bin_2h",
    "time_standard": "TLST",
    "formula_reference": "floor(((TLST_hours + 1) % 24) / 2)",
    "interval_convention": "HALF_OPEN"
  },

  "hour_stem_rule": {
    "mode": "table_groups",
    "groups": [
      { "day_stems": [0, 5], "hour_stems_by_hour_branch": [0,1,2,3,4,5,6,7,8,9,0,1] },
      { "day_stems": [1, 6], "hour_stems_by_hour_branch": [2,3,4,5,6,7,8,9,0,1,2,3] },
      { "day_stems": [2, 7], "hour_stems_by_hour_branch": [4,5,6,7,8,9,0,1,2,3,4,5] },
      { "day_stems": [3, 8], "hour_stems_by_hour_branch": [6,7,8,9,0,1,2,3,4,5,6,7] },
      { "day_stems": [4, 9], "hour_stems_by_hour_branch": [8,9,0,1,2,3,4,5,6,7,8,9] }
    ],
    "validation": {
      "require_length_12": true,
      "hour_branch_range": [0, 11]
    }
  },

  "hidden_stems": {
    "mode": "table",
    "ordering": "principal_central_residual",
    "branch_to_hidden": {
      "Zi":   ["Gui"],
      "Chou": ["Ji", "Gui", "Xin"],
      "Yin":  ["Jia", "Bing", "Wu"],
      "Mao":  ["Yi"],
      "Chen": ["Wu", "Yi", "Gui"],
      "Si":   ["Bing", "Geng", "Wu"],
      "Wu":   ["Ding", "Ji"],
      "Wei":  ["Ji", "Yi", "Ding"],
      "Shen": ["Geng", "Ren", "Wu"],
      "You":  ["Xin"],
      "Xu":   ["Wu", "Xin", "Ding"],
      "Hai":  ["Ren", "Jia"]
    }
  },

  "hidden_stems_weighting": {
    "mode": "role_weights",
    "role_weights": { "principal": 1.0, "central": 0.5, "residual": 0.3 }
  }
}

Implementer-Notes (damit es wirklich “ready” ist)

1) Wie Month-Stem-Table gelesen wird

year_stem_index ermitteln (0..9).

passende Gruppe suchen (enthaelt year_stem_index).

month_index = 0..11 gemaess month_order_by_index (Index 0 = Yin ab 315 deg).

month_stem_index = month_stems_by_month_index[month_index].

1) Wie Hour-Stem-Table gelesen wird

day_stem_index (0..9).

Gruppe finden.

hour_branch aus TLST: 0..11.

hour_stem_index = hour_stems_by_hour_branch[hour_branch].
Das Hour-Table-Schema passt zu der bekannten Sexagenary-Hours-Tabelle (5er-Gruppen).

1) Der “Anchor” ist der groesste Hebel fuer Korrektheit

In /validate sollte es eine harte Regel geben:

wenn anchor_verification != "verified" -> Warning (dev) oder Error (prod), je nach Policy.
