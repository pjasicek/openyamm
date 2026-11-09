"""Refresh review-only LOD models, UV production measurements and motion provenance."""
from pathlib import Path
import sys,json,hashlib,copy,csv,collections,numpy as np
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2];R=P/'review/round2'
sys.path.insert(0,str(ROOT/'tools'));from build_actor_lods import read_glb,write_glb
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((P/'review/viewer/manifest.json').read_text())
entries=[]
for level in range(1,4):
 for tier in 'abc':
  doc,blob=read_glb(P/f'work/final_check_lod{level}.glb');data=bytearray(blob)
  for mat in doc['materials']:
   stem={'PeasantF3_A':'mfp','PeasantF3Head_A':'mfp_head'}.get(mat['name'])
   if not stem:continue
   pixels=(P/f'work/round2/textures/{stem}_mfp_{tier}.png').read_bytes()
   data.extend(b'\0'*(-len(data)%4));doc['bufferViews'].append({'buffer':0,'byteOffset':len(data),'byteLength':len(pixels)});data.extend(pixels)
   doc['images'].append({'bufferView':len(doc['bufferViews'])-1,'mimeType':'image/png'})
   t=mat['pbrMetallicRoughness']['baseColorTexture'];doc['textures'].append(dict(doc['textures'][t['index']],source=len(doc['images'])-1));t['index']=len(doc['textures'])-1
  out=R/f'lod_models/lod{level}_{tier}.glb';out.parent.mkdir(exist_ok=True);write_glb(out,doc,data);h=sha(out)
  entries.append({'id':f'lod{level}_{tier}','label':f'LOD{level} / {tier}','revision':manifest['revision'],'url':f'../round2/lod_models/{out.name}?v={h[:12]}','sha256':h})
(R/'lod_viewer_models.json').write_text(json.dumps(entries,indent=2))
(R/'standard_viewer_manifest.json').write_text(json.dumps(manifest,indent=2))
hashes={e['id']:e['sha256']for e in entries+manifest['models']}
plan=json.loads((R/'capture_after.json').read_text())
for row in plan:
 if row[0].startswith('lods/'):
  name=row[0].split('/')[1];bits=name.split('_');key=f'lod{bits[0][-1]}_{bits[1]}' if bits[0]!='lod0' else f'mfp_{bits[1]}';row[5]=hashes[key]
(R/'capture_after.json').write_text(json.dumps(plan,indent=2))
# Production measurements use actual UV/3D areas; no pass/fail gate is introduced.
m=np.load(P/'work/round2/mesh0.npz');rows=[]
for phase,key,dim in [('before','old_uv',[(1088,1024),(1024,1024)]),('after','uv',[(4096,4096),(1024,1024)])]:
 for mi in [0,1]:
  ids=np.flatnonzero(m['mat']==mi);uv=m[key][ids];tri=m['tri'][ids];parents=list(range(len(ids)));edges={}
  def root(i):
   while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
   return i
  for i,(vs,coords)in enumerate(zip(tri,uv)):
   for j in range(3):
    k=(j+1)%3;e=tuple(sorted([(int(vs[j]),*np.round(coords[j],6)),(int(vs[k]),*np.round(coords[k],6))]))
    if e in edges:parents[root(i)]=root(edges[e])
    else:edges[e]=i
  groups=collections.defaultdict(list)
  for i in range(len(ids)):groups[root(i)].append(i)
  co=m['co'][tri];area=np.linalg.norm(np.cross(co[:,1]-co[:,0],co[:,2]-co[:,0]),axis=1)*.5
  a=uv[:,1]-uv[:,0];b=uv[:,2]-uv[:,0];ua=np.abs(a[:,0]*b[:,1]-a[:,1]*b[:,0])*.5*dim[mi][0]*dim[mi][1]
  for index,faces in enumerate(groups.values()):
   ar=float(area[faces].sum());pixels=float(ua[faces].sum());density=(pixels/max(ar,1e-16))**.5/100
   pieces,counts=np.unique(m['piece'][tri[faces].ravel()],return_counts=True)
   rows.append({'phase':phase,'material':'body'if mi==0 else'head','island':index,'triangles':len(faces),'area_cm2':ar*10000,'pixel_area':pixels,'texels_cm':density,'dominant_piece':int(pieces[counts.argmax()])})
for phase in ['before','after']:
 part=[r for r in rows if r['phase']==phase]
 head=[r for r in part if r['material']=='head'];torso=[r for r in part if r['material']=='body'and r['dominant_piece']==0]
 hd=(sum(r['pixel_area']for r in head)/sum(r['area_cm2']for r in head))**.5
 td=(sum(r['pixel_area']for r in torso)/sum(r['area_cm2']for r in torso))**.5
 for r in part:r['ratio_to_head']=r['texels_cm']/hd;r['ratio_to_torso']=r['texels_cm']/td
with(R/'uv_islands.csv').open('w')as f:
 writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
(R/'uv_density.json').write_text(json.dumps({'method':'sqrt(UV pixel area / surface cm2); islands joined only across matching mesh/UV edges; same triangles before/after','measurements':json.loads((R/'authoring.json').read_text()),'islands_csv':'uv_islands.csv','island_counts':{phase:{mat:sum(r['phase']==phase and r['material']==mat for r in rows)for mat in ['body','head']}for phase in ['before','after']}},indent=2))
sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as G
old=G.Glb(P/'work/round2/before/export/mm6_mfp.glb');new=G.Glb(P/'export/mm6_mfp.glb')
oc={n:c for n,c,*_ in old.clips()};nc={n:c for n,c,*_ in new.clips()};names=sorted(n for n in new.names if n.startswith('B_'))
oi=[old.names[n]for n in names];ni=[new.names[n]for n in names]
def difference(clip,times,other=None):
 return float(np.abs(old.pose(oc[clip],np.array(times))[:,oi]-new.pose(nc[clip],np.array(times if other is None else other))[:,ni]).max())
motion={'sampler':'Unmodified shared run_gates.Glb.pose','before_sha256':sha(P/'work/round2/before/export/mm6_mfp.glb'),'after_sha256':sha(P/'export/mm6_mfp.glb'),'attack_frames_0_32_max_matrix_delta':difference('Attack',np.arange(33)/48),'old_frame48_vs_new_frame54_max_matrix_delta':difference('Attack',[1.0],[1.125]),'running_40_samples_max_matrix_delta':difference('Running',np.arange(40)*.8/39),'running_source':'anim_library/humanoid_set/Unarmed.glb / UnarmedRunForward2; planted native-size leg gait retained from round 1','running_source_sha256':sha(ROOT/'anim_library/humanoid_set/Unarmed.glb'),'running_authorship':'scripts/round1_running.py; work/round1/normal_run.blend','impact_s':.65625,'attack_duration_s':1.125}
(R/'motion_preservation.json').write_text(json.dumps(motion,indent=2))
print('Review LOD models, per-island UV measurements and motion receipt refreshed')
