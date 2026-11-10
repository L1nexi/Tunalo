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
    # Open-Meteo WMO 代码；沿用 ADR-0004 的显著度标尺。
    0: _weather_salience(clear=1.0),
    1: _weather_salience(clear=0.75),
    2: _weather_salience(clear=0.25, cloudy=0.25),
    3: _weather_salience(cloudy=1.0),
    45: _weather_salience(),
    48: _weather_salience(),
    51: _weather_salience(rain=0.3),
    53: _weather_salience(rain=0.6),
    55: _weather_salience(rain=0.85),
    56: _weather_salience(rain=0.3),
    57: _weather_salience(rain=0.85),
    61: _weather_salience(rain=0.75),
    63: _weather_salience(rain=1.0),
    65: _weather_salience(rain=2.0),
    66: _weather_salience(rain=0.75),
    67: _weather_salience(rain=2.0),
    71: _weather_salience(snow=0.25),
    73: _weather_salience(snow=0.75),
    75: _weather_salience(snow=1.5),
    77: _weather_salience(snow=0.25),
    80: _weather_salience(rain=0.85),
    81: _weather_salience(rain=1.5),
    82: _weather_salience(rain=4.0),
    85: _weather_salience(snow=0.35),
    86: _weather_salience(snow=1.5),
    # 雷暴本身强烈支持雨景；冰雹代码也由雨语义承接。
    95: _weather_salience(rain=3.0),
    96: _weather_salience(rain=3.0),
    97: _weather_salience(rain=4.0),
    99: _weather_salience(rain=4.0),
}


class WeatherPolicy(Policy):
    config_key = "weather"

    def __init__(self, config: WeatherPolicyConfig) -> None:
        super().__init__(config)

    def evaluate(self, context: Context) -> WeatherEvaluation:
        weather = context.weather
        values = None
        if weather is not None and weather.code is not None:
            values = _CODE_SALIENCE.get(weather.code)
        return WeatherEvaluation(
            policy_id=self.config_key,
            salience=values.copy() if values is not None else _weather_salience(),
            details=WeatherDetails(
                weather_code=weather.code if weather is not None else None,
                available=weather is not None and weather.code is not None,
                mapped=values is not None,
            ),
        )
