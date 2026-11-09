from pathlib import Path
import runpy
p=Path(__file__).resolve().parents[1]
for n in ['export_audit.py','build_lods.py']:runpy.run_path(str(p/'scripts'/n),run_name='__main__')
