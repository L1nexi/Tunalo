from __future__ import annotations

from configurations.runtime_models import SeasonPolicyConfig
from core.math_utils import periodic_salience
from core.models.context import Context
from core.models.selection import VARIABLE_ITEMS, ContextVariable, SeasonDetails, SeasonEvaluation
from core.policies.base import Policy


class SeasonPolicy(Policy):
    config_key = "season"

    def __init__(self, config: SeasonPolicyConfig) -> None:
        super().__init__(config)
        self._peaks = {"spring": config.spring_peak, "summer": config.summer_peak, "autumn": config.autumn_peak, "winter": config.winter_peak}
        self._half_width = config.plateau_half_width
        self._activation_alpha = config.activation_alpha

    def evaluate(self, context: Context) -> SeasonEvaluation:
        items = VARIABLE_ITEMS[ContextVariable.SEASON]
        salience = {
            item: periodic_salience(
                context.time.tm_yday,
                self._peaks[item],
                365,
                plateau_half_width=self._half_width,
                alpha=self._activation_alpha,
            )
            for item in items
        }
        return SeasonEvaluation(
            policy_id=self.config_key, salience=salience, details=SeasonDetails(day_of_year=context.time.tm_yday, peaks=self._peaks.copy())
        )
