"""Selected-to-active surface rebake; accepted rig, UV domains and source maps remain immutable."""
import bpy, json, sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];T=P/'textures/round2';W=P/'work/round2';sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(W/'lod0_selected.blend'))
sc=bpy.context.scene;low=bpy.data.objects['Body'];rig=bpy.data.objects['Rig']
for ob in list(bpy.data.objects):
 if ob not in (low,rig):bpy.data.objects.remove(ob,do_unlink=True)
with bpy.data.libraries.load(str(P/'review/triangle_reduction/baseline/work/rig_textured.blend'),link=False)as(a,b):b.objects=['Body']
high=b.objects[0];sc.collection.objects.link(high);high.name='AcceptedBakeSource';high.hide_render=False;high.hide_set(False);high.parent=None;high.modifiers.clear()
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
for mod in low.modifiers:mod.show_render=False;mod.show_viewport=False
bpy.context.view_layer.update()
# Isolate corresponding disconnected parts to prevent adjacent fingers and crown rays stealing texels.
coordinates={};parts=sorted({x.value for x in high.data.attributes['piece'].data});offsets={p:Vector(((i%12)*3,(i//12)*3,0))for i,p in enumerate(parts)}
for ob in (low,high):
 coordinates[ob.name]=[v.co.copy()for v in ob.data.vertices]
 for v in ob.data.vertices:v.co+=offsets[ob.data.attributes['piece'].data[v.index].value]
 ob.data.update()
 for poly in ob.data.polygons:poly.material_index=int(ob.data.attributes['head'].data[poly.index].value)
low.data.materials.clear();high.data.materials.clear()
for ob in (low,high):
 for name in ['Lich_A','LichHead_A']:
  mat=bpy.data.materials.new(name+'_bake_'+ob.name);mat.use_nodes=True;ob.data.materials.append(mat)
for ob in (low,high):
 for poly in ob.data.polygons:poly.material_index=int(ob.data.attributes['head'].data[poly.index].value)
uv=low.data.uv_layers.get('BakeUV')or low.data.uv_layers.new(name='BakeUV')
for f in low.data.polygons:
 src=low.data.uv_layers['HeadUV'if f.material_index else 'UVMap']
 for li in f.loop_indices:uv.data[li].uv=src.data[li].uv
low.data.uv_layers.active=uv;uv.active_render=True
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.render.bake.use_selected_to_active=True
sc.render.bake.cage_extrusion=.006;sc.render.bake.max_ray_distance=.04;sc.render.bake.margin=16
sc.render.bake.normal_space='TANGENT';sc.render.bake.normal_r='POS_X';sc.render.bake.normal_g='POS_Y';sc.render.bake.normal_b='POS_Z'
reports=[]
for kind,suffix in [('coverage','coverage')]:
 outputs=[]
 for slot,prefix in enumerate(['lch','lch_head']):
  mat=high.data.materials[slot];nt=mat.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial')
  image=bpy.data.images.new(prefix+'_white',1,1,alpha=False);image.generated_color=(1,1,1,1);image.colorspace_settings.name='Non-Color'
  tex=nt.nodes.new('ShaderNodeTexImage');tex.image=image;uvnode=nt.nodes.new('ShaderNodeUVMap');uvnode.uv_map='HeadUV'if slot else 'UVMap';nt.links.new(uvnode.outputs['UV'],tex.inputs['Vector'])
  if kind=='normal':
   shader=nt.nodes.new('ShaderNodeBsdfPrincipled');nm=nt.nodes.new('ShaderNodeNormalMap');nm.uv_map=uvnode.uv_map
   nt.links.new(tex.outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],shader.inputs['Normal'])
  else:
   shader=nt.nodes.new('ShaderNodeEmission');nt.links.new(tex.outputs['Color'],shader.inputs['Color'])
  nt.links.new(shader.outputs[0],out.inputs['Surface'])
  target=bpy.data.images.new(f'{prefix}_{kind}_rebaked',1024,1024,alpha=True);target.colorspace_settings.name='sRGB'if kind=='base'else 'Non-Color'
  target.generated_color=(.5,.5,1,0)if kind=='normal'else (0,0,0,0)
  nt=low.data.materials[slot].node_tree;node=nt.nodes.new('ShaderNodeTexImage');node.image=target;nt.nodes.active=node;outputs.append((target,T/f'{prefix}_{suffix}.png'))
 bpy.ops.object.select_all(action='DESELECT');high.select_set(True);low.select_set(True);bpy.context.view_layer.objects.active=low
 bpy.ops.object.bake(type='NORMAL'if kind=='normal'else 'EMIT',use_clear=True)
 for im,path in outputs:im.filepath_raw=str(path);im.file_format='PNG';im.save()
 reports.append({'kind':kind,'files':[str(path.relative_to(P))for im,path in outputs]});print('REBAKED',kind,flush=True)
for ob in (low,high):
 for v,co in zip(ob.data.vertices,coordinates[ob.name]):v.co=co
 ob.data.update()
bpy.data.objects.remove(high,do_unlink=True)
for mod in low.modifiers:mod.show_render=True;mod.show_viewport=True
low.data.uv_layers.remove(low.data.uv_layers['BakeUV']);low.data.uv_layers.active=low.data.uv_layers['UVMap'];low.data.uv_layers.active.active_render=True
bpy.ops.wm.save_as_mainfile(filepath=str(W/'lod0_coverage.blend'))
(P/'review/triangle_rebake/coverage_bake.json').write_text(json.dumps({'source':'review/triangle_reduction/baseline/work/rig_textured.blend','target':'work/round2/lod0_selected.blend','method':'Cycles selected-to-active; corresponding parts exploded together; original UV domains retained but texels projected again from accepted surface','normal':'tangent +X +Y +Z; accepted tangent normal combined with geometry difference','cage_m':.006,'max_ray_m':.04,'maps':reports},indent=2)+'\n')
