import bpy,numpy as np,json,sys
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v11.blend'));r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];sc=bpy.context.scene;me=o.data
pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
hd=np.zeros(len(me.polygons),np.int32);me.attributes['head'].data.foreach_get('value',hd);ids=sorted({v for f in me.polygons if hd[f.index] for v in f.vertices})
a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
common.workbench_clay(sc,False);sc.display.shading.show_cavity=False
o.data.materials.clear()
for name,color in [('cape',(.3,.65,.3,1)),('body',(.6,.1,.1,1)),('head',(.8,.8,.1,1))]:
 m=bpy.data.materials.new(name);m.diffuse_color=color;o.data.materials.append(m)
for f in me.polygons:f.material_index=2 if hd[f.index] else 0 if pv[f.vertices[0]]==0 else 1
for frame in [24,55]:
 sc.frame_set(frame);ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();X=np.array([mesh.vertices[i].co[:] for i in ids]);ev.to_mesh_clear()
 print('HEAD_POSE',frame,'bounds',X.min(0),X.max(0),{n:{'head':list(r.pose.bones[n].head),'D':list((r.pose.bones[n].matrix@r.data.bones[n].matrix_local.inverted()).to_quaternion())} for n in ['B_Spine2','B_Neck','B_Head']})
 for view,offset in [('side',(2,0,0)),('above',(0,0,2))]:
  c=Vector(X.mean(0));cam=common.ortho_camera('head',c+Vector(offset),(0,0,0),.75);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-Vector(offset)).to_track_quat('-Z','Y');sc.camera=cam
  sc.render.resolution_x=sc.render.resolution_y=600;sc.render.filepath=str(p/f'review/feet_cloak_20261011/head_{frame}_{view}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
