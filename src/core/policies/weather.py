from __future__ import annotations

from configurations.runtime_models import WeatherPolicyConfig
from core.models.context import Context
from core.models.selection import SemanticItem, WeatherDetails, WeatherEvaluation
from core.models.weather import WeatherType
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


_TYPE_SALIENCE: dict[WeatherType, dict[SemanticItem, float]] = {
    # 天气类型由集成侧从来源代码归类；这里沿用 ADR-0004 的显著度标尺。
    WeatherType.CLEAR: _weather_salience(clear=1.0),
    WeatherType.MAINLY_CLEAR: _weather_salience(clear=0.75),
    WeatherType.PARTLY_CLOUDY: _weather_salience(clear=0.25, cloudy=0.25),
    WeatherType.OVERCAST: _weather_salience(cloudy=1.0),
    WeatherType.FOG: _weather_salience(),
    WeatherType.LIGHT_DRIZZLE: _weather_salience(rain=0.3),
    WeatherType.DRIZZLE: _weather_salience(rain=0.6),
    WeatherType.DENSE_DRIZZLE: _weather_salience(rain=0.85),
    WeatherType.LIGHT_FREEZING_DRIZZLE: _weather_salience(rain=0.3),
    WeatherType.DENSE_FREEZING_DRIZZLE: _weather_salience(rain=0.85),
    WeatherType.LIGHT_RAIN: _weather_salience(rain=0.75),
    WeatherType.RAIN: _weather_salience(rain=1.0),
    WeatherType.HEAVY_RAIN: _weather_salience(rain=2.0),
    WeatherType.LIGHT_FREEZING_RAIN: _weather_salience(rain=0.75),
    WeatherType.HEAVY_FREEZING_RAIN: _weather_salience(rain=2.0),
    WeatherType.LIGHT_SNOW: _weather_salience(snow=0.25),
    WeatherType.SNOW: _weather_salience(snow=0.75),
    WeatherType.HEAVY_SNOW: _weather_salience(snow=1.5),
    WeatherType.SNOW_GRAINS: _weather_salience(snow=0.25),
    WeatherType.LIGHT_RAIN_SHOWER: _weather_salience(rain=0.85),
    WeatherType.RAIN_SHOWER: _weather_salience(rain=1.5),
    WeatherType.VIOLENT_RAIN_SHOWER: _weather_salience(rain=4.0),
    WeatherType.LIGHT_SNOW_SHOWER: _weather_salience(snow=0.35),
    WeatherType.HEAVY_SNOW_SHOWER: _weather_salience(snow=1.5),
    # 雷暴本身强烈支持雨景；冰雹类型也由雨语义承接。
    WeatherType.THUNDERSTORM: _weather_salience(rain=3.0),
    WeatherType.THUNDERSTORM_WITH_HAIL: _weather_salience(rain=3.0),
    WeatherType.STRONG_THUNDERSTORM: _weather_salience(rain=4.0),
    WeatherType.STRONG_THUNDERSTORM_WITH_HAIL: _weather_salience(rain=4.0),
}


class WeatherPolicy(Policy):
    config_key = "weather"

    def __init__(self, config: WeatherPolicyConfig) -> None:
        super().__init__(config)

    def evaluate(self, context: Context) -> WeatherEvaluation:
        weather = context.weather
        weather_type = weather.type if weather is not None else None
        values = _TYPE_SALIENCE.get(weather_type) if weather_type is not None else None
        return WeatherEvaluation(
            policy_id=self.config_key,
            salience=values.copy() if values is not None else _weather_salience(),
            details=WeatherDetails(
                weather_type=weather_type,
                available=weather_type is not None,
                mapped=values is not None,
            ),
        )
