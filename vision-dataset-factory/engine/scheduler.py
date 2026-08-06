import asyncio
import time
import subprocess
import sys
from typing import Dict, Any

class WorkflowScheduler:
    """A lightweight scheduler to trigger pipeline executions periodically."""
    def __init__(self, config_path: str, interval_seconds: int):
        self.config_path = config_path
        self.interval_seconds = interval_seconds
        self.running = False

    async def start(self):
        self.running = True
        print(f"Starting VDF Scheduler. Running '{self.config_path}' every {self.interval_seconds} seconds.")
        while self.running:
            print(f"\n[Scheduler] Triggering pipeline run at {time.strftime('%Y-%m-%d %H:%M:%S')}...")
            try:
                # Spawn execution as a subprocess to keep logs/memory separate
                process = await asyncio.create_subprocess_exec(
                    sys.executable, "-m", "engine.executor", "--config", self.config_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    print("[Scheduler] Pipeline execution completed successfully.")
                else:
                    print(f"[Scheduler] Pipeline execution failed with code {process.returncode}.")
                    print(f"[Scheduler] Error output:\n{stderr.decode()}")
            except Exception as e:
                print(f"[Scheduler] Error running scheduled job: {e}")

            print(f"[Scheduler] Next execution in {self.interval_seconds}s...")
            await asyncio.sleep(self.interval_seconds)

    def stop(self):
        self.running = False
        print("Stopping VDF Scheduler.")

if __name__ == "__main__":
    # Example scheduling execution
    import argparse
    parser = argparse.ArgumentParser(description="VDF Pipeline Scheduler")
    parser.add_argument("--config", type=str, default="configs/pipeline.yaml", help="Path to config")
    parser.add_argument("--interval", type=int, default=3600, help="Interval in seconds (default: 1 hour)")
    args = parser.parse_args()

    scheduler = WorkflowScheduler(args.config, args.interval)
    try:
        asyncio.run(scheduler.start())
    except KeyboardInterrupt:
        scheduler.stop()
