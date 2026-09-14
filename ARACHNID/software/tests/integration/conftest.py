import sys
from pathlib import Path

SOFTWARE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(SOFTWARE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOFTWARE_ROOT))
