from pathlib import Path
import bpy,runpy,subprocess
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/finish_head_atlas.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/export_audit.py'),run_name='__main__')
bpy.ops.wm.read_factory_settings(use_empty=True)
runpy.run_path(str(p/'scripts/build_lods.py'),run_name='__main__')
subprocess.run(['python3',str(p/'scripts/finish_runtime.py')],check=True)
