import os,sys,runpy,bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];os.chdir(P)
L=ROOT/'anim_library/humanoid_set';MX=ROOT/'anim_library/mixamo'
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('retarget.py',['work/rig_v1.blend','work/rig_v2s.blend',f'{L}/Armed.glb:ArmedIdle:GripRef',f'{L}/Armed.glb:ArmedWalk:Walking',f'{L}/Relax.glb:RelaxRunForward:Running',f'{L}/Unarmed.glb:UnarmedGetHitF1:Hit',f'{L}/Armed.glb:ArmedDeath1:Death'])
run('retarget_mixamo.py',['work/rig_v2s.blend','work/rig_v2.blend',f'{MX}/Standard Idle.fbx:Standing',f'{MX}/Sword And Shield Slash.fbx:Attack:plant',f'{MX}/Standing Taunt Battlecry.fbx:Fidget:plant',f'{MX}/Sword And Shield Slash.fbx:AttackFull:turn',f'{MX}/Standing Taunt Battlecry.fbx:FidgetFull:turn'])
os.environ['FA']='0.5';os.environ['FA_RAMP']='0.0,0.15'
run('twist_bones.py',['work/rig_v2.blend','work/rig_v2t.blend']);run('dwarf_weights.py')
run('finger_weights.py',['work/rig_v3.blend','work/rig_v4.blend'])
os.environ['R_HANDLE']='0.018';os.environ['GRIP_RENDER']=str(P/'review/grip');run('grip_solve.py',['work/rig_v4.blend','GripRef',8])
run('apply_grip.py',['work/rig_v4.blend','work/rig_v6.blend']);run('clip_timing.py')
roles=['Standing','Walking','Running','Attack','Hit','Death','Fidget']
run('g5_hand_stretch.py',['work/rig_v6t.blend',*roles])
picks=[f'{n}:{f}'for n in roles for f in range(0,int(bpy.data.actions[n].frame_range[1])+1,4)]
run('g4_weights.py',['work/rig_v6t.blend','pilot',*picks])
