"""Bake the retained high mesh's smooth surface onto the reduced body before combining painted detail."""
from pathlib import Path
import bpy
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv.blend'));rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
body=bpy.data.objects['Body'];high=bpy.data.objects['BodyHigh'];me=body.data
for f in me.polygons:
 if me.attributes['head'].data[f.index].value:
  for li in f.loop_indices:me.uv_layers['UVMap'].data[li].uv=(.9995,.9995)
me.uv_layers.active=me.uv_layers['UVMap']
for uv in me.uv_layers:uv.active_render=uv.name=='UVMap'
image=bpy.data.images.new('Geometry normal',1024,1024,alpha=False);image.colorspace_settings.name='Non-Color';mat=bpy.data.materials.new('Normal bake');mat.use_nodes=True;n=mat.node_tree.nodes.new('ShaderNodeTexImage');n.image=image;mat.node_tree.nodes.active=n;me.materials.clear();me.materials.append(mat)
for f in me.polygons:f.material_index=0
for ob in bpy.data.objects:ob.hide_render=ob not in (body,high);ob.hide_set(ob not in (body,high));ob.select_set(ob in (body,high))
bpy.context.view_layer.objects.active=body;sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=16;sc.render.bake.use_selected_to_active=True;sc.render.bake.cage_extrusion=.02;sc.render.bake.max_ray_distance=.05;sc.render.bake.margin=8;bpy.ops.object.bake(type='NORMAL');image.filepath_raw=str(P/'work/geometry_normal_UVMap.png');image.file_format='PNG';image.save();print('GEOMETRY_NORMAL',image.filepath_raw,flush=True)
