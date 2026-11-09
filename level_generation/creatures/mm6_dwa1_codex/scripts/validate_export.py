from pathlib import Path
import sys,json,hashlib,numpy as np
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array,image_of
roles=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'];report={}
for file,kind in [('mm6_dwa1.glb','body'),('mm6_dwa1_axe.glb','axe')]:
 d,b=read_glb(P/'export'/file);counts=[];dims=set();maxerr=0;weight_rows=[];bones=len(d.get('skins',[{'joints':[]}])[0]['joints'])
 for i in range(len(d['accessors'])):assert np.isfinite(accessor_array(d,b,i)).all(),(file,i)
 for mesh in d['meshes']:
  assert len(mesh['primitives'])==1
  counts.append(sum(d['accessors'][q['indices']]['count']//3 for q in mesh['primitives']))
  for primitive_index,q in enumerate(mesh['primitives']):
   attrs=q['attributes'];pos=accessor_array(d,b,attrs['POSITION']);idx=accessor_array(d,b,q['indices']);assert idx.max()<len(pos)
   if kind=='body':
    total=np.zeros(len(pos),np.float64);sets=sorted(k for k in attrs if k.startswith('WEIGHTS_'))
    assert sets in (['WEIGHTS_0'],['WEIGHTS_0','WEIGHTS_1'])
    for key in sets:
     w=accessor_array(d,b,attrs[key]);j=accessor_array(d,b,attrs[key.replace('WEIGHTS_','JOINTS_')]);assert w.shape==(len(pos),4) and w.min()>=0 and j.max()<bones
     assert d['accessors'][attrs[key]]['componentType']==5126
     total+=w.astype(np.float64).sum(axis=1)
    err=float(abs(total-1).max());maxerr=max(maxerr,err);assert err<1e-4,(file,mesh['name'],err)
    weight_rows.append({'mesh':mesh['name'],'primitive':primitive_index,'sets':sets,'vertices':len(pos),'max_error':err})
   else:assert 'JOINTS_0'not in attrs
 for mat in d['materials']:
  assert mat.get('extras',{}).get('openyamm_specular_mask')is True and mat['pbrMetallicRoughness']['metallicFactor']==0
  for tx in [mat['pbrMetallicRoughness']['baseColorTexture']['index'],mat['pbrMetallicRoughness']['metallicRoughnessTexture']['index'],mat['normalTexture']['index']]:dims.add(image_of(d,b,tx)[0].size)
 variants=[v['name']for v in d['extensions']['KHR_materials_variants']['variants']];assert variants==['dwa1_a','dwa1_b','dwa1_c']
 assert len(d['meshes'][0]['extras']['openyamm_lods'])==3
 if kind=='body':assert len(d['meshes'][0]['extras']['openyamm_shadow_lods'])==4 and set(a['name']for a in d['animations'])==set(roles) and bones==57
 else:assert not d.get('animations')and not d.get('skins')
 report[kind]={'file':file,'triangles':counts,'joints':bones,'texture_sizes':sorted(dims),'variants':variants,'weight_sum_max_error':maxerr,'skin_weight_primitives':weight_rows,'weight_sum_tolerance':1e-4,'bytes':(P/'export'/file).stat().st_size,'sha256':hashlib.sha256((P/'export'/file).read_bytes()).hexdigest()}
# All sampled animation values, channel targets and inverse bind matrices survive packing and splitting exactly.
a,ab=read_glb(P/'export/mm6_dwa1_runtime_lod0.glb');d,b=read_glb(P/'export/mm6_dwa1.glb')
for sa,da in zip(a['animations'],d['animations']):
 assert sa['name']==da['name']and sa['channels']==da['channels']
 for x,y in zip(sa['samplers'],da['samplers']):
  for k in ['input','output']:assert np.array_equal(accessor_array(a,ab,x[k]),accessor_array(d,b,y[k]))
assert np.array_equal(accessor_array(a,ab,a['skins'][0]['inverseBindMatrices']),accessor_array(d,b,d['skins'][0]['inverseBindMatrices']))
report['animation_and_bind_parity']='exact'
g4=json.loads((P/'review/g4_exported.json').read_text());g5=json.loads((P/'review/g5_exported.json').read_text());g6=json.loads((P/'review/g6_exported.json').read_text());cloth=json.loads((P/'review/skirt_intersections.json').read_text());motion=json.loads((P/'review/motion_metrics_exported.json').read_text());extra=json.loads((P/'review/extra_exported_gates.json').read_text());uv=json.loads((P/'review/uv_gate.json').read_text());report['clips']={}
for n in roles:
 p99=max(v['stretch_p99']for k,x in g4.items()if k.split(':')[0]==n for v in x.values());hand=max(x['max_edge_ratio']for x in g5[n].values());contact=max(v[0]for v in g6[n]['contacts'].values());assert p99<=2 and hand<4.5 and contact<=.002 and cloth[n]['max_crossing_edges']==0;assert extra[n]['floor_min_max_m'][0]>=-.002
 if n!='Dead':assert not motion['production'][n]['trace_flags']
 report['clips'][n]={'G4_arm_p99':p99,'G5_hand_max':hand,'G6_max_contact_m':contact,'skirt_crossing_edges':0,'floor_min_m':extra[n]['floor_min_max_m'][0],'posture':g6[n]['posture']}
for layer,r in uv.items():
 assert not r['collapsed_faces']and r['overlap_texels']==0
 for part,(lo,mid,hi)in r['density_px_per_cm'].items():assert lo>mid*.25 and hi<mid*3,(layer,part,lo,mid,hi)
blow=extra['Attack']['blow'];assert blow['signed_lead']>.4 and blow['edge_share']>.8;report['blow']=blow
for name in ['viewer_check.json','playback_check.json']:
 r=json.loads((P/'review'/name).read_text());assert r['ready']=='true'and not r['consoleErrors']and not r['failed']and r['switched']==24
 if 'playback'in r:assert len(r['playback'])==16 and all(x['ok']for x in r['playback'])
round4={}
for name in ['sole_gate','elbow_gate','artifact_parity','locomotion_gate','flap_stretch_gate','bindings_check','palms_gate']:
 r=json.loads((P/f'review/round4/{name}.json').read_text());assert r['pass'],name
 if 'runtime_sha256'in r:assert r['runtime_sha256']==report['body']['sha256']
 round4[name]={k:v for k,v in r.items()if k!='clips'}
assert json.loads((P/'review/round4/gate_run.json').read_text())['runtime_sha256']==report['body']['sha256']
for name in ['viewer_check.json','playback_check.json']:
 assert json.loads((P/'review'/name).read_text())['runtime_artifact_sha256']==report['body']['sha256']
report['review_round4']=round4

for evidence in ['final_visual','lod_gates']:
 r=json.loads((P/f'review/round4/{evidence}.json').read_text());assert r['pass']and r['runtime_sha256']==report['body']['sha256'];report[evidence]=r

report['status']='PASS';(P/'review/final_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':report['status'],'runtime_sha256':report['body']['sha256'],'axe_sha256':report['axe']['sha256'],'body_triangles':report['body']['triangles'],'axe_triangles':report['axe']['triangles'],'max_weight_error':report['body']['weight_sum_max_error']},indent=2))
