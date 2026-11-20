import runpy,subprocess
from pathlib import Path
p=Path(__file__).resolve().parents[1]
subprocess.run(['/usr/bin/python3','tools/prepare_actor_glb.py',str(p/'export/mm6_pman_v2_lod0.glb'),str(p/'export/mm6_pman_v2_runtime_lod0.glb')],check=True)
runpy.run_path(str(p/'scripts/build_lods.py'),run_name='__main__')
subprocess.run(['/usr/bin/python3',str(p/'scripts/assemble_runtime.py')],check=True)
