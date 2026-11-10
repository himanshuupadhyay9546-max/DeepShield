import sys
from pathlib import Path

# Add project root and backend root to sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"

for path_str in [str(root_dir), str(backend_dir)]:
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
