# Branch Mapping Module
# Implements: SHIFT_BOUNDARIES vs SHIFT_LONGITUDES conventions per BaZodiac Spec v1.0.0

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Tuple
from math import floor, degrees, radians, sin, cos, atan2, sqrt


# =============================================================================
# CONSTANTS
# =============================================================================

# Default configuration per spec
DEFAULT_ZI_APEX_DEG: float = 270.0  # Center of Zi sector
DEFAULT_BRANCH_WIDTH_DEG: float = 30.0
DEFAULT_PHI_APEX_OFFSET_DEG: float = 15.0  # Ingress vs Apex shift

# Branch names (for reference)
BRANCH_NAMES = [
    "Zi", "Chou", "Yin", "Mao", "Chen", "Si", 
    "Wu", "Wei", "Shen", "You", "Xu", "Hai"
]

BRANCH_ORDER = {
    "Zi": 0, "Chou": 1, "Yin": 2, "Mao": 3, "Chen": 4, "Si": 5,
    "Wu": 6, "Wei": 7, "Shen": 8, "You": 9, "Xu": 10, "Hai": 11
}


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

BranchConvention = Literal["SHIFT_BOUNDARIES", "SHIFT_LONGITUDES"]
IntervalConvention = Literal["HALF_OPEN", "CLOSED"]

@dataclass(frozen=True)
class BranchMappingConfig:
    """Configuration for branch mapping conventions."""
    
    zi_apex_deg: float = DEFAULT_ZI_APEX_DEG
    branch_width_deg: float = DEFAULT_BRANCH_WIDTH_DEG
    phi_apex_offset_deg: float = DEFAULT_PHI_APEX_OFFSET_DEG
    convention: BranchConvention = "SHIFT_BOUNDARIES"
    interval_convention: IntervalConvention = "HALF_OPEN"


@dataclass(frozen=True)
class BranchMappingResult:
    """Result of branch mapping."""
    
    branch_index: int
    branch_name: str
    center_deg: float
    lower_bound_deg: float
    upper_bound_deg: float
    distance_to_boundary_deg: float
    unstable: bool  # True if near boundary


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def wrap360(degrees: float) -> float:
    """Wrap angle to [0, 360) range."""
    result = degrees % 360.0
    if result < 0:
        result += 360.0
    return result


def wrap180(degrees: float) -> float:
    """Wrap angle to (-180, 180] range."""
    result = wrap360(degrees + 180.0) - 180.0
    return result


def delta_deg(a: float, b: float) -> float:
    """Angular distance in degrees [0, 180]."""
    delta = abs(wrap360(a) - wrap360(b))
    if delta > 180.0:
        delta = 360.0 - delta
    return delta


def calculate_branch_centers(
    zi_apex_deg: float,
    width_deg: float
) -> List[float]:
    """
    Calculate center longitudes for all 12 branches.
    
    Args:
        zi_apex_deg: Center of Zi sector (default 270°)
        width_deg: Width of each branch (default 30°)
    
    Returns:
        List of 12 branch center longitudes
    """
    half_width = width_deg / 2.0
    b0 = zi_apex_deg - half_width  # Start of Zi sector
    return [wrap360(b0 + width_deg * i) for i in range(12)]


