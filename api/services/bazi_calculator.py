# BaZodiac Calculator Service
# Compute BaZi pillars (year, month, day, hour) from time scales

from typing import Dict, Any, Optional
from datetime import datetime
from ..utils.core import (
    STEM_NAMES, BRANCH_NAMES,
    hour_branch_from_tlst, hard_branch_mapping, wrap360
)

# ============== Standard BaZi Ruleset ==============

STANDARD_BAZI_RULESET = {
    "ruleset_id": "standard_bazi_v1",
    "ruleset_version": "1.0.0",
    "stem_order": STEM_NAMES,
    "branch_order": BRANCH_NAMES,
    "day_cycle_anchor": {
        "anchor_jdn": 2419451,  # Assumed JiaZi day (needs verification)
        "anchor_sexagenary_index": 0
    },
    "year_boundary": {
        "mode": "solar_longitude_crossing",
        "solar_longitude_deg": 315.0  # LiChun
    },
    "month_boundary": {
        "mode": "JIEQI_CROSSING",
        "month_start_solar_longitude_deg": 315.0,
        "step_deg": 30.0
    },
    "hidden_stems": {
        "Zi": ["Gui"],
        "Chou": ["Ji", "Gui", "Xin"],
        "Yin": ["Jia", "Bing", "Wu"],
        "Mao": ["Yi"],
        "Chen": ["Wu", "Yi", "Gui"],
        "Si": ["Bing", "Geng", "Wu"],
        "Wu": ["Ding", "Ji"],
        "Wei": ["Ji", "Yi", "Ding"],
        "Shen": ["Geng", "Ren", "Wu"],
        "You": ["Xin"],
        "Xu": ["Wu", "Xin", "Ding"],
        "Hai": ["Ren", "Jia"]
    }
}


