"""User service: registration and login business logic.

Direct port of `services/user/user.service.js`. Errors raised here are
GraphQL-aware (`AppError` subclasses) so they propagate cleanly through
Strawberry resolvers with the right `extensions.code`.
"""
from __future__ import annotations

from app.core.errors import AuthError, ValidationError
from app.core.security import create_access_token, hash_password, verify_password
from app.services.user.models import OrganizationDocument, UserDocument


class UserService:
    """Stateless collection of user-related operations."""

    @staticmethod
    async def create_user(
        name: str,
        email: str,
        password: str,
        phone: str,
        organization: str,
        tin: str,
    ) -> bool:
        existing = await UserDocument.find_one(UserDocument.email == email)
        if existing is not None:
            raise ValidationError("User already exists")

        org = await OrganizationDocument.find_one(
            OrganizationDocument.name == organization
        )
        if org is None:
            org = OrganizationDocument(name=organization, tin=tin)
            await org.insert()

        user = UserDocument(
            name=name,
            email=email,
            phone=phone,
            password=hash_password(password),
            organization=org,
        )
        await user.insert()

        org.users.append(user.id)
        await org.save()

        return True

    @staticmethod
    async def login_user(
        email: str, password: str
    ) -> tuple[str, UserDocument, OrganizationDocument]:
        user = await UserDocument.find_one(
            UserDocument.email == email,
            fetch_links=True,
        )
        if user is None:
            raise AuthError("Invalid credentials")

        if not verify_password(password, user.password):
            raise AuthError("Invalid credentials")

        token = create_access_token(
            {
                "id": str(user.id),
                "email": user.email,
                "role": user.role.value,
            }
        )

        # `user.organization` is a resolved OrganizationDocument because of
        # `fetch_links=True` above.
        org: OrganizationDocument = user.organization  # type: ignore[assignment]
        return token, user, org

    @staticmethod
    async def get_me(user_id: str) -> tuple[UserDocument, OrganizationDocument]:
        user = await UserDocument.get(user_id, fetch_links=True)
        if user is None:
            raise AuthError("Not authenticated")
        org: OrganizationDocument = user.organization  # type: ignore[assignment]
        return user, org
