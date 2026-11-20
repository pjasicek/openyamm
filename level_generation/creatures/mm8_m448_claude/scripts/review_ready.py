from pathlib import Path
import runpy
p=Path(__file__).resolve().parents[1]
for name in ('fit_ready.py','export_runtime.py','review_textured.py'):
 runpy.run_path(str(p/'scripts'/name),run_name='__main__')
