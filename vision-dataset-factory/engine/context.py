import os
import uuid
import time
from typing import Dict, Any, List, Set

class PipelineContext:
    def __init__(self, run_id: str = None, storage_dir: str = "storage", pipeline_config: Dict[str, Any] = None):
        self.run_id = run_id or str(uuid.uuid4())
        self.storage_dir = storage_dir
        self.db_path = os.path.join(storage_dir, "vdf.db")
        self.pipeline_config = pipeline_config or {}
        
        # Shared intermediate state between nodes
        self.state: Dict[str, Any] = {}
        
        # Track completed nodes for resuming
        self.completed_nodes: Set[str] = set()
        
        # Observability & telemetry metrics
        self.telemetry: Dict[str, Any] = {
            "run_id": self.run_id,
            "pipeline_name": self.pipeline_config.get("pipeline", {}).get("name", "unnamed"),
            "start_time": time.time(),
            "end_time": None,
            "duration": 0.0,
            "status": "RUNNING",
            "nodes": {}
        }

    def start_node(self, node_name: str):
        self.telemetry["nodes"][node_name] = {
            "status": "RUNNING",
            "start_time": time.time(),
            "end_time": None,
            "duration": 0.0,
            "error": None,
            "items_processed": 0,
            "items_failed": 0
        }

    def complete_node(self, node_name: str, items_processed: int = 0, items_failed: int = 0):
        node_tel = self.telemetry["nodes"].get(node_name, {})
        node_tel["status"] = "SUCCESS"
        node_tel["end_time"] = time.time()
        node_tel["duration"] = node_tel["end_time"] - node_tel["start_time"]
        node_tel["items_processed"] = items_processed
        node_tel["items_failed"] = items_failed
        self.completed_nodes.add(node_name)

    def fail_node(self, node_name: str, error_msg: str):
        node_tel = self.telemetry["nodes"].get(node_name, {})
        node_tel["status"] = "FAILED"
        node_tel["end_time"] = time.time()
        if "start_time" in node_tel and node_tel["start_time"]:
            node_tel["duration"] = node_tel["end_time"] - node_tel["start_time"]
        node_tel["error"] = error_msg

    def finish_pipeline(self, status: str = "SUCCESS"):
        self.telemetry["status"] = status
        self.telemetry["end_time"] = time.time()
        self.telemetry["duration"] = self.telemetry["end_time"] - self.telemetry["start_time"]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize context to JSON-safe dictionary for checkpointing."""
        return {
            "run_id": self.run_id,
            "storage_dir": self.storage_dir,
            "pipeline_config": self.pipeline_config,
            "state": self.state,
            "completed_nodes": list(self.completed_nodes),
            "telemetry": self.telemetry
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PipelineContext":
        """Reconstruct context from a serialized dictionary."""
        ctx = cls(
            run_id=d.get("run_id"),
            storage_dir=d.get("storage_dir", "storage"),
            pipeline_config=d.get("pipeline_config")
        )
        ctx.state = d.get("state", {})
        ctx.completed_nodes = set(d.get("completed_nodes", []))
        ctx.telemetry = d.get("telemetry", {})
        return ctx
