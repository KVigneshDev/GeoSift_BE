"""Beanie ODM documents for User and Organization.

These mirror `services/user/user.model.js` and `services/user/organization.model.js`
from the original project. Beanie gives us Pydantic-validated documents on top
of Motor — the Pythonic equivalent of Mongoose.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from beanie import Document, Link, PydanticObjectId
from pydantic import EmailStr, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class OrganizationDocument(Document):
    name: str
    users: list[PydanticObjectId] = Field(default_factory=list)
    deleted_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    class Settings:
        name = "organizations"
        indexes = [
            "name",
        ]


class UserDocument(Document):
    email: EmailStr
    password: str
    name: str
    phone: str
    email_verified: bool = False
    role: UserRole = UserRole.USER
    deleted_at: Optional[datetime] = None
    organization: Optional[Link[OrganizationDocument]] = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    class Settings:
        name = "users"
        indexes = [
            "email",
        ]
