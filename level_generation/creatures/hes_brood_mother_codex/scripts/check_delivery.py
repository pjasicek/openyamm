"""Bind final export evidence to exact all-clip geometry parity, LODs and runtime material checks."""
import contextlib,hashlib,importlib.util,io,json,sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from PIL import Image
P=Path(__file__).resolve().parents[1];R=P.parents[2];sys.dont_write_bytecode=True
sys.path.insert(0,str(P.parent/'claude_shared/gates'))
from run_gates import Glb,load_meshes,sample_grid
old=Glb(P/'work/texture_ready.glb');new=Glb(P/'export/hes_brood_mother.glb')
a=load_meshes(old);all_meshes=load_meshes(new);b=[m for m in all_meshes if m.label=='BroodMother/colour0'];assert len(b)==1
T=np.concatenate([m.rest[m.faces] for m in a]);S=b[0].rest[b[0].faces]
_,ids=cKDTree(S.mean(1)).query(T.mean(1));assert len(set(ids))==len(ids)==len(S)==12043
errors=np.array([np.linalg.norm(T-np.roll(S[ids],k,axis=1),axis=2).max(1) for k in range(3)])
roll=errors.argmin(0);maxrest=float(errors.min(0).max());assert maxrest<1e-5
corners=(np.arange(3)[None,:]-roll[:,None])%3
clips={n:(anim,t0,t1) for n,anim,t0,t1 in new.clips()};assert set(clips)=={n for n,*_ in old.clips()}
report={'asset':'export/hes_brood_mother.glb','sha256':new.sha256,'gated_source_sha256':old.sha256,'lod0_triangles':len(S),'rest_face_correspondence':'bijective with same winding','maximum_rest_error_m':maxrest,'clips':{},'failures':[]}
for name,oa,t0,t1 in old.clips():
 na,n0,n1=clips[name];assert abs(t0-n0)<1e-6 and abs(t1-n1)<1e-6
 times=sample_grid(t0,t1,60);maxerr=0
 for op,np_ in zip(old.pose(oa,times),new.pose(na,times)):
  left=np.concatenate([m.posed(op)[m.faces] for m in a]);right=b[0].posed(np_)[b[0].faces][ids]
  right=np.take_along_axis(right,corners[:,:,None],axis=1)
  maxerr=max(maxerr,float(np.linalg.norm(left-right,axis=2).max()))
 assert maxerr<1e-5,(name,maxerr)
 report['clips'][name]={'duration_s':float(t1-t0),'samples':len(times),'maximum_posed_error_m':maxerr}
 print('PARITY',name,maxerr,flush=True)
for label in ['gates','sockets']:
 evidence=json.loads((P/f'review/texture_ready_{label}.json').read_text());assert evidence['status']=='pass' and evidence['sha256']==old.sha256
 report[label]={'status':'pass_by_all_clip_surface_preservation','evidence':f'review/texture_ready_{label}.json'}
node=next(n for n in new.doc['nodes'] if n.get('name')=='BroodMother');base=node['mesh'];extras=new.doc['meshes'][base]['extras']
assert base not in extras['openyamm_lods'] and base not in extras['openyamm_shadow_lods']
levels=[base]+extras['openyamm_lods'];report['lod_triangles']=[];report['lod_floor_min_m']=[]
for level,mi in enumerate(levels):
 mesh=next(m for m in all_meshes if m.label==f'BroodMother/colour{level}');report['lod_triangles'].append(len(mesh.faces))
 lo=float(mesh.rest[:,2].min());assert lo>=-.002;report['lod_floor_min_m'].append(lo)
 for prim in new.doc['meshes'][mi]['primitives']:
  for acc in prim['attributes'].values():assert np.isfinite(new.accessor(acc)).all()
  assert np.max(abs(new.accessor(prim['attributes']['WEIGHTS_0']).sum(1)-1))<1e-4
node['mesh']=base
assert len(new.doc['skins'][0]['joints'])==50
for mat in new.doc['materials']:
 assert not mat.get('doubleSided',False)
 if mat.get('extras',{}).get('openyamm_specular_mask'):
  tex=mat['pbrMetallicRoughness']['metallicRoughnessTexture']['index'];im=new.doc['images'][new.doc['textures'][tex]['source']];v=new.doc['bufferViews'][im['bufferView']];start=v.get('byteOffset',0)
  red=np.asarray(Image.open(io.BytesIO(new.data[start:start+v['byteLength']])).convert('RGB'))[:,:,0]
  assert red.min()<200,'Specular channel was replaced with white'
variants=new.doc['extensions']['KHR_materials_variants']['variants'];assert variants==[{'name':'hbm'}]
source=R/'level_generation/decorations/mm8_3d/animated/scripts/check_winding.py';spec=importlib.util.spec_from_file_location('winding',source);w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
out=io.StringIO()
with contextlib.redirect_stdout(out):bad=w.check(new.path)
assert bad==0;(P/'review/final_winding.txt').write_text(out.getvalue());report['inverted_closed_parts']=bad
report['lod_audit']=json.loads((P/'work/lod_repair/work/hes_brood_mother/result.json').read_text());assert report['lod_audit']['passed']
report['status']='pass';(P/'review/delivery_checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='lod_audit'},indent=2))
