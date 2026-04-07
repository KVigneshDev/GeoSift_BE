"""MongoDB connection bootstrap.
Beanie is initialized with the document models so that they're query-ready everywhere.
"""
from __future__ import annotations

import logging

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None


async def connect_db() -> None:
    """Connect to MongoDB and initialize Beanie with all document models."""
    global _client

    # Imported here to avoid circular imports during module load.
    from app.services.user.models import OrganizationDocument, UserDocument

    _client = AsyncIOMotorClient(settings.mongo_uri)
    db = _client.get_default_database()

    await init_beanie(
        database=db,  # type: ignore
        document_models=[
            UserDocument,
            OrganizationDocument,
        ],
    )

    logger.info("✅ MongoDB Connected: %s", _client.address)


async def disconnect_db() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