def branch_from_longitude(
    longitude_deg: float,
    zi_apex_deg: float = DEFAULT_ZI_APEX_DEG,
    width_deg: float = DEFAULT_BRANCH_WIDTH_DEG,
    convention: BranchConvention = "SHIFT_BOUNDARIES",
    interval_convention: IntervalConvention = "HALF_OPEN"
) -> int:
    """
    Map a longitude to a branch index.
    
    Implements SHIFT_BOUNDARIES convention per spec:
    
    K1 SHIFT_BOUNDARIES (recommended):
        branch(lambda) = floor(wrap360(lambda - B0) / width)
        where B0 = zi_apex_deg - width/2
    
    K2 SHIFT_LONGITUDES:
        lambda_apex = wrap360(lambda - phi_apex_offset_deg)
        branch(lambda) = floor(wrap360(lambda_apex - B0_apex) / width)
        where B0_apex = wrap360(B0 - phi_apex_offset_deg)
    
    Args:
        longitude_deg: Ecliptic longitude (0-360°)
        zi_apex_deg: Center of Zi sector
        width_deg: Branch width
        convention: SHIFT_BOUNDARIES or SHIFT_LONGITUDES
        interval_convention: HALF_OPEN or CLOSED
    
    Returns:
        Branch index (0-11)
    """
    half_width = width_deg / 2.0
    b0 = zi_apex_deg - half_width  # Lower bound of Zi sector
    
    if convention == "SHIFT_BOUNDARIES":
        # Shift the longitude by B0, then wrap
        shifted = wrap360(longitude_deg - b0)
        
        # Map to branch using floor
        branch = int(floor(shifted / width_deg)) % 12
        
    elif convention == "SHIFT_LONGITUDES":
        # First shift by apex offset
        lambda_apex = wrap360(longitude_deg - phi_apex_offset_deg)
        
        # Shift by B0_apex (B0 shifted by phi_apex_offset_deg)
        b0_apex = wrap360(b0 - phi_apex_offset_deg)
        shifted = wrap360(lambda_apex - b0_apex)
        
        # Map to branch
        branch = int(floor(shifted / width_deg)) % 12
    
    return branch


def branch_boundaries(
    branch_index: int,
    zi_apex_deg: float = DEFAULT_ZI_APEX_DEG,
    width_deg: float = DEFAULT_BRANCH_WIDTH_DEG
) -> Tuple[float, float]:
    """
    Get lower and upper bounds for a branch.
    
    Args:
        branch_index: Branch index (0-11)
        zi_apex_deg: Center of Zi sector
        width_deg: Branch width
    
    Returns:
        (lower_bound_deg, upper_bound_deg)
    """
    half_width = width_deg / 2.0
    b0 = zi_apex_deg - half_width  # Lower bound of Zi sector
    
    center = wrap360(b0 + width_deg * branch_index)
    lower = wrap360(center - half_width)
    upper = wrap360(center + half_width)
    
    return (lower, upper)


def branch_mapping_with_diagnostics(
    longitude_deg: float,
    zi_apex_deg: float = DEFAULT_ZI_APEX_DEG,
    width_deg: float = DEFAULT_BRANCH_WIDTH_DEG,
    phi_apex_offset_deg: float = DEFAULT_PHI_APEX_OFFSET_DEG,
    convention: BranchConvention = "SHIFT_BOUNDARIES",
    interval_convention: IntervalConvention = "HALF_OPEN",
    boundary_warning_deg: float = 0.1
) -> BranchMappingResult:
    """
    Map longitude to branch with full diagnostics.
    
    Args:
        longitude_deg: Ecliptic longitude
        zi_apex_deg: Center of Zi sector
        width_deg: Branch width
        phi_apex_offset_deg: Apex offset for SHIFT_LONGITUDES
        convention: Branch convention
        interval_convention: Interval convention
        boundary_warning_deg: Warning threshold for boundary proximity
    
    Returns:
        BranchMappingResult with diagnostics
    """
    # Calculate branch
    branch = branch_from_longitude(
        longitude_deg,
        zi_apex_deg,
        width_deg,
        convention,
        interval_convention
    )
    
    # Calculate bounds
    lower, upper = branch_boundaries(branch, zi_apex_deg, width_deg)
    
    # Calculate center
    center = (lower + upper) / 2.0
    if lower > upper:
        # Wrap-around case
        center = wrap360(center)
    
    # Calculate distance to nearest boundary
    dist_to_lower = delta_deg(longitude_deg, lower)
    dist_to_upper = delta_deg(longitude_deg, upper)
    distance_to_boundary = min(dist_to_lower, dist_to_upper)
    
    # Determine if unstable (near boundary)
    unstable = distance_to_boundary < boundary_warning_deg
    
    return BranchMappingResult(
        branch_index=branch,
        branch_name=BRANCH_NAMES[branch],
        center_deg=center,
        lower_bound_deg=lower,
        upper_bound_deg=upper,
        distance_to_boundary_deg=distance_to_boundary,
        unstable=unstable
    )


