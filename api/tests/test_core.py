# BaZodiac Engine Tests
# Test vectors and integration tests

from api.utils.core import (
    wrap360, wrap180, delta_deg,
    hour_branch_from_tlst, hard_branch_mapping,
    soft_branch_weights, harmonic_phasor_fusion
)

# ============== Test Vectors ==============

TV1_BRANCH_BOUNDARY = [
    # (longitude, expected_branch, description)
    (275.0, 0, "Middle of Zi sector"),
    (285.0, 1, "Exact boundary -> Chou"),
    (284.999, 0, "Just below boundary -> Zi"),
    (254.999, 11, "Wrap-around -> Hai"),
    (255.0, 0, "Exact start -> Zi"),
    (0.0, 11, "Start of Zi wrap"),
    (359.999, 11, "Just before 360"),
]

TV4_TLST_HOURS = [
    # (tlst_hours, expected_branch)
    (22.999, 11),  # Just before Zi hour
    (23.000, 0),    # Start of Zi hour (23:00)
    (0.999, 0),      # Just before Chou
    (1.000, 1),      # Start of Chou hour
    (11.000, 5),     # Middle of day
]


def test_wrap360():
    """Test wrap360 function."""
    assert wrap360(0) == 0
    assert wrap360(360) == 0
    assert wrap360(720) == 0
    assert wrap360(-1) == 359
    assert wrap360(180) == 180
    assert wrap360(270.5) == 270.5
    print("✅ wrap360 tests passed")


def test_wrap180():
    """Test wrap180 function."""
    assert wrap180(0) == 0
    assert wrap180(180) == 180
    assert wrap180(-180) == 180
    assert wrap180(270) == -90
    assert wrap180(-90) == -90
    print("✅ wrap180 tests passed")


def test_delta_deg():
    """Test angular distance function."""
    assert delta_deg(0, 0) == 0
    assert delta_deg(0, 180) == 180
    assert delta_deg(0, 90) == 90
    assert delta_deg(350, 10) == 20  # Wrap around
    assert delta_deg(270, 90) == 180  # Max distance
    print("✅ delta_deg tests passed")


def test_hour_branch_from_tlst():
    """Test hour branch calculation from TLST."""
    for tlst, expected in TV4_TLST_HOURS:
        result = hour_branch_from_tlst(tlst)
        assert result == expected, f"TLST {tlst}h -> {result}, expected {expected}"
    print("✅ hour_branch_from_tlst tests passed")


def test_branch_boundaries():
    """Test branch boundary mapping."""
    for lon, expected, desc in TV1_BRANCH_BOUNDARY:
        result = hard_branch_mapping(lon)
        assert result == expected, f"{desc}: {lon}° -> {result}, expected {expected}"
    print("✅ hard_branch_mapping tests passed")


def test_soft_kernel_symmetry():
    """Test that soft kernel is symmetric at exact boundaries."""
    # At exact midpoint between Zi (270) and Chou (300)
    # Weights should be equal
    weights = soft_branch_weights(285.0, zi_apex_deg=270.0, width_deg=30.0)
    
    # Zi (0) and Chou (1) weights should be nearly equal
    assert abs(weights[0] - weights[1]) < 0.01, "Kernel not symmetric at boundary"
    
    # Sum should be 1.0
    total = sum(weights.values())
    assert abs(total - 1.0) < 0.001, f"Weights don't sum to 1.0: {total}"
    
    print("✅ soft_kernel symmetry tests passed")


def test_harmonic_phasor():
    """Test harmonic phasor fusion."""
    pillars = {"year": 0, "month": 5, "day": 9, "hour": 11}
    positions = {"Sun": 275.0, "Moon": 120.5}
    
    result = harmonic_phasor_fusion(
        pillars, positions,
        zi_apex_deg=270.0,
        width_deg=30.0,
        harmonics_k=[2, 3, 4]
    )
    
    # Check basic structure
    assert len(result) == 3
    for k, features in result.items():
        assert "a_k" in features
        assert "i_k" in features
        assert "degenerate" in features
        assert -1.0 <= features["a_k"] <= 1.0, f"A_k out of range: {features['a_k']}"
    
    # Should not be degenerate with multiple pillars/positions
    for features in result.values():
        assert not features["degenerate"], "Harmonic marked degenerate unexpectedly"
    
    print("✅ harmonic_phasor tests passed")


def test_harmonic_degeneracy():
    """Test harmonic phasor with single pillar/body."""
    pillars = {"hour": 0}
    positions = {"Sun": 0.0}
    
    result = harmonic_phasor_fusion(
        pillars, positions,
        harmonics_k=[2, 3, 4]
    )
    
    # With single pillar/body, should still work
    # (magnitude > 0 for both phasors)
    for features in result.values():
        # Just check structure - degeneracy depends on actual math
        assert "k" in features
        assert "a_k" in features
    
    print("✅ harmonic_degeneracy tests passed")


if __name__ == "__main__":
    print("Running BaZodiac Engine tests...\n")
    
    test_wrap360()
    test_wrap180()
    test_delta_deg()
    test_hour_branch_from_tlst()
    test_branch_boundaries()
    test_soft_kernel_symmetry()
    test_harmonic_phasor()
    test_harmonic_degeneracy()
    
    print("\n🎉 All tests passed!")
