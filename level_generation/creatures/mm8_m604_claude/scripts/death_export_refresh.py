from pathlib import Path
import runpy
p=Path(__file__).resolve().parents[1]
for n in ['ground_final.py','export_runtime.py','death_source_jerk.py','changed_checks.py']:runpy.run_path(str(p/'scripts'/n),run_name='__main__')
