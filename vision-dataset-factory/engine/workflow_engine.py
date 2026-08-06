import asyncio
import traceback
from typing import Dict, Any, List, Set
from .context import PipelineContext
from .checkpoint import CheckpointManager

class PipelineNode:
    """Base interface for all workflow pipeline stages."""
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config

    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute this node's logic. Must be overridden by subclasses."""
        raise NotImplementedError("Subclasses must implement execute()")

class WorkflowEngine:
    """Manages the registration, dependency sorting, and execution of a pipeline DAG."""
    def __init__(self, pipeline_config: Dict[str, Any], node_instances: Dict[str, PipelineNode]):
        self.pipeline_config = pipeline_config
        self.node_instances = node_instances

    def get_execution_order(self) -> List[str]:
        """Performs topological sorting on pipeline nodes based on their dependencies."""
        pipeline_sec = self.pipeline_config.get("pipeline", {})
        nodes_list = pipeline_sec.get("nodes", [])
        
        # Build adjacency list and dependency counts
        graph = {}
        in_degree = {}
        node_names = set()
        
        for node in nodes_list:
            name = node["name"]
            node_names.add(name)
            if name not in graph:
                graph[name] = []
            if name not in in_degree:
                in_degree[name] = 0
                
            deps = node.get("depends_on", [])
            for dep in deps:
                if dep not in graph:
                    graph[dep] = []
                graph[dep].append(name)
                in_degree[name] = in_degree.get(name, 0) + 1

        # Check for invalid dependencies
        for node in nodes_list:
            for dep in node.get("depends_on", []):
                if dep not in node_names:
                    raise ValueError(f"Node '{node['name']}' depends on undefined node '{dep}'")

        # Kahn's algorithm for topological sorting
        queue = [node for node in node_names if in_degree[node] == 0]
        order = []
        
        while queue:
            # Sort queue to ensure deterministic execution order for nodes at same level
            queue.sort()
            curr = queue.pop(0)
            order.append(curr)
            
            for neighbor in graph.get(curr, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
                    
        if len(order) != len(node_names):
            raise ValueError("Cycle detected in pipeline DAG dependencies!")
            
        return order

    async def run(self, context: PipelineContext, resume: bool = False) -> PipelineContext:
        """Executes the pipeline DAG. Handles resuming and checkpointing."""
        import os
        checkpoint_dir = os.path.join(context.storage_dir, "logs", "checkpoints")
        checkpoint_manager = CheckpointManager(checkpoint_dir)
        
        order = self.get_execution_order()
        print(f"Workflow execution order: {' -> '.join(order)}")
        
        context.telemetry["status"] = "RUNNING"
        
        for node_name in order:
            if resume and node_name in context.completed_nodes:
                print(f"Node '{node_name}' already completed in checkpoint. Skipping.")
                continue

            node_instance = self.node_instances.get(node_name)
            if not node_instance:
                raise KeyError(f"No execution instance registered for node '{node_name}'")

            print(f"--- Starting Node: {node_name} ---")
            context.start_node(node_name)
            
            # Save checkpoint *before* executing so we record the transition to RUNNING
            checkpoint_manager.save_checkpoint(context, node_name)
            
            # Simple retry loop configuration (default: no retries, 1 attempt)
            retries = node_instance.config.get("retries", 0)
            delay = node_instance.config.get("retry_delay", 2.0)
            
            attempts = retries + 1
            success = False
            error_msg = ""
            
            for attempt in range(1, attempts + 1):
                try:
                    # Run node execution
                    context = await node_instance.execute(context)
                    success = True
                    break
                except Exception as e:
                    error_msg = f"Attempt {attempt}/{attempts} failed: {str(e)}\n{traceback.format_exc()}"
                    print(f"Error executing node '{node_name}': {error_msg}")
                    if attempt < attempts:
                        print(f"Waiting {delay}s before retrying...")
                        await asyncio.sleep(delay)
            
            if success:
                items_proc = context.state.get(f"{node_name}_processed_count", 0)
                items_fail = context.state.get(f"{node_name}_failed_count", 0)
                context.complete_node(node_name, items_processed=items_proc, items_failed=items_fail)
                checkpoint_manager.save_checkpoint(context, node_name)
                print(f"--- Node '{node_name}' Completed Successfully ---\n")
            else:
                context.fail_node(node_name, error_msg)
                checkpoint_manager.save_checkpoint(context, node_name)
                context.finish_pipeline(status="FAILED")
                print(f"--- Node '{node_name}' Failed. Aborting Pipeline. ---\n")
                raise RuntimeError(f"Pipeline node '{node_name}' failed after {attempts} attempts.")
                
        context.finish_pipeline(status="SUCCESS")
        print("Workflow execution completed successfully.")
        return context
