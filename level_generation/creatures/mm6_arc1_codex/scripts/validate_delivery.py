"""Assert the selected batch exports, attachment transforms, materials, sources and evidence."""
import json,sys,hashlib
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array,image_of
from split_attachment import split_primitive
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'files':{},'preservation':{},'gates':{}}
source,sb=read_glb(P/'export/mm6_arc1_lods_shadowfix.glb')
def channels(d,b):
 out={}
 for a in d.get('animations',[]):
  for c in a['channels']:
   t=c['target'];s=a['samplers'][c['sampler']];out[a['name'],d['nodes'][t['node']]['name'],t['path']]=(accessor_array(d,b,s['input']),accessor_array(d,b,s['output']))
 return out
for name in ['mm6_arc1.glb','mm6_arc1_bow.glb','mm6_arc1_arrow.glb']:
 path=P/'export'/name;d,b=read_glb(path);tri={};influences=0;weight_error=0.
 for m in d['meshes']:
  tri[m['name']]=0
  for p in m['primitives']:
   attrs={k:accessor_array(d,b,v)for k,v in p['attributes'].items()};idx=accessor_array(d,b,p['indices']);assert idx.max()<len(attrs['POSITION']);assert all(np.isfinite(v).all()for v in attrs.values());assert abs(np.linalg.norm(attrs['NORMAL'],axis=1)-1).max()<.001;tri[m['name']]+=len(idx)//3
   weights=[v for k,v in attrs.items()if k.startswith('WEIGHTS_')]
   if weights:
    w=np.concatenate(weights,axis=1);weight_error=max(weight_error,float(abs(w.sum(1)-1).max()));assert abs(w.sum(1)-1).max()<1e-4;influences=max(influences,int((w>1e-6).sum(1).max()));assert influences<=8
   assert len(m['primitives'])==1
 sizes=[list(image_of(d,b,i)[0].size)for i in range(len(d['textures']))]
 for m in d['materials']:
  assert m['pbrMetallicRoughness']['metallicFactor']==0;assert m['extras']['openyamm_specular_mask'] is True
 if name=='mm6_arc1.glb':
  assert len(d['skins'])==1 and len(d['skins'][0]['joints'])==63
  assert len(d['meshes'])==8 and len(d['images'])==4 and len(d['materials'])==3
  assert all(x==[2080,1024]for x in sizes)
  assert [x['name']for x in d['extensions']['KHR_materials_variants']['variants']]==['arc1_a','arc1_b','arc1_c']
  expected=channels(source,sb);actual=channels(d,b);assert expected.keys()==actual.keys()
  for k in expected:assert all(np.array_equal(x,y)for x,y in zip(expected[k],actual[k])),k
  report['preservation']['all_animation_channels_and_times_identical_after_split_and_head_merge']=True
  report['clips']={a['name']:max(float(accessor_array(d,b,s['input']).max())for s in a['samplers'])for a in d['animations']};assert set(report['clips'])=={'Standing','Walking','Attack','Cast','Hit','Death','Dead','Fidget'}
 else:
  assert not d.get('skins')and not d.get('animations')and len(d['meshes'])==4
  bone='Bow'if '_bow' in name else 'Arrow';slot=source['skins'][0]['joints'].index(next(i for i,n in enumerate(source['nodes'])if n.get('name')==bone));ib=accessor_array(source,sb,source['skins'][0]['inverseBindMatrices'])[slot].reshape(4,4).T;errors=[]
  for level in range(4):
   pts=[]
   for p in source['meshes'][level]['primitives']:
    _,t=split_primitive(source,sb,p,slot)
    if len(t):pts.extend(accessor_array(source,sb,p['attributes']['POSITION'])[np.unique(t)].tolist())
   pts=np.c_[np.array(pts),np.ones(len(pts))]@ib.T
   p=d['meshes'][level]['primitives'][0];actual=accessor_array(d,b,p['attributes']['POSITION']);err=max(cKDTree(pts[:,:3]).query(actual)[0].max(),cKDTree(actual).query(pts[:,:3])[0].max());assert err<1e-6,(bone,level,err);errors.append(float(err))
  report['preservation'][bone+'_split_position_error_m']=errors
 report['files'][str(path.relative_to(P))]={'sha256':sha(path),'bytes':path.stat().st_size,'triangles':tri,'texture_sizes':sizes,'max_influences':influences,'max_skin_weight_sum_error':weight_error}
