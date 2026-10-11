from __future__ import annotations

import math
import re
from collections import deque
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from configurations.runtime_models import ActivityPolicyConfig
from core.math_utils import exponential_decay
from core.models.activity_target import normalize_match_text, normalize_process_name
from core.models.context import Context
from core.models.selection import VARIABLE_ITEMS, ActivityDetails, ActivityEvaluation, ContextVariable, SemanticItem
from core.policies.base import Policy

_MATCH_SOURCE_PRIORITY = {
    "process": 0,
    "title": 1,
}

_MATCH_TYPE_PRIORITY = {
    "contains": 0,
    "regex": 1,
    "exact": 2,
}


class ActivityKind(StrEnum):
    WORK = "work"
    LEISURE = "leisure"
    OTHER = "other"


_ACTIVITY_BY_TAG = {"focus": ActivityKind.WORK, "chill": ActivityKind.LEISURE}
# 每个类别明确指定支持项和反向项；OTHER 没有方向证据，但仍占据窗口槽位。
_ACTIVITY_RELATIONS: dict[ActivityKind, tuple[SemanticItem, SemanticItem]] = {
    ActivityKind.WORK: (SemanticItem.FOCUS, SemanticItem.CHILL),
    ActivityKind.LEISURE: (SemanticItem.CHILL, SemanticItem.FOCUS),
}


@dataclass(frozen=True)
class CompiledActivityMatcher:
    source: str
    match: str
    pattern: str
    tag: str
    activity: ActivityKind
    case_sensitive: bool
    declaration_order: int
    regex: re.Pattern[str] | None = None

    @property
    def literal_length(self) -> int:
        if self.match == "regex":
            return 0
        return len(self.pattern)

    @property
    def priority(self) -> tuple[int, int, int, int]:
        return (
            _MATCH_SOURCE_PRIORITY[self.source],
            _MATCH_TYPE_PRIORITY[self.match],
            self.literal_length,
            -self.declaration_order,
        )


class ActivityPolicy(Policy):
    config_key = "activity"
    WINDOW_SIZE = 600

    def __init__(self, config: ActivityPolicyConfig) -> None:
        """Build the configured classifier and observation window.

        Raises:
            re.error: If a configured regular expression is invalid.
        """
        super().__init__(config)
        self.matchers: list[CompiledActivityMatcher] = []
        for declaration_order, matcher in enumerate(config.matchers):
            compiled_regex = None
            if matcher.match == "regex":
                flags = 0 if matcher.case_sensitive else re.IGNORECASE
                compiled_regex = re.compile(matcher.pattern, flags)
            self.matchers.append(
                CompiledActivityMatcher(
                    source=matcher.source,
                    match=matcher.match,
                    pattern=matcher.pattern,
                    tag=matcher.tag,
                    activity=_ACTIVITY_BY_TAG[matcher.tag],
                    case_sensitive=matcher.case_sensitive,
                    declaration_order=declaration_order,
                    regex=compiled_regex,
                )
            )

        self._history: deque[ActivityKind] = deque(maxlen=self.WINDOW_SIZE)
        self._weights = tuple(exponential_decay(age, scale=config.age_scale, power=3, base=2) for age in range(self.WINDOW_SIZE))
        self._denominator = math.fsum(self._weights)

    def evaluate(self, context: Context) -> ActivityEvaluation:
        activity, details = self._classify_window(context)
        self._history.appendleft(activity)
        return ActivityEvaluation(policy_id=self.config_key, salience=self._build_salience(), details=details)

    def _build_salience(self) -> dict[SemanticItem, float]:
        items = VARIABLE_ITEMS[ContextVariable.ACTIVITY]
        support = {item: 0.0 for item in items}
        opposition = {item: 0.0 for item in items}
        for activity, (supported_item, opposed_item) in _ACTIVITY_RELATIONS.items():
            evidence = math.fsum(weight for weight, observed in zip(self._weights, self._history) if observed == activity)
            support[supported_item] = evidence
            opposition[opposed_item] = evidence

        return {item: (support[item] - opposition[item]) / self._denominator for item in items}

    def _classify_window(
        self,
        context: Context,
    ) -> tuple[ActivityKind, ActivityDetails]:
        details = ActivityDetails(
            window_title=context.window.title,
            process=context.window.process,
        )

        matched = self._select_matcher(context)
        if matched is not None:
            details.match_source = matched.source
            details.matched_rule = matched.pattern
            details.matched_tag = matched.tag
            return matched.activity, details

        return ActivityKind.OTHER, details

    def _select_matcher(self, context: Context) -> CompiledActivityMatcher | None:
        matched: CompiledActivityMatcher | None = None

        for matcher in self.matchers:
            if not self._matcher_matches(matcher, context):
                continue
            if matched is None or matcher.priority > matched.priority:
                matched = matcher

        return matched

    def _matcher_matches(
        self,
        matcher: CompiledActivityMatcher,
        context: Context,
    ) -> bool:
        observed = context.window.process if matcher.source == "process" else context.window.title
        if matcher.match == "exact":
            return self._matches_exact(matcher, observed)
        if matcher.match == "contains":
            return self._matches_contains(matcher, observed)
        return matcher.regex.search(observed) is not None

    @staticmethod
    def _matches_exact(
        matcher: CompiledActivityMatcher,
        observed: str,
    ) -> bool:
        if matcher.source == "process":
            pattern = normalize_process_name(matcher.pattern, case_sensitive=matcher.case_sensitive)
            observed = normalize_process_name(observed, case_sensitive=matcher.case_sensitive)
        else:
            pattern = normalize_match_text(matcher.pattern, case_sensitive=matcher.case_sensitive)
            observed = normalize_match_text(observed, case_sensitive=matcher.case_sensitive)
        return observed == pattern

    @staticmethod
    def _matches_contains(
        matcher: CompiledActivityMatcher,
        observed: str,
    ) -> bool:
        pattern = normalize_match_text(matcher.pattern, case_sensitive=matcher.case_sensitive)
        observed = normalize_match_text(observed, case_sensitive=matcher.case_sensitive)
        return pattern in observed

    def export_state(self) -> dict[str, Any]:
        return {"observations": list(self._history)}

    def import_state(self, state: dict[str, Any]) -> None:
        self._history = deque(state["observations"], maxlen=self.WINDOW_SIZE)
