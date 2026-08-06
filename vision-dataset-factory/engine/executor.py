import os
import sys
import argparse
import asyncio
from typing import Dict, Any

# Ensure project root is in PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
from engine.context import PipelineContext
from engine.workflow_engine import WorkflowEngine, PipelineNode
from engine.checkpoint import CheckpointManager
from database.db import init_db

# Registry maps plugin string identifiers to module paths and class names
# This satisfies the requirement that new plugins can be added by implementing
# an interface and updating configs.
PLUGIN_REGISTRY = {
    "sources.openfoodfacts": ("plugins.sources.openfoodfacts", "OpenFoodFactsSource"),
    "sources.local_folder": ("plugins.sources.local_folder", "LocalFolderSource"),
    "downloader": ("downloader.downloader", "DownloaderNode"),
    "deduplication": ("dedup.dedup", "DeduplicationNode"),
    "quality_check": ("quality.quality", "QualityCheckNode"),
    "auto_annotation": ("plugins.annotators.annotation_node", "AnnotationNode"),
    "yolo_exporter": ("plugins.exporters.yolo", "YoloExporterNode"),
}

def resolve_plugin_class(plugin_name: str) -> type:
    """Dynamically imports and returns the plugin class from registry or module path."""
    if plugin_name in PLUGIN_REGISTRY:
        module_path, class_name = PLUGIN_REGISTRY[plugin_name]
    else:
        # Fallback: support dynamic custom plugin paths, e.g. "plugins.my_custom_plugin.MyClass"
        if "." not in plugin_name:
            raise ValueError(f"Plugin name '{plugin_name}' not recognized and cannot be dynamically parsed.")
        parts = plugin_name.split(".")
        class_name = parts[-1]
        module_path = ".".join(parts[:-1])
        
    try:
        import importlib
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except Exception as e:
        raise ImportError(f"Failed to load plugin '{plugin_name}' (module: {module_path}, class: {class_name}): {e}")

def load_pipeline_config(config_path: str) -> Dict[str, Any]:
    """Loads the pipeline configuration from a YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Pipeline config file not found: {config_path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

async def main_async():
    parser = argparse.ArgumentParser(description="Vision Dataset Factory Workflow Executor")
    parser.add_argument("--config", type=str, default="configs/pipeline.yaml", help="Path to pipeline YAML configuration")
    parser.add_argument("--resume", type=str, default=None, help="Run ID of the pipeline checkpoint to resume")
    parser.add_argument("--storage", type=str, default=None, help="Override storage root directory path")
    args = parser.parse_args()

    # 1. Load pipeline configuration
    try:
        config = load_pipeline_config(args.config)
    except Exception as e:
        print(f"Failed to load config: {e}")
        sys.exit(1)

    # 2. Setup storage directory
    pipeline_sec = config.get("pipeline", {})
    storage_dir = args.storage or pipeline_sec.get("storage_dir", "storage")
    os.makedirs(storage_dir, exist_ok=True)

    # Create sub-folders as per design layout
    subfolders = ["raw", "normalized", "quality", "annotations", "datasets", "exports", "models", "artifacts", "logs"]
    for folder in subfolders:
        os.makedirs(os.path.join(storage_dir, folder), exist_ok=True)

    # 3. Initialize isolated database (SQLite)
    db_path = os.path.join(storage_dir, "vdf.db")
    print(f"Initializing VDF database at {db_path}...")
    init_db(db_path)

    # 4. Instantiate context
    checkpoint_mgr = CheckpointManager(checkpoint_dir=os.path.join(storage_dir, "logs", "checkpoints"))
    
    if args.resume:
        print(f"Attempting to resume pipeline execution for Run ID: {args.resume}")
        context = checkpoint_mgr.get_latest_checkpoint(args.resume)
        if not context:
            print(f"No checkpoint found for Run ID '{args.resume}'. Starting fresh.")
            context = PipelineContext(storage_dir=storage_dir, pipeline_config=config)
            resume_flag = False
        else:
            print(f"Checkpoint loaded successfully. Last completed nodes: {list(context.completed_nodes)}")
            resume_flag = True
    else:
        context = PipelineContext(storage_dir=storage_dir, pipeline_config=config)
        resume_flag = False

    # 5. Instantiate pipeline nodes dynamically
    node_instances: Dict[str, PipelineNode] = {}
    nodes_config = pipeline_sec.get("nodes", [])
    
    for node_cfg in nodes_config:
        node_name = node_cfg["name"]
        plugin_name = node_cfg["plugin"]
        node_spec_cfg = node_cfg.get("config", {})
        
        try:
            plugin_cls = resolve_plugin_class(plugin_name)
            node_instances[node_name] = plugin_cls(node_name, node_spec_cfg)
        except Exception as e:
            print(f"Error initializing node '{node_name}' with plugin '{plugin_name}': {e}")
            sys.exit(1)

    # 6. Instantiate Workflow Engine and execute
    engine = WorkflowEngine(config, node_instances)
    
    try:
        await engine.run(context, resume=resume_flag)
    except Exception as e:
        print(f"Pipeline execution aborted: {e}")
        sys.exit(1)

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
