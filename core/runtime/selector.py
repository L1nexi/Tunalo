from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from configurations.runtime_models import MatchingConfig
from core.math_utils import softmax
from core.models.association import Association
from core.models.context import Context
from core.models.scene import SceneId
from core.models.selection import SEMANTIC_ITEMS, VARIABLE_SEMANTIC_ITEMS, Salience, Selection, SemanticItem
from core.policies.base import Policy


def salience_to_scene_scores[SceneKey: str](
    salience: Mapping[SemanticItem, float], associations: Mapping[SceneKey, Association]
) -> dict[SceneKey, float]:
    scores = {}
    for scene_id, association in associations.items():
        values = [max(salience[item] for item in items) for items in association.values()]
        scores[scene_id] = math.fsum(values) / math.sqrt(len(association))
    return scores


def calculate_distribution[SceneKey: str](
    salience: Salience,
    associations: Mapping[SceneKey, Association],
    config: MatchingConfig,
) -> Selection[SceneKey]:
    """Calculate the full distribution from validated semantic and matching inputs.

    This is independent of the Selector class so that it is pure functional and testable in isolation.
    """
    s = salience.root
    # positive 为满足正向阈值的语义项集合
    positive = {item for item, value in s.items() if value >= config.positive_boundary}
    # negative 为满足负向阈值的语义项集合
    negative = {item for item, value in s.items() if value <= -config.negative_boundary}
    # excluded 为被负向阈值排除的场景字典
    excluded = {}
    for scene_id, association in associations.items():
        excluded_items = frozenset(item for alternatives in association.values() if alternatives <= negative for item in alternatives)
        if excluded_items:
            excluded[scene_id] = excluded_items
    # safe 为排除了 excluded 的场景字典
    safe = {scene_id: association for scene_id, association in associations.items() if scene_id not in excluded}
    if not safe:
        return Selection(probabilities={}, salience=s, reason="no_safe_scenes", excluded_scenes=excluded)

    # candidates 为逐变量的可行场景字典，满足正向阈值与反向阈值
    candidates = {
        variable: {scene_id: association for scene_id, association in safe.items() if variable in association and association[variable] & positive}
        for variable in VARIABLE_SEMANTIC_ITEMS
    }

    selected_tier = None
    for index, tier in enumerate(config.preference_tiers):
        effective = [variable for variable in tier if candidates[variable]]
        if effective:
            selected_tier = index
            break
    else:
        # 显示偏好穷尽仍无候选，放宽正向阈值要求进行尽力选择
        candidates = {
            variable: {scene_id: association for scene_id, association in safe.items() if variable in association}
            for variable in VARIABLE_SEMANTIC_ITEMS
        }
        effective = [variable for variable in VARIABLE_SEMANTIC_ITEMS if candidates[variable]]

    strengths = {variable: max(max(s[item], 0.0) for item in VARIABLE_SEMANTIC_ITEMS[variable]) for variable in effective}
    # Softmax on effective sources proportionally renormalizes away empty sources.
    budgets = softmax(strengths, config.variable_temperature)
    scores = salience_to_scene_scores(s, safe)
    probabilities = {scene_id: 0.0 for scene_id in associations}
    for variable in effective:
        conditional = softmax({scene_id: scores[scene_id] for scene_id in candidates[variable]}, config.scene_temperature)
        for scene_id, probability in conditional.items():
            probabilities[scene_id] += budgets[variable] * probability
    return Selection(
        probabilities=probabilities,
        salience=s,
        reason="preference" if selected_tier is not None else "best_effort",
        selected_tier=selected_tier,
        sources=effective,
        excluded_scenes=excluded,
    )


class Selector:
    def __init__(self, associations: Mapping[SceneId, Association], policies: list[Policy], config: MatchingConfig) -> None:
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
