# BaZodiac Validation Service
# Invariant checks and error code catalog

from typing import Dict, List, Any, Optional
from ..models.schemas import (
    EngineConfig, BirthEvent, ValidationIssue, ValidationEvidence
)

# ============== Error Codes Catalog ==============

ERROR_CODES = {
    # RefData errors
    "REFDATA_NETWORK_FORBIDDEN": {
        "message": "Network access attempted in offline mode",
        "severity": "ERROR"
    },
    "REFDATA_MANIFEST_MISSING": {
        "message": "Reference data manifest not found",
        "severity": "ERROR"
    },
    "EPHEMERIS_MISSING": {
        "message": "Ephemeris data not available",
        "severity": "ERROR"
    },
    "EPHEMERIS_HASH_MISMATCH": {
        "message": "Ephemeris file hash mismatch",
        "severity": "ERROR"
    },
    "TZDB_SIGNATURE_INVALID": {
        "message": "Timezone database signature verification failed",
        "severity": "ERROR"
    },
    "LEAP_SECONDS_FILE_EXPIRED": {
        "message": "Leap seconds file has expired",
        "severity": "ERROR"
    },
    
    # Time errors
    "MISSING_TT": {
        "message": "Terrestrial Time (TT) computation failed",
        "severity": "ERROR"
    },
    "EOP_MISSING": {
        "message": "Earth Orientation Parameters not available",
        "severity": "WARNING"
    },
    "EOP_STALE": {
        "message": "Earth Orientation Parameters data is stale",
        "severity": "WARNING"
    },
    "DST_AMBIGUOUS_LOCAL_TIME": {
        "message": "DST ambiguity: local time exists in both before/after",
        "severity": "ERROR"
    },
    "DST_NONEXISTENT_LOCAL_TIME": {
        "message": "DST gap: local time does not exist",
        "severity": "ERROR"
    },
    
    # BaZi errors
    "MISSING_DAY_CYCLE_ANCHOR": {
        "message": "Day cycle anchor not provided",
        "severity": "ERROR"
    },
    
    # Branch convention errors
    "INCONSISTENT_BRANCH_ORIGIN_FOR_SHIFTED_LONGITUDES": {
        "message": "SHIFT_LONGITUDES requires consistent B0_apex usage",
        "severity": "ERROR"
    },
    
    # Angle errors
    "INVALID_LAMBDA": {
        "message": "Ecliptic longitude not in [0, 360)",
        "severity": "ERROR"
    },
    
    # Interpretation errors
    "INTERP_DERIVATION_EMPTY": {
        "message": "Interpretation statement has no feature derivation",
        "severity": "ERROR"
    },
    "INTERP_LINT_FAIL": {
        "message": "Interpretation failed claim linter",
        "severity": "ERROR"
    }
}


