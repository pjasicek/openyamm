import bpy,sys,json,math,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));b=bpy.data.objects['Body'];me=b.data;T=P/'textures'
def material(name,base,normal,mr):
 m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;bs=nt.nodes.get('Principled BSDF')
 def tex(path,cs):
  n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(T/path));n.image.colorspace_settings.name=cs;return n
 base=tex(base,'sRGB');nt.links.new(base.outputs['Color'],bs.inputs['Base Color']);nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex(normal,'Non-Color').outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal']);sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex(mr,'Non-Color').outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic']);nt.nodes.active=base;return m
hd=np.array([x.value for x in me.attributes['head'].data]);me.materials.clear()
for prefix,suffix in [('PeasantF3',''),('PeasantF3Head','_head')]:me.materials.append(material(prefix+'_A','mfp'+suffix+'_basecolor_1k.png','mfp'+suffix+'_normal_1k.png','mfp'+suffix+'_metal_rough_1k.png'))
me.polygons.foreach_set('material_index',hd.tolist())
for f in me.polygons:
 if hd[f.index]:
  for i in f.loop_indices:me.uv_layers['UVMap'].data[i].uv=me.uv_layers['HeadUV'].data[i].uv
me.uv_layers.active=me.uv_layers['UVMap'];me.uv_layers.active.active_render=True
k=bpy.data.objects['KnifeAsset'];k.data.materials.clear();k.data.materials.append(material('Knife_A','knife/basecolor_1k.png','knife/normal_1k.png','knife/metal_rough_1k.png'))
for f in k.data.polygons:f.material_index=0
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_textured.blend'))
sc=bpy.context.scene;common.workbench_clay(sc,True);rig=bpy.data.objects['Rig']
for a in bpy.data.actions:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];folder=P/'review/textured_clips'/a.name;folder.mkdir(parents=True,exist_ok=True)
 for j,f in enumerate(np.linspace(0,a.frame_range[1],6)):
  sc.frame_set(int(f),subframe=float(f%1));lo,hi=common.world_bounds([b]);center=(lo+hi)/2;span=max(1.90,hi.z-lo.z+ .2, (hi.y-lo.y)*1.55,(hi.x-lo.x)*1.55)
  common.render_views(str(folder/f'{j:02}'),center.z,span,views=('front','left','three_quarter'),resolution=(360,540),target=(center.x,center.y))
