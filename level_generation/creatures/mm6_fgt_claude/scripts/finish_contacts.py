from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for name in ('build_native_prop.py','g6_audit.py'):
 runpy.run_path(str(p/name),run_name='__main__')

runpy.run_path(str(p/'g7_export.py'),run_name='__main__')
runpy.run_path(str(p/'export_uploads.py'),run_name='__main__')
