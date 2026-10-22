from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

from core.models.selection import VARIABLE_SEMANTIC_ITEMS, ContextVariable, SemanticItem


@dataclass(frozen=True, eq=False)
class Association(Mapping[ContextVariable, frozenset[SemanticItem]]):
    _groups: Mapping[ContextVariable, frozenset[SemanticItem]]

    def __deepcopy__(self, memo: dict[int, object]) -> Association:
        """Share this immutable value in Profile snapshots; mappingproxy cannot be deep-copied."""
        return self

    def __init__(self, *items: SemanticItem) -> None:
        """Group a scene's semantic alternatives by variable.

        Raises:
            ValueError: If no semantic items are supplied.
        """
        if not items:
            raise ValueError("An association must contain at least one semantic item")
        semantic_items = frozenset(items)
        groups = {
            variable: associated
            for variable, vocabulary in VARIABLE_SEMANTIC_ITEMS.items()
            if (associated := semantic_items.intersection(vocabulary))
        }
        object.__setattr__(self, "_groups", MappingProxyType(groups))

    def __getitem__(self, variable: ContextVariable) -> frozenset[SemanticItem]:
        """Return a variable's alternatives.

        Raises:
            KeyError: If the scene does not associate the variable.
        """
        return self._groups[variable]

    def __iter__(self) -> Iterator[ContextVariable]:
        return iter(self._groups)

    def __len__(self) -> int:
        return len(self._groups)

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        def from_groups(groups: dict[ContextVariable, frozenset[SemanticItem]]) -> Association:
            """Build an association from validated groups.

            Raises:
                ValueError: If a semantic item belongs to a different variable.
            """
            for variable, items in groups.items():
                if not items.issubset(VARIABLE_SEMANTIC_ITEMS[variable]):
                    raise ValueError(f"Semantic items must belong to {variable.value}")
            association = object.__new__(cls)
            object.__setattr__(
                association, "_groups", MappingProxyType({variable: groups[variable] for variable in VARIABLE_SEMANTIC_ITEMS if variable in groups})
            )
            return association

        groups_schema = core_schema.dict_schema(
            keys_schema=handler.generate_schema(ContextVariable),
            values_schema=core_schema.frozenset_schema(handler.generate_schema(SemanticItem), min_length=1),
            min_length=1,
        )
        association_schema = core_schema.no_info_after_validator_function(from_groups, groups_schema)
        return core_schema.json_or_python_schema(
            json_schema=association_schema,
            python_schema=core_schema.union_schema([core_schema.is_instance_schema(cls), association_schema]),
            serialization=core_schema.plain_serializer_function_ser_schema(dict, return_schema=groups_schema),
        )
