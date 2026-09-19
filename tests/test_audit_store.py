from datetime import datetime, timezone

from remediation.audit import AuditEntry
from remediation.audit_store import SQLiteAuditStore


def test_audit_store_persists_entries(tmp_path) -> None:
    database = tmp_path / "audit.db"

    store = SQLiteAuditStore(database)

    entry = AuditEntry(
        requester="dhrithi",
        action="restart",
        target="deployment/default/web",
        parameters={"reason": "test"},
        approval="approved",
        timestamp=datetime.now(timezone.utc),
        success=True,
    )

    store.record(entry)

    assert store.count() == 1

    entries = store.list()

    assert len(entries) == 1
    assert entries[0].requester == "dhrithi"
    assert entries[0].action == "restart"
    assert entries[0].target == "deployment/default/web"
    assert entries[0].parameters == {"reason": "test"}
    assert entries[0].approval == "approved"
    assert entries[0].success is True


def test_audit_store_survives_new_instance(tmp_path) -> None:
    database = tmp_path / "audit.db"

    first_store = SQLiteAuditStore(database)

    first_store.record(
        AuditEntry(
            requester="dhrithi",
            action="scale",
            target="deployment/default/web",
            parameters={"replicas": 3},
            approval="approved",
            success=True,
        )
    )

    second_store = SQLiteAuditStore(database)

    entries = second_store.list()

    assert len(entries) == 1
    assert entries[0].action == "scale"
    assert entries[0].parameters == {"replicas": 3}


def test_empty_audit_store(tmp_path) -> None:
    database = tmp_path / "audit.db"

    store = SQLiteAuditStore(database)

    assert store.count() == 0
    assert store.list() == []