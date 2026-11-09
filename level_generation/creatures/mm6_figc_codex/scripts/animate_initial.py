import bpy,sys,runpy,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);L=P.parents[2]/'anim_library/humanoid_set';MX=P.parents[2]/'anim_library/mixamo'
def run(n,*args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('retarget.py',P/'work/rig_v1.blend',P/'work/rig_v2s.blend',f'{L}/Armed.glb:ArmedIdle:GripRef',f'{L}/Armed.glb:ArmedWalk:Walking',f'{L}/Relax.glb:RelaxRunForward:Running',f'{L}/Unarmed.glb:UnarmedGetHitF1:Hit')
run('retarget_mixamo.py',P/'work/rig_v2s.blend',P/'work/rig_v2.blend',f'{MX}/Standard Idle.fbx:Standing',f'{MX}/Sword And Shield Slash.fbx:Attack:plant',f'{MX}/Standing Taunt Battlecry.fbx:Fidget:plant',f'{MX}/Sword And Shield Slash.fbx:AttackFull:turn',f'{MX}/Standing Taunt Battlecry.fbx:FidgetFull:turn',f'{MX}/Standing React Death Backward.fbx:Death')
run('twist_bones.py',P/'work/rig_v2.blend',P/'work/rig_v2t.blend');run('weights_figc.py');run('finger_weights.py',P/'work/rig_v3.blend',P/'work/rig_v4f.blend')
os.environ['GRIP_RENDER']=str(P/'review/grip_R');run('grip_solve.py',P/'work/rig_v4f.blend','GripRef',8);os.environ.pop('GRIP_RENDER')
run('apply_grip.py',P/'work/rig_v4f.blend',P/'work/rig_v5.blend')
run('g5_hand_stretch.py',P/'work/rig_v5.blend','Standing','Walking','Running','Attack','Hit','Fidget','Death')
run('g4_weights.py',P/'work/rig_v5.blend','initial','Standing:0','Walking:8','Running:8','Attack:9','Attack:18','Attack:27','Hit:6','Fidget:40','Death:45')
