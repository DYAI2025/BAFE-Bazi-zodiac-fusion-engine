# Harmonic Phasor Fusion Module
# Implements: Harmonic embedding, phase alignment, fusion features per BaZodiac Spec v1.0.0

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from math import sin, cos, pi, radians, degrees, sqrt, exp, floor
from cmath import exp as cexp, polar


# =============================================================================
# CONSTANTS
# =============================================================================

# Default configuration per spec
DEFAULT_PHI_APEX_OFFSET_DEG: float = 15.0  # Ingress vs Apex shift
DEFAULT_ZI_APEX_DEG: float = 270.0  # Center of Zi sector
DEFAULT_BRANCH_WIDTH_DEG: float = 30.0
DEFAULT_HARMONICS: List[int] = [2, 3, 4, 6, 12]
DEFAULT_KAPPA: float = 4.0  # von Mises concentration parameter

# Element symbols for logging
HARMONIC_LABELS: Dict[int, str] = {
    2: "Opposition/Balance",
    3: "Trine/Harmony", 
    4: "Square/Tension",
    6: "Sextile/Opportunity",
    12: "Duodecim/Integration"
}


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

@dataclass(frozen=True)
class FusionConfig:
    """Fusion configuration per BaZodiac spec."""
    
    phi_apex_offset_deg: float = DEFAULT_PHI_APEX_OFFSET_DEG
    zi_apex_deg: float = DEFAULT_ZI_APEX_DEG
    branch_width_deg: float = DEFAULT_BRANCH_WIDTH_DEG
    harmonics_k: List[int] = field(default_factory=lambda: DEFAULT_HARMONICS.copy())
    kappa: float = DEFAULT_KAPPA
    fusion_mode: str = "harmonic_phasor"  # "harmonic_phasor", "soft_kernel", "hard_segment"
    harmonic_phase_convention: str = "apex_shifted"  # "raw", "apex_shifted"
    epsilon_norm: float = 1e-10  # Avoid division by zero
    
    def __post_init__(self):
        """Validate configuration."""
        if not 0 <= self.phi_apex_offset_deg < 360:
            raise ValueError(f"phi_apex_offset_deg must be in [0, 360), got {self.phi_apex_offset_deg}")
        if not 0 <= self.zi_apex_deg < 360:
            raise ValueError(f"zi_apex_deg must be in [0, 360), got {self.zi_apex_deg}")
        if self.branch_width_deg <= 0:
            raise ValueError(f"branch_width_deg must be positive, got {self.branch_width_deg}")
        if self.kappa <= 0:
            raise ValueError(f"kappa must be positive, got {self.kappa}")
        if self.fusion_mode not in ["harmonic_phasor", "soft_kernel", "hard_segment"]:
            raise ValueError(f"Unknown fusion_mode: {self.fusion_mode}")


@dataclass(frozen=True)
class HarmonicFeatures:
    """Harmonic features for a single harmonic k."""
    
    k: int
    r_k: complex  # BaZi reference phasor
    o_k: complex  # West object phasor
    i_k: float    # Intensity: |R_k + O_k|^2
    x_k: float    # Cross-term: Re(conj(R_k) * O_k)
    a_k: float    # Alignment: normalized X_k in [-1, 1]
    magnitude_r: float = 0.0
    magnitude_o: float = 0.0
    degenerate: bool = False
    
    def __post_init__(self):
        """Calculate derived features."""
        if self.degenerate:
            return
        self.magnitude_r = abs(self.r_k)
        self.magnitude_o = abs(self.o_k)


@dataclass(frozen=True)
class FusionResult:
    """Complete fusion result."""
    
    config: FusionConfig
    harmonics: Dict[int, HarmonicFeatures]
    branch_weights: Dict[int, float]  # Soft weights if computed
    
    # Summary metrics
    total_alignment: float = 0.0
    dominant_harmonic: int = 0
    degeneracy_flags: List[str] = field(default_factory=list)
    
    # Provenance
    bazi_phases: Dict[str, float] = field(default_factory=dict)
    west_phases: Dict[str, float] = field(default_factory=dict)


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def deg2rad(degrees: float) -> float:
    """Convert degrees to radians."""
    return degrees * pi / 180.0


def wrap360(degrees: float) -> float:
    """Wrap angle to [0, 360) range."""
    result = degrees % 360.0
    if result < 0:
        result += 360.0
    return result


