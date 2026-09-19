import json
import sqlite3
from datetime import datetime
from typing import Any

from models.evidence import Evidence
from storage.evidence_store import EvidenceStore


class SQLiteEvidenceStore(EvidenceStore):
    """SQLite-backed persistent evidence store."""

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
                CREATE TABLE IF NOT EXISTS evidence (
                    id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    evidence_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    namespace TEXT,
                    resource TEXT,
                    data TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def save(self, evidence: Evidence) -> str:
        evidence_id = self._make_id(evidence)

        namespace = self._metadata(evidence, "namespace")
        resource = self._metadata(evidence, "resource")

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO evidence (
                    id,
                    source,
                    evidence_type,
                    timestamp,
                    namespace,
                    resource,
                    data
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence_id,
                    evidence.source,
                    evidence.evidence_type,
                    evidence.timestamp.isoformat(),
                    namespace,
                    resource,
                    json.dumps(self._to_data(evidence)),
                ),
            )
            connection.commit()

        return evidence_id

    def get(self, evidence_id: str) -> Evidence | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM evidence WHERE id = ?",
                (evidence_id,),
            ).fetchone()

        if row is None:
            return None

        return self._from_row(row)

    def list(self) -> list[Evidence]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM evidence ORDER BY timestamp"
            ).fetchall()

        return [self._from_row(row) for row in rows]

    def search(self, **filters: Any) -> list[Evidence]:
        query = "SELECT * FROM evidence"
        clauses: list[str] = []
        values: list[Any] = []

        for field in ("source", "namespace", "resource"):
            value = filters.get(field)

            if value is not None:
                clauses.append(f"{field} = ?")
                values.append(value)

        if filters.get("start_time") is not None:
            clauses.append("timestamp >= ?")
            values.append(filters["start_time"].isoformat())

        if filters.get("end_time") is not None:
            clauses.append("timestamp <= ?")
            values.append(filters["end_time"].isoformat())

        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        query += " ORDER BY timestamp"

        with self._connect() as connection:
            rows = connection.execute(query, values).fetchall()

        results = [self._from_row(row) for row in rows]

        entity = filters.get("entity")
        if entity is not None:
            results = [
                item
                for item in results
                if self._metadata(item, "entity") == entity
            ]

        return results

    def delete(self, evidence_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM evidence WHERE id = ?",
                (evidence_id,),
            )
            connection.commit()

        return cursor.rowcount > 0

    @staticmethod
    def _make_id(evidence: Evidence) -> str:
        return (
            f"{evidence.source}:"
            f"{evidence.evidence_type}:"
            f"{evidence.timestamp.isoformat()}"
        )

    @staticmethod
    def _metadata(evidence: Evidence, field: str) -> Any:
        value = getattr(evidence, field, None)

        if value is not None:
            return value

        metadata = getattr(evidence, "metadata", None)

        if isinstance(metadata, dict):
            return metadata.get(field)

        return None

    @staticmethod
    def _to_data(evidence: Evidence) -> dict[str, Any]:
        metadata = getattr(evidence, "metadata", None)

        if isinstance(metadata, dict):
            return metadata

        data = getattr(evidence, "data", None)

        if isinstance(data, dict):
            return data

        return {}

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Evidence:
        data = json.loads(row["data"])

        return Evidence(
            source=row["source"],
            evidence_type=row["evidence_type"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            metadata=data,
        )