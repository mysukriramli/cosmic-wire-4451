import os
import math
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timezone as dt_timezone

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
import numpy as np
import pandas as pd
from scipy.signal import correlate, coherence
from scipy.fft import fft, fftfreq
import h3
import structlog

# ---------------------------------------------------------------------------
# Logging & Service Configuration
# ---------------------------------------------------------------------------
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)
logger = structlog.get_logger('cosmic_wire')

app = FastAPI(
    title='cosmic-wire-4451',
    description='Deterministic Celestial, Space Weather & Orbital Resonance Intelligence Engine',
    version='2.0.0',
)

# ---------------------------------------------------------------------------
# Safe Type Conversion Helpers
# ---------------------------------------------------------------------------
def _safe_num(val: Any = 0.0, default: float = 0.0, *_extra_args, **_extra_kwargs) -> float:
    try:
        if val is None:
            return default
        if isinstance(val, (int, float)):
            return float(val)
        if hasattr(val, 'item'):
            return float(val.item())
        if isinstance(val, str):
            import re
            m = re.search(r'[-+]?\d*\.?\d+', val)
            return float(m.group(0)) if m else default
        return default
    except Exception:
        return default

# ---------------------------------------------------------------------------
# Astronomical & Solar-Terrestrial Physics Engines
# ---------------------------------------------------------------------------
def calculate_solar_flux_index(
    day_of_year: int = 1,
    solar_cycle_phase: float = 0.55,
    solar_position: float = 0.0,
    *args: Any,
    **kwargs: Any,
) -> float:
    """
    Step 1: Solar Flux Engine.
    Deterministic 10.7 cm Solar Radio Flux (F10.7 in SFU).
    Models Solar Cycle 25 amplitude, 27.275-day Bartels solar rotation,
    and annual orbital eccentricity (Earth perihelion/aphelion).
    """
    cycle_modulation = math.sin(math.pi * (solar_cycle_phase % 1.0))
    rotation_modulation = math.sin(2.0 * math.pi * ((day_of_year % 27.275) / 27.275))
    orbital_distance_factor = 1.0 + 0.033 * math.cos(2.0 * math.pi * (day_of_year - 3) / 365.25)

    base_f107 = (70.0 + 115.0 * cycle_modulation + 25.0 * rotation_modulation) * orbital_distance_factor
    f107 = float(np.clip(base_f107, 65.0, 260.0))
    return round(f107, 1)

def calculate_geomagnetic_state(
    solar_flux: float = 140.0,
    solar_wind_speed: float = 450.0,
    day_of_year: int = 1,
    hour_utc: float = 12.0,
    *args: Any,
    **kwargs: Any,
) -> Dict[str, float]:
    """
    Step 2: Geomagnetic Activity Engine.
    Derives planetary Kp proxy and geomagnetic risk (0-100) using solar wind dynamic
    pressure and the Russell-McPherron semi-annual equinoctial enhancement effect.
    """
    # Russell-McPherron effect peaks near equinoxes (March 20 ~ DOY 80, Sept 22 ~ DOY 265)
    dist_to_equinox = min(abs(day_of_year - 80), abs(day_of_year - 265))
    equinox_boost = 1.0 + 0.22 * math.cos(2.0 * math.pi * dist_to_equinox / 182.6)

    wind_factor = (max(300.0, solar_wind_speed) - 300.0) / 500.0
    flux_factor = (max(65.0, solar_flux) - 65.0) / 195.0
    diurnal_harm = 0.4 * math.cos(2.0 * math.pi * (hour_utc - 18.0) / 24.0)

    kp_raw = (1.5 + 4.5 * wind_factor + 2.0 * flux_factor + diurnal_harm) * equinox_boost
    kp_proxy = float(np.clip(kp_raw, 0.0, 9.0))
    geomagnetic_risk = float(np.clip((kp_proxy / 9.0) * 100.0, 0.0, 100.0))

    return {
        'kp_proxy': round(kp_proxy, 1),
        'geomagnetic_risk': round(geomagnetic_risk, 1),
    }

