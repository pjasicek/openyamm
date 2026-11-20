"""Replay measured anatomy, rig construction and isolated deformation probes."""
from pathlib import Path
import runpy
P=Path(__file__).resolve().parents[1]
for name in ('fit_anatomy.py','build_rig.py','probe_rig.py'):
 print('STAGE',name,flush=True);runpy.run_path(str(P/'scripts'/name),run_name='__main__')
