import os,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];os.chdir(p);sys.path.insert(0,str(p/'scripts'))
def run(name,args=()):
 sys.argv=[name,'--']+[str(x) for x in args];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
run('reduce_rigged.py',[p/'work/rig_v4f.blend',p/'work/rig_v4.blend'])
os.environ['GRIP_RENDER']=str(p/'review/grip')
run('grip_solve.py',[p/'work/rig_v4.blend','Walking','6'])
run('apply_grip.py',[p/'work/rig_v4.blend',p/'work/rig_v5.blend'])
run('polish_arm_weights.py')
run('g5_hand_stretch.py',[p/'work/rig_v5.blend','Standing','Walking','Running','Attack','Hit','Death','Fidget'])
run('clip_sheet.py',[p/'work/rig_v5.blend',p/'review/clay_first','three_quarter','6','Standing','Walking','Attack','Hit','Death'])
