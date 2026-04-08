"""Strawberry GraphQL types for the user feature.

Mirrors `services/user/user.graphql`:

    type User {
      id: ID!
      name: String!
      email: String!
      phone: String
      organization: Organization!
    }

    type Organization {
      id: ID!
      name: String!
    }
"""
from __future__ import annotations

from typing import Optional

import strawberry

from app.services.user.models import OrganizationDocument, UserDocument


@strawberry.type(name="Organization")
class OrganizationType:
    id: strawberry.ID
    name: str

    @classmethod
    def from_document(cls, doc: OrganizationDocument) -> "OrganizationType":
        return cls(
            id=strawberry.ID(str(doc.id)),
            name=doc.name,
        )


@strawberry.type(name="User")
class UserType:
    id: strawberry.ID
    name: str
    email: str
    phone: Optional[str] = None
    organization: OrganizationType

    @classmethod
    def from_document(
        cls,
        user: UserDocument,
        organization: OrganizationDocument,
    ) -> "UserType":
        return cls(
            id=strawberry.ID(str(user.id)),
            name=user.name,
            email=user.email,
            phone=user.phone,
            organization=OrganizationType.from_document(organization),
        )
