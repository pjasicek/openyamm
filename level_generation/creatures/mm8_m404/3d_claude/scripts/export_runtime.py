"""Export the reviewed textured master with the same dense keys as the motion pilot."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Matrix
p=Path(__file__).resolve().parents[1];T=p/'textures'
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_delivery_animation.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sword=bpy.data.objects['SwordMesh'];me=body.data
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
bpy.context.view_layer.update()
head=np.array([x.value for x in me.attributes['head'].data]);uv=me.uv_layers['UVMap'].data;huv=me.uv_layers['HeadUV'].data
for face in me.polygons:
 if head[face.index]:
  for loop in face.loop_indices:uv[loop].uv=huv[loop].uv
for layer in list(me.uv_layers):
 if layer.name!='UVMap':me.uv_layers.remove(layer)
me.uv_layers.active=me.uv_layers['UVMap']
def material(name,base,normal,orm):
 m=bpy.data.materials.new(name);m.use_nodes=True;nodes=m.node_tree.nodes;links=m.node_tree.links
 bsdf=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
 def image(path,space):
  n=nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(T/path));n.image.colorspace_settings.name=space;return n
 links.new(image(base,'sRGB').outputs['Color'],bsdf.inputs['Base Color'])
 if normal:
  n=nodes.new('ShaderNodeNormalMap');links.new(image(normal,'Non-Color').outputs['Color'],n.inputs['Color']);links.new(n.outputs['Normal'],bsdf.inputs['Normal'])
 sep=nodes.new('ShaderNodeSeparateColor');links.new(image(orm,'Non-Color').outputs['Color'],sep.inputs['Color'])
 links.new(sep.outputs['Green'],bsdf.inputs['Roughness']);links.new(sep.outputs['Blue'],bsdf.inputs['Metallic'])
 return m
me.materials.clear()
for label,stem in [('M404_A','m404'),('M404Head_A','m404_head')]:
 me.materials.append(material(label,stem+'_basecolor_1k.png',stem+'_normal_1k.png',stem+'_metal_rough_1k.png'))
me.polygons.foreach_set('material_index',head.tolist())
sword.data.materials.clear();sword.data.materials.append(material('Sword_A','props/sword_base.png',None,'props/sword_orm.png'))
for material_data in list(bpy.data.materials):
 if material_data.users==0:bpy.data.materials.remove(material_data)
for image_data in list(bpy.data.images):
 if image_data.users==0:bpy.data.images.remove(image_data)
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/warrior_finished.blend'))
for ob in bpy.data.objects:ob.select_set(ob in (body,sword))
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name=body.data.name='M404'
for name in ('piece','garment','finger','head','orig_co'):
 if name in body.data.attributes:body.data.attributes.remove(body.data.attributes[name])
keep=('Standing','Walking','Attack','Attack2','Hit','Fidget','Death','Dead')
for a in list(bpy.data.actions):
 if a.name not in keep:bpy.data.actions.remove(a);continue
 a.frame_end*=8;a.frame_start*=8
 curves=[fc for layer in a.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
 groups={}
 for fc in curves:
  for k in fc.keyframe_points:
   k.interpolation='LINEAR';k.co[0]*=8
  fc.update()
  if fc.data_path.endswith('rotation_quaternion'):groups.setdefault(fc.data_path,{})[fc.array_index]=fc
 for group in groups.values():
  if len(group)!=4:continue
  keys=[group[i].keyframe_points for i in range(4)];prev=None
  for j in range(min(map(len,keys))):
   q=[keys[i][j].co[1] for i in range(4)]
   if prev is not None and sum(a*b for a,b in zip(q,prev))<0:
    for i in range(4):keys[i][j].co[1]*=-1
    q=[-v for v in q]
   prev=q
for o in bpy.data.objects:o.select_set(o in (body,rig))
bpy.context.view_layer.objects.active=rig;bpy.context.scene.render.fps=240;bpy.context.scene.render.fps_base=1
a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
bpy.ops.export_scene.gltf(filepath=str(p/'export/mm8_m404_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_image_format='AUTO',export_reset_pose_bones=True,export_anim_slide_to_zero=True)

bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();co=np.array([v.co[:] for v in mesh.vertices]);ev.to_mesh_clear()
body_vertices=sorted({v for face in body.data.polygons if face.material_index!=2 for v in face.vertices})
info={'visible_standing_height_m':float(np.ptp(co[body_vertices,2])),'triangles':sum(len(f.vertices)-2 for f in body.data.polygons),'clip_durations':{a.name:float(a.frame_range[1]-a.frame_range[0])/240 for a in bpy.data.actions}}
(p/'export/export_info.json').write_text(json.dumps(info,indent=2)+'\n');print('EXPORTED',info)