def calculate_alignment_strength(
    sun_elevation: float = 0.0,
    moon_elevation: float = 0.0,
    angular_separation: float = 0.0,
    ecliptic_latitude: float = 0.0,
    *args: Any,
    **kwargs: Any,
) -> float:
    """
    Step 3: Orbital Alignment Engine.
    Computes celestial syzygy alignment strength (0-100) from true angular separation
    and moon distance to the ecliptic plane. Eliminates hardcoded 88.4.
    """
    theta_rad = math.radians(angular_separation)
    # Alignment peaks at syzygy (0 deg New Moon, 180 deg Full Moon) and drops at quadrature (90 deg)
    syzygy_component = abs(math.cos(theta_rad))

    ecliptic_penalty = max(0.0, min(1.0, abs(ecliptic_latitude) / 5.145))
    ecliptic_factor = 1.0 - 0.22 * ecliptic_penalty

    raw_alignment = (20.0 + 78.5 * (syzygy_component ** 1.5)) * ecliptic_factor
    return round(float(np.clip(raw_alignment, 10.0, 99.5)), 1)

def calculate_resonance_strength(
    solar_flux: float = 140.0,
    kp_index: float = 3.0,
    moon_phase_angle: float = 0.0,
    solar_wind_speed: float = 450.0,
    *args: Any,
    **kwargs: Any,
) -> float:
    """
    Step 4: Resonance Engine.
    Cross-correlation and frequency synchronization between solar rotation and lunar synodic periods.
    """
    t = np.linspace(0, 10, 500)
    solar_wave = np.sin(2.0 * np.pi * 0.1 * t + (solar_flux / 100.0))
    lunar_wave = np.sin(2.0 * np.pi * 0.1 * t + (kp_index / 5.0) + moon_phase_angle)
    corr = correlate(solar_wave, lunar_wave, mode='full')
    corr_metric = float(np.max(corr) / len(t) * 100.0)

    phase_diff = abs((solar_flux / 100.0) - (moon_phase_angle + kp_index / 5.0)) % (2.0 * np.pi)
    phase_coherence = (math.cos(phase_diff) + 1.0) / 2.0

    resonance = 0.65 * corr_metric + 0.35 * (phase_coherence * 100.0)
    return round(float(np.clip(resonance, 15.0, 99.0)), 1)

def calculate_darkness_score(solar_elevation: float) -> Tuple[float, str]:
    """
    Step 7: Darkness Engine.
    Computes darkness score (0-100) using astronomical twilight thresholds.
    Day (>0°), Civil Twilight (0° to -6°), Nautical Twilight (-6° to -12°),
    Astronomical Twilight (-12° to -18°), Deep Night (<-18°).
    """
    if solar_elevation >= 10.0:
        darkness = 0.0
        state = "BRIGHT_DAY"
    elif solar_elevation >= 0.0:
        darkness = 5.0 + (10.0 - solar_elevation) * 2.0
        state = "DAYLIGHT"
    elif solar_elevation >= -6.0:
        darkness = 25.0 + (-solar_elevation / 6.0) * 30.0
        state = "CIVIL_TWILIGHT"
    elif solar_elevation >= -12.0:
        darkness = 55.0 + ((-solar_elevation - 6.0) / 6.0) * 25.0
        state = "NAUTICAL_TWILIGHT"
    elif solar_elevation >= -18.0:
        darkness = 80.0 + ((-solar_elevation - 12.0) / 6.0) * 15.0
        state = "ASTRONOMICAL_TWILIGHT"
    else:
        darkness = min(100.0, 95.0 + ((-solar_elevation - 18.0) / 10.0) * 5.0)
        state = "NIGHT"

    return round(float(np.clip(darkness, 0.0, 100.0)), 1), state

