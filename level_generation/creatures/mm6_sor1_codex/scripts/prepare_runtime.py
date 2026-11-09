import subprocess
from pathlib import Path
p=Path(__file__).resolve().parents[1]
r=subprocess.run(['python3',str(p.parents[2]/'tools/prepare_actor_glb.py'),str(p/'export/mm6_sor1_lod0.glb'),str(p/'export/mm6_sor1_runtime_lod0.glb')],check=True,capture_output=True,text=True)
(p/'work/prepare_runtime.log').write_text(r.stdout+r.stderr);print(r.stdout)
