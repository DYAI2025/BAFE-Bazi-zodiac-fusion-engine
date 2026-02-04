# BaZodiac Engine API Server
# FastAPI application with all endpoints

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List, Dict, Any

from .models.schemas import (
    EngineConfig, BirthEvent, ChartResponse, ValidateRequest, ValidateResponse,
    TimeScales, BodyPosition, FusionMode, BranchConvention, ComplianceMode,
    HealthResponse
)
from .services.time_model import TimeModelService
from .services.bazi_calculator import BaZiCalculator
from .services.fusion import FusionService
from .services.validation import ValidationService

# ============== App Setup ==============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown handlers."""
    print("🚀 BaZodiac Engine API starting...")
    yield
    print("👋 BaZodiac Engine API shutting down...")

app = FastAPI(
    title="BaZodiac Engine API",
    description="Deterministic BaZi + Western Astrology Fusion Engine",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== Dependency Injection ==============

def get_bazi_calculator() -> BaZiCalculator:
    return BaZiCalculator()

def get_fusion_service() -> FusionService:
    return FusionService()

# ============== Health Check ==============

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

# ============== Validation Endpoint ==============

@app.post("/validate", response_model=ValidateResponse, tags=["Validation"])
async def validate_request(request: ValidateRequest):
    """
    Validate request without computation.
    
    Checks configuration, rules, and data integrity.
    """
    # Run validation
    result = ValidationService.run_full_validation(
        config=request.engine_config,
        birth_event=request.birth_event
    )
    
    return ValidateResponse(
        compliance_status=result["compliance_status"],
        errors=result["errors"],
        warnings=result["warnings"],
        evidence=result["evidence"]
    )

# ============== Chart Computation ==============

@app.post("/chart", response_model=ChartResponse, tags=["Computation"])
async def compute_chart(
    engine_config: EngineConfig,
    birth_event: BirthEvent,
    bodies: List[str] = Query(default=["Sun", "Moon"], description="Planets to compute"),
    include_validation: bool = True,
    include_fusion: bool = True
):
    """
    Compute complete BaZodiac chart.
    
    Returns time scales, positions, BaZi pillars, fusion features, and validation.
    """
    # 1. Validate config
    config_errors = ValidationService.validate_config(engine_config)
    if config_errors:
        raise HTTPException(status_code=400, detail=config_errors)
    
    # 2. Time computation
    try:
        time_result = TimeModelService.compute_tlst(
            utc_dt=datetime.fromisoformat(birth_event.local_datetime.replace("Z", "+00:00")),
            geo_lon_deg=birth_event.geo_lon_deg
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Time computation failed: {str(e)}")
    
    # 3. Ephemeris (placeholder - would use SwissEph)
    # For now, approximate positions
    from .utils.core import wrap360
    
    positions = {}
    tt_dt = datetime.fromisoformat(time_result["tt"].replace("Z", "+00:00"))
    days_since_epoch = (tt_dt - datetime(2000, 1, 1)).total_seconds() / 86400.0
    
    # Approximate mean longitude for demonstration
    for body in bodies:
        if body == "Sun":
            # Mean anomaly approximation
            mean_long = (280.46 + 0.9856474 * days_since_epoch) % 360
            positions[body] = mean_long
        elif body == "Moon":
            # Simplified lunar position
            mean_long = (218.316 + 13.176396 * days_since_epoch) % 360
            positions[body] = mean_long
        else:
            # Placeholder for other bodies
            positions[body] = wrap360(days_since_epoch * 0.5 + 100)
    
    # 4. BaZi computation
    calculator = BaZiCalculator()
    sun_lambda = positions.get("Sun", 0)
    
    bazi_result = calculator.compute_pillars(
        utc_dt=datetime.fromisoformat(time_result["utc"].replace("Z", "+00:00")),
        tlst_hours=time_result["tlst_hours"],
        sun_lambda_deg=sun_lambda
    )
    
    # 5. Fusion computation
    fusion_result = None
    if include_fusion:
        pillars = {
            "year": bazi_result["year"]["branch_index"],
            "month": bazi_result["month"]["branch_index"],
            "day": bazi_result["day"]["branch_index"],
            "hour": bazi_result["hour"]["branch_index"]
        }
        
        try:
            fusion_result = FusionService.apply_fusion(
                pillars=pillars,
                positions=positions,
                fusion_mode=engine_config.fusion_mode.value,
                zi_apex_deg=engine_config.zi_apex_deg,
                width_deg=engine_config.branch_width_deg,
                convention=engine_config.branch_coordinate_convention.value,
                phi_offset_deg=engine_config.phi_apex_offset_deg,
                harmonics_k=engine_config.harmonics_k,
                kappa=engine_config.kappa
            )
        except Exception as e:
            # Fusion is optional
            fusion_result = {"mode": engine_config.fusion_mode.value, "error": str(e)}
    
    # 6. Validation
    validation = None
    if include_validation:
        validation_result = ValidationService.run_full_validation(
            config=engine_config,
            birth_event=birth_event,
            positions=[{"body": k, "lambda_deg": v} for k, v in positions.items()],
            pillars=bazi_result,
            times=time_result
        )
        validation = {
            "ok": validation_result["ok"],
            "compliance_status": validation_result["compliance_status"],
            "errors": validation_result["errors"],
            "warnings": validation_result["warnings"],
            "evidence": validation_result["evidence"]
        }
    
    # 7. Build response
    response = {
        "engine_version": engine_config.engine_version,
        "parameter_set_id": engine_config.parameter_set_id,
        "config_fingerprint": engine_config.fingerprint(),
        "birth_event": birth_event.dict(),
        "time_scales": {
            "utc": time_result.get("utc"),
            "tt": time_result.get("tt"),
            "jd_ut": time_result.get("jd_utc"),
            "jd_tt": time_result.get("jd_tt"),
            "lmst_hours": time_result.get("lmst_hours"),
            "tlst_hours": time_result.get("tlst_hours"),
            "eot_min": time_result.get("eot_min"),
            "quality": time_result.get("quality", {})
        },
        "positions": [{"body": k, "lambda_deg": v} for k, v in positions.items()],
        "bazi": bazi_result,
        "fusion": fusion_result,
        "validation": validation
    }
    
    return ChartResponse(**response)

# ============== Features Endpoint ==============

@app.post("/features", tags=["Computation"])
async def compute_features(
    engine_config: EngineConfig,
    birth_event: BirthEvent,
    bodies: List[str] = Query(default=["Sun", "Moon"])
):
    """
    Compute features only (skips fusion).
    
    Returns time scales, positions, and BaZi pillars.
    """
    return await compute_chart(
        engine_config=engine_config,
        birth_event=birth_event,
        bodies=bodies,
        include_validation=True,
        include_fusion=False
    )

# ============== Fusion Endpoint ==============

@app.post("/fusion", tags=["Computation"])
async def compute_fusion(
    pillars: Dict[str, int],
    positions: Dict[str, float],
    fusion_mode: FusionMode = FusionMode.harmonic_phasor,
    zi_apex_deg: float = 270.0,
    branch_width_deg: float = 30.0,
    branch_coordinate_convention: BranchConvention = BranchConvention.SHIFT_BOUNDARIES,
    phi_apex_offset_deg: float = 15.0,
    harmonics_k: Optional[List[int]] = None
):
    """
    Compute fusion features from pre-computed pillars and positions.
    
    Useful when you have external ephemeris/calculator.
    """
    service = FusionService()
    
    try:
        result = service.apply_fusion(
            pillars=pillars,
            positions=positions,
            fusion_mode=fusion_mode.value,
            zi_apex_deg=zi_apex_deg,
            width_deg=branch_width_deg,
            convention=branch_coordinate_convention.value,
            phi_offset_deg=phi_apex_offset_deg,
            harmonics_k=harmonics_k or [2, 3, 4, 6, 12]
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== Run with: uvicorn main:app --reload ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
