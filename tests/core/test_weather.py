from __future__ import annotations

import threading
from collections.abc import Iterator
from concurrent.futures import Future
from queue import Queue

import pytest
import requests

from configurations.runtime_models import WeatherPolicyConfig
from core.models.context import Context
from core.policies.weather import WeatherPolicy
from core.sensors.weather import WeatherSensor


class _Response:
    status_code = 200

    @staticmethod
    def json() -> dict[str, object]:
        return {
            "weather": [{"id": 800, "main": "Clear"}],
        }


type WeatherRequest = tuple[Future[_Response], threading.Thread]


@pytest.fixture
def weather_requests(monkeypatch: pytest.MonkeyPatch) -> Iterator[Queue[WeatherRequest]]:
    pending: Queue[WeatherRequest] = Queue()
    active: list[WeatherRequest] = []

    def request(*args: object, **kwargs: object) -> _Response:
        reply: Future[_Response] = Future()
        worker = threading.current_thread()
        active.append((reply, worker))
        pending.put((reply, worker))
        return reply.result(timeout=5)

    monkeypatch.setattr("integrations.openweather.requests.get", request)
    yield pending
    for reply, worker in active:
        if not reply.done():
            reply.set_exception(requests.Timeout("unfinished test request"))
        worker.join(timeout=5)
        assert not worker.is_alive()


def respond_weather(pending: Queue[WeatherRequest], response: _Response | Exception) -> None:
    reply, worker = pending.get(timeout=1)
    if isinstance(response, Exception):
        reply.set_exception(response)
    else:
        reply.set_result(response)
    worker.join(timeout=1)
    assert not worker.is_alive()


def _config() -> WeatherPolicyConfig:
    return WeatherPolicyConfig(api_key="key", lat=31.0, lon=121.0)


def test_first_weather_failure_still_exposes_source_without_a_success_time(weather_requests: Queue[WeatherRequest]) -> None:
    sensor = WeatherSensor(_config())
    source = sensor.collect().source_fingerprint
    assert source

    respond_weather(weather_requests, requests.Timeout("fixture timeout"))

    current = sensor.collect()
    assert (current.source_fingerprint, current.last_success_at) == (source, None)


def test_weather_success_is_timestamped_when_the_request_completes(monkeypatch: pytest.MonkeyPatch, weather_requests: Queue[WeatherRequest]) -> None:
    clock = [1000.0]
    monkeypatch.setattr("core.sensors.weather.time.time", lambda: clock[0])
    sensor = WeatherSensor(_config())
    source = sensor.collect().source_fingerprint

    clock[0] = 1010.0
    respond_weather(weather_requests, _Response())

    current = sensor.collect()
    assert (current.last_success_at, current.source_fingerprint) == (1010.0, source)


def test_same_source_configuration_update_preserves_cached_weather(monkeypatch: pytest.MonkeyPatch, weather_requests: Queue[WeatherRequest]) -> None:
    monkeypatch.setattr("core.sensors.weather.time.time", lambda: 1000.0)
    config = _config()
    sensor = WeatherSensor(config)
    sensor.collect()
    respond_weather(weather_requests, _Response())
    original = sensor.collect()

    replacement = WeatherSensor(config.model_copy(update={"fetch_interval": 900.0}))
    replacement.import_state(sensor.export_state())
    assert replacement.collect() == original


@pytest.mark.parametrize("changes", [{"api_key": "other-key"}, {"lat": 32.0}, {"lon": 122.0}])
def test_new_weather_source_does_not_inherit_previous_success(
    monkeypatch: pytest.MonkeyPatch, weather_requests: Queue[WeatherRequest], changes: dict[str, str | float]
) -> None:
    monkeypatch.setattr("core.sensors.weather.time.time", lambda: 1000.0)
    config = _config()
    sensor = WeatherSensor(config)
    sensor.collect()
    respond_weather(weather_requests, _Response())
    original = sensor.collect()

    replacement = WeatherSensor(config.model_copy(update=changes))
    replacement.import_state(sensor.export_state())
    replacement.collect()
    respond_weather(weather_requests, requests.Timeout("fixture timeout"))

    current = replacement.collect()
    assert current.source_fingerprint != original.source_fingerprint
    assert current.last_success_at is None


@pytest.mark.parametrize("api_key", ["key", "other-key"])
def test_late_weather_request_cannot_update_a_replacement(
    monkeypatch: pytest.MonkeyPatch, weather_requests: Queue[WeatherRequest], api_key: str
) -> None:
    monkeypatch.setattr("core.sensors.weather.time.time", lambda: 1000.0)
    sensor = WeatherSensor(_config())
    sensor.collect()
    old_reply, old_worker = weather_requests.get(timeout=1)
    replacement = WeatherSensor(_config().model_copy(update={"api_key": api_key}))
    replacement.import_state(sensor.export_state())
    replacement.collect()
    new_reply, new_worker = weather_requests.get(timeout=1)

    old_reply.set_result(_Response())
    old_worker.join(timeout=1)

    assert sensor.collect().last_success_at == 1000.0
    assert replacement.collect().last_success_at is None
    new_reply.set_exception(requests.Timeout("fixture timeout"))
    new_worker.join(timeout=1)


def test_weather_sensor_construction_makes_no_request(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []
    monkeypatch.setattr("integrations.openweather.requests.get", lambda *_args, **_kwargs: calls.append(1))

    WeatherSensor(_config())

    assert calls == []


def test_weather_sensor_warning_identifies_timeout_without_exposing_request(
    weather_requests: Queue[WeatherRequest], caplog: pytest.LogCaptureFixture
) -> None:
    sensor = WeatherSensor(_config())

    sensor.collect()
    respond_weather(weather_requests, requests.Timeout("request URL contained appid=fake-secret"))

    warnings = [record.message for record in caplog.records if record.name == "Tunalo.Sensor"]
    assert any("reason=timeout" in message for message in warnings)
    assert all("fake-secret" not in message for message in warnings)


def test_failed_weather_refresh_keeps_cached_semantic_evidence(monkeypatch: pytest.MonkeyPatch, weather_requests: Queue[WeatherRequest]) -> None:
    clock = [1000.0]
    monkeypatch.setattr("core.sensors.weather.time.time", lambda: clock[0])

    class RainResponse(_Response):
        @staticmethod
        def json() -> dict[str, object]:
            return {"weather": [{"id": 504, "main": "Rain"}]}

    sensor = WeatherSensor(_config())
    sensor.collect()
    clock[0] = 1010.0
    respond_weather(weather_requests, RainResponse())
    cached = sensor.collect()
    assert WeatherPolicy(_config()).evaluate(Context(weather=cached)).salience["rain"] == 4

    clock[0] = 10000.0
    assert sensor.collect() == cached
    respond_weather(weather_requests, requests.Timeout("fixture timeout"))
    current = sensor.collect()
    assert (current.last_success_at, WeatherPolicy(_config()).evaluate(Context(weather=current)).salience["rain"]) == (1010.0, 4)
