from pathlib import Path
import bpy,runpy,sys,os,ast,math,json
from mathutils import Vector,Quaternion,Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));os.environ['ARM_ABDUCT_DEG']='10'
sys.argv=['retarget.py','--',str(p/'work/rig_v9h.blend'),str(p/'work/rig_v9u.blend'),str(p.parents[2]/'anim_library/humanoid_set/Unarmed.glb')+':UnarmedDeath1:Death'];runpy.run_path(str(p/'scripts/retarget.py'),run_name='__main__')
rig=bpy.data.objects['Rig'];act=bpy.data.actions['Death'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
g=json.loads((p/'work/grip_pose.json').read_text())['finger_local'];g.update({b.name:[1,0,0,0] for b in rig.data.bones if b.name.startswith('B_L_Finger')})
for f in range(int(act.frame_range[1])+1):
 bpy.context.scene.frame_set(f)
 for n,q in g.items():
  pb=rig.pose.bones[n];pb.rotation_quaternion=Quaternion(q);pb.keyframe_insert('rotation_quaternion',frame=f)
FA=.5;UA=.5;tree=ast.parse((p/'scripts/twist_bones.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'twist_about','bake_twist'}],type_ignores=[]),'twist','exec'),globals());bake_twist(act)
from g6_head_clearance import Clearance
c=Clearance(bpy.data.objects['Body']);rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];worst=(0,None)
for f in range(int(act.frame_range[1])+1):
 bpy.context.scene.frame_set(f);d=c.measure()[0]
 if d>worst[0]:worst=(d,f)
print('UNARMED_DEATH_HEAD',worst,'frames',act.frame_range[:])
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v9u.blend'))
sys.argv=['clip_sheet.py','--',str(p/'work/rig_v9u.blend'),str(p/'revision_02/motion/death_candidate'),'three_quarter','9','Death'];runpy.run_path(str(p/'scripts/clip_sheet.py'),run_name='__main__')
