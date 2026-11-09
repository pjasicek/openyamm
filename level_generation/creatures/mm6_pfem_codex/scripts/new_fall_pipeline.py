import runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for n in ('retarget_pilots.py','ground_feet.py','build_native_base.py','review_body_clips.py','build_skirt.py'):
 runpy.run_path(str(p/'scripts'/n),run_name='__main__')
