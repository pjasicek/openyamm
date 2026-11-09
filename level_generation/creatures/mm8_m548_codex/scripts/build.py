"""Rebuild source exports and runtime LODs from the selected animated master."""
from pathlib import Path
import runpy,subprocess
P=Path(__file__).resolve().parents[1];R=P.parents[2]
runpy.run_path(str(P/'scripts/export.py'),run_name='__main__')
subprocess.run(['/usr/bin/python3',str(R/'tools/prepare_actor_glb.py'),str(P/'export/mm8_m548_lod0.glb'),str(P/'export/mm8_m548_prepared.glb')],check=True)
runpy.run_path(str(P/'scripts/build_lods.py'),run_name='__main__')
subprocess.run(['/usr/bin/python3',str(P/'scripts/finish_runtime.py')],check=True)
