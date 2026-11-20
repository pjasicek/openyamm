"""Fit the last gesture and rebuild/audit the resulting editable masters in one isolated Blender process."""
from pathlib import Path
import runpy
import sys
S = Path(__file__).resolve().parent
for name, args in [('finalize_authoring.py', []),
                   ('probe_hand_gate.py', []), ('audit_authoring.py', [])]:
    sys.argv = [str(S / name), '--', *args]
    runpy.run_path(str(S / name), run_name='__main__')
