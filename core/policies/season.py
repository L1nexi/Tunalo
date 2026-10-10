from __future__ import annotations

from configurations.runtime_models import SeasonPolicyConfig
from core.math_utils import interpolate_periodic
from core.models.context import Context
from core.models.semantics import VARIABLE_ITEMS, ContextVariable
from core.models.trace import SeasonDetails, SeasonEvaluation
from core.policies.base import Policy


class SeasonPolicy(Policy):
    config_key = "season"

    def __init__(self, config: SeasonPolicyConfig) -> None:
        super().__init__(config)
        self._peaks = {"spring": config.spring_peak, "summer": config.summer_peak, "autumn": config.autumn_peak, "winter": config.winter_peak}
        self._half_width = config.plateau_half_width
        self._curve_q = config.curve_q

    def evaluate(self, context: Context) -> SeasonEvaluation:
        items = VARIABLE_ITEMS[ContextVariable.SEASON]
        values = (1.0, 0.0, -1.0, 0.0)
        salience = {
            item: interpolate_periodic(
                context.time.tm_yday,
                [(self._peaks[anchor], values[(index - own_index) % 4]) for index, anchor in enumerate(items)],
                365,
                self._half_width,
                self._curve_q,
            )
            for own_index, item in enumerate(items)
        }
        return SeasonEvaluation(
            policy_id=self.config_key, salience=salience, details=SeasonDetails(day_of_year=context.time.tm_yday, peaks=self._peaks.copy())
        )
