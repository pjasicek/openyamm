"""Reproject the unreduced artwork and tangent normals onto the measured LOD0 surface."""
import bpy,sys,json,shutil
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import round1_materials as M
bpy.ops.wm.open_mainfile(filepath=str(P/globals().get('INPUT','work/round1_lod0.blend')));r=bpy.data.objects['Rig'];low=[bpy.data.objects['Body'],bpy.data.objects['AxeMesh']];r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();M.setup(*low)
# Import only the authoritative unreduced surfaces; the rig and all action samples stay unchanged.
with bpy.data.libraries.load(str(P/'work/round1_high.blend'),link=False) as (src,dst):dst.objects=['Body','AxeMesh']
high=[]
for obj in dst.objects:
 bpy.context.collection.objects.link(obj);high.append(obj);obj.name='BakeSource_'+('Body' if len(high)==1 else 'AxeMesh')
 for mod in list(obj.modifiers):obj.modifiers.remove(mod)
M.setup(*high)
for obj in low:
 for mod in obj.modifiers:mod.show_render=False;mod.show_viewport=False
out=P/globals().get('TEXTURES','textures/round1_rebaked');out.mkdir(parents=True,exist_ok=True)
for source in (P/'textures').glob('*.png'):shutil.copy2(source,out/source.name)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=4;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.bake.use_selected_to_active=True;sc.render.bake.cage_extrusion=.018;sc.render.bake.max_ray_distance=.036;sc.render.bake.margin=12;sc.render.bake.use_clear=True;sc.render.bake.normal_space='TANGENT';report=[]
for lo,hi in zip(low,high):
 if globals().get('ONLY') and lo.name!=globals()['ONLY']:continue
 for suffix in ['basecolor','metal_rough','region_mask','ao','normal']:
  targets=[]
  for mat in lo.data.materials:
   prefix=mat['prefix']
   if prefix=='axe' and suffix in ['region_mask','ao']:continue
   original=bpy.data.images.load(str(P/'textures'/(prefix+'_basecolor.png')),check_existing=True);img=bpy.data.images.new(prefix+'_rebaked_'+suffix,width=original.size[0],height=original.size[1],alpha=True,float_buffer=False);img.colorspace_settings.name='sRGB' if suffix=='basecolor' else 'Non-Color';node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=img;mat.node_tree.nodes.active=node;targets.append((prefix,img))
  if not targets:continue
  for mat in hi.data.materials:
   nt=mat.node_tree;output=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
   if suffix=='normal':nt.links.new(bs.outputs[0],output.inputs['Surface'])
   else:
    prefix=mat['prefix'];node=nt.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(P/'textures'/(prefix+'_'+suffix+'.png')),check_existing=True);node.image.colorspace_settings.name='sRGB' if suffix=='basecolor' else 'Non-Color';emit=nt.nodes.new('ShaderNodeEmission');nt.links.new(node.outputs['Color'],emit.inputs[0]);nt.links.new(emit.outputs[0],output.inputs['Surface'])
  bpy.ops.object.select_all(action='DESELECT');lo.select_set(True);hi.select_set(True);bpy.context.view_layer.objects.active=lo
  bpy.ops.object.bake(type='NORMAL' if suffix=='normal' else 'EMIT')
  for prefix,img in targets:
   dest=out/(prefix+'_'+suffix+'.png');img.filepath_raw=str(dest);img.file_format='PNG';img.save();pixels=np.array(img.pixels[:],np.float32);assert np.isfinite(pixels).all()
   if suffix not in ['region_mask']:assert float(pixels.reshape(-1,4)[:,:3].max())>.1
   report.append({'file':str(dest.relative_to(P)),'size':list(img.size),'source':'work/round1_high.blend','target':'work/round1_lod0.blend','normal_convention':'+Y tangent' if suffix=='normal' else None});print('REBAKED',dest.name,flush=True)
for obj in high:bpy.data.objects.remove(obj,do_unlink=True)
for obj in low:
 for mod in obj.modifiers:mod.show_render=True;mod.show_viewport=True
M.setup(*low,directory=out,rebaked=True);bpy.ops.wm.save_as_mainfile(filepath=str(P/globals().get('OUTPUT','work/round1_baked.blend')));(P/globals().get('REPORT','review/round1/rebake.json')).write_text(json.dumps(report,indent=2))