def check_convention_consistency(
    longitude_deg: float,
    zi_apex_deg: float = DEFAULT_ZI_APEX_DEG,
    width_deg: float = DEFAULT_BRANCH_WIDTH_DEG,
    phi_apex_offset_deg: float = DEFAULT_PHI_APEX_OFFSET_DEG
) -> Tuple[bool, str]:
    """
    Check if SHIFT_BOUNDARIES and SHIFT_LONGITUDES give same result.
    
    Args:
        longitude_deg: Test longitude
        zi_apex_deg: Center of Zi sector
        width_deg: Branch width
        phi_apex_offset_deg: Apex offset
    
    Returns:
        (is_consistent, message)
    """
    # Calculate using both conventions
    branch_k1 = branch_from_longitude(
        longitude_deg, zi_apex_deg, width_deg,
        "SHIFT_BOUNDARIES", "HALF_OPEN"
    )
    
    branch_k2 = branch_from_longitude(
        longitude_deg, zi_apex_deg, width_deg,
        "SHIFT_LONGITUDES", "HALF_OPEN"
    )
    
    # These should be different!
    # The whole point is that SHIFT_LONGITUDES uses shifted coordinates
    
    if branch_k1 == branch_k2:
        return (True, f"Both conventions give branch {branch_k1}")
    else:
        return (False, f"K1={branch_k1}, K2={branch_k2} (expected different)")


def equivalence_test(
    longitude_deg: float,
    zi_apex_deg: float = DEFAULT_ZI_APEX_DEG,
    width_deg: float = DEFAULT_BRANCH_WIDTH_DEG,
    phi_apex_offset_deg: float = DEFAULT_PHI_APEX_OFFSET_DEG
) -> Dict:
    """
    Test equivalence between conventions.
    
    Note: These conventions are NOT equivalent for shifted longitudes!
    This test is for validation purposes.
    
    Returns:
        Dictionary with test results
    """
    # SHIFT_BOUNDARIES: map lambda directly
    b1 = branch_from_longitude(
        longitude_deg, zi_apex_deg, width_deg,
        "SHIFT_BOUNDARIES", "HALF_OPEN"
    )
    
    # SHIFT_LONGITUDES: shift lambda first, then map
    lambda_apex = wrap360(longitude_deg - phi_apex_offset_deg)
    b2 = branch_from_longitude(
        lambda_apex, zi_apex_deg, width_deg,
        "SHIFT_BOUNDARIES", "HALF_OPEN"
    )
    
    return {
        "longitude_deg": longitude_deg,
        "lambda_apex_deg": lambda_apex,
        "shift_boundaries_branch": b1,
        "shift_longitudes_branch": b2,
        "equivalent": b1 == b2,
        "note": "These should differ by phi_apex_offset_deg when away from boundaries"
    }