class ValidationService:
    """Run invariant checks on engine configuration and results."""
    
    @staticmethod
    def validate_config(config: EngineConfig) -> List[ValidationIssue]:
        """Validate engine configuration."""
        errors = []
        
        # Check deterministic flag
        if not config.deterministic:
            errors.append(ValidationIssue(
                code="NON_DETERMINISTIC",
                message="Engine must be deterministic",
                severity="ERROR"
            ))
        
        # Check branch convention consistency
        if config.branch_coordinate_convention.value == "SHIFT_LONGITUDES":
            # SHIFT_LONGITUDES requires phi_apex_offset != 0
            if config.phi_apex_offset_deg == 0:
                errors.append(ValidationIssue(
                    code="INCONSISTENT_BRANCH_ORIGIN_FOR_SHIFTED_LONGITUDES",
                    message="SHIFT_LONGITUDES requires non-zero phi_apex_offset_deg"
                ))
        
        # Check fusion mode parameters
        if config.fusion_mode.value == "harmonic_phasor":
            if not config.harmonics_k:
                errors.append(ValidationIssue(
                    code="MISSING_HARMONICS",
                    message="harmonic_phasor mode requires harmonics_k list"
                ))
        
        # Check sidereal mode
        if config.zodiac_mode.value == "sidereal" and not config.ayanamsa_id:
            errors.append(ValidationIssue(
                code="MISSING_AYANAMSA",
                message="sidereal mode requires ayanamsa_id"
            ))
        
        return errors
    
    @staticmethod
    def validate_positions(positions: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """Validate planetary positions."""
        errors = []
        
        for pos in positions:
            lambda_deg = pos.get("lambda_deg", 0)
            if not (0 <= lambda_deg < 360):
                errors.append(ValidationIssue(
                    code="INVALID_LAMBDA",
                    message=f"Body {pos.get('body', 'unknown')}: lambda {lambda_deg} not in [0, 360)",
                    severity="ERROR",
                    path=f"/positions/{pos.get('body')}/lambda_deg"
                ))
        
        return errors
    
    @staticmethod
    def validate_pillars(pillars: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate BaZi pillars."""
        errors = []
        
        for name, pillar in pillars.items():
            if "stem_index" in pillar:
                if not (0 <= pillar["stem_index"] <= 9):
                    errors.append(ValidationIssue(
                        code="INVALID_STEM_INDEX",
                        message=f"{name} stem index {pillar['stem_index']} not in [0, 9]"
                    ))
            if "branch_index" in pillar:
                if not (0 <= pillar["branch_index"] <= 11):
                    errors.append(ValidationIssue(
                        code="INVALID_BRANCH_INDEX",
                        message=f"{name} branch index {pillar['branch_index']} not in [0, 11]"
                    ))
        
        return errors
    
    @staticmethod
    def validate_time_scales(times: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate time scale results."""
        errors = []
        warnings = []
        
        # TLST range check
        tlst_hours = times.get("tlst_hours")
        if tlst_hours is not None:
            if not (0 <= tlst_hours < 24):
                errors.append(ValidationIssue(
                    code="INVALID_TLST",
                    message=f"TLST {tlst_hours} not in [0, 24)"
                ))
        
        # Quality flag warnings
        if times.get("quality", {}).get("tlst") == "degraded":
            warnings.append(ValidationIssue(
                code="TLST_DEGRADED",
                message="TLST computed with degraded precision (EoT missing)"
            ))
        
        return errors + warnings
    
    @staticmethod
    def run_full_validation(
        config: EngineConfig,
        birth_event: Optional[BirthEvent] = None,
        positions: Optional[List[Dict[str, Any]]] = None,
        pillars: Optional[Dict[str, Any]] = None,
        times: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run complete validation suite.
        
        Returns validation report with status, errors, warnings, evidence.
        """
        all_errors = []
        all_warnings = []
        
        # Config validation
        all_errors.extend(ValidationService.validate_config(config))
        
        # Birth event validation
        if birth_event:
            if birth_event.geo_lon_deg < -180 or birth_event.geo_lon_deg > 180:
                all_errors.append(ValidationIssue(
                    code="INVALID_GEO_LON",
                    message=f"Longitude {birth_event.geo_lon_deg} not in [-180, 180]"
                ))
        
        # Position validation
        if positions:
            all_errors.extend(ValidationService.validate_positions(positions))
        
        # Pillar validation
        if pillars:
            all_errors.extend(ValidationService.validate_pillars(pillars))
        
        # Time validation
        if times:
            all_errors.extend(ValidationService.validate_time_scales(times))
        
        # Determine compliance status
        if len(all_errors) == 0:
            compliance_status = "COMPLIANT"
        elif any(e.severity == "ERROR" for e in all_errors):
            compliance_status = "NON_COMPLIANT"
        else:
            compliance_status = "DEGRADED"
        
        # Build evidence
        evidence = ValidationEvidence(
            refdata={
                "refdata_pack_id": config.refdata.get("refdata_pack_id", "unknown"),
                "mode": config.refdata.get("refdata_mode", "unknown"),
                "allow_network": config.refdata.get("allow_network", False)
            },
            time={
                "tlst_quality": times.get("quality", {}).get("tlst", "unknown") if times else "unknown"
            },
            discretization={
                "interval_convention": config.interval_convention,
                "branch_coordinate_convention": config.branch_coordinate_convention.value
            }
        )
        
        return {
            "ok": len(all_errors) == 0,
            "compliance_status": compliance_status,
            "errors": all_errors,
            "warnings": all_warnings,
            "evidence": evidence.dict()
        }
