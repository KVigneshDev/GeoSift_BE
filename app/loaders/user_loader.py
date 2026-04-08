"""Batched user loader."""
from __future__ import annotations

from beanie import PydanticObjectId
from strawberry.dataloader import DataLoader

from app.services.user.models import UserDocument


async def _load_users(ids: list[str]) -> list[UserDocument | None]:
    object_ids = [PydanticObjectId(i) for i in ids]
    users = await UserDocument.find({"_id": {"$in": object_ids}}).to_list()

    by_id = {str(u.id): u for u in users}
    return [by_id.get(i) for i in ids]


def create_user_loader() -> DataLoader[str, UserDocument | None]:
    return DataLoader(load_fn=_load_users)
