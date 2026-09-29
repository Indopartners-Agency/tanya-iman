"""Database seeder.

Populates the 13 canonical topics (and 'lainnya' fallback) from config/topics.yml
and initial system_config values into the configured storage backend.
Idempotent: safe to run multiple times without overwriting curated answers.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.loader import topics as load_topics
from models import SystemConfig, Topic
from storage import Storage, get_storage

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_CONFIG = {
    "retention_months": "12",
    "rate_limit_per_hour": "30",
    "similarity_threshold": "0.72",
}


async def seed_database(storage: Storage) -> None:
    now = datetime.now(UTC)

    # 1. Seed topics
    raw_topics = load_topics()
    for item in raw_topics:
        slug = item["slug"]
        existing = await storage.get_topic(slug)
        if existing is None:
            topic = Topic(
                slug=slug,
                name_id=item["name_id"],
                name_en=item["name_en"],
                curated_status="draft",
                updated_at=now,
            )
            await storage.save_topic(topic)
            logger.info("Created topic: %s", slug)
        else:
            # Preserve editorial curation and counters, update localized names
            existing.name_id = item["name_id"]
            existing.name_en = item["name_en"]
            await storage.save_topic(existing)
            logger.debug("Preserved existing topic: %s", slug)

    # 2. Seed system_config
    for key, value in DEFAULT_SYSTEM_CONFIG.items():
        existing_cfg = await storage.get_system_config(key)
        if existing_cfg is None:
            cfg = SystemConfig(
                key=key,
                value=value,
                updated_at=now,
            )
            await storage.set_system_config(cfg)
            logger.info("Initialized system_config: %s = %s", key, value)
        else:
            logger.debug("Preserved existing system_config: %s", key)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    storage = get_storage()
    logger.info("Seeding database using storage: %s", type(storage).__name__)
    await seed_database(storage)
    logger.info("Database seeding completed.")


if __name__ == "__main__":
    asyncio.run(main())
