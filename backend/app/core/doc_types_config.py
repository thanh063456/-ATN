import os
import yaml
from pydantic import BaseModel, ValidationError
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class DocSubTypeConfig(BaseModel):
    code: str
    keywords: list[str] = []

class DocTypeConfig(BaseModel):
    code: str
    name: str
    group: str
    title_patterns: list[str] = []
    so_hieu_patterns: list[str] = []
    body_hints: list[str] = []
    subtypes: list[DocSubTypeConfig] = []

class DocTypesRoot(BaseModel):
    types: list[DocTypeConfig]

# Load and validate on import
YAML_PATH = os.path.join(os.path.dirname(__file__), "doc_types.yaml")

def load_doc_types() -> DocTypesRoot:
    try:
        with open(YAML_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        if not data:
            raise ValueError(f"Empty YAML file: {YAML_PATH}")
            
        return DocTypesRoot(**data)
    except FileNotFoundError:
        logger.critical(f"doc_types.yaml not found at {YAML_PATH}")
        raise
    except ValidationError as e:
        logger.critical(f"Validation error in doc_types.yaml: {e}")
        raise
    except yaml.YAMLError as e:
        logger.critical(f"YAML parsing error in doc_types.yaml: {e}")
        raise

DOC_TYPES_CONFIG = load_doc_types()
DOC_TYPES_MAP = {t.code: t for t in DOC_TYPES_CONFIG.types}

async def seed_document_categories(session: AsyncSession) -> None:
    """
    Idempotent seeder: upserts doc types into document_categories table.
    Does not delete existing rows.
    """
    from app.models.document_categories import DocumentCategory
    
    logger.info(f"Seeding {len(DOC_TYPES_CONFIG.types)} document categories...")
    
    # Get existing categories
    result = await session.execute(select(DocumentCategory))
    existing_cats = result.scalars().all()
    existing_map = {c.code: c for c in existing_cats}
    
    new_cats = []
    updated_cats = 0
    
    for t in DOC_TYPES_CONFIG.types:
        if t.code in existing_map:
            # Update name if changed (optional, but good for idempotent updates)
            cat = existing_map[t.code]
            if cat.name != t.name:
                cat.name = t.name
                updated_cats += 1
        else:
            new_cat = DocumentCategory(
                code=t.code,
                name=t.name,
                description=f"Auto-seeded from doc_types.yaml (Group: {t.group})"
            )
            session.add(new_cat)
            new_cats.append(new_cat)
            
    if new_cats or updated_cats > 0:
        await session.commit()
        logger.info(f"Seeded {len(new_cats)} new categories, updated {updated_cats} existing categories.")
    else:
        logger.info("No new categories to seed.")