def calculate_aurora_opportunity(
    lat: float = 64.1466,
    kp_index: float = 3.0,
    darkness_score: float = 85.0,
    *args: Any,
    **kwargs: Any,
) -> Dict[str, float]:
    """
    Step 5: Aurora Opportunity Engine.
    Implements Störmer/Feldstein auroral oval boundary expansion physics.
    """
    abs_lat = abs(lat)
    equatorward_boundary = 66.5 - 2.1 * kp_index
    poleward_boundary = 78.0 - 0.5 * kp_index

    if equatorward_boundary <= abs_lat <= poleward_boundary:
        spatial_prob = 1.0
    elif abs_lat < equatorward_boundary:
        dist = equatorward_boundary - abs_lat
        spatial_prob = math.exp(-0.5 * (dist / 4.0) ** 2)
    else:
        dist = abs_lat - poleward_boundary
        spatial_prob = math.exp(-0.5 * (dist / 5.0) ** 2)

    geomagnetic_intensity = min(1.0, (kp_index / 9.0) ** 0.8)
    darkness_factor = max(0.0, min(1.0, darkness_score / 100.0))
    if darkness_score < 30.0:
        darkness_factor *= (darkness_score / 30.0)

    raw_visibility = (0.50 * spatial_prob + 0.50 * geomagnetic_intensity) * darkness_factor * 100.0
    aurora_visibility = round(float(np.clip(raw_visibility, 0.0, 100.0)), 1)
    opp_score = round(float(np.clip(aurora_visibility * 0.95 + min(20.0, kp_index * 2.5), 0.0, 100.0)), 1)
    aurora_probability = round(aurora_visibility / 100.0, 2)

    return {
        'aurora_visibility': aurora_visibility,
        'opportunity_score': opp_score,
        'aurora_probability': aurora_probability,
    }

def calculate_cosmic_opportunity(
    aurora_visibility: float = 50.0,
    astronomy_quality: float = 75.0,
    darkness_score: float = 85.0,
    space_weather_risk: float = 40.0,
    alignment_strength: float = 80.0,
    *args: Any,
    **kwargs: Any,
) -> float:
    """
    Step 8: Cosmic Opportunity Model.
    Deterministic synthesis across observation conditions, sky darkness, and celestial alignment.
    """
    a_vis = max(0.0, min(100.0, aurora_visibility))
    a_qual = max(0.0, min(100.0, astronomy_quality))
    dark = max(0.0, min(100.0, darkness_score))
    align = max(0.0, min(100.0, alignment_strength))
    sw_risk = max(0.0, min(100.0, space_weather_risk))

    sw_opp = 100.0 - abs(sw_risk - 55.0) * 0.9
    raw_opp = (
        0.25 * a_qual
        + 0.25 * align
        + 0.20 * dark
        + 0.15 * a_vis
        + 0.15 * sw_opp
    )
    return round(float(np.clip(raw_opp, 10.0, 99.0)), 1)

def calculate_cosmic_state_index(
    space_weather_risk: float,
    alignment_strength: float,
    resonance_strength: float,
    darkness_score: float,
    visibility_quality: float,
    opportunity_score: float,
    *args: Any,
    **kwargs: Any,
) -> float:
    """
    Step 9: Unified Cosmic Signal (cosmic_state_index).
    Primary machine-consumable celestial telemetry index (0-100).
    """
    raw = (
        0.20 * alignment_strength
        + 0.20 * resonance_strength
        + 0.20 * opportunity_score
        + 0.15 * visibility_quality
        + 0.15 * darkness_score
        + 0.10 * space_weather_risk
    )
    return round(float(np.clip(raw, 0.0, 100.0)), 1)

# ---------------------------------------------------------------------------
# Dynamic State Management
# ---------------------------------------------------------------------------
class CosmicState:
    last_update: Optional[datetime] = None
    solar_flux: float = 135.0
    kp_index: float = 3.5
    solar_wind_speed: float = 430.0
    geomagnetic_risk: float = 38.9
    resonance_strength: float = 78.4
    alignment_strength: float = 82.5
    opportunity_score: float = 80.5
    astronomical_importance: float = 88.0
    visibility_quality: float = 82.0
    space_weather_risk: float = 45.2
    cosmic_state_index: float = 79.5

state = CosmicState()

