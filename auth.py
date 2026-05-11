from __future__ import annotations

import hashlib
import json
import os
import secrets
from datetime import datetime, timezone
from typing import Any


_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_USERS_PATH = os.path.join(_BASE_DIR, "users.json")
_LOGIN_HISTORY_PATH = os.path.join(_BASE_DIR, "login_history.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_password(pwd: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256(f"{pwd}{salt}".encode("utf-8")).hexdigest()
    return password_hash, salt


def verify_password(pwd: str, password_hash: str, salt: str) -> bool:
    check = hashlib.sha256(f"{pwd}{salt}".encode("utf-8")).hexdigest()
    return secrets.compare_digest(check, str(password_hash))


def save_users(data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(_USERS_PATH), exist_ok=True)
    tmp = f"{_USERS_PATH}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _USERS_PATH)


def load_users() -> dict[str, Any]:
    if os.path.exists(_USERS_PATH):
        try:
            with open(_USERS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    now = _now_iso()

    admin_hash, admin_salt = hash_password("Admin2024!")
    biblio_hash, biblio_salt = hash_password("Biblio2024!")
    user_hash, user_salt = hash_password("User2024!")

    data = {
        "admin": {
            "password_hash": admin_hash,
            "salt": admin_salt,
            "role": "administrador",
            "display_name": "Administrador UDEC",
            "created_at": now,
            "active": True,
        },
        "biblio": {
            "password_hash": biblio_hash,
            "salt": biblio_salt,
            "role": "bibliotecario",
            "display_name": "Bibliotecario UDEC",
            "created_at": now,
            "active": True,
        },
        "usuario": {
            "password_hash": user_hash,
            "salt": user_salt,
            "role": "usuario_comun",
            "display_name": "Usuario General",
            "created_at": now,
            "active": True,
        },
    }
    save_users(data)
    return data


def _save_login_history(events: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(_LOGIN_HISTORY_PATH), exist_ok=True)
    tmp = f"{_LOGIN_HISTORY_PATH}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _LOGIN_HISTORY_PATH)


def get_login_history() -> list[dict[str, Any]]:
    if not os.path.exists(_LOGIN_HISTORY_PATH):
        return []
    try:
        with open(_LOGIN_HISTORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [e for e in data if isinstance(e, dict)]
    except Exception:
        pass
    return []


def clear_login_history() -> None:
    _save_login_history([])


def log_event(username: str, success: bool) -> None:
    events = get_login_history()
    users = load_users()
    role = None
    if success and username in users and isinstance(users.get(username), dict):
        role = users[username].get("role")

    events.append({
        "timestamp": _now_iso(),
        "username": username,
        "success": bool(success),
        "role": role,
    })
    if len(events) > 500:
        events = events[-500:]
    _save_login_history(events)


def authenticate(username: str, password: str) -> dict[str, Any] | None:
    users = load_users()
    u = users.get(username)
    if not isinstance(u, dict) or not u.get("active", True):
        log_event(username, False)
        return None

    if not verify_password(password, str(u.get("password_hash", "")), str(u.get("salt", ""))):
        log_event(username, False)
        return None

    user = {
        "username": username,
        "role": str(u.get("role", "usuario_comun")),
        "display_name": str(u.get("display_name", username)),
    }
    log_event(username, True)
    return user


def get_all_users() -> list[dict[str, Any]]:
    users = load_users()
    out: list[dict[str, Any]] = []
    for username, u in users.items():
        if not isinstance(u, dict):
            continue
        out.append({
            "username": username,
            "display_name": u.get("display_name"),
            "role": u.get("role"),
            "active": bool(u.get("active", True)),
            "created_at": u.get("created_at"),
        })
    out.sort(key=lambda x: str(x.get("username", "")).lower())
    return out


def create_user(username: str, pwd: str, role: str, display_name: str) -> None:
    if not username or any(c.isspace() for c in username):
        raise ValueError("invalid_username")
    users = load_users()
    if username in users:
        raise ValueError("username_exists")
    password_hash, salt = hash_password(pwd)
    users[username] = {
        "password_hash": password_hash,
        "salt": salt,
        "role": role,
        "display_name": display_name,
        "created_at": _now_iso(),
        "active": True,
    }
    save_users(users)


def update_user(username: str, **fields: Any) -> None:
    users = load_users()
    u = users.get(username)
    if not isinstance(u, dict):
        raise ValueError("user_not_found")

    allowed = {"role", "display_name", "active"}
    for k, v in fields.items():
        if k in allowed:
            u[k] = v

    users[username] = u
    save_users(users)


def delete_user(username: str) -> None:
    users = load_users()
    if username not in users:
        raise ValueError("user_not_found")

    admins = [u for u in users.values() if isinstance(u, dict) and u.get("role") == "administrador" and u.get("active", True)]
    if isinstance(users.get(username), dict) and users[username].get("role") == "administrador" and len(admins) <= 1:
        raise ValueError("cannot_delete_last_admin")

    users.pop(username, None)
    save_users(users)
