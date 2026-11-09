import bpy,sys,runpy,os,json,math
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];os.chdir(P);sys.path.insert(0,str(P/'scripts'))
def run(n,args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
L=ROOT/'anim_library/humanoid_set'
items=[f'{L}/2Hand Staff.glb:StaffAttack{i}:Staff{i}' for i in range(1,7)]
items += [f'{L}/2Hand Staff.glb:{s}:{s}' for s in ['StaffCastLAttack1','StaffCastLAttack2','StaffCastLAttack3','StaffCastLAOE1','StaffCastSummon1']]
run('retarget.py',['work/source_actions_mixamo.blend','work/round2_sources.blend',*items])
run('retarget_mixamo.py',['work/round2_sources.blend','work/round2_sources.blend',f'{ROOT}/anim_library/mixamo/Standing React Death Backward.fbx:DeathMixamo'])
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_grip.blend'))
from staff_ik import Side,swing_twist_deg
rig=bpy.data.objects['Rig'];G=json.loads((P/'work/grip_pose.json').read_text());scene=bpy.context.scene
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];scene.frame_set(0)
print('DIAGNOSTIC REST / STANDING',flush=True)
for sd in 'LR':
 s=Side(sd);b=rig.pose.bones[f'B_{sd}_Hand'];m=b.matrix.to_3x3();n=s.rest['Hand'].inverted()@Vector((0,-1,0));long=s.rest['Hand'].inverted()@(rig.data.bones[f'B_{sd}_Finger2'].head_local-rig.data.bones[f'B_{sd}_Hand'].head_local).normalized()
 ua=rig.pose.bones[f'B_{sd}_UpperArm'];print(sd,'palm',list(m@n),'long',list(m@long),'upper twist',swing_twist_deg(ua.rotation_quaternion,s.uA),'hinge',list(s.hinge_local()),'uA',list(s.uA),'hand frame', [list(r) for r in m],flush=True)
