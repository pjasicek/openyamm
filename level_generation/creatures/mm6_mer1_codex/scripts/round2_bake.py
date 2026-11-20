"""Rebake every candidate from the unreduced textured mesh, including lost detail in tangent normals."""
import bpy,bmesh,json,time,subprocess
from collections import Counter
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def bake(obj,folder):
 folder.mkdir(parents=True,exist_ok=True);scene=bpy.context.scene;rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 # The validated target already has fresh UVs: body 2K, head 1K, at least 33px island gaps.
 me=obj.data;me.calc_loop_triangles();uv=me.uv_layers.active.data
 for mi in range(2):
  area=0.
  for t in me.loop_triangles:
   if me.polygons[t.polygon_index].material_index==mi:
    a,b,c=[uv[l].uv for l in t.loops];area+=abs((b-a).cross(c-a))
  assert area>.05,('Collapsed UV layout',mi,area)
 with bpy.data.libraries.load(str(P/'work/round2/master.blend'),link=False)as(src,dst):dst.objects=[obj.name]
 high=dst.objects[0];scene.collection.objects.link(high);high.name='Bake source';high.parent=rig
 for mod in high.modifiers:
  if mod.type=='ARMATURE':mod.object=rig
 high.hide_render=False;high.hide_set(False)
 for i,m in enumerate(high.data.materials):high.data.materials[i]=m.copy()
 sources=list(high.data.materials);original=[];source_tex=[]
 for i,m in enumerate(sources):
  nt=m.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');original.append(out.inputs['Surface'].links[0].from_socket)
  base=bs.inputs['Base Color'].links[0].from_node.image;mr=bs.inputs['Roughness'].links[0].from_node.inputs[0].links[0].from_node.image
  mask=bpy.data.images.load(str(P/'textures/round2/mer1_region_mask.png'),check_existing=False)if i==0 and obj.name=='Body'else None
  if mask:mask.colorspace_settings.name='Non-Color'
  classes=bpy.data.images.load(str(P/'textures/round2'/('mer1_body_material_classes.png'if i==0 else'mer1_head_material_classes.png')),check_existing=False)if obj.name=='Body'else None
  if classes:classes.colorspace_settings.name='Non-Color'
  source_tex.append({'basecolor':base,'metal_rough':mr,'region_mask':mask,'material_classes':classes,'coverage':None})
 indices=[f.material_index for f in obj.data.polygons];obj.data.materials.clear();targets=[]
 for i in range(len(sources)):
  mat=bpy.data.materials.new(('Merchant_A'if i==0 else'MerchantHead_A')if obj.name=='Body'else'MerchantClub');mat.use_nodes=True;target=mat.node_tree.nodes.new('ShaderNodeTexImage');mat.node_tree.nodes.active=target;obj.data.materials.append(mat);targets.append(target)
 for f,i in zip(obj.data.polygons,indices):f.material_index=i
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.bake.use_selected_to_active=True;scene.render.bake.use_cage=True;scene.render.bake.cage_extrusion=.08;scene.render.bake.max_ray_distance=.16;scene.render.bake.margin=0;scene.render.bake.use_clear=False;scene.render.bake.normal_space='TANGENT';scene.render.bake.normal_r='POS_X';scene.render.bake.normal_g='POS_Y';scene.render.bake.normal_b='POS_Z'
 # Isolate corresponding pieces so an expanded bake cage cannot project the pouch onto the tunic.
 pairs=[]
 ids=sorted({Counter(obj.data.attributes['piece'].data[i].value for i in f.vertices).most_common(1)[0][0] for f in obj.data.polygons})if 'piece'in obj.data.attributes else[None]
 for pid in ids:
  pair=[]
  for source in [high,obj]:
   part=source.copy();part.data=source.data.copy();scene.collection.objects.link(part);part.hide_render=False;part.hide_set(False)
   if pid is not None:
    bm=bmesh.new();bm.from_mesh(part.data);layer=bm.verts.layers.int['piece'];keep={pid}
    if source==high:
     for child,parent in [(14,0),(15,0),(16,10),(17,12)]:
      if pid==parent and child not in ids:keep.add(child)
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if Counter(v[layer]for v in f.verts).most_common(1)[0][0]not in keep],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(part.data);bm.free()
   assert len(part.data.polygons)>0,(source.name,pid)
   pair.append(part)
  pairs.append(pair)
 high.hide_render=True;obj.hide_render=True
 maps=[{}for _ in sources];receipt={}
 for key in ['basecolor','region_mask','metal_rough','normal','material_classes','coverage']:
  for i,(m,target)in enumerate(zip(sources,targets)):
   im=bpy.data.images.new(f'{folder.name}_{i}_{key}',width=(2048 if i==0 else 1024),height=(2048 if i==0 else 1024),alpha=False);im.colorspace_settings.name='sRGB'if key=='basecolor'else'Non-Color';target.image=im;maps[i][key]=im
   nt=m.node_tree;out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL')
   if key=='normal':nt.links.new(original[i],out.inputs['Surface'])
   else:
    em=nt.nodes.new('ShaderNodeEmission');tex=nt.nodes.new('ShaderNodeTexImage');tex.image=source_tex[i][key]
    if tex.image:nt.links.new(tex.outputs['Color'],em.inputs['Color'])
    else:em.inputs['Color'].default_value=(1,1,1,1)if key=='coverage'else(0,0,0,1)
    nt.links.new(em.outputs[0],out.inputs['Surface'])
  started=time.time()
  for hi,lo in pairs:
   bpy.ops.object.select_all(action='DESELECT');hi.select_set(True);lo.select_set(True);bpy.context.view_layer.objects.active=lo;bpy.ops.object.bake(type='NORMAL'if key=='normal'else'EMIT')
  receipt[key]={'seconds':time.time()-started,'images':[]}
  for i in range(len(sources)):
   im=maps[i][key];im.filepath_raw=str(folder/f'{i}_{key}.png');im.file_format='PNG';im.save();receipt[key]['images'].append(str(Path(im.filepath_raw).relative_to(P)))
  print('REBAKE',folder.name,key,receipt[key]['seconds'],flush=True)
 # A self-baked UV coverage map distinguishes projection misses from unused atlas space.
 obj.hide_render=False;scene.render.bake.use_selected_to_active=False;scene.render.bake.use_clear=True
 for i,(m,target)in enumerate(zip(obj.data.materials,targets)):
  nt=m.node_tree;im=bpy.data.images.new(f'{folder.name}_{i}_uv_coverage',width=(2048 if i==0 else 1024),height=(2048 if i==0 else 1024),alpha=False);im.colorspace_settings.name='Non-Color';target.image=im;maps[i]['uv_coverage']=im;em=nt.nodes.new('ShaderNodeEmission');em.inputs['Color'].default_value=(1,1,1,1);nt.links.new(em.outputs[0],nt.nodes.get('Material Output').inputs['Surface'])
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.bake(type='EMIT')
 for i in range(len(sources)):
  im=maps[i]['uv_coverage'];im.filepath_raw=str(folder/f'{i}_uv_coverage.png');im.file_format='PNG';im.save()
 assert all(sum(im.pixels[0::4])>10000 for im in [row['uv_coverage']for row in maps]),'Empty bake coverage'
 from project_open_boundaries import complete
 complete(obj,high,source_tex,folder)
 subprocess.run(['/usr/bin/python3',str(P/'scripts/pad_rebake.py'),str(folder),str(len(sources))],check=True)
 for maps_i in maps:
  for im in maps_i.values():im.reload()
 for i,m in enumerate(obj.data.materials):
  nt=m.node_tree;bs=nt.nodes.get('Principled BSDF');nt.links.new(bs.outputs['BSDF'],nt.nodes.get('Material Output').inputs['Surface']);nodes={}
  for key,im in maps[i].items():n=nt.nodes.new('ShaderNodeTexImage');n.image=im;nodes[key]=n
  nt.links.new(nodes['basecolor'].outputs['Color'],bs.inputs['Base Color']);nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(nodes['normal'].outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal']);sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(nodes['metal_rough'].outputs['Color'],sep.inputs[0]);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic']);nt.nodes.active=nodes['basecolor'];m['openyamm_specular_mask']=True;m['openyamm_specular']=1.
 
 for pair in pairs:
  for part in pair:bpy.data.objects.remove(part,do_unlink=True)
 bpy.data.objects.remove(high,do_unlink=True);(folder/'receipt.json').write_text(json.dumps(receipt,indent=2));return maps
