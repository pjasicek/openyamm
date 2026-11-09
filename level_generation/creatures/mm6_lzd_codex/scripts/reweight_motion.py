import runpy,sys,bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
s= (P/'scripts/weights_lizard.py').read_text().replace("work/rig_v4.blend","work/rig_motion_twist.blend").replace("work/rig_v5.blend","work/rig_reweighted.blend")
exec(compile(s,str(P/'scripts/weights_lizard.py'),'exec'))
