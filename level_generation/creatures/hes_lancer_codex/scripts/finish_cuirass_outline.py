"""Fit the full cuirass outline to the retained clips, with a two-hand ready elbow adjustment."""
import bpy,sys,runpy,math
from pathlib import Path
from mathutils import Quaternion
P=Path(__file__).resolve().parents[1];S=P/'scripts';sys.path.insert(0,str(S));import armik
src=P/'work/lancer_review2.blend'
def step(name,*args):
 print('CUIRASS_OUTLINE',name,flush=True);sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(S/name),run_name='__main__')
step('armour_spec_lancer.py');step('make_armour.py',P/'work/lancer_review2_base.blend',S/'armour_lancer.json',src);step('skin_shell.py',src,S/'armour_lancer.json',src)
r=bpy.data.objects['Rig'];sc=bpy.context.scene
for name in ('Carbine_Standing','Carbine_Fidget'):
 act=bpy.data.actions[name];r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];keys=[]
 for frame in range(int(act.frame_range[1])+1):
  sc.frame_set(frame);h=armik.W(r,'B_R_Hand').copy();u=armik.W(r,'B_R_UpperArm').translation;e=armik.W(r,'B_R_Forearm').translation;pole=u+Quaternion((h.translation-u).normalized(),math.radians(20))@(e-u)
  armik.solve(r,'R',h.translation,pole,h.to_3x3().normalized());assert (armik.W(r,'B_R_Hand').translation-h.translation).length<1e-5
  keys.append({f'B_R_{n}':r.pose.bones[f'B_R_{n}'].matrix_basis.copy() for n in ('UpperArm','Forearm','Hand')})
 previous={}
 for f,pose in enumerate(keys):
  for n,m in pose.items():
   b=r.pose.bones[n];q=m.to_quaternion()
   if n in previous and q.dot(previous[n])<0:q=-q
   previous[n]=q.copy();b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=m.translation;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
r.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(src))
step('relax_death_arms.py',src,src,'Carbine','Rifle');step('bake_new_twists.py',src,src,'Carbine_Standing','Carbine_Fidget','Carbine_Death');step('helper_bones.py',src,src)
step('make_lance.py',src,src);step('refresh_hull_uv.py',src,src)
clips=['Carbine_Standing','Carbine_Fidget','Carbine_Attack','Lancer_Running','Carbine_Walking','Carbine_Hit','Carbine_Death','Carbine_Dead']
step('gates.py',src,'review2',*clips);step('shell_stretch.py',src,S/'armour_lancer.json','review2',*clips);step('shell_leak.py',src,S/'armour_lancer.json','review2',*clips);step('armour_gate.py',src,'review2',S/'armour_lancer.json',*clips)
step('render_review.py','lancer_review2.blend','Carbine_Standing','0','front')
