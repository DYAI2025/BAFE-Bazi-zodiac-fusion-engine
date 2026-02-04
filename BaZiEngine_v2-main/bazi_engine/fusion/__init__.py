# Fusion Module - BaZodiac Engine
# Provides fusion between BaZi and Western astrology

from .harmonics import (
    FusionConfig,
    FusionResult,
    HarmonicFeatures,
    compute_fusion_features,
    fusion_to_dict,
    validate_fusion_config,
    validate_harmonic_result,
    DEFAULT_PHI_APEX_OFFSET_DEG,
    DEFAULT_ZI_APEX_DEG,
    DEFAULT_BRANCH_WIDTH_DEG,
    DEFAULT_HARMONICS,
    DEFAULT_KAPPA
)

__all__ = [
    "FusionConfig",
    "FusionResult", 
    "HarmonicFeatures",
    "compute_fusion_features",
    "fusion_to_dict",
    "validate_fusion_config",
    "validate_harmonic_result",
    "DEFAULT_PHI_APEX_OFFSET_DEG",
    "DEFAULT_ZI_APEX_DEG",
    "DEFAULT_BRANCH_WIDTH_DEG",
    "DEFAULT_HARMONICS",
    "DEFAULT_KAPPA"
]
