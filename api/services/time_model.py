# BaZodiac Time Model Service
# Time scale conversions and TLST computation

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from ..utils.core import gregorian_to_jd, wrap360

class TimeModelService:
    """Compute time scales: UTC → UT1 → TT → LMST → TLST"""
    
    # Approximate equation of time (minutes) by day of year
    # Simplified NOAA-based approximation
    EOT_APPROX_PARAMS = {
        "A": -2.8,
        "B": -12.3,
        "C": -4.4,
        "D": 0.0
    }
    
    @staticmethod
    def local_to_utc(
        local_dt: datetime,
        tz_id: Optional[str],
        tz_offset_sec: Optional[int],
        dst_policy: str = "error"
    ) -> datetime:
        """
        Convert local datetime to UTC.
        
        Args:
            local_dt: Local datetime
            tz_id: Timezone ID (e.g., "Europe/Berlin")
            tz_offset_sec: Manual offset in seconds
            dst_policy: "error" | "earlier" | "later"
        
        Returns:
            UTC datetime
        """
        if tz_id:
            # Would use pytz or zoneinfo in production
            # For now, require manual offset or raise
            if tz_offset_sec is None:
                raise ValueError(f"tz_id {tz_id} requires tz_offset_sec for now")
            offset = timedelta(seconds=tz_offset_sec)
        elif tz_offset_sec is not None:
            offset = timedelta(seconds=tz_offset_sec)
        else:
            raise ValueError("Either tz_id or tz_offset_sec required")
        
        # Apply offset (naive datetime assumption)
        utc_dt = local_dt.replace(tzinfo=None) - offset
        return utc_dt
    
    @staticmethod
    def utc_to_tt(utc_dt: datetime, leap_seconds: int = 37) -> datetime:
        """
        Convert UTC to TT (Terrestrial Time).
        
        TT = UTC + TAI-UTC + 32.184s
        Currently TAI-UTC = 37 seconds (2026)
        """
        tai_offset = timedelta(seconds=leap_seconds + 32.184)
        tt_dt = utc_dt + tai_offset
        return tt_dt
    
    @staticmethod
    def compute_lmst(utc_dt: datetime, geo_lon_deg: float) -> float:
        """
        Compute Local Mean Solar Time in hours.
        
        LMST = (UT1_hours + lon/15) mod 24
        """
        ut1_hours = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
        lmst = (ut1_hours + geo_lon_deg / 15.0) % 24.0
        return lmst
    
    @staticmethod
    def approx_eot(day_of_year: int) -> float:
        """
        Approximate Equation of Time in minutes.
        
        Simplified version based on NOAA formulas.
        """
        B = 360.0 / 365.0 * (day_of_year - 81)
        B_rad = B * 3.14159 / 180.0
        
        # Simplified EOT approximation
        eot = (
            9.87 * math.sin(2 * B_rad) -
            7.53 * math.cos(B_rad) -
            1.5 * math.sin(B_rad)
        )
        return eot
    
    @staticmethod
    def compute_tlst(
        utc_dt: datetime,
        geo_lon_deg: float,
        eot_min: Optional[float] = None,
        leap_seconds: int = 37
    ) -> Dict[str, Any]:
        """
        Complete TLST computation.
        
        Returns dict with all time scales and quality flags.
        """
        # Julian Date
        jd_utc = gregorian_to_jd(
            utc_dt.year, utc_dt.month, utc_dt.day,
            utc_dt.hour + utc_dt.minute / 60.0
        )
        
        # TT
        tt_dt = TimeModelService.utc_to_tt(utc_dt, leap_seconds)
        jd_tt = gregorian_to_jd(
            tt_dt.year, tt_dt.month, tt_dt.day,
            tt_dt.hour + tt_dt.minute / 60.0
        )
        
        # LMST
        lmst_hours = TimeModelService.compute_lmst(utc_dt, geo_lon_deg)
        
        # EoT (approximate or override)
        if eot_min is None:
            day_of_year = utc_dt.timetuple().tm_yday
            eot_min = TimeModelService.approx_eot(day_of_year)
        
        # TLST = LMST + EoT
        tlst_hours = (lmst_hours + eot_min / 60.0) % 24.0
        
        # Quality assessment
        quality = {
            "utc": "ok",
            "tt": "ok" if leap_seconds > 0 else "missing",
            "lmst": "ok",
            "tlst": "ok" if eot_min is not None else "degraded"
        }
        
        return {
            "utc": utc_dt.isoformat() + "Z",
            "tt": tt_dt.isoformat() + "Z",
            "jd_utc": round(jd_utc, 5),
            "jd_tt": round(jd_tt, 5),
            "lmst_hours": round(lmst_hours, 6),
            "tlst_hours": round(tlst_hours, 6),
            "eot_min": round(eot_min, 3),
            "quality": quality,
            "day_of_year": day_of_year
        }


import math  # For EOT calculation
