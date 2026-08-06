"""Allow `python -m seed run ...`."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
for p in (str(HERE), str(BACKEND)):
    if p not in sys.path:
        sys.path.insert(0, p)

from run import main

if __name__ == "__main__":
    raise SystemExit(main())