def update_cosmic_state(dt_utc: Optional[datetime] = None) -> None:
    """Updates operational state deterministically without pseudo-random noise."""
    if dt_utc is None:
        dt_utc = datetime.now(dt_timezone.utc)

    doy = dt_utc.timetuple().tm_yday
    hour_utc = dt_utc.hour + dt_utc.minute / 60.0

    # Solar Cycle 25 phase (epoch 2020.0, cycle ~ 11.0 years)
    years_since_cycle_start = (dt_utc.year - 2020) + (doy / 365.25)
    solar_cycle_phase = (years_since_cycle_start % 11.0) / 11.0

    # Calculate solar flux and wind
    s_flux = calculate_solar_flux_index(day_of_year=doy, solar_cycle_phase=solar_cycle_phase)
    wind_base = 360.0 + 110.0 * math.sin(math.pi * solar_cycle_phase) + 60.0 * math.cos(2.0 * math.pi * ((doy % 27.275) / 27.275))
    s_wind = round(float(np.clip(wind_base, 300.0, 780.0)), 1)

    # Geomagnetic state
    geo_state = calculate_geomagnetic_state(
        solar_flux=s_flux,
        solar_wind_speed=s_wind,
        day_of_year=doy,
        hour_utc=hour_utc,
    )
    kp = geo_state['kp_proxy']
    geo_risk = geo_state['geomagnetic_risk']

    # Orbital alignment & resonance
    orbit_ref = compute_orbital_mechanics(lat=0.0, lon=0.0, dt_utc=dt_utc)
    align_score = calculate_alignment_strength(
        sun_elevation=orbit_ref['solar_elevation'],
        moon_elevation=orbit_ref['lunar_elevation'],
        angular_separation=orbit_ref['angular_separation'],
    )
    res_score = calculate_resonance_strength(
        solar_flux=s_flux,
        kp_index=kp,
        moon_phase_angle=orbit_ref['moon_phase_angle'],
        solar_wind_speed=s_wind,
    )

    sw_risk = round(float(np.clip(0.45 * geo_risk + 0.35 * (s_flux / 260.0 * 100.0) + 0.20 * (s_wind / 800.0 * 100.0), 0.0, 100.0)), 1)
    astro_imp = round(float(np.clip(70.0 + 25.0 * math.sin(math.pi * solar_cycle_phase) + 5.0 * (align_score / 100.0), 0.0, 100.0)), 1)
    vis_qual = round(float(np.clip(86.0 - 14.0 * (kp / 9.0), 20.0, 98.0)), 1)

    darkness_ref, _ = calculate_darkness_score(orbit_ref['solar_elevation'])
    opp = calculate_cosmic_opportunity(
        aurora_visibility=min(100.0, kp * 11.0),
        astronomy_quality=vis_qual,
        darkness_score=darkness_ref,
        space_weather_risk=sw_risk,
        alignment_strength=align_score,
    )

    cs_idx = calculate_cosmic_state_index(
        space_weather_risk=sw_risk,
        alignment_strength=align_score,
        resonance_strength=res_score,
        darkness_score=darkness_ref,
        visibility_quality=vis_qual,
        opportunity_score=opp,
    )

    state.solar_flux = s_flux
    state.kp_index = kp
    state.solar_wind_speed = s_wind
    state.geomagnetic_risk = geo_risk
    state.resonance_strength = res_score
    state.alignment_strength = align_score
    state.space_weather_risk = sw_risk
    state.astronomical_importance = astro_imp
    state.visibility_quality = vis_qual
    state.opportunity_score = opp
    state.cosmic_state_index = cs_idx
    state.last_update = dt_utc

update_cosmic_state()

async def background_pipeline():
    """Autonomous periodic telemetry refresh pipeline without random noise."""
    while True:
        try:
            update_cosmic_state()
            logger.info(
                'Pipeline update executed',
                event_name='autonomous_update',
                kp=state.kp_index,
                risk=state.geomagnetic_risk,
                alignment=state.alignment_strength,
            )
        except Exception as e:
            logger.error('Error in background pipeline', event_name='pipeline_error', error=str(e))
        await asyncio.sleep(900)

@app.on_event('startup')
async def startup_event():
    update_cosmic_state()
    asyncio.create_task(background_pipeline())
    logger.info('CosmicWire service started', event_name='startup')

