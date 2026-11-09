from pathlib import Path
import runpy
p=Path(__file__).resolve().parents[1]
for name in ['build_lods.py','revision_export_checks.py']:
 runpy.run_path(str(p/'scripts'/name),run_name='__main__')
