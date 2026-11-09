"""Check final exports, texture translation, bindings and provenance without replacing shared rig gates."""
import sys,json,hashlib,subprocess,collections,shutil
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];R=P/'review/round5';sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'))
from merge_head_material import read_glb,accessor_array,image_of
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'files':{},'preservation':{},'texture_verification':{}}
def channels(d,b):
 out={}
 for a in d.get('animations',[]):
  for c in a['channels']:
   t=c['target'];s=a['samplers'][c['sampler']]
   out[a['name'],d['nodes'][t['node']]['name'],t['path']]=(accessor_array(d,b,s['input']),accessor_array(d,b,s['output']))
 return out
caps={'mm6_arc1.glb':[9531,5223,1904,620],'mm6_arc1_bow.glb':[2108,1150,420,193],'mm6_arc1_arrow.glb':[92,40,5,4]}
for name,counts in caps.items():
 file=P/'export'/name;d,b=read_glb(file);old,ob=read_glb(R/'baseline/export'/name);raw,rb=read_glb(P/'work/round5/runtime_unpadded'/name)
 triangles={};weight_error=0.;uv_error=0.;centroid_samples=0;centroid_exact=0;max_centroid_channel_difference=0.
 density={'mm6_arc1.glb':.75,'mm6_arc1_bow.glb':.875,'mm6_arc1_arrow.glb':1.}[name];oldsize=np.rint(np.array(image_of(raw,rb,0)[0].size)*density).astype(int);newsize=np.array(image_of(d,b,0)[0].size)
 from PIL import Image
 images=[np.array(image_of(raw,rb,i)[0].convert('RGBA').resize(tuple(oldsize),Image.Resampling.NEAREST if i==3 else Image.Resampling.LANCZOS))for i in range(len(raw['textures']))]
 padded=[np.array(image_of(d,b,i)[0].convert('RGBA'))for i in range(len(d['textures']))]
 assert d['materials']==old['materials'] and len(d['images'])==len(old['images'])
 for mi,(mesh,om,rm)in enumerate(zip(d['meshes'],old['meshes'],raw['meshes'])):
  triangles[mesh['name']]=0
  for prim,op,rp in zip(mesh['primitives'],om['primitives'],rm['primitives']):
   ix=accessor_array(d,b,prim['indices']).reshape(-1,3);triangles[mesh['name']]+=len(ix)
   assert np.array_equal(ix,accessor_array(old,ob,op['indices']).reshape(-1,3))
   weights=[]
   for k,ai in prim['attributes'].items():
    v=accessor_array(d,b,ai);assert np.isfinite(v).all()
    if k!='TEXCOORD_0':assert np.array_equal(v,accessor_array(old,ob,op['attributes'][k])),(name,mi,k)
    if k.startswith('WEIGHTS_'):weights.append(v)
   if weights:weight_error=max(weight_error,float(abs(np.concatenate(weights,1).sum(1)-1).max()))
   if 'Shadow' in mesh['name']:assert d['materials'][prim['material']].get('alphaMode','OPAQUE')=='OPAQUE'
   u=accessor_array(raw,rb,rp['attributes']['TEXCOORD_0'])*oldsize;v=accessor_array(d,b,prim['attributes']['TEXCOORD_0'])*newsize
   delta=v-u;uv_error=max(uv_error,float(abs(delta-np.rint(delta)).max()),float(abs(delta[ix]-delta[ix][:,0,None,:]).max()))
   assert uv_error<.001,(name,mi,uv_error)
   uu=np.clip(np.floor(u[ix].mean(1)).astype(int),[0,0],oldsize-1);vv=np.clip(np.floor(v[ix].mean(1)).astype(int),[0,0],newsize-1)
   for a,z in zip(images,padded):
    err=abs(a[uu[:,1],uu[:,0]].astype(float)-z[vv[:,1],vv[:,0]]).max(1)
    centroid_samples+=len(err);centroid_exact+=int((err==0).sum());max_centroid_channel_difference=max(max_centroid_channel_difference,float(err.max()))
 assert weight_error<1e-4
 assert list(triangles.values())[:4]==counts and all(a>b for a,b in zip(counts,counts[1:]))
 assert centroid_exact/centroid_samples>.998,(name,centroid_exact,centroid_samples)
 plan=json.loads((P/'work/round5'/f'{name}.uv_translation.json').read_text())
 rects=[v['rect']for v in plan['charts'].values()]
 for i,(x,y,w,h)in enumerate(rects):
  assert x>=0 and y>=0 and x+w<=newsize[0] and y+h<=newsize[1]
  # Dilated polygon masks, rather than their bounding rectangles, are disjoint (asserted during packing).
 report['files']['export/'+name]={'sha256':sha(file),'bytes':file.stat().st_size,'triangles':triangles,'images':len(d['images']),'image_dimensions':newsize.tolist(),'max_skin_weight_sum_error':weight_error}
 report['preservation'][name]={'geometry_indices_weights_normals_and_materials_equal_R4':True,'texture_count_unchanged':True}
 report['texture_verification'][name]={'max_integer_translation_or_triangle_distortion_px':uv_error,'exact_centroid_samples':centroid_exact,'total_centroid_samples':centroid_samples,'max_centroid_channel_difference_255':max_centroid_channel_difference,'note':'Tiny float32 UV rounding can choose the neighbouring texel exactly on integer boundaries. Geometry and every triangle UV shape are preserved; uniform per-asset density reduction as recorded. Dilated polygon masks are disjoint; rectangle corners may overlap.'}
 if name=='mm6_arc1.glb':
  topology=[]
  for mesh in d['meshes']:
   p=mesh['primitives'][0];points=accessor_array(d,b,p['attributes']['POSITION']);tri=accessor_array(d,b,p['indices']).reshape(-1,3)
   xyz,rev=np.unique(np.round(points,5),axis=0,return_inverse=True);tri=rev[tri]
   edges=np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1);edge,count=np.unique(edges,axis=0,return_counts=True);bd=edge[count==1]
   heights=xyz[bd][:,:,1]
   topology.append({'mesh':mesh['name'],'boundary_edges':len(bd),'nonmanifold_edges':int((count>2).sum()),'boundary_edges_entirely_below_095m':int((heights.max(1)<.95).sum()),'boundary_edges_intersecting_125_to_145m_band':int(((heights.max(1)>1.25)&(heights.min(1)<1.45)).sum())})
  report['closed_body_scan']={'status':'UNVERIFIED','position_weld_m':1e-5,'rows':topology,'note':'No new topology changes. Height-band counts include clothing, neck, hair and quiver openings; shoulder-band loops need intended-opening classification before certifying the closed-body criterion.'}
  actual=channels(d,b);source=channels(raw,rb);assert actual.keys()==source.keys()
  for k in actual:
   assert np.array_equal(actual[k][0],source[k][0])
   if k[0]in ['Attack','Cast']and k[1:] == ('Arrow','rotation'):
    st,sv=source[(k[0],'Arrow','scale')];t=source[k][0].ravel()
    visible=np.max(np.stack([np.interp(t,st.ravel(),sv[:,i])for i in range(3)],1),1)>1e-6
    assert np.array_equal(actual[k][1][visible],source[k][1][visible])
   else:assert np.array_equal(actual[k][1],source[k][1]),k
  report['preservation']['visible_keyed_poses_unchanged_by_hidden_arrow_fix']=True
  attack={k[1:]:v for k,v in actual.items()if k[0]=='Attack'};cast={k[1:]:v for k,v in actual.items()if k[0]=='Cast'}
  assert attack.keys()==cast.keys()and all(all(np.array_equal(x,y)for x,y in zip(attack[k],cast[k]))for k in attack)
  report['cast_exact_attack_copy']={'channels':len(attack),'equal':True}
  ref={k[1:]:v[1][0]for k,v in actual.items()if k[0]=='Standing'};boundary={}
  for clip in ['Standing','Fidget','Walking','Attack','Cast','Hit','Death']:
   worst=0.
   for k,v in actual.items():
    if k[0]!=clip:continue
    for sample in ([v[1][0]]if clip=='Death'else[v[1][0],v[1][-1]]):
     error=float(abs(sample-ref[k[1:]]).max())
     if k[-1]=='rotation':error=min(error,float(abs(sample+ref[k[1:]]).max()))
     worst=max(worst,error)
   assert worst<1e-5,(clip,worst);boundary[clip]=worst
  report['rest_boundaries']=boundary;report['clips']={a['name']:max(float(accessor_array(d,b,s['input']).max())for s in a['samplers'])for a in d['animations']}
  assert len(d['skins'][0]['joints'])==63 and len(report['clips'])==8
