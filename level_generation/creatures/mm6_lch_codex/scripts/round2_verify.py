"""Final byte-preservation, atlas, numeric quality and rig receipts. Failed quality gates remain failures."""
import sys,json,hashlib,io,csv
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parents[1];R=P/'review/triangle_rebake';sys.dont_write_bytecode=True;sys.path[:0]=[str(P/'scripts'),str(P.parents[2]/'tools')]
from build_actor_lods import read_glb,accessor_bytes
from merge_head_material import accessor_array,image_of
from round1_metrics import measure,ssim
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old,ob=read_glb(P/'review/triangle_reduction/baseline/export/mm6_lch.glb');new,nb=read_glb(P/'export/mm6_lch.glb')
assert old['nodes']==new['nodes'] and old['materials']==new['materials'] and old.get('extensions')==new.get('extensions')
for a,b in zip(old['skins'],new['skins']):
 assert {k:v for k,v in a.items()if k!='inverseBindMatrices'}=={k:v for k,v in b.items()if k!='inverseBindMatrices'}
 assert accessor_bytes(old,ob,a['inverseBindMatrices'])==accessor_bytes(new,nb,b['inverseBindMatrices'])
for a,b in zip(old['animations'],new['animations']):
 assert a['name']==b['name'] and a['channels']==b['channels']
 for x,y in zip(a['samplers'],b['samplers']):
  assert x.get('interpolation','LINEAR')==y.get('interpolation','LINEAR')
  for k in ['input','output']:assert accessor_bytes(old,ob,x[k])==accessor_bytes(new,nb,y[k])
