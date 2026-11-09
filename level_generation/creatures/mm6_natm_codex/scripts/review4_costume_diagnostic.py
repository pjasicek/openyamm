"""Parent-relative costume measurements using the shared GLB pose evaluator; not an implemented shared gate."""
import sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as S
g=S.Glb(P/'export/mm6_natm.glb');old=S.Glb(P/'work/review_round4_before/export/mm6_natm.glb');ms=S.load_meshes(g);standing=next(a for a in g.doc['animations']if a['name']=='Standing');sp=g.pose(standing,np.array([0.]))[0];os=old.pose(next(a for a in old.doc['animations']if a['name']=='Standing'),np.array([0.]))[0];out={'classification':__doc__,'source_sha256':g.sha256,'sample_hz':48,'lods':{},'intentional_motion':'Death/Dead feather floor folds and free cloth hems are preserved. Their full parent-relative offsets are reported, not certified as rigid.'}
for level,m in enumerate(ms[:4]):
 groups={}
 for n in m.bone_names:
  if n.startswith('Feather_B_'):
   mask=m.weight([n])>.99
   if mask.any():groups[n]=(mask,n.removeprefix('Feather_'))
 for n in ['ClothFront','ClothBack']:
  mask=m.weight([n+'*'])>.01
  if mask.any():
   groups[n+'_all']=(mask,'B_Pelvis');top=mask&(m.rest[:,2]>m.rest[mask,2].max()-.01);groups[n+'_upper_moving_row']=(top,'B_Pelvis')
 refpoints=m.posed(sp);refs={n:S.transform(np.linalg.inv(sp[g.names[parent]]),refpoints[mask])for n,(mask,parent)in groups.items()};entries={}
 for role,a,lo,hi in g.clips():
  times=np.linspace(lo,hi,round((hi-lo)*48)+1);poses=g.pose(a,times);result={n:{'vertices':int(mask.sum()),'first_mm':0.,'max_mm':0.,'worst_frame':0.}for n,(mask,parent)in groups.items()}
  for f,pose in enumerate(poses):
   points=m.posed(pose)
   for n,(mask,parent)in groups.items():
    q=S.transform(np.linalg.inv(pose[g.names[parent]]),points[mask]);delta=float(np.linalg.norm(q-refs[n],axis=1).max()*1000)
    if f==0:result[n]['first_mm']=delta
    if delta>result[n]['max_mm']:result[n].update(max_mm=delta,worst_frame=float(times[f]*48))
  entries[role]=result
 out['lods'][str(level)]=entries
# Compare the preserved folded corpse skeleton and original Standing costume frames by node names.
old_mapped=np.array([os[old.names[n.get('name')]]if n.get('name')in old.names else g.rest[i]for i,n in enumerate(g.doc['nodes'])]);out['standing_vs_round3_parent_mm']={}
m=ms[0];pnew=m.posed(sp);pold=m.posed(old_mapped)
for n in m.bone_names:
 if n.startswith('Feather_B_'):
  mask=m.weight([n])>.99;parent=g.names[n.removeprefix('Feather_')]
  if mask.any():out['standing_vs_round3_parent_mm'][n]=float(np.linalg.norm(S.transform(np.linalg.inv(sp[parent]),pnew[mask])-S.transform(np.linalg.inv(old_mapped[parent]),pold[mask]),axis=1).max()*1000)
(P/'review/round4_costume_diagnostic.json').write_text(json.dumps(out,indent=2));print('COSTUME_DIAGNOSTIC',out['standing_vs_round3_parent_mm'],flush=True)