def delta_deg(a: float, b: float) -> float:
    """Angular distance in degrees [0, 180]."""
    delta = abs(wrap360(a) - wrap360(b))
    if delta > 180.0:
        delta = 360.0 - delta
    return delta


def branch_centers(zi_apex_deg: float, width_deg: float, num_branches: int = 12) -> List[float]:
    """
    Calculate branch center longitudes.
    
    Args:
        zi_apex_deg: Center of Zi sector (default 270°)
        width_deg: Width of each branch (default 30°)
        num_branches: Number of branches (default 12)
    
    Returns:
        List of branch center longitudes in degrees
    """
    half_width = width_deg / 2.0
    b0 = zi_apex_deg - half_width  # Start of Zi sector
    return [wrap360(b0 + width_deg * i) for i in range(num_branches)]


def bazi_reference_phase(branch_index: int, zi_apex_deg: float, width_deg: float) -> float:
    """
    Calculate BaZi reference phase for a branch.
    
    Args:
        branch_index: Branch index (0=Zi, 1=Chou, ..., 11=Hai)
        zi_apex_deg: Center of Zi sector
        width_deg: Branch width
    
    Returns:
        Reference phase in degrees
    """
    return wrap360(zi_apex_deg + width_deg * branch_index)


def west_object_phase(
    longitude_deg: float, 
    phi_apex_offset_deg: float,
    convention: str = "apex_shifted"
) -> float:
    """
    Calculate West object's phase for fusion.
    
    Args:
        longitude_deg: Ecliptic longitude of object
        phi_apex_offset_deg: Apex offset for shifted convention
        convention: "raw" or "apex_shifted"
    
    Returns:
        Phase in degrees
    """
    if convention == "raw":
        return wrap360(longitude_deg)
    elif convention == "apex_shifted":
        return wrap360(longitude_deg - phi_apex_offset_deg)
    else:
        raise ValueError(f"Unknown convention: {convention}")


def von_mises_kernel(delta_deg: float, kappa: float) -> float:
    """
    von Mises circular kernel for soft weighting.
    
    Args:
        delta_deg: Angular distance from center
        kappa: Concentration parameter (higher = narrower)
    
    Returns:
        Weight in (0, 1]
    """
    delta_rad = deg2rad(delta_deg)
    return exp(kappa * cos(delta_rad))


def soft_branch_weights(
    longitude_deg: float,
    zi_apex_deg: float,
    width_deg: float,
    kappa: float = DEFAULT_KAPPA
) -> Dict[int, float]:
    """
    Calculate soft branch weights using von Mises kernel.
    
    Args:
        longitude_deg: Longitude of object
        zi_apex_deg: Center of Zi sector
        width_deg: Branch width
        kappa: Concentration parameter
    
    Returns:
        Dictionary of branch_index -> weight (normalized to sum=1)
    """
    centers = branch_centers(zi_apex_deg, width_deg)
    
    # Calculate raw weights
    raw_weights = []
    for center in centers:
        delta = delta_deg(longitude_deg, center)
        weight = von_mises_kernel(delta, kappa)
        raw_weights.append(weight)
    
    # Normalize
    total = sum(raw_weights)
    if total == 0:
        # Degenerate case: uniform weights
        return {i: 1.0 / 12.0 for i in range(12)}
    
    return {i: w / total for i, w in enumerate(raw_weights)}


def hard_branch_mapping(
    longitude_deg: float,
    zi_apex_deg: float,
    width_deg: float
) -> int:
    """
    Hard mapping of longitude to branch index.
    
    Implements SHIFT_BOUNDARIES convention per spec.
    
    Args:
        longitude_deg: Object longitude
        zi_apex_deg: Center of Zi sector
        width_deg: Branch width
    
    Returns:
        Branch index (0-11)
    """
    half_width = width_deg / 2.0
    b0 = zi_apex_deg - half_width  # Start of Zi sector
    
    # Shift and wrap
    shifted = wrap360(longitude_deg - b0)
    
    # Map to branch
    return int(floor(shifted / width_deg)) % 12


# =============================================================================
# HARMONIC FUSION ENGINE
# =============================================================================

