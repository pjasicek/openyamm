import bpy,sys,runpy,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P)
def run(n,*args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('weights_figc.py');run('finger_weights.py',P/'work/rig_v3.blend',P/'work/rig_v4f.blend')
run('grip_from_source_left.py',P.parents[2]/'anim_library/humanoid_set/Armed.glb','ArmedIdle:8')
os.environ['GRIP_RENDER']=str(P/'review/grip_L');run('grip_solve_left.py',P/'work/rig_v4f.blend','GripRef',8);os.environ.pop('GRIP_RENDER')
run('apply_grip.py',P/'work/rig_v4f.blend',P/'work/rig_v5r.blend')
run('apply_grip_left.py',P/'work/rig_v5r.blend',P/'work/rig_v5.blend')
run('reduce_rigged.py',P/'work/rig_v5.blend',P/'work/rig_v6.blend')
run('clip_timing.py')
run('g5_hand_stretch.py',P/'work/rig_v6t.blend','Standing','Walking','Running','Attack','Hit','Fidget','Death')
run('g4_weights.py',P/'work/rig_v6t.blend','timed','Standing:0','Walking:8','Running:8','Attack:14','Attack:23','Attack:32','Hit:6','Fidget:40','Death:45')
