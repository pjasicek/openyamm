"""Bake independent AO maps for the three texture domains; their UVs intentionally overlap each other."""
import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data_clear()
for pb in rig.pose.bones:pb.matrix_basis.identity()
if bpy.data.objects.get('DeathFlames'):bpy.data.objects['DeathFlames'].hide_render=True
bpy.context.view_layer.update();sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24
if sc.world is None:sc.world=bpy.data.worlds.new('World')
sc.world.light_settings.distance=.025
images=[];(P/'textures').mkdir(exist_ok=True)
for slot,label in [(0,'body'),(1,'head')]:
 im=bpy.data.images.new('AO_'+label,1024,1024,alpha=False);mat=body.data.materials[slot];mat.use_nodes=True;node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;mat.node_tree.nodes.active=node;images.append((label,im))
# the wings set is not rebaked, but every material needs an active image to bake
dummy=bpy.data.images.new('AO_unused',8,8,alpha=False);mat=body.data.materials[2];mat.use_nodes=True;node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=dummy;mat.node_tree.nodes.active=node
for o in bpy.data.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body;sc.render.bake.margin=8;sc.render.bake.use_selected_to_active=False;bpy.ops.object.bake(type='AO')
for label,im in images:im.filepath_raw=str(P/'textures'/f'cdr1_{label}_ao_1k.png');im.file_format='PNG';im.save()
print('AO three sets saved',flush=True)
