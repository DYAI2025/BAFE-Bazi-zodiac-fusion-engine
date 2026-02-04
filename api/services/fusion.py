# BaZodiac Fusion Service
# Bridge operators between BaZi and Western systems

from typing import Dict, List, Any, Optional
from ..utils.core import (
    hard_branch_mapping, soft_branch_weights, harmonic_phasor_fusion,
    BRANCH_NAMES
)


class FusionService:
    """Apply fusion operators between BaZi and Western systems."""
    
    @staticmethod
    def apply_hard_segment(
        positions: Dict[str, float],  # body -> lambda_deg
        zi_apex_deg: float = 270.0,
        width_deg: float = 30.0,
        convention: str = "SHIFT_BOUNDARIES",
        phi_offset_deg: float = 15.0
    ) -> List[Dict[str, Any]]:
        """
        Apply hard segment mapping.
        
        Returns list of {body, branch_index, branch_center_deg, distance_to_boundary_deg}
        """
        results = []
        
        for body, lambda_deg in positions.items():
            branch_idx = hard_branch_mapping(
                lambda_deg, zi_apex_deg, width_deg, convention, phi_offset_deg
            )
            
            # Distance to boundary
            half = width_deg / 2.0
            center = zi_apex_deg + width_deg * branch_idx
            distance = abs(lambda_deg - center)
            
            results.append({
                "body": body,
                "branch_index": branch_idx,
                "branch_name": BRANCH_NAMES[branch_idx],
                "branch_center_deg": round(center, 4),
                "distance_to_boundary_deg": round(distance, 4)
            })
        
        return results
    
    @staticmethod
    def apply_soft_kernel(
        positions: Dict[str, float],
        zi_apex_deg: float = 270.0,
        width_deg: float = 30.0,
        kappa: float = 4.0
    ) -> List[Dict[str, Any]]:
        """
        Apply soft kernel weighting.
        
        Returns list of {body, weights: {branch: weight}}
        """
        results = []
        
        for body, lambda_deg in positions.items():
            weights = soft_branch_weights(lambda_deg, zi_apex_deg, width_deg, kappa)
            results.append({
                "body": body,
                "weights": {str(k): round(v, 6) for k, v in weights.items()},
                "kappa": kappa
            })
        
        return results
    
    @staticmethod
    def apply_harmonic_phasor(
        pillars: Dict[str, int],  # name -> branch_index
        positions: Dict[str, float],  # body -> lambda_deg
        zi_apex_deg: float = 270.0,
        width_deg: float = 30.0,
        harmonics_k: List[int] = [2, 3, 4, 6, 12],
        phi_offset_deg: float = 15.0
    ) -> Dict[str, Any]:
        """
        Apply harmonic phasor fusion.
        
        Returns {mode, harmonics: [{k, a_k, i_k, degenerate}], fusion_features}
        """
        # Compute harmonic features
        harmonics_result = harmonic_phasor_fusion(
            pillars, positions, zi_apex_deg, width_deg, harmonics_k, phi_offset_deg
        )
        
        # Extract alignment scores
        a_scores = [h["a_k"] for h in harmonics_result.values()]
        avg_alignment = sum(a_scores) / len(a_scores) if a_scores else 0.0
        
        # Count degeneracies
        degenerate_count = sum(1 for h in harmonics_result.values() if h["degenerate"])
        
        # Fusion features summary
        fusion_features = {
            "avg_alignment": round(avg_alignment, 4),
            "degenerate_harmonics": degenerate_count,
            "strongest_harmonic": max(harmonics_result.values(), key=lambda h: abs(h["a_k"]))["k"]
            if harmonics_result else None
        }
        
        return {
            "mode": "harmonic_phasor",
            "harmonics": list(harmonics_result.values()),
            "fusion_features": fusion_features
        }
    
    @staticmethod
    def apply_fusion(
        pillars: Dict[str, int],
        positions: Dict[str, float],
        fusion_mode: str,
        zi_apex_deg: float = 270.0,
        width_deg: float = 30.0,
        convention: str = "SHIFT_BOUNDARIES",
        phi_offset_deg: float = 15.0,
        harmonics_k: Optional[List[int]] = None,
        kappa: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Apply specified fusion mode.
        
        Returns complete fusion result.
        """
        if fusion_mode == "hard_segment":
            return {
                "mode": fusion_mode,
                "hard_mapping": FusionService.apply_hard_segment(
                    positions, zi_apex_deg, width_deg, convention, phi_offset_deg
                )
            }
        
        elif fusion_mode == "soft_kernel":
            return {
                "mode": fusion_mode,
                "soft_weights": FusionService.apply_soft_kernel(
                    positions, zi_apex_deg, width_deg, kappa or 4.0
                )
            }
        
        elif fusion_mode == "harmonic_phasor":
            return FusionService.apply_harmonic_phasor(
                pillars, positions, zi_apex_deg, width_deg,
                harmonics_k or [2, 3, 4, 6, 12], phi_offset_deg
            )
        
        else:
            raise ValueError(f"Unknown fusion mode: {fusion_mode}")
