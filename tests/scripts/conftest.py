"""Make the ``scripts/`` directory importable so tests can load ``unprocessed_audit`` and ``generate_registry_status_reports``."""
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
