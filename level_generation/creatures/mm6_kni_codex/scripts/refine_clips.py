import sys,os,runpy,bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.path.insert(0,str(P/'scripts'))
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
mx=P.parents[2]/'anim_library/mixamo/Standing Idle 02 Looking.fbx'
run('retarget_mixamo.py',['work/rig_v2.blend','work/rig_v2new.blend',f'{mx}:Fidget:plant',f'{mx}:FidgetFull:turn'])
run('twist_bones.py',['work/rig_v2new.blend','work/rig_v2t.blend'])
run('armour_weights.py');run('finger_weights.py',['work/rig_v3.blend','work/rig_v4.blend'])
run('apply_grip.py',['work/rig_v4.blend','work/rig_v6.blend']);run('clip_timing.py')
run('g4_weights.py',['work/rig_v6t.blend','probe','Attack:10','Hit:6','Fidget:30'])
run('g6_contacts.py',['work/rig_v6t.blend','Standing','Walking','Attack','Hit','Fidget'])
run('g6_head_clearance.py',['work/rig_v6t.blend','Attack','Hit','Fidget'])
