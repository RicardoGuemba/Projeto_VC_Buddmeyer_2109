# -*- coding: utf-8 -*-
"""Testes AuditStore SQLite."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestAuditStore:
    def test_record_cycle_and_fault(self, tmp_path):
        from core.audit_store import AuditStore

        store = AuditStore(db_path=tmp_path / "audit.db")
        store.record_cycle(1, "READY_FOR_NEXT", "complete", 100.0, 200.0)
        store.record_fault("timeout", "TIMEOUT")
        assert store.count_cycles() == 1
        assert store.count_faults() == 1