assert len(new['animations'])==8 and len(new['skins'][0]['joints'])==54
assert sha(P/'integration/actors.yml')=='2033f4e7f77885b834410020a6492003f919b27f983f5c31ecf1812eba9d3b8d'
assert (P/'textures/lch_ramps.json').read_bytes()==(P/'textures/round2/lch_ramps.json').read_bytes()
rects=read(R/'texture_layout.json')['rectangles_lower_left'];counts=[]
for level in range(4):
 mesh=new['meshes'][level];assert len(mesh['primitives'])==1
 prim=mesh['primitives'][0];counts.append(new['accessors'][prim['indices']]['count']//3)
 uv=accessor_array(new,nb,prim['attributes']['TEXCOORD_0']);head=uv[:,0]>.5;u=uv[:,0]*2080-head*1056;v=uv[:,1]*1024;x,y,w,h=rects[level]
 assert u.min()>=x-.001 and u.max()<=x+w+.001
 assert v.min()>=1024-y-h-.001 and v.max()<=1024-y+.001
for mi in [2,3,6,7]:
 a=old['meshes'][mi]['primitives'][0];b=new['meshes'][mi]['primitives'][0]
 assert accessor_bytes(old,ob,a['indices'])==accessor_bytes(new,nb,b['indices'])
 for k,i in a['attributes'].items():
  if k!='TEXCOORD_0':assert accessor_bytes(old,ob,i)==accessor_bytes(new,nb,b['attributes'][k]),(mi,k)
assert counts==[6290,3466,2907,897] and all(a>b for a,b in zip(counts,counts[1:]))
assert all(a<=b for a,b in zip(counts,[16274,8135,2907,897]))
assert len(new['images'])==4
for texture in range(4):assert image_of(new,nb,texture)[0].size==(2080,1024)
for prefix in ['lch','lch_head']:
 for suffix in ['basecolor_1k','normal_1k','metal_rough_1k','region_mask']:assert Image.open(P/f'textures/round2/{prefix}_{suffix}.png').size==(1024,1024)
 assert not np.asarray(Image.open(P/f'textures/round2/{prefix}_metal_rough_1k.png'))[:,:,2].any()
 assert not np.asarray(Image.open(P/f'textures/round2/{prefix}_region_mask.png'))[:,:,1:].any()
# Check metric identity and sensitivity, and the vertical atlas convention explicitly.
a=np.arange(40*40*3,dtype=np.uint8).reshape(40,40,3);assert abs(ssim(a,a)-1)<1e-12 and ssim(a,np.zeros_like(a))<.95
assert (1024-528-480)/1024==16/1024
metrics=[]
for level in range(4):
 tiers=[]
 for tier in range(3):
  views=[measure(R/f'textured/baseline/tier{tier}/lod{level}/{k}.png',R/f'textured/final/tier{tier}/lod{level}/{k}.png')for k in range(8)]
  tiers.append({'tier':tier,'views':views,'pooled_iou':sum(v['intersection']for v in views)/sum(v['union']for v in views),'min_iou':min(v['iou']for v in views),'min_ssim':min(v['ssim']for v in views)})
 row={'level':level,'triangles':counts[level],'actor_height_px':[700,550,220,88][level],'tiers':tiers,'pooled_iou':min(t['pooled_iou']for t in tiers),'min_iou':min(t['min_iou']for t in tiers),'min_ssim':min(t['min_ssim']for t in tiers)}
 row['silhouette_pass']=row['min_iou']>=.99 if level==0 else row['pooled_iou']>=.97 and(level!=3 or row['min_iou']>=.95)
 row['ssim_ge_095']=row['min_ssim']>=.95
 if level in [2,3]:
  v=[measure(R/f'textured/accepted_far/tier0/lod{level}/{k}.png',R/f'textured/final/tier0/lod{level}/{k}.png')for k in range(8)]
  row['versus_same_accepted_far_geometry']={'min_iou':min(x['iou']for x in v),'min_ssim':min(x['ssim']for x in v),'views':v}
 metrics.append(row)
(R/'packaged_metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
gates={};failures=[]
for level in range(4):
 g=read(R/f'lod_{level}_rig.json');c=read(R/f'lod_{level}_contacts.json');assert len(g)==len(c)==8
 assert max(max(x['g4_arm_edge_max'],x['g5_hand_edge_max'],x['whole_mesh_edge_max'])for x in g.values())<1.001
 gates[level]={'g4_max':max(x['g4_arm_edge_max']for x in g.values()),'g5_max':max(x['g5_hand_edge_max']for x in g.values()),'whole_mesh_max':max(x['whole_mesh_edge_max']for x in g.values()),'floor_min_mm':min(x['lowest_vertex_m']for x in g.values())*1000}
 for clip,parts in c.items():
  for part,value in parts.items():
   if value[0]>(1 if part=='head'else .2):failures.append({'lod':level,'clip':clip,'part':part,'depth_mm':value[0]*10})
base=read(R/'lod_baseline_contacts.json');zero=read(R/'lod_0_contacts.json')
for clip in base:
 for part in base[clip]:
  if part.endswith('_cloth'):assert base[clip][part]==zero[clip][part]
trace=read(P/'work/trace_export.json');assert all(not x['flags']for x in trace.values())
credits=sum(j.get('consumed_credits',0)for j in read(P/'creature_3d_progress.json')['meshy']['jobs'].values());assert credits<=100
proof={'runtime_sha256':sha(P/'export/mm6_lch.glb'),'rig_nodes_sockets_inverse_binds_animation_sampler_bytes_unchanged':True,'material_definitions_tier_ramps_unchanged':True,'actors_unchanged':True,'far_2_3_positions_normals_weights_indices_unchanged':True,'far_uvs':'affine mapping into their independently rebaked tiles','shared_runtime_maps':4,'body_and_head_set_px':[1024,1024],'triangles':counts,'rig_gates':gates,'g6_rotation_trace':'pass; no flags','contact_failures':failures,'lod0_cloth_identical_to_accepted_baseline':True,'attack_hyperextension_degrees':[14.656786,9.642762],'absolute_done_criteria_pass':False,'remaining':'Far silhouette/ratio targets; distant textured differences; inherited elbow and contact gates. Not ready for integration.','credits_consumed_total':credits,'new_credits':0}
(R/'preservation.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({'triangles':counts,'quality':[{k:v for k,v in x.items()if k not in ['tiers','versus_same_accepted_far_geometry']}for x in metrics],'rig_gates':gates,'contact_failure_count':len(failures),'credits':credits},indent=2))
