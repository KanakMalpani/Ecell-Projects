"""
Role-based access control (RBAC) for the CRM API.

WHAT THIS FILE DOES
-------------------
Handles user authentication (login), JWT token creation/validation, and
permission checking for every protected API endpoint.

AUTH FLOW
---------
  1. POST /api/v1/auth/login with username + password
  2. verify_password() checks PBKDF2-SHA256 hash (120,000 iterations)
  3. create_access_token() signs JWT with role + agent_id (12-hour expiry)
  4. Protected endpoints use Depends(require_permission("...")) to check JWT + role

FOUR ROLES (ROLE_PERMISSIONS)
-----------------------------
  Agent      — CRUD customers/tickets, summarize, agent query
  Supervisor — Agent permissions + cohort read + HEART read
  Admin      — Full access (*)
  Analytics  — Read-only: customers, tickets, cohorts, HEART

PASSWORD SECURITY
-----------------
  Passwords hashed with PBKDF2-SHA256 at 120,000 iterations.
  Only hashes stored in memory (USERS dict); plaintext never persisted.
  Demo users configured via CRM_DEMO_USERS env var.

PI INTERVIEW TALKING POINTS
---------------------------
  Q: Why JWT instead of session cookies?
  A: Stateless — API can scale without shared session store. Token carries
     role and agent_id so every request is self-contained.

  Q: How does require_permission work?
  A: FastAPI Depends() chain: get_current_user decodes JWT → checker verifies
     role has the required permission string → 403 if missing.

  Q: Is this production-ready auth?
  A: Architecture is sound; production needs OAuth2/SSO, token refresh,
     and secrets in a vault (not .env file).
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from src.config import JWT_SECRET

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 12
_PBKDF2_ITERS = 120_000
_PBKDF2_SALT = b"ecell-crm-auth-v1"


class Role(str, Enum):
    AGENT = "agent"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"
    ANALYTICS = "analytics"


ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.AGENT: {
        "customers:read", "customers:write", "tickets:read", "tickets:write",
        "agent:query", "tickets:summarize",
    },
    Role.SUPERVISOR: {
        "customers:read", "customers:write", "tickets:read", "tickets:write",
        "agent:query", "tickets:summarize", "cohorts:read", "heart:read",
    },
    Role.ADMIN: {"*"},
    Role.ANALYTICS: {"customers:read", "tickets:read", "cohorts:read", "heart:read"},
}


def _password_hash(password: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), _PBKDF2_SALT, _PBKDF2_ITERS
    ).hex()


def _parse_demo_users() -> dict[str, dict]:
    """
    Demo users for evaluation. Override CRM_DEMO_USERS in production.

    Format: username:password:role:agent_id;...
    Passwords are hashed at load — never stored or compared in plaintext.
    """
    raw = os.getenv(
        "CRM_DEMO_USERS",
        "agent1:agent123:agent:AGT-001;"
        "supervisor1:super123:supervisor:SUP-001;"
        "admin1:admin123:admin:ADM-001;"
        "analytics1:analytics123:analytics:ANL-001",
    )
    users: dict[str, dict] = {}
    for entry in raw.split(";"):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split(":")
        if len(parts) != 4:
            logger.warning("Skipping malformed CRM_DEMO_USERS entry")
            continue
        username, password, role_str, agent_id = parts
        try:
            role = Role(role_str)
        except ValueError:
            logger.warning("Unknown role for user %s", username)
            continue
        users[username] = {
            "password_hash": _password_hash(password),
            "role": role,
            "agent_id": agent_id,
        }
    return users


USERS: dict[str, dict] = _parse_demo_users()


def verify_password(plain: str, hashed: str) -> bool:
    return _password_hash(plain) == hashed


def create_access_token(username: str) -> str:
    user = USERS[username]
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": username,
        "role": user["role"].value if isinstance(user["role"], Role) else user["role"],
        "agent_id": user["agent_id"],
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def authenticate_user(username: str, password: str) -> dict | None:
    user = USERS.get(username)
    if not user or not verify_password(password, user["password_hash"]):
        return None
    return {"username": username, "role": user["role"], "agent_id": user["agent_id"]}


def _has_permission(role: Role, permission: str) -> bool:
    perms = ROLE_PERMISSIONS.get(role, set())
    return "*" in perms or permission in perms


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[ALGORITHM])
        username: str = payload.get("sub", "")
        role_str: str = payload.get("role", "")
        agent_id: str = payload.get("agent_id", "")
        role = Role(role_str)
        if username not in USERS:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    except (JWTError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    return {"username": username, "role": role, "agent_id": agent_id}


def require_permission(permission: str):
    async def checker(user: Annotated[dict, Depends(get_current_user)]) -> dict:
        if not _has_permission(user["role"], permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}",
            )
        return user

    return checker
