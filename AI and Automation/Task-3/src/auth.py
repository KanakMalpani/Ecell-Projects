"""Role-based access control for CRM API."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from src.config import JWT_SECRET

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 12


class Role(str, Enum):
    AGENT = "agent"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"
    ANALYTICS = "analytics"


# Demo users — replace with external IdP in production
USERS: dict[str, dict] = {
    "agent1": {"password": "agent123", "role": Role.AGENT, "agent_id": "AGT-001"},
    "supervisor1": {"password": "super123", "role": Role.SUPERVISOR, "agent_id": "SUP-001"},
    "admin1": {"password": "admin123", "role": Role.ADMIN, "agent_id": "ADM-001"},
    "analytics1": {"password": "analytics123", "role": Role.ANALYTICS, "agent_id": "ANL-001"},
}


ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.AGENT: {"customers:read", "customers:write", "tickets:read", "tickets:write", "agent:query", "tickets:summarize"},
    Role.SUPERVISOR: {"customers:read", "customers:write", "tickets:read", "tickets:write", "agent:query", "tickets:summarize", "cohorts:read"},
    Role.ADMIN: {"*"},
    Role.ANALYTICS: {"customers:read", "tickets:read", "cohorts:read", "heart:read"},
}


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


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
    if not user or user["password"] != password:
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
    except (JWTError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    return {"username": username, "role": role, "agent_id": agent_id}


def require_permission(permission: str):
    async def checker(user: Annotated[dict, Depends(get_current_user)]) -> dict:
        if not _has_permission(user["role"], permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing permission: {permission}")
        return user

    return checker
