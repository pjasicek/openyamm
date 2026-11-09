import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/contact_master.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene

def material(name,tag):
 m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
 def tex(suffix,space):
  t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(P/f'textures/natm_{tag}_{suffix}.png'));t.image.colorspace_settings.name=space;return t
 nt.links.new(tex('basecolor','sRGB').outputs['Color'],bs.inputs['Base Color']);nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal','Non-Color').outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal']);sp=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('metal_rough','Non-Color').outputs['Color'],sp.inputs['Color']);nt.links.new(sp.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sp.outputs['Blue'],bs.inputs['Metallic']);return m
body.data.materials.clear();body.data.materials.append(material('Natm_B','body'));body.data.materials.append(material('NatmHead_B','head'));flags=[a.value for a in body.data.attributes['head'].data]
for f in body.data.polygons:
 f.material_index=flags[f.index]
 if f.material_index:
  for i in f.loop_indices:body.data.uv_layers['UVMap'].data[i].uv=body.data.uv_layers['HeadUV'].data[i].uv
body.data.uv_layers.remove(body.data.uv_layers['HeadUV']);body.data.uv_layers.active=body.data.uv_layers['UVMap'];body.data.uv_layers.active.active_render=True
for name in ['Spear','Buckler']:
 ob=bpy.data.objects[name+'Mesh'];ob.data.materials.clear();ob.data.materials.append(material('Natm'+name+'_B',name.lower()))
 for f in ob.data.polygons:f.material_index=0
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
for im in bpy.data.images:
 if im.source=='FILE'and im.has_data:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/material_master.blend'))
common.setup_render((700,900));sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.55,.55,.55,1);sc.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.6
for loc,power,size in [((3,-4,5),450,4),((-3,-2,3),300,3),((0,3,4),350,3)]:
 ld=bpy.data.lights.new('Softbox','AREA');ld.energy=power;ld.shape='DISK';ld.size=size;o=bpy.data.objects.new('Softbox',ld);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.9))-o.location).to_track_quat('-Z','Y').to_euler()
sc.view_settings.view_transform='Standard';sc.view_settings.look='Medium High Contrast'if False else 'None';sc.view_settings.exposure=0
for name,f in [('Standing',0),('Death',90),('Death',103)]:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(f);common.render_views(str(P/f'review/material_{name}_{f}'),.75,3.0,views=('front','left','three_quarter'),resolution=(600,700))
