"""Retain the existing painted materials and preview the runtime region ramps."""
import bpy,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def material(name,prefix,directory,flip_normal=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
 def tex(suffix,cs):
  node=nt.nodes.new('ShaderNodeTexImage');node.name=suffix;node.image=bpy.data.images.load(str(directory/(prefix+'_'+suffix+'.png')),check_existing=True);node.image.colorspace_settings.name=cs;return node
 base=tex('basecolor','sRGB');nt.links.new(base.outputs['Color'],bs.inputs['Base Color']);nt.nodes.active=base
 norm=tex('normal','Non-Color');nm=nt.nodes.new('ShaderNodeNormalMap');color=norm.outputs['Color']
 if flip_normal:
  separate=nt.nodes.new('ShaderNodeSeparateColor');combine=nt.nodes.new('ShaderNodeCombineColor');inv=nt.nodes.new('ShaderNodeMath');inv.operation='SUBTRACT';inv.inputs[0].default_value=1;nt.links.new(color,separate.inputs[0]);nt.links.new(separate.outputs[1],inv.inputs[1]);nt.links.new(separate.outputs[0],combine.inputs[0]);nt.links.new(inv.outputs[0],combine.inputs[1]);nt.links.new(separate.outputs[2],combine.inputs[2]);color=combine.outputs[0]
 nt.links.new(color,nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
 mr=tex('metal_rough','Non-Color');separate=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(mr.outputs[0],separate.inputs[0]);nt.links.new(separate.outputs[1],bs.inputs['Roughness']);bs.inputs['Metallic'].default_value=0
 m['prefix']=prefix;return m
def setup(body,axe,directory=None,rebaked=False):
 directory=directory or P/'textures';body.data.materials.clear();axe.data.materials.clear()
 for unused in list(bpy.data.materials):
  if unused.users==0:bpy.data.materials.remove(unused)
 me=body.data;hd=np.array([a.value for a in me.attributes['head'].data])
 if 'HeadUV' in me.uv_layers:
  uv=me.uv_layers['UVMap'].data;hu=me.uv_layers['HeadUV'].data
  for face in me.polygons:
   if hd[face.index]:
    for i in face.loop_indices:uv[i].uv=hu[i].uv
  me.uv_layers.remove(me.uv_layers['HeadUV'])
 me.uv_layers.active=me.uv_layers['UVMap'];me.materials.clear()
 for name,prefix in [('Minotaur_A','min1_body'),('MinotaurHead_A','min1_head')]:me.materials.append(material(name,prefix,directory,not rebaked))
 me.polygons.foreach_set('material_index',hd.tolist());axe.data.materials.clear();axe.data.materials.append(material('MinotaurAxe','axe',directory))
 for f in axe.data.polygons:f.material_index=0
def tier(objects,tier,directory=None):
 directory=directory or P/'textures';spec=json.loads((P/'textures/min1_ramps.json').read_text())
 for obj in objects:
  for m in obj.data.materials:
   prefix=m.get('prefix','');base=m.node_tree.nodes.get('basecolor')
   if not prefix.startswith('min1_') or base is None:continue
   original=bpy.data.images.load(str(directory/(prefix+'_basecolor.png')),check_existing=True);key=str(directory)+prefix+tier
   img=bpy.data.images.get(key)
   if img is not None:bpy.data.images.remove(img);img=None
   if img is None:
    rgba=np.array(original.pixels[:],np.float32).reshape(-1,4);mask=bpy.data.images.load(str(directory/(prefix+'_region_mask.png')),check_existing=True);w=np.array(mask.pixels[:],np.float32).reshape(-1,4)[:,0:1];a=rgba[:,:3];linear=np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4);ramp=spec['materials'][0]['ramps']['min1_'+tier][0];t=np.clip((linear@np.array([.2126,.7152,.0722])-ramp['range'][0])/(ramp['range'][1]-ramp['range'][0]),0,1)*15;i=np.minimum(t.astype(int),14);u=t-i;colors=np.array(ramp['colors']);mapped=colors[i]*(1-u[:,None])+colors[i+1]*u[:,None];linear=linear*(1-w)+mapped*w;rgba[:,:3]=np.where(linear<=.0031308,linear*12.92,1.055*np.maximum(linear,0)**(1/2.4)-.055)
    img=bpy.data.images.new(key,width=original.size[0],height=original.size[1],alpha=True);img.pixels.foreach_set(rgba.ravel());img.update()
   base.image=img;m.node_tree.nodes.active=base
