from pathlib import Path
import runpy
p=Path(__file__).resolve().parents[1]
for name in ('make_sword.py','finish_poses.py','export_runtime.py'):
    runpy.run_path(str(p/'scripts'/name),run_name='__main__')
