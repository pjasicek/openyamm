"""Cycles selected-to-active reprojection into the retained UV layout, including tangent-space detail."""
import bpy,bmesh,json,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def subset(ob,head):
 bm=bmesh.new();bm.from_mesh(ob.data);layer=bm.faces.layers.int['head']
 bmesh.ops.delete(bm,geom=[f for f in bm.faces if bool(f[layer])!=head],context='FACES')
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(ob.data);bm.free()
 if head:
  for a,b in zip(ob.data.uv_layers['UVMap'].data,ob.data.uv_layers['HeadUV'].data):a.uv=b.uv
 ob.data.uv_layers.active=ob.data.uv_layers['UVMap'];ob.data.uv_layers.active.active_render=True
def bake(part,path,dest):
 dest=Path(dest);dest.mkdir(parents=True,exist_ok=True);T=P/'work/round2/high_textures';records=[]
 for section in (['body','head']if part=='body'else['bow']):
  bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['Rig'];rig.animation_data.action=None
  for b in rig.pose.bones:b.matrix_basis.identity()
  target=bpy.data.objects['Body'if part=='body'else'BowAsset']
  with bpy.data.libraries.load(str(P/'work/round2/unreduced.blend'),link=False)as(src,dst):dst.objects=['Body'if part=='body'else'BowAsset']
  source=dst.objects[0];bpy.context.collection.objects.link(source)
  for ob in [target,source]:
   for m in list(ob.modifiers):ob.modifiers.remove(m)
   if part=='body':subset(ob,section=='head')
   else:
    ob.data.uv_layers.active=ob.data.uv_layers['UVMap'];ob.data.uv_layers.active.active_render=True
  for ob in bpy.data.objects:ob.hide_render=ob not in [target,source]
  sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=1;sc.render.threads_mode='FIXED';sc.render.threads=4
  sc.render.bake.use_selected_to_active=True;sc.render.bake.cage_extrusion=.025;sc.render.bake.max_ray_distance=.05;sc.render.bake.margin=12;sc.render.bake.use_clear=True
  prefix='arc1_head_'if section=='head'else'arc1_'if section=='body'else''
  folder=T if part=='body'else T/'bow';suffix={'basecolor':'basecolor_1k.png','metal_rough':'metal_rough_1k.png','normal':'normal_1k.png','region_mask':'region_mask.png'}
  for kind in ['basecolor','metal_rough','region_mask','normal']:
   filename=prefix+suffix[kind];inp=folder/filename
   if not inp.exists():continue
   sm=bpy.data.materials.new('BakeSource');sm.use_nodes=True;nt=sm.node_tree;nt.nodes.clear();output=nt.nodes.new('ShaderNodeOutputMaterial');tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(inp),check_existing=False);tex.image.colorspace_settings.name='sRGB'if kind=='basecolor'else'Non-Color'
   if kind=='normal':
    bs=nt.nodes.new('ShaderNodeBsdfPrincipled');normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex.outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bs.inputs['Normal']);nt.links.new(bs.outputs[0],output.inputs['Surface'])
   else:
    em=nt.nodes.new('ShaderNodeEmission');nt.links.new(tex.outputs['Color'],em.inputs['Color']);nt.links.new(em.outputs[0],output.inputs['Surface'])
   source.data.materials.clear();source.data.materials.append(sm)
   for f in source.data.polygons:f.material_index=0
   tm=bpy.data.materials.new('BakeTarget');tm.use_nodes=True;target.data.materials.clear();target.data.materials.append(tm)
   for f in target.data.polygons:f.material_index=0
   im=bpy.data.images.new('Rebaked',width=1024,height=1024,alpha=True);im.colorspace_settings.name='sRGB'if kind=='basecolor'else'Non-Color';n=tm.node_tree.nodes.new('ShaderNodeTexImage');n.image=im;tm.node_tree.nodes.active=n
   bpy.ops.object.select_all(action='DESELECT');source.select_set(True);target.select_set(True);bpy.context.view_layer.objects.active=target;bpy.ops.object.bake(type='NORMAL'if kind=='normal'else'EMIT')
   out=dest/filename;im.filepath_raw=str(out);im.file_format='PNG';im.save()
   records.append({'section':section,'map':kind,'file':str(out.relative_to(P))});print('REBAKED',out,flush=True)
 return records
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:];print(bake(args[0],P/args[1],P/args[2]))
