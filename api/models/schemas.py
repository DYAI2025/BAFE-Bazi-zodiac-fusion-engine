# BaZodiac Engine API
# FastAPI server for deterministic BaZi + Western Astrology fusion

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from datetime import datetime
from contextlib import asynccontextmanager
import hashlib
import json
import math

# ============== Models ==============

class ZodiacMode(str, Enum):
    tropical = "tropical"
    sidereal = "sidereal"

class TimeStandard(str, Enum):
    CIVIL = "CIVIL"
    LMT = "LMT"
    TLST = "TLST"

class DstPolicy(str, Enum):
    error = "error"
    earlier = "earlier"
    later = "later"

class FusionMode(str, Enum):
    hard_segment = "hard_segment"
    soft_kernel = "soft_kernel"
    harmonic_phasor = "harmonic_phasor"

class BranchConvention(str, Enum):
    SHIFT_BOUNDARIES = "SHIFT_BOUNDARIES"
    SHIFT_LONGITUDES = "SHIFT_LONGITUDES"

class RefDataMode(str, Enum):
    BUNDLED_OFFLINE = "BUNDLED_OFFLINE"
    LOCAL_MIRROR = "LOCAL_MIRROR"
    PROVIDER_BACKED = "PROVIDER_BACKED"

class ComplianceMode(str, Enum):
    STRICT = "STRICT"
    RELAXED = "RELAXED"
    DEV = "DEV"

# ============== Engine Configuration ==============

class EngineConfig(BaseModel):
    engine_version: str = "1.0.0"
    parameter_set_id: str = Field(..., description="Unique parameter set ID")
    deterministic: bool = True
    epoch_id: str = "J2000"
    time_standard: TimeStandard = TimeStandard.TLST
    dst_policy: DstPolicy = DstPolicy.error
    zodiac_mode: ZodiacMode = ZodiacMode.tropical
    ayanamsa_id: Optional[str] = None
    bazi_ruleset_id: str = "standard_bazi_v1"
    fusion_mode: FusionMode = FusionMode.harmonic_phasor
    harmonics_k: List[int] = [2, 3, 4, 6, 12]
    kernel_type: Optional[str] = None
    kappa: Optional[float] = None
    interval_convention: str = "HALF_OPEN"
    branch_coordinate_convention: BranchConvention = BranchConvention.SHIFT_BOUNDARIES
    phi_apex_offset_deg: float = 15.0
    zi_apex_deg: float = 270.0
    branch_width_deg: float = 30.0
    refdata: Dict[str, Any]
    compliance_mode: ComplianceMode = ComplianceMode.DEV
    
    def fingerprint(self) -> str:
        """Generate SHA256 fingerprint of config."""
        canonical = json.dumps(self.dict(exclude_none=True), sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

# ============== Birth Event ==============

class BirthEvent(BaseModel):
    local_datetime: datetime = Field(..., description="ISO 8601 datetime")
    tz_id: Optional[str] = Field(None, description="Timezone ID (e.g., Europe/Berlin)")
    tz_offset_sec: Optional[int] = Field(None, description="Manual offset in seconds")
    dst_policy: Optional[DstPolicy] = None
    geo_lon_deg: float = Field(..., ge=-180, le=180)
    geo_lat_deg: float = Field(..., ge=-90, le=90)

# ============== Time Scales ==============

class TimeScales(BaseModel):
    utc: Optional[str] = None
    ut1: Optional[str] = None
    tt: Optional[str] = None
    jd_ut: Optional[float] = None
    jd_tt: Optional[float] = None
    lmst_hours: Optional[float] = None
    tlst_hours: Optional[float] = None
    eot_min: Optional[float] = None
    quality: Dict[str, str] = {}

# ============== Ephemeris ==============

class BodyPosition(BaseModel):
    body: str
    lambda_deg: float = Field(..., ge=0, lt=360)
    beta_deg: Optional[float] = None
    alpha_deg: Optional[float] = None
    delta_deg: Optional[float] = None
    speed_deg_per_day: Optional[float] = None
    retrograde: Optional[bool] = None

# ============== BaZi ==============

class PillarStem(BaseModel):
    stem_index: int = Field(..., ge=0, le=9)
    branch_index: int = Field(..., ge=0, le=11)
    sexagenary_index: Optional[int] = Field(None, ge=0, le=59)

class BaZiPillars(BaseModel):
    year: PillarStem
    month: PillarStem
    day: PillarStem
    hour: PillarStem

class HiddenStem(BaseModel):
    stem: str
    role: str  # principal, central, residual
    weight: float

class HiddenStemsByPillar(BaseModel):
    year: List[HiddenStem] = []
    month: List[HiddenStem] = []
    day: List[HiddenStem] = []
    hour: List[HiddenStem] = []

class BaZiResult(BaseModel):
    ruleset_id: str
    pillars: BaZiPillars
    hidden_stems: Optional[HiddenStemsByPillar] = None
    boundary_diagnostics: Optional[Dict[str, Any]] = None

# ============== Fusion ==============

class HardSegmentMapping(BaseModel):
    body: str
    branch_index: int
    branch_center_deg: float
    distance_to_boundary_deg: Optional[float] = None

class SoftKernelWeights(BaseModel):
    body: str
    weights: Dict[int, float]  # branch -> weight

class HarmonicFeatures(BaseModel):
    k: int
    a_k: float  # Alignment [-1, 1]
    i_k: float  # Intensity
    x_k: Optional[float] = None
    degenerate: bool = False

class FusionResult(BaseModel):
    mode: FusionMode
    hard_mapping: Optional[List[HardSegmentMapping]] = None
    soft_weights: Optional[List[SoftKernelWeights]] = None
    harmonics: Optional[List[HarmonicFeatures]] = None
    fusion_features: Dict[str, Any] = {}

# ============== Validation ==============

class ValidationIssue(BaseModel):
    code: str
    message: str
    severity: str = "ERROR"
    path: Optional[str] = None

class ValidationEvidence(BaseModel):
    refdata: Dict[str, Any] = {}
    time: Dict[str, Any] = {}
    discretization: Dict[str, Any] = {}

class ValidationReport(BaseModel):
    ok: bool
    compliance_status: str
    errors: List[ValidationIssue] = []
    warnings: List[ValidationIssue] = []
    evidence: ValidationEvidence = ValidationEvidence()

# ============== Complete Chart Response ==============

class ChartResponse(BaseModel):
    engine_version: str
    parameter_set_id: str
    config_fingerprint: str
    birth_event: BirthEvent
    time_scales: TimeScales
    positions: List[BodyPosition]
    bazi: BaZiResult
    fusion: Optional[FusionResult] = None
    validation: ValidationReport

# ============== Validate Request/Response ==============

class ValidateRequest(BaseModel):
    engine_config: EngineConfig
    birth_event: Optional[BirthEvent] = None

class ValidateResponse(BaseModel):
    compliance_status: str
    errors: List[ValidationIssue] = []
    warnings: List[ValidationIssue] = []
    evidence: ValidationEvidence = ValidationEvidence()

# ============== Health Check ==============

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
