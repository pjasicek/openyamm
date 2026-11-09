"""Bake removed geometric detail and short-range AO onto the verified texture UVs."""
import bpy,json,sys
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_source_v2.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
low={n:bpy.data.objects[n] for n in ['Body','Head']}
with bpy.data.libraries.load(str(P/'work/rig_high.blend'),link=False) as (src,dst):dst.objects=['Body','Head']
high={n:o for n,o in zip(['Body','Head'],dst.objects)}
for n,o in high.items():
 bpy.context.scene.collection.objects.link(o);o.parent=None;o.modifiers.clear();o.name=n+'High';o.hide_render=False
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=4
bake=scene.render.bake;bake.use_selected_to_active=True;bake.cage_extrusion=.02;bake.max_ray_distance=.045;bake.margin=12
for name in ['Body']:
 o=low[name];mat=o.data.materials[0];nt=mat.node_tree;image=bpy.data.images.new(name+'GeometryNormal',1024,1024,alpha=False);image.colorspace_settings.name='Non-Color';node=nt.nodes.new('ShaderNodeTexImage');node.image=image;nt.nodes.active=node
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);high[name].select_set(True);bpy.context.view_layer.objects.active=o
 bpy.ops.object.bake(type='NORMAL');image.filepath_raw=str((P/f'textures/{name.lower()}_geometry_normal.png').resolve());image.file_format='PNG';image.save();nt.nodes.remove(node)
 print('GEOMETRY_NORMAL',name,flush=True)
for o in high.values():bpy.data.objects.remove(o,do_unlink=True)
bake.use_selected_to_active=False;scene.cycles.samples=64;scene.world.light_settings.distance=.05
for name in ['Body']:
 o=low[name];mat=o.data.materials[0];nt=mat.node_tree;image=bpy.data.images.new(name+'AO',1024,1024,alpha=False);image.colorspace_settings.name='Non-Color';node=nt.nodes.new('ShaderNodeTexImage');node.image=image;nt.nodes.active=node
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 bpy.ops.object.bake(type='AO');image.filepath_raw=str((P/f'textures/{name.lower()}_ao.png').resolve());image.file_format='PNG';image.save();nt.nodes.remove(node)
 print('AO',name,flush=True)
print('BAKE_COMPLETE')