# Meshy retained the dedicated head UV per corner; body UV is matched geometrically by transfer_uv.py.
d,b=read_glb(P/'texturing/arc1_head_upload.glb');r,rb=read_glb(P/'meshy/head_retexture_v1/model_urls_glb.glb');a=d['meshes'][0]['primitives'][0];z=r['meshes'][0]['primitives'][0]
u=accessor_array(d,b,a['attributes']['TEXCOORD_0'])[accessor_array(d,b,a['indices']).ravel()];v=accessor_array(r,rb,z['attributes']['TEXCOORD_0'])[accessor_array(r,rb,z['indices']).ravel()];assert np.array_equal(u,v);report['preservation']['head_UV_per_corner_identical_to_upload']=True
native=json.loads((P/'source/native_inputs.json').read_text());assert all(sha(P.parents[2]/f)==h for f,h in native.items());report['preservation']['read_only_native_hashes_unchanged']=len(native)
g4=json.loads((P/'work/g4_equipped.json').read_text());g5=json.loads((P/'work/g5_final.json').read_text());g6=json.loads((P/'work/g6_contacts.json').read_text());eq=json.loads((P/'work/equipment_gate.json').read_text());trace=json.loads((P/'review/trace_export.json').read_text())
for clip in report['clips']:
 poses=[v for k,p in g4.items()if k.split(':')[0]==clip for v in p.values()]
 data={'arm_p99':max(v['stretch_p99']for v in poses),'arm_max':max(v['stretch_max']for v in poses),'elbow_area_min':min(v['elbow_area_ratio']for v in poses),'finger_max':max(v['max_edge_stretch']for v in g5[clip].values()),'body_contact_cm':max([v[0]for v in g6[clip].values()]+[0]),'equipment_contact_cm':eq[clip]['equipment_contact_cm'],'floor_min_m':eq[clip]['floor_min_cm']/100,'pelvis_range_m':eq[clip]['pelvis_range_m'],'trunk_lean_degrees':eq[clip]['trunk_lean_degrees'],'trace_flags':trace[clip]['flags']}
 assert data['arm_p99']<2 and data['finger_max']<2.2 and data['body_contact_cm']==0 and data['equipment_contact_cm']==0 and data['floor_min_m']>=0 and not data['trace_flags'],(clip,data)
 report['gates'][clip]=data
checker=json.loads((P/'review/check_viewer.log').read_text());assert checker['ready']=='true'and checker['switched']==24 and not checker['failed']and not checker['consoleErrors'];report['viewer']=checker
for f in ['rig_equipped.blend','rig_textured.blend','runtime_authoring.blend']:report['files']['work/'+f]={'sha256':sha(P/'work'/f)}
report['trace_source_export_sha256']=sha(P/'export/mm6_arc1_lod0.glb')
anatomy=json.loads((P/'review/round3/anatomy_and_feet.json').read_text());assert not anatomy['failures'];report['review_round_3']=anatomy
transition=json.loads((P/'review/round3/transitions_and_head.json').read_text());assert max(transition['head_contacts_cm'].values())<=1;report['review_round_3']['transitions_and_head']=transition
import yaml
entries=yaml.safe_load((P/'integration/actors.yml').read_text())
for e in entries:
 an=e['animation'];assert an['cast']=='Cast' and an['events']['cast']=={'impact':1.2,'launch_socket':'Socket_Arrow_Release'};assert not an.get('sockets',{}).get('palm_right')
report['integration_actors_yml_changed']=sha(P/'integration/actors.yml')!=sha(P/'review/round3/baseline/integration/actors.yml')
weights=(P/'review/round3/check_bindings.log').read_text();assert 'BAD' not in weights;report['skin_weight_checker']=weights
actual=channels(*read_glb(P/'export/mm6_arc1.glb'))
attack={k[1:]:v for k,v in actual.items()if k[0]=='Attack'};cast={k[1:]:v for k,v in actual.items()if k[0]=='Cast'};assert attack.keys()==cast.keys()
assert all(all(np.array_equal(x,y)for x,y in zip(attack[k],cast[k]))for k in attack)
report['cast_exact_attack_copy']={'channels':len(attack),'equal_times_and_values':True}
metric=json.loads((P/'review/round2/reduction/final_material_metrics.json').read_text());assert not metric['failures'];report['reduction']=metric
report['head_all_lods']=json.loads((P/'review/round3/reduction/head_selected.json').read_text());assert all(max(v['head_contacts_cm'].values())<=1 for v in report['head_all_lods'].values())
report['distance_silhouettes']=json.loads((P/'review/round3/reduction/assembled_distance_metrics.json').read_text());assert not report['distance_silhouettes']['failures']
report['angular_acceleration']=json.loads((P/'review/round3/angular_acceleration.json').read_text());assert not report['angular_acceleration']['failures']
caps={'export/mm6_arc1.glb':[9531,5223,1904,620],'export/mm6_arc1_bow.glb':[2108,1150,420,193],'export/mm6_arc1_arrow.glb':[92,40,5,4]}
for name,maximum in caps.items():
 counts=list(report['files'][name]['triangles'].values())[:4];assert all(a>b for a,b in zip(counts,counts[1:]));assert all(a<=b for a,b in zip(counts,maximum))
