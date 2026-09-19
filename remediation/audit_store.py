from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from remediation.audit import AuditEntry


class SQLiteAuditStore:
    """Persistent SQLite storage for remediation audit entries."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS remediation_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    requester TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target TEXT NOT NULL,
                    parameters TEXT NOT NULL,
                    approval TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    error TEXT
                )
                """
            )

    def record(self, entry: AuditEntry) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO remediation_audit (
                    requester,
                    action,
                    target,
                    parameters,
                    approval,
                    timestamp,
                    success,
                    error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.requester,
                    entry.action,
                    entry.target,
                    json.dumps(entry.parameters),
                    entry.approval,
                    entry.timestamp.isoformat(),
                    int(entry.success),
                    entry.error,
                ),
            )

    def list(self) -> list[AuditEntry]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    requester,
                    action,
                    target,
                    parameters,
                    approval,
                    timestamp,
                    success,
                    error
                FROM remediation_audit
                ORDER BY id ASC
                """
            ).fetchall()

        return [
            AuditEntry(
                requester=row[0],
                action=row[1],
                target=row[2],
                parameters=json.loads(row[3]),
                approval=row[4],
                timestamp=datetime.fromisoformat(row[5]),
                success=bool(row[6]),
                error=row[7],
            )
            for row in rows
        ]

    def count(self) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM remediation_audit"
            ).fetchone()

        return int(row[0])


class PersistentAuditLog:
    """AuditLog-compatible adapter backed by SQLite."""

    def __init__(self, store: SQLiteAuditStore) -> None:
        self.store = store

    def record(self, entry: AuditEntry) -> None:
        self.store.record(entry)

    def list(self) -> list[AuditEntry]:
        return self.store.list()