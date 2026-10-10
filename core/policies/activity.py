from __future__ import annotations

import math
import re
from collections import deque
from dataclasses import dataclass
from typing import Any

from configurations.runtime_models import ActivityPolicyConfig
from core.models.activity_target import normalize_match_text, normalize_process_name
from core.models.context import Context
from core.models.trace import ActivityDetails, ActivityEvaluation
from core.policies.base import Policy, _s_curve

_MATCH_SOURCE_PRIORITY = {
    "process": 0,
    "title": 1,
}

_MATCH_TYPE_PRIORITY = {
    "contains": 0,
    "regex": 1,
    "exact": 2,
}


@dataclass(frozen=True)
class CompiledActivityMatcher:
    source: str
    match: str
    pattern: str
    tag: str
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
        """Build the product classifier and observation window.

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
                    case_sensitive=matcher.case_sensitive,
                    declaration_order=declaration_order,
                    regex=compiled_regex,
                )
            )

        self._history: deque[int] = deque(maxlen=self.WINDOW_SIZE)
        self._weights = tuple(2 ** (-((age / config.age_scale) ** 3)) for age in range(self.WINDOW_SIZE))
        self._denominator = math.fsum(self._weights)
        self._curve_q = config.curve_q

    def evaluate(self, context: Context) -> ActivityEvaluation:
        direction, details = self._get_instant_signal(context)
        self._history.appendleft(direction)
        net_direction = math.fsum(weight * observed for weight, observed in zip(self._weights, self._history)) / self._denominator
        focus = math.copysign(_s_curve(abs(net_direction), self._curve_q), net_direction)
        return ActivityEvaluation(policy_id=self.config_key, salience={"focus": focus, "chill": -focus}, details=details)

    def _get_instant_signal(
        self,
        context: Context,
    ) -> tuple[int, ActivityDetails]:
        details = ActivityDetails(
            window_title=context.window.title,
            process=context.window.process,
        )

        matched = self._select_matcher(context)
        if matched is not None:
            details.match_source = matched.source
            details.matched_rule = matched.pattern
            details.matched_tag = matched.tag
            return (1 if matched.tag == "focus" else -1), details

        return 0, details

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
        return {"directions": list(self._history)}

    def import_state(self, state: dict[str, Any]) -> None:
        self._history = deque(state["directions"], maxlen=self.WINDOW_SIZE)
