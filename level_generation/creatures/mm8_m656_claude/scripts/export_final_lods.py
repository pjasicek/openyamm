import runpy,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2]
runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
subprocess.run(['python3',str(R/'tools/prepare_actor_glb.py'),str(P/'export/mm8_m656_lod0.glb'),str(P/'export/mm8_m656_prepared.glb')],check=True)
runpy.run_path(str(P/'scripts/lods_and_parity.py'),run_name='__main__')
