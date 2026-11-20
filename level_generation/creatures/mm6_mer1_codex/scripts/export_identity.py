"""Prove runtime packaging preserves every accepted skin surface, all LODs and attachment coordinates."""
import sys,json,numpy as np
from pathlib import Path
from scipy.spatial import cKDTree
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parents[2]/'tools'));import merge_head_material as G
bd,bb=G.read_glb(P/'export/mm6_mer1.glb');pd,pb=G.read_glb(P/'export/mm6_mer1_club.glb');manifest=json.loads((P/'work/reduction/exports_manifest.json').read_text())
names=sorted(n['name']for n in bd['nodes']if n.get('name'));columns={n:i for i,n in enumerate(names)}
def arrays(d,b,mesh,exclude_club=False):
 skin=d['skins'][0];jointnames=[d['nodes'][i]['name']for i in skin['joints']];pos=[];weights=[];tri=0
 for p in mesh['primitives']:
  if exclude_club and 'Club'in d['materials'][p['material']]['name']:continue
  at=p['attributes'];co=G.accessor_array(d,b,at['POSITION']);w=np.zeros((len(co),len(names)))
  for k,v in at.items():
   if not k.startswith('WEIGHTS_'):continue
   values=G.accessor_array(d,b,v);ji=G.accessor_array(d,b,at[k.replace('WEIGHTS','JOINTS')])
   for j in range(values.shape[1]):w[np.arange(len(co)),[columns[jointnames[n]]for n in ji[:,j]]]+=values[:,j]
  pos.append(co);weights.append(w);tri+=len(G.accessor_array(d,b,p['indices']).ravel())//3
 return np.concatenate(pos),np.concatenate(weights),tri
report={'levels':[],'max_weight_sum_error':0.}
for level,entry in enumerate(manifest):
 d,b=G.read_glb(P/entry['glb']);co,w,tri=arrays(d,b,d['meshes'][0],True);fc,fw,ft=arrays(bd,bb,bd['meshes'][level]);assert tri==ft==entry['body']['triangles']
 distances,ids=cKDTree(co).query(fc,k=min(8,len(co)));near=distances<2e-6;errors=np.max(abs(w[ids]-fw[:,None,:]),axis=2);errors[~near]=np.inf;error=errors.min(1).max();assert error<2e-6,(level,error)
 skin=d['skins'][0];slot=next(i for i,n in enumerate(skin['joints'])if d['nodes'][n]['name']=='Club');ib=G.accessor_array(d,b,skin['inverseBindMatrices'])[slot].reshape(4,4).T
 cp=next(p for p in d['meshes'][0]['primitives']if 'Club'in d['materials'][p['material']]['name']);orig=G.accessor_array(d,b,cp['attributes']['POSITION']);local=(np.c_[orig,np.ones(len(orig))]@ib.T)[:,:3];final=np.concatenate([G.accessor_array(pd,pb,p['attributes']['POSITION'])for p in pd['meshes'][level]['primitives']]);prop_error=cKDTree(local).query(final)[0].max();assert prop_error<2e-6
 report['levels'].append({'level':level,'body_triangles':tri,'club_triangles':entry['club']['triangles'],'body_position_max_m':float(distances[:,0].max()),'body_skin_weight_max_error':float(error),'club_position_max_m':float(prop_error)})
for d,b in [(bd,bb),(pd,pb)]:
 for m in d.get('materials',[]):assert not m.get('extensions'),m['name']
 for m in d['meshes']:
  for p in m['primitives']:
   at=p['attributes'];ws=[G.accessor_array(d,b,i)for n,i in at.items()if n.startswith('WEIGHTS_')]
   if ws:
    error=float(abs(sum(v.sum(1)for v in ws)-1).max());report['max_weight_sum_error']=max(report['max_weight_sum_error'],error);assert error<=1e-4
for kind in ['body','club']:
 counts=[x[kind+'_triangles']for x in report['levels']];assert all(a>b for a,b in zip(counts,counts[1:]));assert all(n<=counts[0]*ratio for n,ratio in zip(counts[1:],[.55,.25,.10 if kind=='body'else .22])),(kind,counts)
total=[x['body_triangles']+x['club_triangles']for x in report['levels']];assert all(n<=total[0]*ratio for n,ratio in zip(total[1:],[.55,.25,.112]));report['combined_triangle_ratios']=[n/total[0]for n in total];report['pass']=True;(P/'review/runtime_geometry_identity.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
