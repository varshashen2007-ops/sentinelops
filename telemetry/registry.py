from typing import Any

from telemetry.adapters import TelemetryAdapter


class TelemetryRegistry:
    """Registry for telemetry source adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, TelemetryAdapter] = {}

    def register(self, name: str, adapter: TelemetryAdapter) -> None:
        """Register a telemetry adapter under a unique name."""
        if not name:
            raise ValueError("Telemetry adapter name cannot be empty.")

        if name in self._adapters:
            raise ValueError(f"Telemetry adapter already registered: {name}")

        self._adapters[name] = adapter

    def get(self, name: str) -> TelemetryAdapter:
        """Return a registered telemetry adapter."""
        try:
            return self._adapters[name]
        except KeyError as exc:
            raise KeyError(f"Telemetry adapter not found: {name}") from exc

    def unregister(self, name: str) -> None:
        """Remove a telemetry adapter."""
        self._adapters.pop(name, None)

    def names(self) -> list[str]:
        """Return registered adapter names."""
        return list(self._adapters.keys())

    def collect(self, name: str, **kwargs: Any):
        """Collect telemetry through a registered adapter."""
        adapter = self.get(name)
        return adapter.collect(**kwargs)