import os
import pytest
import tempfile
import shutil
import json
from engine.context import PipelineContext
from database.db import init_db, get_db_session
from database.models import Product, Source
from plugins.sources.openfoodfacts import OpenFoodFactsSource
from plugins.sources.local_folder import LocalFolderSource

# Subclass OpenFoodFactsSource to mock API calls
class MockOpenFoodFactsSource(OpenFoodFactsSource):
    def _fetch_category_sync(self, category: str) -> list:
        # Return mock API results
        return [
            {
                "product_name": "Mock Cola 500ml",
                "brands": "Mock Brand",
                "quantity": "500ml",
                "code": "1234567890123",
                "image_front_url": "http://mock.url/cola.jpg"
            }
        ]

@pytest.mark.asyncio
async def test_openfoodfacts_source():
    temp_dir = tempfile.mkdtemp()
    
    try:
        config = {
            "pipeline": {
                "name": "test_off",
                "storage_dir": temp_dir,
                "nodes": []
            }
        }
        ctx = PipelineContext(storage_dir=temp_dir, pipeline_config=config)
        init_db(ctx.db_path)
        
        # Instantiate mock plugin
        plugin = MockOpenFoodFactsSource("discover", {
            "categories": ["beverages"],
            "limit_per_category": 1
        })
        
        # Execute plugin
        result_ctx = await plugin.execute(ctx)
        
        # Verify state output
        discovered = result_ctx.state.get("discovered_products", [])
        assert len(discovered) == 1
        assert discovered[0]["name"] == "Mock Cola 500ml"
        assert discovered[0]["barcode"] == "1234567890123"
        assert len(discovered[0]["image_urls"]) == 1
        
        # Verify db insertion
        with get_db_session(ctx.db_path) as session:
            products = session.query(Product).all()
            assert len(products) == 1
            assert products[0].canonical_name == "Mock Cola 500ml"
            assert products[0].barcode == "1234567890123"
            
            src = session.query(Source).first()
            assert src.name == "openfoodfacts"
            assert products[0].source_id == src.id
            
    finally:
        shutil.rmtree(temp_dir)

@pytest.mark.asyncio
async def test_local_folder_source_with_folders():
    temp_dir = tempfile.mkdtemp()
    
    try:
        config = {
            "pipeline": {
                "name": "test_local",
                "storage_dir": temp_dir,
                "nodes": []
            }
        }
        ctx = PipelineContext(storage_dir=temp_dir, pipeline_config=config)
        init_db(ctx.db_path)
        
        # Setup mock directory structure:
        # temp_dir/raw_local/
        #   Product A/
        #     image1.jpg
        #     image2.png
        raw_local_dir = os.path.join(temp_dir, "raw_local")
        os.makedirs(raw_local_dir)
        
        prod_a_dir = os.path.join(raw_local_dir, "Product A")
        os.makedirs(prod_a_dir)
        
        # Create dummy image files
        with open(os.path.join(prod_a_dir, "image1.jpg"), "w") as f:
            f.write("dummy content")
        with open(os.path.join(prod_a_dir, "image2.png"), "w") as f:
            f.write("dummy content")
        with open(os.path.join(prod_a_dir, "not_image.txt"), "w") as f:
            f.write("txt content")
            
        plugin = LocalFolderSource("discover_local", {
            "input_dir": raw_local_dir
        })
        
        result_ctx = await plugin.execute(ctx)
        
        discovered = result_ctx.state.get("discovered_products", [])
        assert len(discovered) == 1
        assert discovered[0]["name"] == "Product A"
        assert len(discovered[0]["image_urls"]) == 2
        # Check they are absolute file URLs
        assert discovered[0]["image_urls"][0].startswith("file://")
        
        with get_db_session(ctx.db_path) as session:
            products = session.query(Product).all()
            assert len(products) == 1
            assert products[0].canonical_name == "Product A"
            
    finally:
        shutil.rmtree(temp_dir)
