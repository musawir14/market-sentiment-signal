import sys
from pathlib import Path

# Add the repo root to Python path so `import src...` works in local + CI runs.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

