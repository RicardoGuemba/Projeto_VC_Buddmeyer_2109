# -*- coding: utf-8 -*-
"""Audit trail SQLite para ciclos e falhas."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class AuditStore:
    """Persistência local de ciclos e falhas."""

    def __init__(self, db_path: Optional[Path] = None):
        base = Path(__file__).resolve().parent.parent
        self._db_path = db_path or (base / "logs" / "audit.db")
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS cycles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    cycle_number INTEGER,
                    state TEXT,
                    centroid_x_mm REAL,
                    centroid_y_mm REAL,
                    outcome TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS faults (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    state TEXT
                );
                """
            )

    def record_cycle(
        self,
        cycle_number: int,
        state: str,
        outcome: str,
        centroid_x_mm: Optional[float] = None,
        centroid_y_mm: Optional[float] = None,
    ) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO cycles (ts, cycle_number, state, centroid_x_mm, centroid_y_mm, outcome)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (ts, cycle_number, state, centroid_x_mm, centroid_y_mm, outcome),
            )

    def record_fault(self, reason: str, state: str = "") -> None:
        ts = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO faults (ts, reason, state) VALUES (?, ?, ?)",
                (ts, reason, state),
            )

    def count_cycles(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM cycles").fetchone()
            return int(row["c"]) if row else 0

    def count_faults(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM faults").fetchone()
            return int(row["c"]) if row else 0


_audit_instance: Optional[AuditStore] = None


def get_audit_store() -> AuditStore:
    global _audit_instance
    if _audit_instance is None:
        _audit_instance = AuditStore()
    return _audit_instance
