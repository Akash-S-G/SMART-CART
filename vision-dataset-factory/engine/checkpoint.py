import os
import json
from typing import Optional
from .context import PipelineContext

class CheckpointManager:
    def __init__(self, checkpoint_dir: str = None):
        self.checkpoint_dir = checkpoint_dir or os.path.join("storage", "logs", "checkpoints")

    def save_checkpoint(self, context: PipelineContext, node_name: str):
        """Save the pipeline context to a checkpoint file for the current node."""
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        filename = f"{context.run_id}_{node_name}.json"
        filepath = os.path.join(self.checkpoint_dir, filename)
        
        # Save the current state
        state_dict = context.to_dict()
        with open(filepath, "w") as f:
            json.dump(state_dict, f, indent=2)
            
        # Also maintain a 'latest' symlink or pointer file for easy resuming
        latest_path = os.path.join(self.checkpoint_dir, f"latest_{context.run_id}.json")
        with open(latest_path, "w") as f:
            json.dump({"run_id": context.run_id, "last_completed_node": node_name, "filepath": filepath}, f, indent=2)

    def load_checkpoint(self, run_id: str, node_name: str) -> Optional[PipelineContext]:
        """Load a pipeline context checkpoint for a specific run and node."""
        filename = f"{run_id}_{node_name}.json"
        filepath = os.path.join(self.checkpoint_dir, filename)
        
        if not os.path.exists(filepath):
            return None
            
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            return PipelineContext.from_dict(data)
        except Exception as e:
            print(f"Error loading checkpoint {filepath}: {e}")
            return None

    def get_latest_checkpoint(self, run_id: str) -> Optional[PipelineContext]:
        """Load the latest checkpoint for a specific run_id."""
        latest_path = os.path.join(self.checkpoint_dir, f"latest_{run_id}.json")
        if not os.path.exists(latest_path):
            return None
            
        try:
            with open(latest_path, "r") as f:
                pointer = json.load(f)
            node_filepath = pointer.get("filepath")
            if os.path.exists(node_filepath):
                with open(node_filepath, "r") as f:
                    data = json.load(f)
                return PipelineContext.from_dict(data)
        except Exception as e:
            print(f"Error loading latest checkpoint for {run_id}: {e}")
        return None