reference={k[1:]:v[1][0]for k,v in actual.items()if k[0]=='Standing'};boundary={}
for clip in ['Standing','Fidget','Walking','Attack','Cast','Hit','Death']:
 worst=0.
 for k,v in actual.items():
  if k[0]!=clip:continue
  for sample in ([v[1][0]]if clip=='Death'else[v[1][0],v[1][-1]]):
   ref=reference[k[1:]];delta=float(abs(sample-ref).max())
   if k[-1]=='rotation':delta=min(delta,float(abs(sample+ref).max()))
   worst=max(worst,delta)
 assert worst<1e-5,(clip,worst);boundary[clip]=worst
report['exported_rest_boundaries_max_scalar_error']=boundary
report['skin_luminance']=json.loads((P/'review/round2/skin_luminance.json').read_text());assert report['skin_luminance']['pass']
report['lod_gates']={str(i):json.loads((P/f'review/round3/lod_gates/lod{i}/status.json').read_text())for i in range(4)};assert all(v['pass']for v in report['lod_gates'].values())
report['lod_gate_maxima']={}
for level in range(4):
 root=P/f'review/round3/lod_gates/lod{level}';read=lambda name:json.loads((root/name).read_text())
 arm=read('g4_equipped.json');hand=read('g5_final.json');body=read('g6_contacts.json');equipment=read('equipment_gate.json');contact=read('contact_gates.json');anatomy=read('anatomy_and_feet.json')
 row={'arm_p99':max(v['stretch_p99']for a in arm.values()for v in a.values()),'finger_max':max(v['max_edge_stretch']for a in hand.values()for v in a.values()),'body_penetration_cm':max([v[0]for a in body.values()for v in a.values()]+[0]),'equipment_penetration_cm':max(v['equipment_contact_cm']for v in equipment.values()),'floor_min_cm':min(v['floor_min_cm']for v in equipment.values()),'grip_gap_mm':max(max(v['grip_gap_mm'].values())for v in contact['clips'].values()),'grip_penetration_mm':max(v['grip_penetration_mm']for v in contact['clips'].values()),'sleeve_penetration_mm':max(v['sleeve_penetration_mm']for v in contact['clips'].values())}
 assert row['arm_p99']<2 and row['finger_max']<2.2 and row['body_penetration_cm']==0 and row['equipment_penetration_cm']==0 and row['floor_min_cm']>=0 and row['grip_gap_mm']<=3 and row['grip_penetration_mm']<=3 and row['sleeve_penetration_mm']<=2 and not contact['failures']and not anatomy['failures'],(level,row)
 report['lod_gate_maxima'][str(level)]=row
report['grip_palms_cloth_locomotion']=json.loads((P/'review/round3/contact_gates.json').read_text());assert not report['grip_palms_cloth_locomotion']['failures']

# R3 changes motion and only far silhouette vertices; prove maps, rig and near geometry stay intact.
report['review_round_3_preservation']={}
for name in ['mm6_arc1.glb','mm6_arc1_bow.glb','mm6_arc1_arrow.glb']:
 before,bb=read_glb(P/'review/round3/baseline/export'/name);after,ab=read_glb(P/'export'/name)
 assert before.get('materials')==after.get('materials'),name
 assert len(before.get('images',[]))==len(after.get('images',[]))
 for i in range(len(before.get('images',[]))):
  x,y=image_of(before,bb,i)[0],image_of(after,ab,i)[0];assert x.size==y.size and x.tobytes()==y.tobytes(),(name,i)
 changes=[]
 for mi,(bm,am)in enumerate(zip(before['meshes'],after['meshes'])):
  for bp,ap in zip(bm['primitives'],am['primitives']):
   assert np.array_equal(accessor_array(before,bb,bp['indices']),accessor_array(after,ab,ap['indices'])),(name,mi,'indices')
   for key in bp['attributes']:
    x,y=accessor_array(before,bb,bp['attributes'][key]),accessor_array(after,ab,ap['attributes'][key])
    same=np.array_equal(x,y)
    if not same:
     assert mi in [3,7] and key in ['POSITION','NORMAL','TANGENT'],(name,mi,key)
     changes.append({'mesh':mi,'attribute':key,'max_scalar_delta':float(abs(x-y).max())})
 report['review_round_3_preservation'][name]={'images_and_materials_identical':True,'changed_geometry_attributes':changes}
assert not report['integration_actors_yml_changed']
assert sha(P/'export/mm6_arc1_arrow.glb')==sha(P/'review/round3/baseline/export/mm6_arc1_arrow.glb')
shared=json.loads((P/'review/round3/shared_final/gates.json').read_text())
report['shared_runner']={'status':shared['status'],'counts':shared['counts'],'report':'review/round3/shared_final/gates.md','runner_sha256':shared['runner_sha256']}
report['technical_completion']='complete'if shared['status']=='PASS'else'pending_shared_gate_findings'
report['near_rebake_metrics_provenance']='R2 measurements retained: near geometry, UVs and every texture pixel verified identical. Current posed distance silhouettes were remeasured.'
report['status']='PASS'if shared['status']=='PASS'else'FAIL'
(P/'review/delivery_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('Export, bindings, source preservation, local gates and viewer checks pass. Shared runner:',shared['status'])
