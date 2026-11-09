import bpy,bmesh,math,json,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
out=p/'texturing';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_reduced.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
bpy.context.view_layer.update()
pv=np.array([a.value for a in me.attributes['piece'].data]);co=np.array([v.co[:] for v in me.vertices]);headpieces={7,8,11}
flag=np.isin(pv,list(headpieces))|((pv==0)&(co[:,2]>1.445))|((pv==1)&(abs(co[:,0])<.12)&(co[:,2]>1.62)&(co[:,1]<.10))
hd=[int(np.all(flag[list(f.vertices)])) for f in me.polygons]
assert sum(hd)>500
a=me.attributes.get('head') or me.attributes.new('head','INT','FACE');a.data.foreach_set('value',hd)
uv=me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap');huv=me.uv_layers.get('HeadUV') or me.uv_layers.new(name='HeadUV')
me.uv_layers.active=huv
for o in bpy.data.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
me=body.data;hd=[x.value for x in me.attributes['head'].data]
for f in me.polygons:f.select=bool(hd[f.index])
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=1.35,island_margin=.018,area_weight=0.,scale_to_bounds=False);bpy.ops.uv.pack_islands(margin=.018,rotate=True);bpy.ops.object.mode_set(mode='OBJECT')
me=body.data;uv=me.uv_layers['UVMap'];huv=me.uv_layers['HeadUV']
# Neutral image makes both static uploads valid textured models. It is never a final material.
mat=bpy.data.materials.new('UploadNeutral');mat.use_nodes=True;im=bpy.data.images.new('UploadNeutral',width=4,height=4);im.pixels=[.6,.6,.6,1]*16;im.pack();node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im
mat.node_tree.links.new(node.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
me.materials.clear();me.materials.append(mat)
for f in me.polygons:f.material_index=0
me.uv_layers.active=uv
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_uvprep.blend'))
for ishead,name in [(False,'m460_body_upload.glb'),(True,'m460_head_upload.glb')]:
 ob=body.copy();ob.data=me.copy();ob.modifiers.clear();ob.parent=None;bpy.context.scene.collection.objects.link(ob)
 if ishead:
  bm=bmesh.new();bm.from_mesh(ob.data);bm.faces.ensure_lookup_table();headflag=bm.faces.layers.int['head'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if not f[headflag]],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(ob.data);bm.free()
  hu=ob.data.uv_layers['HeadUV'];bu=ob.data.uv_layers['UVMap']
  for i in range(len(bu.data)):bu.data[i].uv=hu.data[i].uv
 for layer in list(ob.data.uv_layers):
  if layer.name!='UVMap':ob.data.uv_layers.remove(layer)
 for o in bpy.data.objects:o.select_set(o==ob)
 bpy.context.view_layer.objects.active=ob
 bpy.ops.export_scene.gltf(filepath=str(out/name),use_selection=True,export_format='GLB',export_yup=True,export_animations=False,export_skins=False,export_attributes=False)
 print('UPLOAD',name,sum(len(f.vertices)-2 for f in ob.data.polygons))
 if ishead:
  for item in bpy.data.objects:
   if item.type=='MESH':item.hide_render=(item!=ob)
  common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review/head_upload'),1.55,.55,views=('front','left','back','three_quarter'),resolution=(600,600))
 bpy.data.objects.remove(ob,do_unlink=True)
(p/'work/texture_upload_info.json').write_text(json.dumps({'body_triangles':sum(len(f.vertices)-2 for f in me.polygons),'head_triangles':sum(hd),'head_pieces':sorted(headpieces),'head_uv':'head-only smart unwrap at 77 degrees, 1.8 percent padding'},indent=2))
