import runpy,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent
runpy.run_path(str(P/'build_lods.py'),run_name='__main__')
for name in ('finalize_exports.py','audit_exports.py'):
 subprocess.run(['python3',str(P/name)],check=True)
runpy.run_path(str(P/'lod_visual.py'),run_name='__main__')
