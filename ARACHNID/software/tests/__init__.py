import sys
from pathlib import Path

# Add project root (software/) to sys.path
SOFTWARE_ROOT = str(Path(__file__).resolve().parent.parent)
if SOFTWARE_ROOT not in sys.path:
    sys.path.insert(0, SOFTWARE_ROOT)
