import bpy,sys,runpy,numpy as np
from mathutils import Vector,Matrix
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work';sys.path.insert(0,str(P/'scripts'))
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(W/'master_motion.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
st=bpy.data.actions['Standing'];rig.animation_data.action=st;rig.animation_data.action_slot=st.slots[0];sc.frame_set(0)
neutral={n:rig.pose.bones[n].rotation_quaternion.copy() for n in ['B_Neck','B_Head']}
a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];rows=[]
for f in np.arange(0,109.001,.25):
 sc.frame_set(int(f),subframe=float(f%1));u=np.clip((f-65)/20,0,1);u=u*u*(3-2*u)
 snap={}
 for n,q in neutral.items():
  old=rig.pose.bones[n].rotation_quaternion.copy();q=q if old.dot(q)>=0 else -q;snap[n]=old.slerp(q,float(u))
 rows.append((float(f),snap))
for f,snap in rows:
 for n,q in snap.items():b=rig.pose.bones[n];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
rows=[];inv=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()
for f in np.arange(0,109.001,.25):
 sc.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low=min((body.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
 rows.append((float(f),rig.pose.bones['B_Pelvis'].location.copy()+inv@Vector((0,0,.002-low))))
for f,loc in rows:b=rig.pose.bones['B_Pelvis'];b.location=loc;b.keyframe_insert('location',frame=f)
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.ops.wm.save_as_mainfile(filepath=str(W/'master_motion_final.blend'))
run('g6_head_clearance.py',W/'master_motion_final.blend','Death')
run('transfer_uv.py',W/'master_motion_final.blend',P/'meshy/body_retexture_v1',W/'master_uv_body.blend')
run('transfer_uv.py',W/'master_uv_body.blend',P/'meshy/head_retexture_v1',W/'master_uv.blend','HeadUV')
run('uv_raster.py',W/'master_uv.blend','UVMap',1024)
run('uv_raster.py',W/'master_uv.blend','HeadUV',1024)
run('render_tex.py',W/'master_uv.blend',P/'meshy/body_retexture_v1/texture_urls_0_base_color.png','texture_raw',P/'meshy/head_retexture_v1/texture_urls_0_base_color.png')
