from __future__ import annotations

import pytest

from app import instance as instance_module
from app.instance import SingleInstance


def test_acquire_claims_mutex_when_free(monkeypatch: pytest.MonkeyPatch) -> None:
    closed: list[int] = []
    monkeypatch.setattr(instance_module, "_create_mutex_handle", lambda name: (1234, 0))
    monkeypatch.setattr(instance_module, "_close_mutex_handle", closed.append)

    instance = SingleInstance()

    assert instance.acquire() is True
    assert instance.held is True
    assert closed == []


def test_acquire_returns_false_when_instance_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    closed: list[int] = []
    monkeypatch.setattr(instance_module, "_create_mutex_handle", lambda name: (5678, 183))
    monkeypatch.setattr(instance_module, "_close_mutex_handle", closed.append)

    instance = SingleInstance()

    assert instance.acquire() is False
    assert instance.held is False
    assert closed == [5678]


def test_acquire_raises_when_mutex_cannot_be_created(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(instance_module, "_create_mutex_handle", lambda name: (None, 5))

    with pytest.raises(OSError):
        SingleInstance().acquire()
