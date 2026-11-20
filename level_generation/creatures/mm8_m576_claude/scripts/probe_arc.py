import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parent
for name in ('quick_rig_probe.py','calibrate_hand_axes.py','arc_contact_probe.py'):
 sys.argv=[name];runpy.run_path(str(P/name),run_name='__main__')
