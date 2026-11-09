"""Selected-to-active texture/normal baking from the unreduced, fitted creature."""
import bpy,bmesh,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]

def subset(ob,index,name):
 out=ob.copy();out.data=ob.data.copy();bpy.context.collection.objects.link(out);out.name=name;out.parent=None
 for m in list(out.modifiers):out.modifiers.remove(m)
 bm=bmesh.new();bm.from_mesh(out.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=index],context='FACES');bm.to_mesh(out.data);bm.free();return out

def rebake(folder,size):
 folder.mkdir(parents=True,exist_ok=True);scene=bpy.context.scene;rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();targets=[bpy.data.objects['Body'],bpy.data.objects['KnifeAsset']]
 with bpy.data.libraries.load(str(P/'work/rig_textured.blend'),link=False)as(src,dst):dst.objects=['Body','KnifeAsset']
 high=dst.objects
 for ob in high:
  bpy.context.collection.objects.link(ob);ob.parent=None
  for m in list(ob.modifiers):ob.modifiers.remove(m)
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1;scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=.006;scene.render.bake.max_ray_distance=.025;scene.render.bake.margin=8;scene.render.bake.normal_space='TANGENT'
 paths=[]
 for oi,(low,hi)in enumerate(zip(targets,high)):
  for mi in range(len(low.data.materials)):
   label=['mfp','mfp_head'][mi]if oi==0 else 'knife';dst=subset(low,mi,'Bake destination');src=subset(hi,mi,'Bake source');original=src.data.materials[mi];src.data.materials.clear();mat=original.copy();src.data.materials.append(mat)
   for f in src.data.polygons:f.material_index=0
   dmat=bpy.data.materials.new('Bake receiver');dmat.use_nodes=True;dst.data.materials.clear();dst.data.materials.append(dmat)
   for f in dst.data.polygons:f.material_index=0
   node=dmat.node_tree.nodes.new('ShaderNodeTexImage');dmat.node_tree.nodes.active=node;nt=mat.node_tree;output=nt.nodes.get('Material Output');bs=nt.nodes.get('Principled BSDF');links={key:bs.inputs[key].links[0].from_node for key in ['Base Color','Roughness']if bs.inputs[key].links};base=links['Base Color'];normal=next(n for n in nt.nodes if n.type=='TEX_IMAGE'and n.image and 'normal'in n.image.name.lower());orm=next(n for n in nt.nodes if n.type=='TEX_IMAGE'and n.image and 'metal_rough'in n.image.name.lower());emit=nt.nodes.new('ShaderNodeEmission');mask=nt.nodes.new('ShaderNodeTexImage')
   if oi==0:mask.image=bpy.data.images.load(str(P/'textures'/f'{label}_region_mask.png'),check_existing=True);mask.image.colorspace_settings.name='Non-Color'
   records={}
   for kind,source in [('basecolor',base),('metal_rough',orm),('region_mask',mask),('normal',normal)]:
    if oi==1 and kind=='region_mask':continue
    image=bpy.data.images.new('Baked '+label+' '+kind,width=size,height=size,alpha=False);image.colorspace_settings.name='sRGB'if kind=='basecolor'else'Non-Color';node.image=image
    for link in list(output.inputs['Surface'].links):nt.links.remove(link)
    if kind=='normal':nt.links.new(bs.outputs['BSDF'],output.inputs['Surface'])
    else:nt.links.new(source.outputs['Color'],emit.inputs['Color']);nt.links.new(emit.outputs['Emission'],output.inputs['Surface'])
    bpy.ops.object.select_all(action='DESELECT');src.hide_render=False;dst.hide_render=False;src.select_set(True);dst.select_set(True);bpy.context.view_layer.objects.active=dst;bpy.ops.object.bake(type='NORMAL'if kind=='normal'else'EMIT')
    path=folder/f'{label}_{kind}.png';image.filepath_raw=str(path);image.file_format='PNG';image.save();records[kind]=str(path)
   paths.append({'object':low.name,'material':mi,'label':label,'paths':records})
   bpy.data.objects.remove(src,do_unlink=True);bpy.data.objects.remove(dst,do_unlink=True)
 for ob in high:bpy.data.objects.remove(ob,do_unlink=True)
 for entry in paths:
  ob=bpy.data.objects[entry['object']];old=ob.data.materials[entry['material']];mat=old.copy();ob.data.materials[entry['material']]=mat
  for node in mat.node_tree.nodes:
   if node.type!='TEX_IMAGE'or not node.image:continue
   name=node.image.name.lower();kind='normal'if 'normal'in name else 'metal_rough'if 'metal_rough'in name else 'basecolor'
   node.image=bpy.data.images.load(entry['paths'][kind],check_existing=True);node.image.colorspace_settings.name='sRGB'if kind=='basecolor'else'Non-Color'
 (folder/'bake.json').write_text(json.dumps({'resolution':size,'source':'work/rig_textured.blend','selected_to_active':True,'cage_extrusion_m':.006,'max_ray_m':.025,'materials':paths},indent=2));return paths
