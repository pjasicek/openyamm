from pathlib import Path
import runpy
s=Path(__file__).resolve().parent
for name in ('g7_export.py','export_uploads.py'):runpy.run_path(str(s/name),run_name='__main__')
