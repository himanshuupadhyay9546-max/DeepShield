import sys
from pathlib import Path
import pytest

# Add project root and backend root to sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"

for path_str in [str(root_dir), str(backend_dir)]:
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from backend.app.db.session import init_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure database schema and all tables are initialized for test runs."""
    init_db()

