import sys
from pathlib import Path

SOFTWARE_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if SOFTWARE_ROOT not in sys.path:
    sys.path.insert(0, SOFTWARE_ROOT)
