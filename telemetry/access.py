from typing import Any

from models.evidence import Evidence
from telemetry.registry import TelemetryRegistry


class TelemetryAccess:
    """Reliable access layer for telemetry sources."""

    def __init__(self, registry: TelemetryRegistry) -> None:
        self._registry = registry

    async def collect(
        self,
        source: str,
        **kwargs: Any,
    ) -> list[Evidence]:
        """Collect normalized evidence from a registered telemetry source."""
        return await self._registry.collect(source, **kwargs)

    async def metrics(self, **kwargs: Any) -> list[Evidence]:
        """Collect metrics telemetry."""
        return await self.collect("prometheus", **kwargs)

    async def logs(self, **kwargs: Any) -> list[Evidence]:
        """Collect log telemetry."""
        return await self.collect("loki", **kwargs)

    async def traces(self, **kwargs: Any) -> list[Evidence]:
        """Collect trace telemetry."""
        return await self.collect("jaeger", **kwargs)

    async def kubernetes(self, **kwargs: Any) -> list[Evidence]:
        """Collect Kubernetes evidence."""
        return await self.collect("kubernetes", **kwargs)