def compute_harmonic_phasor(
    phase_deg: float,
    k: int,
    weight: float = 1.0
) -> complex:
    """
    Compute harmonic phasor for a single component.
    
    R_k = w * exp(i * k * theta)
    
    Args:
        phase_deg: Phase angle in degrees
        k: Harmonic number
        weight: Optional weight multiplier
    
    Returns:
        Complex phasor
    """
    theta_rad = deg2rad(phase_deg)
    return weight * cexp(1j * k * theta_rad)


def compute_fusion_features(
    bazi_pillars: Dict[str, int],  # pillar_name -> branch_index
    west_positions: Dict[str, float],  # body_name -> longitude_deg
    weights_bazi: Optional[Dict[str, float]] = None,
    weights_west: Optional[Dict[str, float]] = None,
    config: Optional[FusionConfig] = None
) -> FusionResult:
    """
    Compute complete fusion features from BaZi pillars and Western positions.
    
    Args:
        bazi_pillars: Dictionary of BaZi pillars (e.g., {"year": 0, "month": 5, ...})
        west_positions: Dictionary of Western bodies (e.g., {"Sun": 123.4, ...})
        weights_bazi: Optional weights for each BaZi pillar
        weights_west: Optional weights for each Western body
        config: Fusion configuration
    
    Returns:
        FusionResult with all features
    """
    # Initialize config
    if config is None:
        config = FusionConfig()
    
    # Default weights
    if weights_bazi is None:
        weights_bazi = {pillar: 1.0 for pillar in bazi_pillars}
    if weights_west is None:
        weights_west = {body: 1.0 for body in west_positions}
    
    # Calculate BaZi reference phases
    bazi_phases = {}
    for pillar_name, branch_index in bazi_pillars.items():
        phase = bazi_reference_phase(branch_index, config.zi_apex_deg, config.branch_width_deg)
        bazi_phases[pillar_name] = phase
    
    # Calculate West object phases  
    west_phases = {}
    for body_name, longitude in west_positions.items():
        phase = west_object_phase(
            longitude,
            config.phi_apex_offset_deg,
            config.harmonic_phase_convention
        )
        west_phases[body_name] = phase
    
    # Compute harmonics
    harmonics: Dict[int, HarmonicFeatures] = {}
    degeneracy_flags: List[str] = []
    
    for k in config.harmonics_k:
        # BaZi phasor R_k
        r_k = sum(
            weights_bazi.get(pillar, 1.0) * compute_harmonic_phasor(phase, k)
            for pillar, phase in bazi_phases.items()
        )
        
        # West phasor O_k
        o_k = sum(
            weights_west.get(body, 1.0) * compute_harmonic_phasor(phase, k)
            for body, phase in west_phases.items()
        )
        
        # Calculate features
        magnitude_r = abs(r_k)
        magnitude_o = abs(o_k)
        
        if magnitude_r < config.epsilon_norm or magnitude_o < config.epsilon_norm:
            # Degenerate case
            a_k = 0.0
            degenerate = True
            degeneracy_flags.append(f"harmonic_{k}_degenerate")
        else:
            # Cross-term
            x_k = (r_k.conjugate() * o_k).real
            a_k = x_k / (magnitude_r * magnitude_o)
            degenerate = False
        
        # Intensity
        i_k = abs(r_k + o_k) ** 2
        
        harmonics[k] = HarmonicFeatures(
            k=k,
            r_k=r_k,
            o_k=o_k,
            i_k=i_k,
            x_k=x_k if not degenerate else 0.0,
            a_k=a_k,
            magnitude_r=magnitude_r,
            magnitude_o=magnitude_o,
            degenerate=degenerate
        )
    
    # Calculate soft branch weights for reference
    if west_positions:
        # Use Sun as reference for branch weights
        sun_long = west_positions.get("Sun", 0.0)
        branch_weights = soft_branch_weights(
            sun_long,
            config.zi_apex_deg,
            config.branch_width_deg,
            config.kappa
        )
    else:
        branch_weights = {i: 1.0 / 12.0 for i in range(12)}
    
    # Summary metrics
    total_alignment = sum(abs(hf.a_k) for hf in harmonics.values()) / len(harmonics)
    
    # Find dominant harmonic
    dominant_k = max(
        harmonics.keys(),
        key=lambda k: abs(harmonics[k].i_k),
        default=0
    )
    
    return FusionResult(
        config=config,
        harmonics=harmonics,
        branch_weights=branch_weights,
        total_alignment=total_alignment,
        dominant_harmonic=dominant_k,
        degeneracy_flags=degeneracy_flags,
        bazi_phases=bazi_phases,
        west_phases=west_phases
    )