# ---------------------------------------------------------------------------
# Preserved Analytical Functions
# ---------------------------------------------------------------------------
def compute_orbital_mechanics(
    lat: float = 0.0,
    lon: float = 0.0,
    dt_utc: Optional[datetime] = None,
    *_extra_args,
    **_extra_kwargs,
) -> Dict[str, float]:
    """Calculates orbital phase angles and celestial positions using trigonometric ephemeris math."""
    if dt_utc is None:
        dt_utc = datetime.now(dt_timezone.utc)
    now_ts = dt_utc.timestamp()
    synodic_period = 29.530588853 * 86400.0
    moon_phase_angle = 2.0 * math.pi * ((now_ts / synodic_period) % 1.0)

    day_of_year = dt_utc.timetuple().tm_yday
    hour_utc = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    gamma = 2.0 * math.pi / 365.25 * (day_of_year - 1 + (hour_utc - 12.0) / 24.0)

    eqtime = 229.18 * (
        0.000075 + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2 * gamma) - 0.040849 * math.sin(2 * gamma)
    )
    decl = (
        0.006918 - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma)
        - 0.006758 * math.cos(2 * gamma) + 0.000907 * math.sin(2 * gamma)
        - 0.002697 * math.cos(3 * gamma) + 0.00148 * math.sin(3 * gamma)
    )

    time_offset = eqtime + 4.0 * lon
    tst = (hour_utc * 60.0 + time_offset) % 1440.0
    ha_rad = math.radians((tst / 4.0) - 180.0)
    lat_rad = math.radians(lat)

    sin_solar_elev = math.sin(lat_rad) * math.sin(decl) + math.cos(lat_rad) * math.cos(decl) * math.cos(ha_rad)
    solar_elevation = math.degrees(math.asin(max(-1.0, min(1.0, sin_solar_elev))))

    # Lunar declination oscillation & hour angle
    lunar_decl = math.radians(23.44) * math.sin(2.0 * math.pi * ((now_ts / (27.32166 * 86400.0)) % 1.0))
    lunar_ha = (ha_rad - moon_phase_angle) % (2.0 * math.pi)
    sin_lunar_elev = math.sin(lat_rad) * math.sin(lunar_decl) + math.cos(lat_rad) * math.cos(lunar_decl) * math.cos(lunar_ha)
    lunar_elevation = math.degrees(math.asin(max(-1.0, min(1.0, sin_lunar_elev))))

    # Spherical law of cosines for true angular separation
    cos_sep = math.sin(decl) * math.sin(lunar_decl) + math.cos(decl) * math.cos(lunar_decl) * math.cos(ha_rad - lunar_ha)
    angular_separation = math.degrees(math.acos(max(-1.0, min(1.0, cos_sep))))

    return {
        'moon_phase_angle': float(moon_phase_angle),
        'solar_elevation': float(solar_elevation),
        'lunar_elevation': float(lunar_elevation),
        'angular_separation': float(angular_separation),
    }

def compute_tidal_harmonic_analysis(*_extra_args, **_extra_kwargs) -> Dict[str, float]:
    """Performs harmonic frequency analysis on constituent tidal waves (M2, S2, N2)."""
    t = np.linspace(0, 48, 200)
    m2 = 1.0 * np.sin(2.0 * np.pi * t / 12.42)
    s2 = 0.465 * np.sin(2.0 * np.pi * t / 12.0)
    n2 = 0.193 * np.sin(2.0 * np.pi * t / 12.65)
    tide_signal = m2 + s2 + n2
    amplification = float(np.max(tide_signal) - np.min(tide_signal)) * 30.0
    coastal_sensitivity = float(np.mean(np.abs(np.gradient(tide_signal)))) * 50.0
    return {
        'tidal_amplification': float(np.clip(amplification, 0, 100)),
        'coastal_sensitivity': float(np.clip(coastal_sensitivity, 0, 100)),
    }

def compute_cross_correlation_resonance(*_extra_args, **_extra_kwargs) -> float:
    """Computes cross-correlation and frequency synchronization across multi-cycle wave signals."""
    t = np.linspace(0, 10, 500)
    solar_wave = np.sin(2.0 * np.pi * 0.1 * t + state.solar_flux / 100.0)
    lunar_wave = np.sin(2.0 * np.pi * 0.1 * t + state.kp_index / 5.0)
    corr = correlate(solar_wave, lunar_wave, mode='full')
    resonance_metric = float(np.max(corr) / len(t) * 100.0)
    return float(np.clip(resonance_metric, 0, 100))

# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
@app.get('/')
def root() -> Dict[str, Any]:
    return {
        'status': 'healthy',
        'service': 'cosmic-wire-4451',
        'name': 'cosmic-wire-4451',
        'version': '2.0.0',
    }

@app.get('/health')
def health() -> Dict[str, Any]:
    return {'status': 'healthy'}

