from __future__ import annotations

from config import get_settings
from storage.base import Storage
from storage.memory import MemoryStorage

_instance: Storage | None = None


def get_storage() -> Storage:
    global _instance
    if _instance is None:
        settings = get_settings()
        if settings.storage_backend == "firestore":
            from storage.firestore import FirestoreStorage

            _instance = FirestoreStorage(
                project=settings.gcloud_project,
                database=settings.firestore_database,
            )
        else:
            _instance = MemoryStorage()
    return _instance


def reset_storage(storage: Storage | None = None) -> None:
    """Replace the process-wide storage. Used by tests and nothing else."""
    global _instance
    _instance = storage
