from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from configurations.runtime_models import MatchingConfig
from core.math_utils import softmax
from core.models.context import Context
from core.models.scene import SceneId
from core.models.semantics import SEMANTIC_ITEMS, VARIABLE_ITEMS, ContextVariable, Salience, SemanticItem
from core.models.trace import Selection
from core.policies.base import Policy


def salience_to_scene_scores(salience: Mapping[SemanticItem, float], associations: Mapping[SceneId, frozenset[SemanticItem]]) -> dict[SceneId, float]:
    return {scene_id: math.fsum(salience[item] for item in sorted(items)) / math.sqrt(len(items)) for scene_id, items in associations.items()}


def calculate_distribution(
    salience: Salience,
    associations: Mapping[SceneId, frozenset[SemanticItem]],
    config: MatchingConfig,
) -> Selection:
    """Calculate the full distribution from validated semantic and matching inputs.

    This is independent of the Selector class so that it is pure functional and testable in isolation.
    """
    s = salience.root
    positive = {item for item, value in s.items() if value >= config.positive_boundary}
    negative = {item for item, value in s.items() if value <= -config.negative_boundary}
    excluded = {scene_id: items & negative for scene_id, items in associations.items() if items & negative}
    safe = {scene_id: items for scene_id, items in associations.items() if scene_id not in excluded}
    if not safe:
        return Selection(probabilities={}, salience=s, reason="no_safe_scenes", excluded_scenes=excluded)

    candidates = {
        variable: {scene_id: items for scene_id, items in safe.items() if items & positive & set(variable_items)}
        for variable, variable_items in VARIABLE_ITEMS.items()
    }
    scores = salience_to_scene_scores(s, safe)

    tiers = [*config.preference_tiers, list(ContextVariable)]
    for index, tier in enumerate(tiers):
        significant = [variable for variable in tier if positive.intersection(VARIABLE_ITEMS[variable])]
        effective = [variable for variable in significant if candidates[variable]]
        if not effective:
            continue
        strengths = {variable: max(max(s[item], 0.0) for item in VARIABLE_ITEMS[variable]) for variable in effective}
        # Softmax on effective sources equals dropping empty sources and
        # proportionally renormalizing the tier's original budgets.
        budgets = softmax(strengths, config.variable_temperature)
        probabilities = {scene_id: 0.0 for scene_id in associations}
        for variable in effective:
            conditional = softmax({scene_id: scores[scene_id] for scene_id in candidates[variable]}, config.scene_temperature)
            for scene_id, probability in conditional.items():
                probabilities[scene_id] += budgets[variable] * probability
        return Selection(
            probabilities=probabilities,
            salience=s,
            reason="preference" if index < len(config.preference_tiers) else "neutral",
            selected_tier=index if index < len(config.preference_tiers) else None,
            sources=effective,
            excluded_scenes=excluded,
        )

    effort = softmax(scores, config.scene_temperature)
    return Selection(
        probabilities={scene_id: effort.get(scene_id, 0.0) for scene_id in associations}, salience=s, reason="best_effort", excluded_scenes=excluded
    )


class Selector:
    def __init__(self, associations: Mapping[SceneId, frozenset[SemanticItem]], policies: list[Policy], config: MatchingConfig) -> None:
        self.associations = dict(associations)
        self.policies = policies
        self.config = config

    def select(self, context: Context) -> Selection:
        evaluations = [policy.evaluate(context) for policy in self.policies]
        values = {item: 0.0 for item in SEMANTIC_ITEMS}
        for evaluation in evaluations:
            values.update(evaluation.salience)
        # Policy outputs are trusted and already cover the fixed vocabulary.
        # External tuning inputs use Salience validation at their own boundary.
        result = calculate_distribution(Salience.model_construct(root=values), self.associations, self.config)
        result.policy_evaluations = evaluations
        return result

    def export_state(self) -> dict[str, dict[str, Any]]:
        return {policy.config_key: policy.export_state() for policy in self.policies}

    def import_state(self, state: dict[str, dict[str, Any]]) -> None:
        for policy in self.policies:
            policy.import_state(state[policy.config_key])
