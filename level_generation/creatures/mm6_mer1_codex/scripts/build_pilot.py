import bpy,runpy,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2];L=R/'anim_library/humanoid_set';MX=R/'anim_library/mixamo';os.chdir(P);sys.path.insert(0,str(P/'scripts'))
def run(n,args=()):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('retarget.py',['work/rig_v1.blend','work/pilot_set.blend',f'{L}/Armed.glb:ArmedIdle:GripRef',f'{L}/Armed.glb:ArmedWalk:Walking'])
run('retarget_mixamo.py',['work/pilot_set.blend','work/pilot_raw.blend',f'{MX}/Standard Idle.fbx:Standing',f'{MX}/Sword And Shield Slash.fbx:Attack:plant',f'{MX}/Sword And Shield Slash.fbx:AttackFull:turn'])
run('body_weights.py')
run('finger_weights.py',['work/pilot_weights.blend','work/pilot_fingers.blend'])
run('twist_bones.py',['work/pilot_fingers.blend','work/pilot.blend'])
import common
rig=bpy.data.objects['Rig'];scene=bpy.context.scene;common.workbench_clay(scene)
for name in ['Standing','Walking','Attack']:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for i in range(5):
  f=a.frame_range[1]*i/4;scene.frame_set(int(f),subframe=f%1)
  common.render_views(str(P/'review'/f'pilot_{name}_{i}'),.85,2.05,views=('front','left','three_quarter'),resolution=(300,450))
