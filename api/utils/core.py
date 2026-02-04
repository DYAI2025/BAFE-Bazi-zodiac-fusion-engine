# BaZodiac Core Utilities
# Safe angle operations and mathematical helpers

from typing import Union
import math

Number = Union[int, float]

# ============== Angle Operators ==============

def wrap360(x: Number) -> float:
    """Wrap angle to [0, 360)"""
    result = x % 360.0
    if result < 0:
        result += 360.0
    return result

def wrap180(x: Number) -> float:
    """Wrap angle to (-180, 180]"""
    return wrap360(x + 180.0) - 180.0

def delta_deg(a: Number, b: Number) -> float:
    """Angular distance [0, 180]"""
    d = abs(wrap360(a) - wrap360(b))
    return d if d <= 180.0 else 360.0 - d

def deg2rad(deg: Number) -> float:
    return math.radians(deg)

def rad2deg(rad: Number) -> float:
    return math.degrees(rad)

# ============== Branch Operations ==============

def hour_branch_from_tlst(tlst_hours: Number, width_deg: float = 30.0) -> int:
    """
    Compute hour branch from TLST.
    
    Formula: floor(((TLST + 1) % 24) / 2)
    
    Examples:
        22.999 -> 11 (Hai)
        23.000 -> 0 (Zi)
        0.999 -> 0 (Zi)
        1.000 -> 1 (Chou)
    """
    h = int(((float(tlst_hours) + 1.0) % 24.0) / 2.0) % 12
    return h

def hard_branch_mapping(
    longitude_deg: Number,
    zi_apex_deg: Number = 270.0,
    width_deg: Number = 30.0,
    convention: str = "SHIFT_BOUNDARIES",
    phi_offset_deg: Number = 15.0
) -> int:
    """
    Map longitude to branch using hard segmentation.
    
    SHIFT_BOUNDARIES (default):
        branch = floor((λ - B0) / 30) mod 12
        B0 = zi_apex - 15
    
    SHIFT_LONGITUDES:
        λ_apex = λ - φ_offset
        branch = floor((λ_apex - B0_apex) / 30) mod 12
    """
    half = float(width_deg) / 2.0
    b0 = float(zi_apex_deg) - half  # Start of Zi sector
    
    if convention == "SHIFT_BOUNDARIES":
        shifted = wrap360(float(longitude_deg) - b0)
    else:  # SHIFT_LONGITUDES
        lambda_apex = wrap360(float(longitude_deg) - float(phi_offset_deg))
        b0_apex = wrap360(b0 - float(phi_offset_deg))
        shifted = wrap360(lambda_apex - b0_apex)
    
    return int(math.floor(shifted / float(width_deg))) % 12

def soft_branch_weights(
    longitude_deg: Number,
    zi_apex_deg: Number = 270.0,
    width_deg: Number = 30.0,
    kappa: float = 4.0
) -> dict[int, float]:
    """
    Calculate soft branch weights using von Mises kernel.
    
    Returns dict mapping branch -> weight (sums to 1.0)
    """
    centers = [wrap360(float(zi_apex_deg) + float(width_deg) * i) for i in range(12)]
    
    raw_weights = []
    for center in centers:
        delta = delta_deg(float(longitude_deg), center)
        delta_rad = deg2rad(delta)
        weight = math.exp(kappa * math.cos(delta_rad))
        raw_weights.append(weight)
    
    total = sum(raw_weights)
    if total == 0:
        return {i: 1.0/12.0 for i in range(12)}
    
    return {i: w / total for i, w in enumerate(raw_weights)}

# ============== Harmonic Phasor Fusion ==============

