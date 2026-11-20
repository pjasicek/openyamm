"""Shared PBR material slots and recessed emissive muzzle cores on the approved Sentinel rig."""
import json,math,sys
from pathlib import Path
import bpy,numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/sentinel_textured_rig.blend'))
body=bpy.data.objects['Sentinel'];rig=bpy.data.objects['SentinelRig'];scene=bpy.context.scene
scene.frame_set(0)
images={name:bpy.data.images.load(str(P/f'textures/sentinel_{name}.png'),check_existing=True) for name in ['basecolor','normal','orm']}
for name,im in images.items():im.colorspace_settings.name='sRGB' if name=='basecolor' else 'Non-Color'
def material(name,metal):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.use_backface_culling=True
 n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
 for kind,im in images.items():
  t=n.new('ShaderNodeTexImage');t.image=im
  if kind=='basecolor':l.new(t.outputs['Color'],p.inputs['Base Color'])
  elif kind=='normal':
   normal=n.new('ShaderNodeNormalMap');l.new(t.outputs['Color'],normal.inputs['Color']);l.new(normal.outputs['Normal'],p.inputs['Normal'])
  else:
   sep=n.new('ShaderNodeSeparateColor');l.new(t.outputs['Color'],sep.inputs['Color']);l.new(sep.outputs['Green'],p.inputs['Roughness']);l.new(sep.outputs['Blue'],p.inputs['Metallic'])
 return m
body.data.materials.clear()
for name in ['Sentinel_Armour','Sentinel_Trim','Sentinel_Resin']:body.data.materials.append(material(name,0))
classes=np.load(P/'work/sentinel_face_materials.npy');assert len(classes)==len(body.data.polygons)
for f,c in zip(body.data.polygons,classes):f.material_index=int(c)
energy=bpy.data.materials.new('Sentinel_Energy');energy.use_nodes=True;energy.use_backface_culling=True
p=energy.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.8,.12,.008,1);p.inputs['Metallic'].default_value=0;p.inputs['Roughness'].default_value=.45
p.inputs['Emission Color'].default_value=(1,.22,.012,1);p.inputs['Emission Strength'].default_value=1
pieces=[body]
for name in ['Socket_Muzzle_Upper','Socket_Muzzle_Lower']:
 pos=rig.data.bones[name].head_local.copy();pos.y+=.065
 bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=.085,depth=.012,end_fill_type='NGON',location=pos,rotation=(math.pi/2,0,0))
 o=bpy.context.object;o.name='MuzzleCore';bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 o.data.materials.append(energy);vg=o.vertex_groups.new(name='B_Recoil');vg.add(list(range(len(o.data.vertices))),1,'REPLACE')
 pieces.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in pieces:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
# Triangulate only the two new emitter caps; existing UVs and rig vertices stay intact.
mod=body.modifiers.new('Triangulate','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name)
assert sum(len(f.vertices)-2 for f in body.data.polygons)==9867
scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/sentinel_final_rig.blend'))
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(P/'export/hes_sentinel_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
print('TEXTURED_LOD0',sum(len(f.vertices)-2 for f in body.data.polygons),flush=True)
