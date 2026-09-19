from __future__ import annotations

import json
import sqlite3
from typing import Any, TYPE_CHECKING

from storage.incident_store import IncidentStore

if TYPE_CHECKING:
    from models.incident import Incident


class SQLiteIncidentStore(IncidentStore):
    """SQLite-backed persistent incident store."""

    def __init__(self, database_path: str) -> None:
        self._database_path = database_path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def save(self, incident: "Incident") -> str:
        incident_id = self._incident_id(incident)

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO incidents (id, data)
                VALUES (?, ?)
                """,
                (
                    incident_id,
                    json.dumps(self._serialize(incident)),
                ),
            )
            connection.commit()

        return incident_id

    def get(self, incident_id: str) -> "Incident | None":
        with self._connect() as connection:
            row = connection.execute(
                "SELECT data FROM incidents WHERE id = ?",
                (incident_id,),
            ).fetchone()

        if row is None:
            return None

        return self._deserialize(row["data"])

    def list(self) -> list["Incident"]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT data FROM incidents ORDER BY id"
            ).fetchall()

        return [self._deserialize(row["data"]) for row in rows]

    def search(self, **filters: Any) -> list["Incident"]:
        results = self.list()

        for field, expected in filters.items():
            results = [
                incident
                for incident in results
                if getattr(incident, field, None) == expected
            ]

        return results

    def delete(self, incident_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM incidents WHERE id = ?",
                (incident_id,),
            )
            connection.commit()

        return cursor.rowcount > 0

    @staticmethod
    def _incident_id(incident: "Incident") -> str:
        value = getattr(incident, "id", None)

        if value is not None:
            return str(value)

        raise ValueError("Incident must provide an id")

    @staticmethod
    def _serialize(incident: "Incident") -> dict[str, Any]:
        if hasattr(incident, "model_dump"):
            return incident.model_dump(mode="json")

        if hasattr(incident, "to_dict"):
            payload = incident.to_dict()
        elif hasattr(incident, "__dict__"):
            payload = dict(incident.__dict__)
        else:
            raise TypeError("Incident cannot be serialized")

        # Convert datetime and other Python objects into
        # JSON-safe values before storing them in SQLite.
        return json.loads(json.dumps(payload, default=str))

    @staticmethod
    def _deserialize(data: str) -> "Incident":
        from models.incident import Incident

        payload = json.loads(data)

        if hasattr(Incident, "model_validate"):
            return Incident.model_validate(payload)

        if hasattr(Incident, "from_dict"):
            return Incident.from_dict(payload)

        return Incident(**payload)