def interpret_alignment(a_k: float, threshold_pos: float = 0.6, threshold_neg: float = -0.6) -> str:
    """
    Interpret harmonic alignment score.
    
    Args:
        a_k: Alignment score in [-1, 1]
        threshold_pos: Threshold for positive interpretation
        threshold_neg: Threshold for negative interpretation
    
    Returns:
        Text interpretation
    """
    if a_k >= threshold_pos:
        return f"Strong constructive coupling (k={k})"
    elif a_k <= threshold_neg:
        return f"Strong destructive coupling (k={k})"
    else:
        return f"Neutral coupling (k={k})"


def fusion_to_dict(result: FusionResult) -> Dict:
    """Convert FusionResult to dictionary for JSON serialization."""
    return {
        "config": {
            "phi_apex_offset_deg": result.config.phi_apex_offset_deg,
            "zi_apex_deg": result.config.zi_apex_deg,
            "branch_width_deg": result.config.branch_width_deg,
            "harmonics_k": result.config.harmonics_k,
            "kappa": result.config.kappa,
            "fusion_mode": result.config.fusion_mode,
            "harmonic_phase_convention": result.config.harmonic_phase_convention
        },
        "harmonics": {
            str(k): {
                "k": hf.k,
                "i_k": hf.i_k,
                "x_k": hf.x_k,
                "a_k": hf.a_k,
                "magnitude_r": hf.magnitude_r,
                "magnitude_o": hf.magnitude_o,
                "degenerate": hf.degenerate
            }
            for k, hf in result.harmonics.items()
        },
        "branch_weights": {str(k): v for k, v in result.branch_weights.items()},
        "summary": {
            "total_alignment": result.total_alignment,
            "dominant_harmonic": result.dominant_harmonic,
            "degeneracy_flags": result.degeneracy_flags
        },
        "provenance": {
            "bazi_phases": {k: round(v, 6) for k, v in result.bazi_phases.items()},
            "west_phases": {k: round(v, 6) for k, v in result.west_phases.items()}
        }
    }


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_fusion_config(config: FusionConfig) -> Tuple[bool, List[str]]:
    """
    Validate fusion configuration.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Check angle ranges
    if not 0 <= config.phi_apex_offset_deg < 360:
        errors.append(f"phi_apex_offset_deg {config.phi_apex_offset_deg} not in [0, 360)")
    
    if not 0 <= config.zi_apex_deg < 360:
        errors.append(f"zi_apex_deg {config.zi_apex_deg} not in [0, 360)")
    
    # Check branch width
    if config.branch_width_deg <= 0:
        errors.append(f"branch_width_deg {config.branch_width_deg} must be positive")
    
    # Check kappa
    if config.kappa <= 0:
        errors.append(f"kappa {config.kappa} must be positive")
    
    # Check harmonics
    if not config.harmonics_k:
        errors.append("harmonics_k must not be empty")
    
    # Check mode
    if config.fusion_mode not in ["harmonic_phasor", "soft_kernel", "hard_segment"]:
        errors.append(f"Unknown fusion_mode: {config.fusion_mode}")
    
    return (len(errors) == 0, errors)


def validate_harmonic_result(result: FusionResult) -> Tuple[bool, List[str]]:
    """
    Validate fusion result against invariants.
    
    Returns:
        (is_valid, list_of_warnings/errors)
    """
    issues = []
    
    # Check branch weights normalize to ~1
    weight_sum = sum(result.branch_weights.values())
    if abs(weight_sum - 1.0) > 1e-6:
        issues.append(f"Branch weights sum {weight_sum} != 1.0")
    
    # Check harmonic phases in [0, 360)
    for phase in result.bazi_phases.values():
        if not 0 <= phase < 360:
            issues.append(f"BaZi phase {phase} not in [0, 360)")
    
    for phase in result.west_phases.values():
        if not 0 <= phase < 360:
            issues.append(f"West phase {phase} not in [0, 360)")
    
    # Check alignment in [-1, 1]
    for k, hf in result.harmonics.items():
        if not -1.0 <= hf.a_k <= 1.0:
            issues.append(f"Alignment a_k for k={k} is {hf.a_k}, outside [-1, 1]")
    
    return (len(issues) == 0, issues)
