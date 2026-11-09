import runpy
from pathlib import Path
p=Path(__file__).parent
for n in ['rig_bone_dragon.py','animate_bone_dragon.py','pilot_audit.py']:runpy.run_path(str(p/n),run_name='__main__')