native=json.loads((P/'source/native_inputs.json').read_text());assert all(sha(P.parents[2]/f)==h for f,h in native.items());report['preservation']['native_files_unchanged']=len(native)
r=subprocess.run([sys.executable,str(P.parents[2]/'output/codex_batch/check_bindings.py'),str(P/'integration/actors.yml')],capture_output=True,text=True)
(R/'check_bindings.log').write_text(r.stdout+r.stderr);r.check_returncode();assert 'BAD'not in r.stdout+r.stderr
report['bindings']='PASS, no BAD line';report['integration_actors_yml_changed']=sha(P/'integration/actors.yml')!=sha(R/'baseline/integration/actors.yml');assert not report['integration_actors_yml_changed']
checker=json.loads((P/'review/check_viewer.log').read_text());assert checker['ready']=='true'and checker['switched']==24 and not checker['failed']and not checker['consoleErrors'];report['viewer']=checker
for name in ['check_viewer.log','browser_capture.log']:shutil.copy2(P/'review'/name,R/name)
shared=json.loads((R/'shared_final/gates.json').read_text());baseline=json.loads((P/'review/round4/shared_final/gates.json').read_text())
key=lambda row:tuple(str(row[k])for k in ['asset','clip','lod','gate','region'])
old={key(r):r for r in baseline['gates']};new={key(r):r for r in shared['gates']}
compare={'baseline_counts':baseline['counts'],'final_counts':shared['counts'],'new_failures':[r for k,r in new.items()if r['status']=='FAIL'and old.get(k,{}).get('status')!='FAIL'],'resolved_failures':[r for k,r in old.items()if r['status']=='FAIL'and new.get(k,{}).get('status')=='PASS'],'failure_categories':dict(collections.Counter(r['gate']for r in shared['gates']if r['status']=='FAIL'))}
(R/'shared_comparison.json').write_text(json.dumps(compare,indent=2))
report['shared_runner']={'status':shared['status'],'counts':shared['counts'],'report':'review/round5/shared_final/gates.md'}
report['status']=shared['status'];report['technical_completion']='complete'if shared['status']=='PASS'else'pending_shared_gate_findings'
report['texture_sets']=json.loads((R/'texture_sets.json').read_text());report['native_measurements']=json.loads((R/'native_pose.json').read_text());report['release']=json.loads((R/'release_gate.json').read_text())
for name in ['rig_equipped.blend','rig_textured.blend','runtime_authoring.blend']:report['files']['work/'+name]={'sha256':sha(P/'work'/name)}
(P/'review/delivery_validation.json').write_text(json.dumps(report,indent=2))
print('Final bindings, texture translation, geometry preservation, native hashes, clip boundaries and viewer: PASS. Shared rig gates:',shared['status'],shared['counts'])
