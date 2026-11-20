"""Selected Smart Topology cleanup and neutral textured upload; no final UV commitment."""
import bpy,bmesh,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'))
parts=[o for o in bpy.data.objects if o.type=='MESH'];hair=bpy.data.objects['P07']
# Native mane stops at the waist; keep its crown and taper while shortening the lower length.
for v in hair.data.vertices:
 if v.co.z<1.54:v.co.z=0.98+(v.co.z-0.756)*(1.54-0.98)/(1.54-0.756)
for o in parts:
 n=int(o.name[1:]);a=o.data.attributes.new('piece','INT','POINT');a.data.foreach_set('value',[n]*len(o.data.vertices));o.select_set(True)
 if n in (4,5):
  side='R' if n==4 else 'L';scene=bpy.context.scene;common.workbench_clay(scene)
  for other in parts:other.hide_render=other!=o
  co=np.array([tuple(v.co) for v in o.data.vertices]);c=Vector(co.mean(0))
  for view,offset in [('palm',(0,-1,0)),('back',(0,1,0)),('outer',((-1 if n==4 else 1),0,0))]:
   d=bpy.data.cameras.new('Hand camera');d.type='ORTHO';d.ortho_scale=.27;cam=bpy.data.objects.new('Hand camera',d);scene.collection.objects.link(cam);cam.location=c+Vector(offset);cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam;scene.render.resolution_x=scene.render.resolution_y=700;scene.render.filepath=str(P/f'review/rest_hand_{side}_{view}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
for o in parts:o.hide_render=False;o.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects['P00'];bpy.ops.object.join();body=bpy.context.object;body.name=body.data.name='Body';body.data.materials.clear()
# A neutral embedded image satisfies the rig API without spending the final retexture early.
mat=bpy.data.materials.new('Neutral rig surface');mat.use_nodes=True;body.data.materials.append(mat)
im=bpy.data.images.new('Neutral rig texture',width=4,height=4);im.generated_color=(.45,.45,.45,1);im.pack();tx=mat.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im;mat.node_tree.links.new(tx.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
if not body.data.uv_layers:body.data.uv_layers.new(name='UVMap')
for uv in body.data.uv_layers.active.data:uv.uv=(.5,.5)
orig=body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT');orig.data.foreach_set('vector',[x for v in body.data.vertices for x in v.co])
for o in list(bpy.data.objects):
 if o is not body:bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/step1.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'work/body_for_rig.glb'),export_format='GLB',use_selection=True,export_animations=False,export_skins=False,export_attributes=False,export_yup=True)
assert len(body.data.vertices)>5000
print('CLEAN body triangles',sum(len(f.vertices)-2 for f in body.data.polygons),'vertices',len(body.data.vertices))