def harmonic_phasor_fusion(
    pillars: dict[str, int],  # name -> branch_index
    positions: dict[str, float],  # name -> lambda_deg
    zi_apex_deg: float = 270.0,
    width_deg: float = 30.0,
    harmonics_k: list[int] = [2, 3, 4, 6, 12],
    phi_offset_deg: float = 15.0,
    epsilon_norm: float = 1e-10
) -> dict[int, dict[str, Any]]:
    """
    Compute harmonic fusion features.
    
    R_k = Σ w_i * exp(i * k * θ_i)  # BaZi reference phasor
    O_k = Σ v_p * exp(i * k * λ_p)    # West object phasor
    
    Fusion features:
        I_k = |R_k + O_k|²
        X_k = Re(conj(R_k) * O_k)
        A_k = X_k / (|R_k| * |O_k| + ε)  # Alignment [-1, 1]
    """
    results = {}
    
    for k in harmonics_k:
        # BaZi phasor (branches as unit circle points)
        r_real = 0.0
        r_imag = 0.0
        for idx in pillars.values():
            theta = deg2rad(float(zi_apex_deg) + float(width_deg) * idx)
            r_real += math.cos(k * theta)
            r_imag += math.sin(k * theta)
        
        magnitude_r = math.sqrt(r_real**2 + r_imag**2)
        
        # West phasor (apex-shifted longitudes)
        o_real = 0.0
        o_imag = 0.0
        for lon in positions.values():
            lambda_apex = wrap360(float(lon) - float(phi_offset_deg))
            theta = deg2rad(lambda_apex)
            o_real += math.cos(theta)
            o_imag += math.sin(theta)
        
        magnitude_o = math.sqrt(o_real**2 + o_imag**2)
        
        # Fusion features
        degenerate = magnitude_r < epsilon_norm or magnitude_o < epsilon_norm
        
        if degenerate:
            a_k = 0.0
            x_k = 0.0
        else:
            # X_k = Re(conj(R_k) * O_k)
            x_k = r_real * o_real + r_imag * o_imag
            a_k = x_k / (magnitude_r * magnitude_o)
        
        # I_k = |R_k + O_k|²
        sum_real = r_real + o_real
        sum_imag = r_imag + o_imag
        i_k = sum_real**2 + sum_imag**2
        
        results[k] = {
            "k": k,
            "a_k": round(a_k, 6),
            "i_k": round(i_k, 6),
            "x_k": round(x_k, 6) if not degenerate else None,
            "magnitude_r": round(magnitude_r, 6),
            "magnitude_o": round(magnitude_o, 6),
            "degenerate": degenerate
        }
    
    return results

# ============== Julian Date ==============

def gregorian_to_jd(year: int, month: int, day: int, hour: float) -> float:
    """
    Convert Gregorian date/time to Julian Date.
    
    Args:
        year: Year (e.g., 1992)
        month: Month (1-12)
        day: Day (1-31)
        hour: Hour (0.0 - 23.999...)
    
    Returns:
        Julian Date
    """
    # Algorithm from Meeus
    if month <= 2:
        year -= 1
        month += 12
    
    a = int(year / 100)
    b = 2 - a + int(a / 4)
    
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + hour / 24.0 + b - 1524.5
    
    return jd

def jd_to_gregorian(jd: float) -> tuple[int, int, int, float]:
    """
    Convert Julian Date to Gregorian date/time.
    
    Returns:
        (year, month, day, hour)
    """
    jd += 0.5
    z = int(jd)
    f = jd - z
    
    if z >= 2299161:
        a = int((z - 1867216.25) / 36524.25)
        b = z + 1 + a - int(a / 4)
    else:
        b = z
    
    c = b + 1524
    d = int((c - 122.1) / 365.25)
    e = int(365.25 * d)
    g = int((c - e) / 30.6001)
    
    day = c - e + int(f * 86400.0) - int(30.6001 * g)
    
    if g < 13.5:
        month = g - 1
    else:
        month = g - 13
    
    if month > 2.5:
        year = d - 4716
    else:
        year = d - 4715
    
    hour_frac = (day - int(day)) * 24.0
    day = int(day)
    
    return year, month, day, hour_frac

# ============== Constants ==============

STEM_NAMES = ["Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui"]
BRANCH_NAMES = ["Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai"]

def stem_name(index: int) -> str:
    return STEM_NAMES[index % 10]

def branch_name(index: int) -> str:
    return BRANCH_NAMES[index % 12]

def sexagenary_name(sex_index: int) -> str:
    """Get sexagenary cycle name (e.g., 0 -> JiaZi)"""
    return f"{stem_name(sex_index)}{branch_name(sex_index)}"
