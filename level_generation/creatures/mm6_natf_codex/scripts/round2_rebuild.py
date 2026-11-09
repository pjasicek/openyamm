"""Rebuild motion from cached round2_motion and selected fitted geometry; then run finalize_runtime.py."""
import runpy
from pathlib import Path
p = Path(__file__).resolve().parent
for name in ['round2_fit_motion.py', 'round2_cloth.py', 'round2_drop_shield.py', 'round2_export.py', 'final_sheets.py']:
    runpy.run_path(str(p / name), run_name='__main__')
