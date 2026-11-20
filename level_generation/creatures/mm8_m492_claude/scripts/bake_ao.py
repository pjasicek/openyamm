"""Bake independent AO maps for the three texture domains; their UVs intentionally overlap each other."""
import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data_clear()
for pb in rig.pose.bones:pb.matrix_basis.identity()
if bpy.data.objects.get('MouthFire'):bpy.data.objects['MouthFire'].hide_render=True
bpy.context.view_layer.update();sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24
if sc.world is None:sc.world=bpy.data.worlds.new('World')
sc.world.light_settings.distance=.012
images=[];(P/'textures').mkdir(exist_ok=True)
for slot,label in [(0,'body'),(1,'head'),(2,'wings')]:
 im=bpy.data.images.new('AO_'+label,1024,1024,alpha=False);mat=body.data.materials[slot];mat.use_nodes=True;node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;mat.node_tree.nodes.active=node;images.append((label,im))
for o in bpy.data.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body;sc.render.bake.margin=8;sc.render.bake.use_selected_to_active=False;bpy.ops.object.bake(type='AO')
for label,im in images:im.filepath_raw=str(P/'textures'/f'dragon_{label}_ao_1k.png');im.file_format='PNG';im.save()
print('AO three sets saved',flush=True)

# Bake the original sculpt's geometric detail onto the selected reduced topology.
with bpy.data.libraries.load(str(P/'work/anim_v1.blend'),link=False) as (available,selected):selected.objects=['Body']
high=selected.objects[0];sc.collection.objects.link(high);high.parent=None;high.modifiers.clear()
normal_images=[]
for slot,label in [(0,'body'),(1,'head'),(2,'wings')]:
 im=bpy.data.images.new('GeometryNormal_'+label,2048,2048,alpha=True);im.generated_color=(.5,.5,1,0)
 mat=body.data.materials[slot];node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;mat.node_tree.nodes.active=node;normal_images.append((label,im))
for o in bpy.data.objects:o.select_set(o in (body,high))
bpy.context.view_layer.objects.active=body;sc.render.bake.use_selected_to_active=True;sc.render.bake.cage_extrusion=.003;sc.render.bake.max_ray_distance=.015;sc.render.bake.margin=12
bpy.ops.object.bake(type='NORMAL')
for label,im in normal_images:im.filepath_raw=str(P/'textures'/f'dragon_{label}_geometry_normal_2k.png');im.file_format='PNG';im.save()
print('Source sculpt normals baked onto the reduced UV layout',flush=True)
