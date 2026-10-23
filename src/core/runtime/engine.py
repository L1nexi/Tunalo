from __future__ import annotations

import logging
from dataclasses import dataclass

from configurations.runtime_models import SchedulerConfig
from core.models.context import ContextManager
from core.models.scene import SceneBinding
from core.models.scheduling import ScheduleResult
from core.policies import POLICY_REGISTRY, Policy
from core.runtime.actuator import Actuator
from core.runtime.controller import Controller
from core.runtime.deduce_mode import deduce_mode
from core.runtime.executor import WEExecutor
from core.runtime.selector import Selector
from core.runtime.we_config import WEConfigProber
from core.sensors import SENSOR_REGISTRY
from ui.i18n import set_language

logger = logging.getLogger("Tunalo.Runtime")


@dataclass(frozen=True)
class EngineReplacement:
    executor: WEExecutor
    context_manager: ContextManager
    selector: Selector
    actuator: Actuator
    controller: Controller
    config: SchedulerConfig
    we_config_prober: WEConfigProber


class Engine:
    """Config-bound runtime for sensing, matching, probing, and acting."""

    def __init__(self, replacement: EngineReplacement) -> None:
        self.install_replacement(replacement)

    @classmethod
    def from_config(cls, config: SchedulerConfig) -> Engine:
        """Build and install a complete runtime from a verified config."""

        engine = cls(cls._build_components(config))
        logger.info("Built runtime with %d scenes.", len(config.scenes))
        return engine

    @staticmethod
    def validate_config(config: SchedulerConfig) -> None:
        """Build runtime components once to prove the config can run."""

        Engine._build_components(config)

    def prepare_replacement(self, config: SchedulerConfig) -> EngineReplacement:
        """Build a replacement and import state without changing this engine.

        Raises:
            RuntimeError: If a runtime component rejects the imported state.
        """

        context_state = self.context_manager.export_state()
        selector_state = self.selector.export_state()
        controller_state = self.controller.export_state()
        prepared = self._build_components(config)
        prepared.context_manager.import_state(context_state)
        prepared.selector.import_state(selector_state)
        prepared.controller.import_state(controller_state)
        return prepared

    def install_replacement(self, replacement: EngineReplacement) -> None:
        """Install a prepared replacement at the caller's safe boundary."""

        self.executor = replacement.executor
        self.context_manager = replacement.context_manager
        self.selector = replacement.selector
        self.actuator = replacement.actuator
        self.controller = replacement.controller
        self.we_config_prober = replacement.we_config_prober
        set_language(replacement.config.language)
        self.config = replacement.config

    def schedule(
        self,
        paused: bool,
        manual_requested: bool,
    ) -> ScheduleResult:
        context = self.context_manager.sense()
        selection = self.selector.select(context)
        mode = deduce_mode(
            factual=self.we_config_prober.probe_playlist(),
            paused=paused,
            manual_requested=manual_requested,
        )
        decision = self.controller.decide_action(mode, context, selection)
        action = self.actuator.act(decision)
        if action.executed:
            self.controller.notify_executed(decision)
        return ScheduleResult(
            context=context,
            selection=selection,
            mode=mode,
            decision=decision,
            action=action,
        )

    def ensure_we_alive(self, paused: bool = False) -> None:
        if paused:
            return
        self.executor.keep_alive()

    def get_scene_name(self, scene_id: str) -> str | None:
        scene = self.config.scenes.get(scene_id)
        return scene.name if scene is not None else None

    @staticmethod
    def _build_components(config: SchedulerConfig) -> EngineReplacement:
        executor = WEExecutor(config.wallpaper_engine_path)

        context_manager = ContextManager()
        for sensor_cls in SENSOR_REGISTRY:
            context_manager.register_sensor(sensor_cls.create(config))

        policies: list[Policy] = [cls(getattr(config.policies, cls.config_key)) for cls in POLICY_REGISTRY]

        scene_associations = {scene_id: scene.associations for scene_id, scene in config.scenes.items()}
        selector = Selector(scene_associations, policies, config.matching)
        controller = Controller(config.timing, config.disturbance, scene_associations)
        scene_bindings = {scene_id: SceneBinding(playlist=scene.playlist) for scene_id, scene in config.scenes.items()}
        actuator = Actuator(executor, scene_bindings)

        return EngineReplacement(
            executor=executor,
            context_manager=context_manager,
            selector=selector,
            actuator=actuator,
            controller=controller,
            config=config,
            we_config_prober=WEConfigProber(config.wallpaper_engine_path),
        )
