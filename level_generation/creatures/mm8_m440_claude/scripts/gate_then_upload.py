from pathlib import Path
import runpy
p=Path(__file__).resolve().parents[1]
try:runpy.run_path(str(p/"scripts/run_full_gates.py"),run_name="__main__")
except SystemExit as e:
 if e.code:raise
runpy.run_path(str(p/"scripts/export_uploads.py"),run_name="__main__")
