import bpy,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/review_body_clips.py'),run_name='__main__')
