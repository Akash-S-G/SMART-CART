import os
import pytest
import asyncio
import tempfile
import shutil
from engine.context import PipelineContext
from engine.workflow_engine import WorkflowEngine, PipelineNode
from engine.checkpoint import CheckpointManager

# Mock Pipeline Node
class MockNode(PipelineNode):
    async def execute(self, context: PipelineContext) -> PipelineContext:
        context.state[self.name] = "executed"
        # Increment counter in state
        context.state[f"{self.name}_processed_count"] = 1
        return context

class MockFailNode(PipelineNode):
    async def execute(self, context: PipelineContext) -> PipelineContext:
        raise ValueError("Simulated failure")

def test_topological_sort():
    config = {
        "pipeline": {
            "name": "test_sort",
            "nodes": [
                {"name": "D", "plugin": "mock", "depends_on": ["B", "C"]},
                {"name": "A", "plugin": "mock", "depends_on": []},
                {"name": "B", "plugin": "mock", "depends_on": ["A"]},
                {"name": "C", "plugin": "mock", "depends_on": ["A"]}
            ]
        }
    }
    engine = WorkflowEngine(config, {})
    order = engine.get_execution_order()
    
    # A must come before B and C; B and C must come before D
    assert order.index("A") < order.index("B")
    assert order.index("A") < order.index("C")
    assert order.index("B") < order.index("D")
    assert order.index("C") < order.index("D")

def test_cycle_detection():
    config = {
        "pipeline": {
            "name": "test_cycle",
            "nodes": [
                {"name": "A", "plugin": "mock", "depends_on": ["B"]},
                {"name": "B", "plugin": "mock", "depends_on": ["A"]}
            ]
        }
    }
    engine = WorkflowEngine(config, {})
    with pytest.raises(ValueError, match="Cycle detected"):
        engine.get_execution_order()

def test_missing_dependency():
    config = {
        "pipeline": {
            "name": "test_missing",
            "nodes": [
                {"name": "A", "plugin": "mock", "depends_on": ["Z"]}
            ]
        }
    }
    engine = WorkflowEngine(config, {})
    with pytest.raises(ValueError, match="depends on undefined node"):
        engine.get_execution_order()

@pytest.mark.asyncio
async def test_workflow_execution_and_checkpoints():
    # Setup temporary directory for test storage
    temp_dir = tempfile.mkdtemp()
    try:
        config = {
            "pipeline": {
                "name": "test_run",
                "storage_dir": temp_dir,
                "nodes": [
                    {"name": "step1", "plugin": "mock", "depends_on": []},
                    {"name": "step2", "plugin": "mock", "depends_on": ["step1"]}
                ]
            }
        }
        
        ctx = PipelineContext(storage_dir=temp_dir, pipeline_config=config)
        
        nodes = {
            "step1": MockNode("step1", {}),
            "step2": MockNode("step2", {})
        }
        
        engine = WorkflowEngine(config, nodes)
        
        # Execute workflow
        result_ctx = await engine.run(ctx)
        
        assert result_ctx.state["step1"] == "executed"
        assert result_ctx.state["step2"] == "executed"
        assert "step1" in result_ctx.completed_nodes
        assert "step2" in result_ctx.completed_nodes
        assert result_ctx.telemetry["status"] == "SUCCESS"
        
        # Verify checkpoint file exists
        checkpoint_dir = os.path.join(temp_dir, "logs", "checkpoints")
        checkpoint_path = os.path.join(checkpoint_dir, f"{ctx.run_id}_step2.json")
        assert os.path.exists(checkpoint_path)
        
        # Verify loading checkpoint
        mgr = CheckpointManager(checkpoint_dir)
        loaded_ctx = mgr.load_checkpoint(ctx.run_id, "step2")
        assert loaded_ctx is not None
        assert loaded_ctx.run_id == ctx.run_id
        assert "step1" in loaded_ctx.completed_nodes
        assert "step2" in loaded_ctx.completed_nodes
        assert loaded_ctx.state["step1"] == "executed"
        
    finally:
        shutil.rmtree(temp_dir)

@pytest.mark.asyncio
async def test_workflow_failure_and_resume():
    temp_dir = tempfile.mkdtemp()
    try:
        config = {
            "pipeline": {
                "name": "test_fail",
                "storage_dir": temp_dir,
                "nodes": [
                    {"name": "ok_step", "plugin": "mock", "depends_on": []},
                    {"name": "fail_step", "plugin": "mock", "depends_on": ["ok_step"]}
                ]
            }
        }
        
        ctx = PipelineContext(storage_dir=temp_dir, pipeline_config=config)
        
        nodes = {
            "ok_step": MockNode("ok_step", {}),
            "fail_step": MockFailNode("fail_step", {})
        }
        
        engine = WorkflowEngine(config, nodes)
        
        # Execution should raise RuntimeError due to node failure
        with pytest.raises(RuntimeError):
            await engine.run(ctx)
            
        # Checkpoint for ok_step should exist, but fail_step should not be completed
        checkpoint_dir = os.path.join(temp_dir, "logs", "checkpoints")
        assert os.path.exists(os.path.join(checkpoint_dir, f"{ctx.run_id}_ok_step.json"))
        
        # Load latest checkpoint (should have ok_step completed)
        mgr = CheckpointManager(checkpoint_dir)
        resume_ctx = mgr.get_latest_checkpoint(ctx.run_id)
        assert resume_ctx is not None
        assert "ok_step" in resume_ctx.completed_nodes
        assert "fail_step" not in resume_ctx.completed_nodes
        
        # Swap node behavior for fail_step so it succeeds on resume
        nodes["fail_step"] = MockNode("fail_step", {})
        
        # Execute resuming
        resumed_result = await engine.run(resume_ctx, resume=True)
        assert "ok_step" in resumed_result.completed_nodes
        assert "fail_step" in resumed_result.completed_nodes
        assert resumed_result.state["fail_step"] == "executed"
        assert resumed_result.telemetry["status"] == "SUCCESS"
        
    finally:
        shutil.rmtree(temp_dir)