@app.get('/tools')
def list_tools() -> Dict[str, Any]:
    return {
        'tools': [
            'get_space_weather_consequences',
            'get_aurora_opportunity',
            'get_resonance_state',
            'get_eclipse_consequences',
            'get_alignment_strength',
            'get_cosmicwire_signal',
            'h3_broadcast_tensor',
        ]
    }

@app.get('/get_space_weather_consequences')
def get_space_weather_consequences() -> Dict[str, float]:
    """Wire 2: Solar Flare & Space Weather Consequence Wire."""
    update_cosmic_state()
    gps_risk = float(np.clip(state.geomagnetic_risk * 0.85, 0.0, 100.0))
    radio_risk = float(np.clip((state.solar_flux / 260.0) * 100.0, 0.0, 100.0))
    satellite_risk = float(np.clip((state.solar_wind_speed / 800.0) * 85.0 + (state.kp_index / 9.0) * 15.0, 0.0, 100.0))
    return {
        'gps_risk': round(gps_risk, 1),
        'radio_risk': round(radio_risk, 1),
        'satellite_risk': round(satellite_risk, 1),
    }

@app.get('/get_aurora_opportunity')
def get_aurora_opportunity(lat: float = 64.1466, lon: float = -21.9426) -> Dict[str, float]:
    """Wire 3: Aurora Opportunity Wire."""
    if lat < -90 or lat > 90 or lon < -180 or lon > 180:
        raise HTTPException(status_code=400, detail='Invalid coordinates')
    update_cosmic_state()

    orbit = compute_orbital_mechanics(lat, lon)
    darkness, _ = calculate_darkness_score(orbit['solar_elevation'])
    aurora_res = calculate_aurora_opportunity(
        lat=lat,
        kp_index=state.kp_index,
        darkness_score=darkness,
    )
    return {
        'aurora_visibility': round(aurora_res['aurora_visibility'], 1),
        'opportunity_score': round(aurora_res['opportunity_score'], 1),
    }

@app.get('/get_resonance_state')
def get_resonance_state() -> Dict[str, float]:
    """Wire 9: Resonance Wire."""
    calculated_resonance = compute_cross_correlation_resonance()
    final_res = (state.resonance_strength + calculated_resonance) / 2.0
    return {'resonance_strength': round(float(final_res), 1)}

@app.get('/get_eclipse_consequences')
def get_eclipse_consequences(lat: float = 2.27, lon: float = 102.55) -> Dict[str, Any]:
    """
    Wire 1: Eclipse Consequence Wire.
    Step 6: Derives visibility, attention spike, and population exposure from orbital geometry.
    """
    if lat < -90 or lat > 90 or lon < -180 or lon > 180:
        raise HTTPException(status_code=400, detail='Invalid coordinates')

    orbit = compute_orbital_mechanics(lat, lon)
    ang_sep = orbit.get('angular_separation', 180.0)
    sol_elev = orbit.get('solar_elevation', 0.0)
    lun_elev = orbit.get('lunar_elevation', 0.0)

    theta_rad = math.radians(ang_sep)
    syzygy_quality = abs(math.cos(theta_rad))

    elev_factor = 1.0 if (sol_elev > 0.0 or lun_elev > 0.0) else max(0.2, 1.0 - abs(sol_elev) / 90.0)
    visibility_score = float(np.clip(70.0 + 30.0 * (syzygy_quality ** 1.8) * elev_factor, 0.0, 100.0))
    attention_spike = float(np.clip(visibility_score * 0.92 + 8.0 * syzygy_quality, 0.0, 100.0))

    base_pop = 34000000
    population_exposed = int(base_pop * (visibility_score / 100.0))

    return {
        'visibility_score': round(visibility_score, 1),
        'attention_spike': round(attention_spike, 1),
        'population_exposed': population_exposed,
        'angular_separation': round(ang_sep, 2),
        'duration_minutes': round(max(0.0, (1.0 - (ang_sep % 90.0) / 90.0) * 180.0), 1),
        'darkness_effect': round(syzygy_quality * 100.0, 1),
    }

@app.get('/get_alignment_strength')
def get_alignment_strength() -> Dict[str, float]:
    """Wire 10: Alignment Wire."""
    update_cosmic_state()
    return {'alignment_strength': round(float(state.alignment_strength), 1)}

