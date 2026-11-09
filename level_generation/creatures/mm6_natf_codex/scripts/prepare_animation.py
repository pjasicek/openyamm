import os,sys,runpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];os.chdir(P);sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
L=ROOT/'anim_library/humanoid_set';MX=ROOT/'anim_library/mixamo'
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
# The separated thumb tip lacks the CMC segment inside the palm. Add it before rest-frame construction.
f=json.loads((P/'work/finger_joints.json').read_text());j=json.loads((P/'work/joints_final.json').read_text())['joints']
if not (P/'work/finger_joints_before_cmc.json').exists():
 (P/'work/finger_joints_before_cmc.json').write_text(json.dumps(f,indent=2))
else:f=json.loads((P/'work/finger_joints_before_cmc.json').read_text())
for sd in 'LR':
 ns=['B_R_Finger0','B_R_Finger0.001','B_R_Finger0.002'] if sd=='R' else ['B_L_Finger0','B_L_Finger01','B_L_Finger02']
 w=Vector(j[f'{sd}_Hand']);b=Vector(f[sd][ns[0]]);mid=Vector(f[sd][ns[1]])
 for n,pt in zip(ns,[w.lerp(b,.35),b,mid]):f[sd][n]=list(pt)
(p:=P/'work/finger_joints.json').write_text(json.dumps(f,indent=2))
run('build_rig.py')
run('finger_weights.py',['work/rig_v1.blend','work/rig_fingers.blend'])
run('retarget_mixamo.py',['work/rig_fingers.blend','work/rig_idle.blend',f'{MX}/Standard Idle.fbx:Standing',f'{MX}/Dying Backwards.fbx:Death'])
run('retarget.py',['work/rig_idle.blend','work/source_actions.blend',f'{L}/Armed.glb:ArmedWalk:Walking',f'{L}/Relax.glb:RelaxRunForward:Running',f'{L}/Unarmed.glb:UnarmedGetHitF1:Hit',f'{L}/1Hand.glb:DaggerAttackR2:Attack:plant',f'{L}/1Hand.glb:DaggerAttackR2:AttackFull',f'{L}/Armed.glb:ArmedCastRAttackHand1:Cast:plant',f'{L}/Armed.glb:ArmedCastRAttackHand1:CastFull'])
