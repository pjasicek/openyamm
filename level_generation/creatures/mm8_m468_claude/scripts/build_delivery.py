from pathlib import Path
import subprocess,runpy,bpy
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/export_runtime.py'),run_name='__main__')
subprocess.run(['python3','tools/prepare_actor_glb.py',str(p/'export/mm8_m468_lod0.glb'),str(p/'export/mm8_m468_runtime_lod0.glb')],check=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
runpy.run_path(str(p/'scripts/build_lods.py'),run_name='__main__')
subprocess.run(['python3',str(p/'scripts/finish_runtime.py')],check=True)
runpy.run_path(str(p/'scripts/run_final_gates.py'),run_name='__main__')