@app.get('/get_cosmicwire_signal')
def get_cosmicwire_signal(lat: float = 2.27, lon: float = 102.55) -> Dict[str, Any]:
    """Wire 12: CosmicWire Unified Signal."""
    if lat < -90 or lat > 90 or lon < -180 or lon > 180:
        raise HTTPException(status_code=400, detail='Invalid coordinates')
    update_cosmic_state()
    return {
        'astronomical_importance': round(float(state.astronomical_importance), 1),
        'resonance_strength': round(float(state.resonance_strength), 1),
        'alignment_strength': round(float(state.alignment_strength), 1),
        'visibility_quality': round(float(state.visibility_quality), 1),
        'space_weather_risk': round(float(state.space_weather_risk), 1),
        'opportunity_score': round(float(state.opportunity_score), 1),
        'cosmic_state_index': round(float(state.cosmic_state_index), 1),
    }

@app.get('/h3_broadcast_tensor')
def h3_broadcast_tensor(
    h3_cell: str = '8a2a1072b59ffff',
    lat: float = 2.0442,
    lon: float = 102.5689,
) -> Dict[str, Any]:
    """H3 Cosmic Tensor endpoint resolving location-specific celestial features without randomness."""
    if lat < -90 or lat > 90 or lon < -180 or lon > 180:
        raise HTTPException(status_code=400, detail='Invalid coordinates')
    update_cosmic_state()

    target_h3 = h3_cell
    if not target_h3 or len(target_h3) < 5:
        try:
            if hasattr(h3, 'latlng_to_cell'):
                target_h3 = str(h3.latlng_to_cell(lat, lon, 8))
            else:
                target_h3 = str(h3.geo_to_h3(lat, lon, 8))
        except Exception:
            target_h3 = '8a2a1072b59ffff'

    orbit = compute_orbital_mechanics(lat, lon)
    darkness_score, _ = calculate_darkness_score(orbit['solar_elevation'])

    vis_quality = float(np.clip(state.visibility_quality * 0.95 + (darkness_score / 100.0) * 5.0, 0.0, 100.0))
    aurora_res = calculate_aurora_opportunity(lat=lat, kp_index=state.kp_index, darkness_score=darkness_score)
    aurora_prob = aurora_res['aurora_probability']
    eclipse_vis = float(np.clip(abs(math.cos(math.radians(orbit['angular_separation']))), 0.0, 1.0))

    return {
        'h3': target_h3,
        'visibility_quality': round(vis_quality, 1),
        'aurora_probability': round(aurora_prob, 2),
        'eclipse_visibility': round(eclipse_vis, 2),
        'darkness_score': round(darkness_score, 1),
    }

@app.get('/wires/tidal')
def get_tidal_consequences() -> Dict[str, float]:
    """Wire 4: Tidal Consequence Wire."""
    return compute_tidal_harmonic_analysis()

@app.get('/wires/darkness')
def get_darkness_opportunity(lat: float = 2.27, lon: float = 102.55) -> Dict[str, float]:
    """Wire 5: Darkness Opportunity Wire."""
    if lat < -90 or lat > 90 or lon < -180 or lon > 180:
        raise HTTPException(status_code=400, detail='Invalid coordinates')

    orbit = compute_orbital_mechanics(lat, lon)
    darkness_score, _ = calculate_darkness_score(orbit.get('solar_elevation', 0.0))

    observation_window = float(np.clip(90.0 - abs(orbit.get('solar_elevation', 0.0)), 0.0, 100.0))
    astronomy_quality = float(np.clip(observation_window * 0.70 + darkness_score * 0.30, 0.0, 100.0))

    return {
        'observation_window': round(observation_window, 1),
        'astronomy_quality': round(astronomy_quality, 1),
    }

@app.get('/wires/opportunity')
def get_celestial_opportunity() -> Dict[str, bool]:
    """Wire 11: Celestial Opportunity Wire."""
    update_cosmic_state()
    return {
        'eclipse': state.astronomical_importance > 85.0 or state.alignment_strength > 90.0,
        'aurora': state.kp_index >= 4.0,
        'meteor': state.resonance_strength > 75.0,
        'dark_sky': state.visibility_quality > 75.0,
    }

# ---------------------------------------------------------------------------
# CLI & Standalone Server Execution
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=False)
