import bpy,bmesh,sys,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3/uv_master.blend'));C.reset();o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];s=bpy.context.scene;pv=np.array([a.value for a in o.data.attributes['piece'].data])
for mi,prefix in [(1,'head'),(2,'hands')]:
 m=bpy.data.materials.new('MerchantHead_A'if mi==1 else'MerchantHands_A');m.use_nodes=True;nt=m.node_tree;bs=nt.nodes.get('Principled BSDF');ts={}
 for key in ['basecolor','normal','metal_rough']:
  t=nt.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(P/'textures/round3'/f'{prefix}_{key}.png'),check_existing=False);t.image.colorspace_settings.name='sRGB'if key=='basecolor'else'Non-Color';ts[key]=t
 nt.links.new(ts['basecolor'].outputs['Color'],bs.inputs['Base Color']);nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(ts['normal'].outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal']);sp=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(ts['metal_rough'].outputs['Color'],sp.inputs[0]);nt.links.new(sp.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sp.outputs['Blue'],bs.inputs['Metallic']);nt.nodes.active=ts['basecolor'];o.data.materials[mi]=m
# Let the neck base and collar follow the same neck joint, with a soft transition into the head.
for v in o.data.vertices:
 part=pv[v.index];x,y,z=v.co;t=0
 if part==0 and z<1.475:t=float(np.clip((1.475-z)/.055,0,1))
 elif part==1 and abs(x)<.21 and z>1.31:t=float(np.clip((z-1.31)/.065,0,1))*float(np.clip((.21-abs(x))/.055,0,1))
 if t:
  t=t*t*(3-2*t);w={o.vertex_groups[g.group].name:g.weight*(1-t)for g in v.groups};w['B_Neck']=w.get('B_Neck',0)+t
  for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
  ws=sorted(w.items(),key=lambda x:-x[1])[:4];total=sum(x for _,x in ws)
  for n,x in ws:
   if x>1e-8:o.vertex_groups[n].add([v.index],x/total,'REPLACE')
C.reset();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round3/master.blend'));common.workbench_clay(s,True);s.display.shading.show_specular_highlight=False
for role,t in [('Standing',0),('Attack',.375),('Attack',.9167),('Death',1.3)]:
 C.activate(role,t);common.render_views(str(P/'review/round3'/f'master_{role}_{t}'),1.15,1.2,views=('front','left','three_quarter'),resolution=(800,900))
 if role=='Standing':
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();coords=[v.co.copy()for v in me.vertices];ev.to_mesh_clear()
  for name,ids,scale in [('face',np.where(np.isin(pv,[0,11,14,15]))[0],.43),('hand',np.where(pv==3)[0],.23)]:
   center=sum((coords[i]for i in ids),Vector())/len(ids);common.render_views(str(P/'review/round3'/('new_'+name)),center.z,scale,views=('front','left','back','three_quarter'),target=(center.x,center.y),resolution=(800,800))
