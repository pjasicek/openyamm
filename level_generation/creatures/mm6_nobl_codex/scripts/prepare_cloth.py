import os,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];os.chdir(p);sys.path.insert(0,str(p/'scripts'))
for n in ['prepare_clips.py','clip_timing.py','cloak_rig.py']:
 sys.argv=[n,'--'];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
