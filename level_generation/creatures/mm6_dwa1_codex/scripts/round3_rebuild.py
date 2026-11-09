import bpy,runpy,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
subprocess.run(['/usr/bin/python3',str(P/'scripts/round3_package_lod0.py')],check=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
runpy.run_path(str(P/'scripts/build_lods.py'),run_name='__main__')
subprocess.run(['/usr/bin/python3',str(P/'scripts/package_lods.py')],check=True)
runpy.run_path(str(P/'scripts/import_final.py'),run_name='__main__')
