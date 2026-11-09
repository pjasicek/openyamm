"""Driver: fix_cuffs.py, fix_legs.py (both idempotent) and export_runtime.py on the textured master, without
re-authoring any clip."""
import runpy, sys
from pathlib import Path
P = Path(__file__).resolve().parents[1]
for n in ('fix_cuffs.py', 'fix_legs.py', 'export_runtime.py'):
    sys.argv = [n]; runpy.run_path(str(P / 'scripts' / n), run_name='__main__')
