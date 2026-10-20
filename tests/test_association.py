from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from configurations.runtime_models import SceneConfig
from core.models.association import Association
from core.models.selection import ContextVariable, SemanticItem


def test_association_exposes_alternatives_grouped_by_variable() -> None:
    association = Association(SemanticItem.SNOW, SemanticItem.WINTER, SemanticItem.RAIN)

    assert dict(association) == {
        ContextVariable.SEASON: frozenset({SemanticItem.WINTER}),
        ContextVariable.WEATHER: frozenset({SemanticItem.RAIN, SemanticItem.SNOW}),
    }
    assert list(association) == [ContextVariable.SEASON, ContextVariable.WEATHER]
    assert len(association) == 2


def test_association_deduplicates_items_and_compares_content_independently_of_input_order() -> None:
    first = Association(SemanticItem.WORK, SemanticItem.LEISURE, SemanticItem.WORK)
    second = Association(SemanticItem.LEISURE, SemanticItem.WORK)

    assert first == second
    assert len(first) == 1
    assert first[ContextVariable.ACTIVITY] == frozenset({SemanticItem.WORK, SemanticItem.LEISURE})
    assert first != Association(SemanticItem.WORK)


def test_association_reports_absent_variables_through_mapping_access() -> None:
    association = Association(SemanticItem.RAIN)

    assert ContextVariable.WEATHER in association
    assert ContextVariable.ACTIVITY not in association
    assert association.get(ContextVariable.ACTIVITY) is None
    with pytest.raises(KeyError):
        association[ContextVariable.ACTIVITY]


def test_association_and_its_alternatives_are_read_only() -> None:
    association = Association(SemanticItem.RAIN, SemanticItem.SNOW)

    with pytest.raises(TypeError):
        association[ContextVariable.WEATHER] = frozenset({SemanticItem.CLEAR})
    with pytest.raises(AttributeError):
        association[ContextVariable.WEATHER].add(SemanticItem.CLEAR)

    assert association[ContextVariable.WEATHER] == frozenset({SemanticItem.RAIN, SemanticItem.SNOW})


def test_association_requires_at_least_one_item() -> None:
    with pytest.raises(ValueError):
        Association()


@pytest.mark.parametrize(
    "raw_associations",
    [
        {"weather": ["snow", "rain", "rain"], "season": ["winter"]},
        {ContextVariable.SEASON: frozenset({SemanticItem.WINTER}), ContextVariable.WEATHER: frozenset({SemanticItem.RAIN, SemanticItem.SNOW})},
        Association(SemanticItem.WINTER, SemanticItem.RAIN, SemanticItem.SNOW),
    ],
)
def test_scene_config_accepts_grouped_items_or_an_association(raw_associations: object) -> None:
    scene = SceneConfig.model_validate({"playlist": "Winter", "associations": raw_associations})

    assert dict(scene.associations) == {
        ContextVariable.SEASON: frozenset({SemanticItem.WINTER}),
        ContextVariable.WEATHER: frozenset({SemanticItem.RAIN, SemanticItem.SNOW}),
    }
    assert scene.playlist == "Winter"


@pytest.mark.parametrize(
    "raw_associations",
    [
        {},
        {"weather": []},
        {"weather": ["rain"], "season": []},
        {"weather": ["rain", "unknown"]},
        {"weather": ["rain", None]},
        {"unknown": ["rain"]},
        {"season": ["rain"]},
        {"weather": ["rain", "winter"]},
        ["winter", "rain", "snow"],
    ],
)
def test_scene_config_rejects_empty_or_invalid_associations(raw_associations: object) -> None:
    with pytest.raises(ValidationError):
        SceneConfig.model_validate({"playlist": "Winter", "associations": raw_associations})


def test_scene_config_preserves_variable_groups_when_serializing_and_loading() -> None:
    scene = SceneConfig(playlist="Winter", associations=Association(SemanticItem.WINTER, SemanticItem.RAIN, SemanticItem.SNOW), item_count=7)

    assert scene.model_dump()["associations"] == {
        ContextVariable.SEASON: frozenset({SemanticItem.WINTER}),
        ContextVariable.WEATHER: frozenset({SemanticItem.RAIN, SemanticItem.SNOW}),
    }
    payload = json.loads(scene.model_dump_json())
    assert {variable: set(items) for variable, items in payload["associations"].items()} == {"season": {"winter"}, "weather": {"rain", "snow"}}
    restored = SceneConfig.model_validate_json(json.dumps(payload))
    assert restored == scene
    assert restored.associations[ContextVariable.WEATHER] == frozenset({SemanticItem.RAIN, SemanticItem.SNOW})
