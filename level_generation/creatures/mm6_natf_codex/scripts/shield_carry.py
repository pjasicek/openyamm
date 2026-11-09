import bpy,sys,json,math,runpy
from pathlib import Path
from mathutils import Quaternion,Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));bpy.ops.wm.open_mainfile(filepath=str(P/'work/production_master.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(0);names=[f'B_L_{k}'for k in ['Clavicle','UpperArm','Forearm','Hand']];ST={n:rig.pose.bones[n].rotation_quaternion.copy()for n in names}
for a in bpy.data.actions:
 if not a.use_fake_user:continue
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];end=int(a.frame_range[1]);prev={}
 for f in range(end+1):
  sc.frame_set(f);amp={'Standing':.005,'Fidget':.025,'Walking':.035,'Running':.050,'Hit':.050,'Attack':.025,'Cast':.03}.get(a.name,0);theta=amp*math.sin(f/max(1,end)*math.tau)
  for n in names:
   pb=rig.pose.bones[n];q=ST[n].copy()
   if n.endswith('UpperArm'):q=q@Quaternion(Vector((0,0,1)),theta)
   if n.endswith('Clavicle')and a.name not in ['Dead','Death']:q=q.slerp(pb.rotation_quaternion,.15)
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q.copy();pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
ns=runpy.run_path(str(P/'scripts/bake_twist.py'));[ns['bake_twist'](a)for a in bpy.data.actions if a.use_fake_user]
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/carry_master.blend'));(P/'review/shield_carry.md').write_text('The heavy shield arm retains its fitted carrying pose relative to the torso, with small gait, hit and fidget motion. The selected library clips still drive pelvis, trunk and the blade arm. During Death it follows the library torso fall; the hand remains on the same rear grip. This avoids forcing the wrist to counter-rotate against the library clavicle.\n')