def all_branch_centers(zi_apex_deg: float = DEFAULT_ZI_APEX_DEG,
                       width_deg: float = DEFAULT_BRANCH_WIDTH_DEG) -> Dict[int, Dict]:
    """
    Get all branch centers with names and bounds.
    
    Returns:
        Dictionary mapping branch_index to branch info
    """
    centers = calculate_branch_centers(zi_apex_deg, width_deg)
    result = {}
    
    for i, center in enumerate(centers):
        lower, upper = branch_boundaries(i, zi_apex_deg, width_deg)
        result[i] = {
            "name": BRANCH_NAMES[i],
            "center_deg": round(center, 6),
            "lower_bound_deg": round(lower, 6),
            "upper_bound_deg": round(upper, 6),
            "half_width_deg": round(width_deg / 2, 6)
        }
    
    return result


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_config(config: BranchMappingConfig) -> Tuple[bool, List[str]]:
    """
    Validate branch mapping configuration.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Check angle ranges
    if not 0 <= config.zi_apex_deg < 360:
        errors.append(f"zi_apex_deg {config.zi_apex_deg} not in [0, 360)")
    
    if not 0 <= config.phi_apex_offset_deg < 360:
        errors.append(f"phi_apex_offset_deg {config.phi_apex_offset_deg} not in [0, 360)")
    
    # Check width
    if config.branch_width_deg <= 0:
        errors.append(f"branch_width_deg {config.branch_width_deg} must be positive")
    
    # Check convention
    if config.convention not in ["SHIFT_BOUNDARIES", "SHIFT_LONGITUDES"]:
        errors.append(f"Unknown convention: {config.convention}")
    
    return (len(errors) == 0, errors)


def validate_interval_convention(
    longitude_deg: float,
    branch_index: int,
    zi_apex_deg: float,
    width_deg: float,
    convention: IntervalConvention
) -> Tuple[bool, str]:
    """
    Validate that longitude falls in correct interval for branch.
    
    Args:
        longitude_deg: Test longitude
        branch_index: Expected branch
        zi_apex_deg: Center of Zi sector
        width_deg: Branch width
        convention: HALF_OPEN or CLOSED
    
    Returns:
        (is_valid, message)
    """
    lower, upper = branch_boundaries(branch_index, zi_apex_deg, width_deg)
    
    if convention == "HALF_OPEN":
        # [lower, upper) - lower included, upper excluded
        # Handle wrap-around
        if lower < upper:
            in_interval = lower <= longitude_deg < upper
        else:
            in_interval = longitude_deg >= lower or longitude_deg < upper
        
        if not in_interval:
            return (False, f"Longitude {longitude_deg} not in [{lower}, {upper}) for branch {branch_index}")
    
    elif convention == "CLOSED":
        # [lower, upper] - both inclusive
        if lower < upper:
            in_interval = lower <= longitude_deg <= upper
        else:
            in_interval = longitude_deg >= lower or longitude_deg <= upper
        
        if not in_interval:
            return (False, f"Longitude {longitude_deg} not in [{lower}, {upper}] for branch {branch_index}")
    
    return (True, f"Longitude {longitude_deg} in correct interval for branch {branch_index}")


# =============================================================================
# TEST VECTORS
# =============================================================================

def run_test_vectors() -> Dict:
    """
    Run spec test vectors for branch mapping.
    
    TV1: Branch boundary (zi_apex=270, width=30)
    TV2: Wrap-around at sector start
    TV4: Convention equivalence (should differ!)
    """
    zi_apex = 270.0
    width = 30.0
    phi_offset = 15.0
    
    results = {
        "config": {"zi_apex_deg": zi_apex, "branch_width_deg": width},
        "test_vectors": []
    }
    
    # TV1: Branch boundaries
    test_cases_tv1 = [
        (275.0, 0, "Zi"),    # In Zi sector [255, 285)
        (285.0, 1, "Chou"), # Boundary -> Chou
        (284.999, 0, "Zi"), # Just below boundary
        (254.999, 11, "Hai"), # Wrap-around: Hai [225, 255)
        (255.0, 0, "Zi")     # Boundary -> Zi
    ]
    
    for lambda_deg, expected_idx, expected_name in test_cases_tv1:
        result = branch_mapping_with_diagnostics(
            lambda_deg, zi_apex, width, phi_offset,
            "SHIFT_BOUNDARIES", "HALF_OPEN"
        )
        passed = (result.branch_index == expected_idx)
        results["test_vectors"].append({
            "name": f"TV1_lambda_{lambda_deg}",
            "input": lambda_deg,
            "expected": expected_idx,
            "got": result.branch_index,
            "passed": passed,
            "details": {
                "branch_name": result.branch_name,
                "bounds": [result.lower_bound_deg, result.upper_bound_deg],
                "distance_to_boundary": result.distance_to_boundary_deg,
                "unstable": result.unstable
            }
        })
    
    # TV4: Convention comparison (should differ!)
    lambda_test = 275.0
    equiv = equivalence_test(lambda_test, zi_apex, width, phi_offset)
    results["test_vectors"].append({
        "name": "TV4_convention_equivalence",
        "input": lambda_test,
        "shift_boundaries": equiv["shift_boundaries_branch"],
        "shift_longitudes": equiv["shift_longitudes_branch"],
        "equivalent": equiv["equivalent"],
        "note": "Should NOT be equivalent (this is the point of the offset)"
    })
    
    # All branch centers
    results["branch_centers"] = all_branch_centers(zi_apex, width)
    
    return results


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import json
    
    print("BaZodiac Branch Mapping Test Vectors")
    print("=" * 50)
    
    results = run_test_vectors()
    print(json.dumps(results, indent=2))
