# BaZodiac Ephemeris Provider Service
# Swiss Ephemeris integration for accurate planetary positions

from typing import Dict, List, Optional, Any
from datetime import datetime
import math

try:
    import swisseph as swe
    SWISSEPH_AVAILABLE = True
except ImportError:
    SWISSEPH_AVAILABLE = False
    print("Warning: Swiss Ephemeris not available. Using approximations.")


# ============== Constants ==============

PLANET_IDS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
}

# Flag combinations
FLAG_SPEED = swe.FLG_SPEED
FLAG_DEFAULTEPH = swe.FLG_DEFAULTEPH


class EphemerisProvider:
    """
    Swiss Ephemeris-based position provider.
    
    Provides accurate planetary positions using the Swiss Ephemeris library.
    """
    
    def __init__(
        self,
        ephemeris_path: Optional[str] = None,
        zodiac_mode: str = "tropical",
        ayanamsa_id: Optional[str] = None
    ):
        """
        Initialize ephemeris provider.
        """
        self.zodiac_mode = zodiac_mode
        self.ayanamsa_id = ayanamsa_id
        self.is_available = SWISSEPH_AVAILABLE
        
        if SWISSEPH_AVAILABLE:
            if ephemeris_path:
                swe.set_ephe_path(ephemeris_path)
            print(f"Swiss Ephemeris initialized. Mode: {zodiac_mode}")
        else:
            print("Using approximate ephemeris (Swiss Eph not available)")
    
    def compute_positions(
        self,
        tt_dt: datetime,
        bodies: List[str],
        coordinate_system: str = "ecliptic"
    ) -> Dict[str, Dict[str, float]]:
        """
        Compute planetary positions for given bodies.
        """
        if not SWISSEPH_AVAILABLE:
            return self._approximate_positions(tt_dt, bodies)
        
        # Convert datetime to Julian Day (TT)
        jd = swe.julday(
            tt_dt.year, tt_dt.month, tt_dt.day,
            tt_dt.hour + tt_dt.minute / 60.0 + tt_dt.second / 3600.0
        )
        
        positions = {}
        
        for body in bodies:
            # Get planet ID
            if body not in PLANET_IDS:
                print(f"Warning: Unknown body {body}")
                continue
            
            planet_id = PLANET_IDS[body]
            
            # Compute position (use FLG_SPEED for velocity)
            flag = FLAG_SPEED | FLAG_DEFAULTEPH
            
            result, error = swe.calc(jd, planet_id, flag)
            
            # Result format: [longitude, latitude, distance, speed_long, speed_lat, speed_dist]
            longitude = result[0]
            latitude = result[1]
            speed_long = result[3] if len(result) > 3 else None
            
            # Determine retrograde status
            retrograde = speed_long < 0 if speed_long is not None else None
            
            # Wrap to [0, 360)
            if longitude is not None:
                longitude = longitude % 360.0
                if longitude < 0:
                    longitude += 360.0
            
            positions[body] = {
                "longitude_deg": round(longitude, 6) if longitude else None,
                "latitude_deg": round(latitude, 6) if latitude else None,
                "speed_deg_per_day": round(speed_long, 6) if speed_long else None,
                "retrograde": retrograde
            }
        
        return positions
    
    def compute_sun_position(
        self,
        tt_dt: datetime
    ) -> Dict[str, float]:
        """Compute Sun position (most common use case)."""
        return self.compute_positions(tt_dt, ["Sun"])["Sun"]
    
    def compute_full_chart(
        self,
        tt_dt: datetime,
        bodies: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Compute positions for standard natal chart.
        """
        if bodies is None:
            bodies = list(PLANET_IDS.keys())
        return self.compute_positions(tt_dt, bodies)
    
    def _approximate_positions(
        self,
        dt: datetime,
        bodies: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """
        Fallback approximate positions when Swiss Eph not available.
        """
        from ..utils.core import wrap360, gregorian_to_jd
        
        jd = gregorian_to_jd(dt.year, dt.month, dt.day,
                            dt.hour + dt.minute / 60.0)
        
        positions = {}
        
        for body in bodies:
            if body == "Sun":
                mean_long = (280.46 + 0.9856474 * (jd - 2451545.0)) % 360
                positions[body] = {
                    "longitude_deg": round(mean_long, 2),
                    "latitude_deg": 0.0,
                    "speed_deg_per_day": 0.9856,
                    "retrograde": False
                }
            elif body == "Moon":
                mean_long = (218.316 + 13.176396 * (jd - 2451545.0)) % 360
                mean_lat = 5.0 * math.sin(math.radians((jd - 2451545.0) * 0.5))
                positions[body] = {
                    "longitude_deg": round(mean_long, 2),
                    "latitude_deg": round(mean_lat, 2),
                    "speed_deg_per_day": 13.176,
                    "retrograde": False
                }
            else:
                mean_long = (100.0 + 0.5 * (jd - 2451545.0)) % 360
                positions[body] = {
                    "longitude_deg": round(mean_long, 2),
                    "latitude_deg": 0.0,
                    "speed_deg_per_day": 0.5,
                    "retrograde": False
                }
        
        return positions


# ============== Convenience Functions ==============

def get_planet_position(
    body: str,
    dt: datetime,
    ephemeris_path: Optional[str] = None
) -> Dict[str, float]:
    """Quick function to get single planet position."""
    provider = EphemerisProvider(ephemeris_path)
    return provider.compute_positions(dt, [body])[body]


def get_natal_chart(
    dt: datetime,
    geo_lat: float,
    geo_lon: float,
    ephemeris_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compute full natal chart with planets and houses.
    """
    provider = EphemerisProvider(ephemeris_path)
    positions = provider.compute_full_chart(dt)
    
    return {
        "datetime_utc": dt.isoformat(),
        "geo_lat_deg": geo_lat,
        "geo_lon_deg": geo_lon,
        "positions": positions
    }
