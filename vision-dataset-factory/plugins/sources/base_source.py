import os
from typing import Dict, Any, List
from engine.context import PipelineContext
from engine.workflow_engine import PipelineNode
from database.db import get_db_session
from database.models import Source, Product

class BaseSource(PipelineNode):
    """Abstract base class for all product data discovery sources."""
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.source_name = self.config.get("source_name", name)
        self.license = self.config.get("license", "unknown")
        self.website_url = self.config.get("website_url", "")

    async def get_or_create_source(self, db_session) -> Source:
        """Retrieves or registers the source metadata record in the database."""
        src = db_session.query(Source).filter_by(name=self.source_name).first()
        if not src:
            src = Source(
                name=self.source_name,
                website_url=self.website_url,
                license=self.license
            )
            db_session.add(src)
            db_session.commit()
            db_session.refresh(src)
        return src

    async def register_products(self, context: PipelineContext, products_data: List[Dict[str, Any]]) -> int:
        """Registers a list of raw discovered products into the canonical catalog."""
        registered_count = 0
        
        # Open db session
        with get_db_session(context.db_path) as session:
            source = await self.get_or_create_source(session)
            
            for prod in products_data:
                # Check for duplicates by barcode or name/brand if barcode is missing
                existing = None
                barcode = prod.get("barcode")
                if barcode:
                    existing = session.query(Product).filter_by(barcode=barcode, source_id=source.id).first()
                else:
                    existing = session.query(Product).filter_by(
                        canonical_name=prod["name"], 
                        canonical_brand=prod.get("brand"),
                        source_id=source.id
                    ).first()
                    
                if not existing:
                    new_prod = Product(
                        canonical_brand=prod.get("brand"),
                        canonical_name=prod["name"],
                        variant=prod.get("variant"),
                        barcode=barcode,
                        category=prod.get("category"),
                        source_id=source.id,
                        raw_metadata=prod
                    )
                    session.add(new_prod)
                    registered_count += 1
                    
            session.commit()
            
        print(f"[{self.name}] Registered {registered_count} new products out of {len(products_data)} items from '{self.source_name}'.")
        return registered_count

    # Subclasses override this to implement scraping/discovery logic
    async def execute(self, context: PipelineContext) -> PipelineContext:
        raise NotImplementedError("Source plugins must implement execute(context)")
