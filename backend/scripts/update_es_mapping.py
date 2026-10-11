import asyncio
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app.core.elasticsearch import get_es_client, INDEX_NAME, INDEX_MAPPINGS

async def update_mapping():
    es = get_es_client()
    try:
        # Update mapping
        await es.indices.put_mapping(
            index=INDEX_NAME,
            properties=INDEX_MAPPINGS["properties"]
        )
        print("Successfully updated Elasticsearch mapping with document_type and document_subtype.")
    except Exception as e:
        print(f"Failed to update mapping: {e}")

if __name__ == "__main__":
    asyncio.run(update_mapping())
