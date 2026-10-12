"""Utility to re-embed all existing article_chunks in Firestore using Vertex AI."""

import asyncio
import logging
from google.oauth2.credentials import Credentials
from google.cloud import firestore
import subprocess

from ingestion.embedder import VertexAIEmbedder, _get_gcloud_token

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("reembed")


async def main() -> None:
    token = _get_gcloud_token()
    creds = Credentials(token)

    project_id = "project-philip-501910"
    db_name = "tanya-iman"

    db = firestore.AsyncClient(project=project_id, database=db_name, credentials=creds)
    embedder = VertexAIEmbedder(project_id=project_id)

    coll = db.collection("article_chunks")
    docs = [d async for d in coll.stream()]
    logger.info("Found %d article_chunks in Firestore to re-embed", len(docs))

    # Process in batches of 10
    batch_size = 10
    for i in range(0, len(docs), batch_size):
        chunk_docs = docs[i : i + batch_size]
        texts = [doc.to_dict().get("text", "") for doc in chunk_docs]

        logger.info("Embedding batch %d..%d / %d...", i + 1, min(i + batch_size, len(docs)), len(docs))
        vectors = await embedder.embed_texts(texts)

        for doc, vec in zip(chunk_docs, vectors, strict=True):
            await doc.reference.update(
                {
                    "embedding": vec,
                    "embedding_model": embedder.model_name,
                }
            )

    logger.info("Successfully re-embedded and updated all %d chunks in Firestore!", len(docs))


if __name__ == "__main__":
    asyncio.run(main())
