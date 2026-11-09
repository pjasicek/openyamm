from pathlib import Path
import runpy
p=Path(__file__).resolve().parents[1]
for name in ('measure_runtime.py','build_lods.py'):
 runpy.run_path(str(p/'scripts'/name),run_name='__main__')
