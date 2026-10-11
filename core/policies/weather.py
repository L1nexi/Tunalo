from __future__ import annotations

from configurations.runtime_models import WeatherPolicyConfig
from core.models.context import Context
from core.models.selection import SemanticItem, WeatherDetails, WeatherEvaluation
from core.policies.base import Policy

_WEAK_OPPOSITION = 0.25


def _weather_salience(*, clear: float = 0.0, cloudy: float = 0.0, rain: float = 0.0, snow: float = 0.0) -> dict[SemanticItem, float]:
    """从晴朗、阴天和降水的正向证据，共享推导四项天气显著度。

    雨的正向依据同时承接雷暴情境，不等同于降雨量。
    晴朗与降水强反向，阴天与二者弱反向；阴天表达无降水且不明显晴朗，
    不能因为下雨时云多就额外支持阴天。降水强度取雨雪的最大值，避免
    混合雨雪重复增强公共证据；雨雪各自的正向强度仍分别保留。
    弱反向采用 0.25 的比例，降水超过 1 后仍保持对阴天的弱反向程度。
    """
    precipitation = max(rain, snow)
    weak_precipitation = _WEAK_OPPOSITION * min(precipitation, 1.0)
    weak_cloudy = _WEAK_OPPOSITION * cloudy
    return {
        SemanticItem.CLEAR: clear - precipitation - weak_cloudy,
        SemanticItem.CLOUDY: cloudy - _WEAK_OPPOSITION * clear - weak_precipitation,
        SemanticItem.RAIN: rain - clear - weak_cloudy,
        SemanticItem.SNOW: snow - clear - weak_cloudy,
    }


_CODE_SALIENCE: dict[int, dict[SemanticItem, float]] = {
    # 雷暴本身强烈支持雨景；伴随小雨或毛毛雨不降低雷暴的显著度。
    200: _weather_salience(rain=3.0),
    201: _weather_salience(rain=3.0),
    202: _weather_salience(rain=4.0),
    210: _weather_salience(rain=2.0),
    211: _weather_salience(rain=3.0),
    212: _weather_salience(rain=4.0),
    221: _weather_salience(rain=3.0),
    230: _weather_salience(rain=3.0),
    231: _weather_salience(rain=3.0),
    232: _weather_salience(rain=3.0),
    300: _weather_salience(rain=0.3),
    301: _weather_salience(rain=0.6),
    302: _weather_salience(rain=0.85),
    310: _weather_salience(rain=0.45),
    311: _weather_salience(rain=0.8),
    312: _weather_salience(rain=1.3),
    313: _weather_salience(rain=0.95),
    314: _weather_salience(rain=1.7),
    321: _weather_salience(rain=0.9),
    500: _weather_salience(rain=0.75),
    501: _weather_salience(rain=1.0),
    502: _weather_salience(rain=2.0),
    503: _weather_salience(rain=3.0),
    504: _weather_salience(rain=4.0),
    511: _weather_salience(rain=1.5),
    520: _weather_salience(rain=0.85),
    521: _weather_salience(rain=1.5),
    522: _weather_salience(rain=3.0),
    531: _weather_salience(rain=1.8),
    600: _weather_salience(snow=0.25),
    601: _weather_salience(snow=0.75),
    602: _weather_salience(snow=1.5),
    611: _weather_salience(rain=0.85, snow=0.35),
    612: _weather_salience(rain=0.75, snow=0.25),
    613: _weather_salience(rain=1.0, snow=0.5),
    615: _weather_salience(rain=0.75, snow=0.25),
    616: _weather_salience(rain=1.0, snow=0.5),
    620: _weather_salience(snow=0.35),
    621: _weather_salience(snow=0.85),
    622: _weather_salience(snow=1.5),
    701: _weather_salience(),
    711: _weather_salience(),
    721: _weather_salience(),
    731: _weather_salience(),
    741: _weather_salience(),
    751: _weather_salience(),
    761: _weather_salience(),
    762: _weather_salience(),
    771: _weather_salience(),
    781: _weather_salience(),
    # 少云仍偏晴朗，疏云保留过渡证据；浓云和全阴偏阴天。
    800: _weather_salience(clear=1.0),
    801: _weather_salience(clear=0.75),
    802: _weather_salience(clear=0.25, cloudy=0.25),
    803: _weather_salience(cloudy=0.75),
    804: _weather_salience(cloudy=1.0),
}

_MAIN_SALIENCE: dict[str, dict[SemanticItem, float]] = {
    "thunderstorm": _weather_salience(rain=3.0),
    "drizzle": _weather_salience(rain=0.6),
    "rain": _weather_salience(rain=1.0),
    "snow": _weather_salience(snow=0.75),
    "clear": _weather_salience(clear=1.0),
    "clouds": _weather_salience(cloudy=1.0),
    "mist": _weather_salience(),
    "smoke": _weather_salience(),
    "haze": _weather_salience(),
    "dust": _weather_salience(),
    "fog": _weather_salience(),
    "sand": _weather_salience(),
    "ash": _weather_salience(),
    "squall": _weather_salience(),
    "tornado": _weather_salience(),
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
        return WeatherEvaluation(
            policy_id=self.config_key,
            salience=values.copy() if values is not None else _weather_salience(),
            details=WeatherDetails(
                weather_id=weather.id if weather is not None else None,
                weather_main=weather.main if weather is not None else None,
                available=weather is not None,
                mapped=values is not None,
            ),
        )
