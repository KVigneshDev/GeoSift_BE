"""Per-request DataLoader factory.
"""
from __future__ import annotations

from dataclasses import dataclass

from strawberry.dataloader import DataLoader

from app.loaders.user_loader import create_user_loader
from app.services.user.models import UserDocument


@dataclass
class Loaders:
    user_loader: DataLoader[str, UserDocument | None]


def create_loaders() -> Loaders:
    return Loaders(
        user_loader=create_user_loader(),
    )
