"""Requested welded-boundary counts and preservation receipt for the geometry-only revision."""
import sys,json,hashlib,copy
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
from scipy.spatial import cKDTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'));import merge_head_material as g
D=P/'review/round3';native=json.loads((D/'native_regions.json').read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def anim(d,b):
 result={}
 for a in d['animations']:
  for c in a['channels']:
   s=a['samplers'][c['sampler']];key=a['name']+':'+d['nodes'][c['target']['node']]['name']+':'+c['target']['path'];h=hashlib.sha256()
   for k in ['input','output']:h.update(g.accessor_array(d,b,s[k]).tobytes())
   result[key]=h.hexdigest()
 return result
def images(d,b):
 out=[]
 for im in d['images']:
  view=d['bufferViews'][im['bufferView']];offset=view.get('byteOffset',0);out.append(hashlib.sha256(b[offset:offset+view['byteLength']]).hexdigest())
 return out
def mesh(d,b,mi):
 positions=[];faces=[];signatures=[];offset=0
 for p in d['meshes'][mi]['primitives']:
  attrs=p['attributes'];v=g.accessor_array(d,b,attrs['POSITION']);positions.extend(v[:,[0,2,1]]*np.array([1,-1,1]));faces.extend(g.accessor_array(d,b,p['indices']).reshape(-1,3)+offset);offset+=len(v)
  js=np.concatenate([g.accessor_array(d,b,attrs[k]) for k in sorted(attrs) if k.startswith('JOINTS_')],axis=1);ws=np.concatenate([g.accessor_array(d,b,attrs[k]) for k in sorted(attrs) if k.startswith('WEIGHTS_')],axis=1)
  signatures.extend([tuple(sorted((int(j),round(float(w),6)) for j,w in zip(jr,wr) if w>1e-7)) for jr,wr in zip(js,ws)])
 return np.array(positions),np.array(faces),signatures
def boundaries(pos,faces,labels):
 keys={};ids=[];verts=[];piece=[]
 for v,tag in zip(pos,labels):
  key=tuple(np.round(v,6))
  if key not in keys:keys[key]=len(verts);verts.append(v);piece.append(tag)
  ids.append(keys[key])
 triangles=np.array(ids)[faces];edges=Counter()
 for f in triangles:
  if len(set(f))<3:continue
  for a,b in zip(f,np.roll(f,-1)):edges[tuple(sorted((a,b)))]+=1
 boundary=[e for e,n in edges.items() if n==1];under=[e for e in boundary if max(verts[i][2] for i in e)<1.10]
 groups=Counter('skin' if all(piece[i]==0 for i in e) else 'kilt' if all(piece[i]==1 for i in e) else 'belt_ornament' if all(piece[i]==6 for i in e) else 'other' for e in under)
 return {'triangles':len(faces),'all_open_edges':len(boundary),'below_belt_open_edges':len(under),'below_belt_by_piece':dict(groups),'unintended_skin_below_belt':groups['skin'],'nonmanifold_edges':sum(n>2 for n in edges.values())}
results={};documents={}
for state,path in [('before',D/'before/mm6_min1.glb'),('after',P/'export/mm6_min1.glb')]:
 d,b=g.read_glb(path);documents[state]=(d,b);base=next(n['mesh'] for n in d['nodes'] if n.get('name')=='Minotaur');extra=d['meshes'][base]['extras'];results[state]={}
 for level,mi in enumerate([base]+extra['openyamm_lods']):
  pos,faces,signatures=mesh(d,b,mi);region=native[state][str(level)];distance,index=cKDTree(region['positions']).query(pos);assert distance.max()<3e-6,distance.max();labels=np.array(region['piece'])[index]
  results[state]['colour'+str(level)]=boundaries(pos,faces,labels)
  sp,sf,ss=mesh(d,b,extra['openyamm_shadow_lods'][level]);groups=defaultdict(list)
  for i,key in enumerate(signatures):groups[key].append(i)
  sl=[]
  for point,key in zip(sp,ss):
   candidates=groups[key];dist=np.linalg.norm(pos[candidates]-point,axis=1);nearest=int(np.argmin(dist));assert dist[nearest]<.01501;sl.append(labels[candidates[nearest]])
  results[state]['shadow'+str(level)]=boundaries(sp,sf,sl)
  if state=='after':
   assert results[state]['colour'+str(level)]['unintended_skin_below_belt']==0
   assert results[state]['shadow'+str(level)]['unintended_skin_below_belt']==0
   preview=copy.deepcopy(d);next(n for n in preview['nodes'] if n.get('name')=='Minotaur')['mesh']=mi
   g.write_glb(D/f'lod{level}.glb',preview,bytearray(b))
old,ob=documents['before'];new,nb=documents['after'];before_anim=anim(old,ob);after_anim=anim(new,nb)
assert before_anim==after_anim
assert images(old,ob)==images(new,nb),'Changed embedded texture payload'
assert (D/'before/mm6_min1_axe.glb').read_bytes()==(P/'export/mm6_min1_axe.glb').read_bytes()
assert (D/'before/actors.yml').read_bytes()==(P/'integration/actors.yml').read_bytes()
report={'revision':'mm6_min1_codex_review_round3','body_sha256':sha(P/'export/mm6_min1.glb'),'method':'Position welding at 1 micrometre; native piece IDs transferred by exact bind positions, shadow labels by identical skin weights and nearest corresponding colour vertex. Below belt = both edge endpoints below 1.10 m.','intended_openings':'Ragged kilt hem, kilt waistband, belt jewel back. No skin openings are intended. Upper mane/ornament boundaries are outside the scoped hip repair.','boundaries':results,'preservation':{'animation_channels_byte_identical':len(before_anim),'embedded_textures_byte_identical':True,'axe_glb_byte_identical':True,'actors_yml_byte_identical':True,'kilt_double_sided':all(m.get('doubleSided') for m in new['materials'])}}
(D/'geometry_receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
