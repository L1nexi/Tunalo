from __future__ import annotations

from configurations.runtime_models import WeatherPolicyConfig
from core.models.context import Context
from core.models.trace import WeatherDetails, WeatherEvaluation
from core.policies.base import Policy

_CODE_SALIENCE: dict[int, tuple[float, float]] = {
    200: (0.25, 0),
    201: (0.5, 0),
    202: (1, 0),
    210: (0, 0),
    211: (0, 0),
    212: (0, 0),
    221: (0, 0),
    230: (0.1, 0),
    231: (0.2, 0),
    232: (0.35, 0),
    300: (0.1, 0),
    301: (0.2, 0),
    302: (0.35, 0),
    310: (0.15, 0),
    311: (0.3, 0),
    312: (0.65, 0),
    313: (0.45, 0),
    314: (0.85, 0),
    321: (0.4, 0),
    500: (0.25, 0),
    501: (0.5, 0),
    502: (1, 0),
    503: (1.5, 0),
    504: (2, 0),
    511: (0.75, 0),
    520: (0.35, 0),
    521: (0.75, 0),
    522: (1.5, 0),
    531: (0.9, 0),
    600: (0, 0.25),
    601: (0, 0.75),
    602: (0, 1.5),
    611: (0.35, 0.35),
    612: (0.25, 0.25),
    613: (0.5, 0.5),
    615: (0.25, 0.25),
    616: (0.5, 0.5),
    620: (0, 0.35),
    621: (0, 0.85),
    622: (0, 1.5),
    701: (0, 0),
    711: (0, 0),
    721: (0, 0),
    731: (0, 0),
    741: (0, 0),
    751: (0, 0),
    761: (0, 0),
    762: (0, 0),
    771: (0, 0),
    781: (0, 0),
    800: (0, 0),
    801: (0, 0),
    802: (0, 0),
    803: (0, 0),
    804: (0, 0),
}
_MAIN_SALIENCE: dict[str, tuple[float, float]] = {
    "thunderstorm": (0, 0),
    "drizzle": (0.2, 0),
    "rain": (0.5, 0),
    "snow": (0, 0.75),
    "clear": (0, 0),
    "clouds": (0, 0),
    "mist": (0, 0),
    "smoke": (0, 0),
    "haze": (0, 0),
    "dust": (0, 0),
    "fog": (0, 0),
    "sand": (0, 0),
    "ash": (0, 0),
    "squall": (0, 0),
    "tornado": (0, 0),
}


class WeatherPolicy(Policy):
    config_key = "weather"

    def __init__(self, config: WeatherPolicyConfig) -> None:
        super().__init__(config)

    def evaluate(self, context: Context) -> WeatherEvaluation:
        weather = context.weather
        values = None
        if weather is not None:
            values = _CODE_SALIENCE.get(weather.id)
            if values is None:
                values = _MAIN_SALIENCE.get(weather.main.casefold())
        rain, snow = values if values is not None else (0.0, 0.0)
        return WeatherEvaluation(
            policy_id=self.config_key,
            salience={"clear": 0.0, "cloudy": 0.0, "rain": rain, "snow": snow},
            details=WeatherDetails(
                weather_id=weather.id if weather is not None else None,
                weather_main=weather.main if weather is not None else None,
                available=weather is not None,
                mapped=values is not None,
            ),
        )
