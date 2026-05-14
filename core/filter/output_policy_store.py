import json
import sqlite3
import time
from typing import Any, Dict, List, Optional


class OutputPolicyStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS output_filter_policies (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    enabled INTEGER NOT NULL DEFAULT 1,
                    review_enabled INTEGER NOT NULL DEFAULT 1,
                    rules_json TEXT NOT NULL,
                    templates_json TEXT NOT NULL,
                    updated_by TEXT,
                    updated_at INTEGER NOT NULL
                )
                '''
            )

    def get_policy(self) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute('SELECT * FROM output_filter_policies WHERE id = 1').fetchone()

        if row is None:
            return {
                'enabled': 1,
                'review_enabled': 1,
                'rules': [],
                'templates': {},
                'updated_by': None,
                'updated_at': None,
            }

        return {
            'enabled': row['enabled'],
            'review_enabled': row['review_enabled'],
            'rules': json.loads(row['rules_json'] or '[]'),
            'templates': json.loads(row['templates_json'] or '{}'),
            'updated_by': row['updated_by'],
            'updated_at': row['updated_at'],
        }

    def upsert_policy(
        self,
        *,
        enabled: bool,
        review_enabled: bool,
        rules: List[Dict[str, Any]],
        templates: Dict[str, str],
        updated_by: str,
    ) -> Dict[str, Any]:
        now = int(time.time())
        with self._connect() as conn:
            conn.execute(
                '''
                INSERT INTO output_filter_policies (
                    id, enabled, review_enabled, rules_json, templates_json, updated_by, updated_at
                ) VALUES (1, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    enabled = excluded.enabled,
                    review_enabled = excluded.review_enabled,
                    rules_json = excluded.rules_json,
                    templates_json = excluded.templates_json,
                    updated_by = excluded.updated_by,
                    updated_at = excluded.updated_at
                ''',
                (
                    1 if enabled else 0,
                    1 if review_enabled else 0,
                    json.dumps(rules, ensure_ascii=False),
                    json.dumps(templates, ensure_ascii=False),
                    updated_by,
                    now,
                ),
            )
        return self.get_policy()
