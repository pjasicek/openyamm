import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
rig.location=(0,0,0);bpy.context.view_layer.update();sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=64
if not sc.world:sc.world=bpy.data.worlds.new('World')
sc.world.light_settings.distance=.035;images=[]
for label,mat in zip(['body','head'],body.data.materials):
 img=bpy.data.images.new('AO_'+label,1024,1024,alpha=False);mat.use_nodes=True;node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=img;mat.node_tree.nodes.active=node;images.append((label,img))
for ob in bpy.data.objects:ob.select_set(ob==body)
bpy.context.view_layer.objects.active=body;sc.render.bake.margin=8;sc.render.bake.use_selected_to_active=False;bpy.ops.object.bake(type='AO')
for label,img in images:img.filepath_raw=str(P/f'textures/naga_{label}_ao.png');img.file_format='PNG';img.save()
