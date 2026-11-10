from __future__ import annotations

from dataclasses import dataclass

import requests

from core.models.weather import WeatherType
from integrations.request_failure import request_failure_reason

CURRENT_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
VALIDATION_TIMEOUT_SECONDS = 8.0

_WMO_WEATHER_TYPES: dict[int, WeatherType] = {
    0: WeatherType.CLEAR,
    1: WeatherType.MAINLY_CLEAR,
    2: WeatherType.PARTLY_CLOUDY,
    3: WeatherType.OVERCAST,
    45: WeatherType.FOG,
    48: WeatherType.FOG,
    51: WeatherType.LIGHT_DRIZZLE,
    53: WeatherType.DRIZZLE,
    55: WeatherType.DENSE_DRIZZLE,
    56: WeatherType.LIGHT_FREEZING_DRIZZLE,
    57: WeatherType.DENSE_FREEZING_DRIZZLE,
    61: WeatherType.LIGHT_RAIN,
    63: WeatherType.RAIN,
    65: WeatherType.HEAVY_RAIN,
    66: WeatherType.LIGHT_FREEZING_RAIN,
    67: WeatherType.HEAVY_FREEZING_RAIN,
    71: WeatherType.LIGHT_SNOW,
    73: WeatherType.SNOW,
    75: WeatherType.HEAVY_SNOW,
    77: WeatherType.SNOW_GRAINS,
    80: WeatherType.LIGHT_RAIN_SHOWER,
    81: WeatherType.RAIN_SHOWER,
    82: WeatherType.VIOLENT_RAIN_SHOWER,
    85: WeatherType.LIGHT_SNOW_SHOWER,
    86: WeatherType.HEAVY_SNOW_SHOWER,
    95: WeatherType.THUNDERSTORM,
    96: WeatherType.THUNDERSTORM_WITH_HAIL,
    97: WeatherType.STRONG_THUNDERSTORM,
    99: WeatherType.STRONG_THUNDERSTORM_WITH_HAIL,
}


def classify_weather_code(code: int) -> WeatherType:
    """Translate an Open-Meteo WMO weather code into the shared weather type."""
    return _WMO_WEATHER_TYPES.get(code, WeatherType.UNKNOWN)


class WeatherRejected(RuntimeError):
    """Open-Meteo rejected submitted weather settings."""

    code: str
    path: tuple[str, ...]


class InvalidLocation(WeatherRejected):
    code = "weather_location_invalid"
    path = ("weather", "location")


class QuotaExceeded(WeatherRejected):
    code = "weather_api_quota_exceeded"
    path = ("weather",)


class WeatherUnavailable(RuntimeError):
    """Open-Meteo could not complete a weather request."""

    def __init__(self, message: str, *, reason: str, http_status: int | None = None) -> None:
        super().__init__(message)
        self.reason = reason
        self.http_status = http_status


@dataclass(frozen=True)
class WeatherObservation:
    code: int
    type: WeatherType


def fetch_weather(
    latitude: float,
    longitude: float,
    *,
    timeout: float = VALIDATION_TIMEOUT_SECONDS,
) -> WeatherObservation:
    """Fetch and parse the current weather.

    Raises:
        WeatherRejected: If the service rejects the settings or quota.
        WeatherUnavailable: If the request fails or its response is unusable.
    """
    try:
        response = requests.get(
            CURRENT_WEATHER_URL,
            params={"latitude": latitude, "longitude": longitude, "current": "weather_code"},
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise WeatherUnavailable("weather service is unavailable", reason=request_failure_reason(exc)) from exc

    if response.status_code == 200:
        try:
            payload = response.json()
        except ValueError as exc:
            raise WeatherUnavailable("weather service returned invalid JSON", reason="invalid_json") from exc
        if not isinstance(payload, dict):
            raise WeatherUnavailable("weather service returned invalid data", reason="invalid_response")
        current = payload.get("current")
        if not isinstance(current, dict):
            raise WeatherUnavailable("weather service returned incomplete data", reason="invalid_response")
        code = current.get("weather_code")
        if isinstance(code, bool) or not isinstance(code, int):
            raise WeatherUnavailable("weather service returned incomplete data", reason="invalid_response")
        return WeatherObservation(code=code, type=classify_weather_code(code))
    if response.status_code == 400:
        raise InvalidLocation("weather location is invalid")
    if response.status_code == 429:
        raise QuotaExceeded("weather API quota exceeded")
    raise WeatherUnavailable(
        f"weather service returned HTTP {response.status_code}",
        reason="http_status",
        http_status=response.status_code,
    )


def validate_weather_connection(latitude: float, longitude: float) -> None:
    """Verify weather settings with a parsed observation.

    Raises:
        WeatherRejected: If the service rejects the settings or quota.
        WeatherUnavailable: If the request fails or its response is unusable.
    """
    fetch_weather(latitude, longitude)
