import sqlite3
import time
import uuid
from typing import Callable, Dict, Optional

from core.admin.admin_security import parse_roles, serialize_roles


def _default_password_hasher(password: str) -> str:
    from api.v1.auth import create_users_table, get_password_hash

    create_users_table()
    return get_password_hash(password)


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_users_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            display_name TEXT,
            created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
            username TEXT,
            roles TEXT,
            password_hash TEXT,
            avatar TEXT,
            rolePermission TEXT,
            menuPermission TEXT,
            tenantId TEXT
        )
        '''
    )
    conn.commit()


def ensure_admin_user(
    db_path: str,
    username: str,
    password: str,
    *,
    display_name: Optional[str] = None,
    password_hasher: Optional[Callable[[str], str]] = None,
) -> Dict[str, object]:
    password_hasher = password_hasher or _default_password_hasher
    display_name = display_name or username

    with _connect(db_path) as conn:
        _ensure_users_table(conn)
        row = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        hashed_password = password_hasher(password)
        roles = ['user', 'admin']
        now = int(time.time())

        if row is None:
            user_id = str(uuid.uuid4())
            conn.execute(
                '''
                INSERT INTO users (
                    id, display_name, created_at, username, roles, password_hash,
                    avatar, rolePermission, menuPermission, tenantId
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    user_id,
                    display_name,
                    now,
                    username,
                    serialize_roles(roles),
                    hashed_password,
                    '',
                    serialize_roles([]),
                    serialize_roles([]),
                    'default',
                ),
            )
            conn.commit()
            return {'created': True, 'user_id': user_id, 'username': username}

        existing_roles = parse_roles(row['roles'])
        merged_roles = list(dict.fromkeys([*existing_roles, 'admin'])) if existing_roles else roles
        conn.execute(
            '''
            UPDATE users
            SET display_name = ?, roles = ?, password_hash = ?
            WHERE username = ?
            ''',
            (
                display_name,
                serialize_roles(merged_roles),
                hashed_password,
                username,
            ),
        )
        conn.commit()
        return {'created': False, 'user_id': row['id'], 'username': username}
