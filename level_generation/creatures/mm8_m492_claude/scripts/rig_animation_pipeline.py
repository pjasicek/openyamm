from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for name in ['rig_dragon.py','add_mouth_fire.py','animate_dragon.py','check_junctions.py']:
 runpy.run_path(str(p/name),run_name='__main__')
