"""Refresh the final editable project, scale, head-look clearance and LOD review stills."""
import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for name in ('run_full_gates.py','editable_delivery.py','measure_scale.py','head_look_clearance.py','lod_visual.py'):
 runpy.run_path(str(P/name),run_name='__main__')