class BaZiCalculator:
    """Compute BaZi pillars from time inputs."""
    
    def __init__(self, ruleset: Dict[str, Any] = STANDARD_BAZI_RULESET):
        self.ruleset = ruleset
    
    def compute_pillars(
        self,
        utc_dt: datetime,
        tlst_hours: float,
        sun_lambda_deg: float,
        year_stem_override: Optional[int] = None,
        month_stem_override: Optional[int] = None,
        day_stem_override: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Compute all four BaZi pillars.
        
        Args:
            utc_dt: UTC datetime
            tlst_hours: True Local Solar Time in hours [0, 24)
            sun_lambda_deg: Sun ecliptic longitude in degrees
            overrides: Optional pre-computed stems
        
        Returns:
            Dict with year, month, day, hour pillars
        """
        # Day pillar (sexagenary cycle)
        day_pillar = self._compute_day_pillar(utc_dt)
        
        # Year pillar (solar longitude crossing)
        year_pillar = self._compute_year_pillar(sun_lambda_deg)
        
        # Month pillar (jieqi crossing or apex segments)
        month_pillar = self._compute_month_pillar(sun_lambda_deg, year_pillar["stem_index"])
        
        # Hour pillar (TLST-based)
        hour_pillar = self._compute_hour_pillar(tlst_hours, day_pillar["stem_index"])
        
        # Apply overrides if provided
        if year_stem_override is not None:
            year_pillar["stem_index"] = year_stem_override
        if month_stem_override is not None:
            month_pillar["stem_index"] = month_stem_override
        if day_stem_override is not None:
            day_pillar["stem_index"] = day_stem_override
        
        # Hidden stems
        hidden_stems = self._compute_hidden_stems({
            "year": year_pillar,
            "month": month_pillar,
            "day": day_pillar,
            "hour": hour_pillar
        })
        
        # Boundary diagnostics
        diagnostics = self._boundary_diagnostics(sun_lambda_deg, tlst_hours)
        
        return {
            "ruleset_id": self.ruleset["ruleset_id"],
            "year": year_pillar,
            "month": month_pillar,
            "day": day_pillar,
            "hour": hour_pillar,
            "hidden_stems": hidden_stems,
            "boundary_diagnostics": diagnostics
        }
    
    def _compute_day_pillar(self, utc_dt: datetime) -> Dict[str, int]:
        """
        Compute day pillar from sexagenary cycle.
        
        Day index = (JDN - anchor_jdn) mod 60
        """
        # Simplified Julian Day approximation
        year, month, day = utc_dt.year, utc_dt.month, utc_dt.day
        hour = utc_dt.hour + utc_dt.minute / 60.0
        
        # Quick JDN approximation
        if month <= 2:
            year -= 1
            month += 12
        
        jdn = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + int(0.5) + 1721119
        
        anchor_jdn = self.ruleset["day_cycle_anchor"]["anchor_jdn"]
        anchor_index = self.ruleset["day_cycle_anchor"]["anchor_sexagenary_index"]
        
        sexagenary_index = (jdn - anchor_jdn + anchor_index) % 60
        stem_index = sexagenary_index % 10
        branch_index = sexagenary_index % 12
        
        return {
            "stem_index": stem_index,
            "branch_index": branch_index,
            "sexagenary_index": sexagenary_index
        }
    
    def _compute_year_pillar(self, sun_lambda_deg: float) -> Dict[str, int]:
        """
        Compute year pillar from solar longitude crossing.
        
        Year changes at LiChun (315° = start of Yin month)
        """
        li_chun_deg = self.ruleset["year_boundary"]["solar_longitude_deg"]
        
        # Approximate year stem from branch (Earthly Branch offset)
        # Zi year = JiaZi + 9 cycles = GuiHai
        # Actually: JiaZi year starts with Zi branch, but this varies by school
        
        # Simplified: branch determines stem offset
        # Using: JiaZi (year) = Jia at JiaYin? This is complex
        
        # For now: use solar longitude to get year number
        # Year number from 4 Feb approx
        # (Simplified - needs proper JDN anchor)
        
        return {
            "stem_index": 0,  # Placeholder - needs proper anchor
            "branch_index": 0,  # Placeholder
            "sexagenary_index": 0
        }
    
    def _compute_month_pillar(
        self,
        sun_lambda_deg: float,
        year_stem_index: int
    ) -> Dict[str, int]:
        """
        Compute month pillar from JieQi crossing or Sun position.
        
        Month branch from Sun longitude.
        Month stem from Five Tigers formula:
            month_stem = (year_stem * 2 + 2 + month_index) mod 10
        """
        month_boundary_deg = self.ruleset["month_boundary"]["month_start_solar_longitude_deg"]
        step_deg = self.ruleset["month_boundary"]["step_deg"]
        
        # Month index from Sun longitude
        # 0 = Yin month starting at 315°
        shifted = wrap360(sun_lambda_deg - month_boundary_deg)
        month_index = int(shifted / step_deg) % 12
        
        # Five Tigers formula
        month_stem = (year_stem_index * 2 + 2 + month_index) % 10
        
        return {
            "stem_index": month_stem,
            "branch_index": month_index,
            "sexagenary_index": None
        }
    
    def _compute_hour_pillar(
        self,
        tlst_hours: float,
        day_stem_index: int
    ) -> Dict[str, int]:
        """
        Compute hour pillar from TLST.
        
        Hour branch from TLST:
            hour_branch = floor(((TLST + 1) % 24) / 2)
        
        Hour stem from Five Rats formula:
            hour_stem = (day_stem * 2 + hour_branch) mod 10
        """
        hour_branch = hour_branch_from_tlst(tlst_hours)
        hour_stem = (day_stem_index * 2 + hour_branch) % 10
        
        return {
            "stem_index": hour_stem,
            "branch_index": hour_branch,
            "sexagenary_index": None
        }
    
    def _compute_hidden_stems(
        self,
        pillars: Dict[str, Dict[str, int]]
    ) -> Dict[str, list]:
        """Compute hidden stems for each pillar branch."""
        hidden_table = self.ruleset["hidden_stems"]
        result = {}
        
        for pillar_name, pillar in pillars.items():
            branch_idx = pillar["branch_index"]
            branch_name = BRANCH_NAMES[branch_idx]
            
            if branch_name in hidden_table:
                hidden_list = hidden_table[branch_name]
                stems = []
                for i, stem_name in enumerate(hidden_list):
                    stem_idx = STEM_NAMES.index(stem_name)
                    role = "principal" if i == 0 else ("central" if i == 1 else "residual")
                    weight = 1.0 if i == 0 else (0.5 if i == 1 else 0.3)
                    stems.append({
                        "stem": stem_name,
                        "stem_index": stem_idx,
                        "role": role,
                        "weight": weight
                    })
                result[pillar_name] = stems
            else:
                result[pillar_name] = []
        
        return result
    
    def _boundary_diagnostics(
        self,
        sun_lambda_deg: float,
        tlst_hours: float
    ) -> Dict[str, Any]:
        """Check for boundary proximity and instability."""
        month_boundary_deg = self.ruleset["month_boundary"]["month_start_solar_longitude_deg"]
        step_deg = self.ruleset["month_boundary"]["step_deg"]
        
        # Month boundary distance
        shifted = wrap360(sun_lambda_deg - month_boundary_deg)
        month_boundary_distance = shifted % step_deg
        month_unstable = month_boundary_distance < 0.5  # Within 0.5°
        
        # Hour boundary distance (in minutes)
        hour_boundary_min = ((tlst_hours + 1) % 24) % 2 * 60
        hour_boundary_distance = hour_boundary_min if hour_boundary_min > 0 else 120
        hour_unstable = hour_boundary_distance < 2.0  # Within 2 minutes
        
        return {
            "month_boundary_distance_deg": round(month_boundary_distance, 3),
            "month_branch_unstable": month_unstable,
            "hour_boundary_distance_min": round(hour_boundary_distance, 1),
            "hour_branch_unstable": hour_unstable
        }
