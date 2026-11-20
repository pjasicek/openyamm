"""Compare the requested Attack-only revision against the retained delivery."""
from pathlib import Path
import runpy,json,hashlib,numpy as np
P=Path(__file__).resolve().parents[1]
G=runpy.run_path(str(P.parent/'claude_shared/gates/run_gates.py'),run_name='nightmare_revision')
old=G['Glb'](P/'work/attack_revision_base/mm8_m600_lod0.glb')
new=G['Glb'](P/'export/mm8_m600_lod0.glb')
report={'status':'PASS','old_sha256':hashlib.sha256(old.path.read_bytes()).hexdigest() if hasattr(old,'path') else None,
        'new_sha256':hashlib.sha256((P/'export/mm8_m600_lod0.glb').read_bytes()).hexdigest(),'clips':{},'eye_tips':{}}
nodes=[{n.get('name'):i for i,n in enumerate(a.nodes)} for a in [old,new]]
bones=[new.nodes[i]['name'] for i in new.doc['skins'][0]['joints']]
assert len(bones)==58
# Mesh topology, UVs, normals and semantic joint weights must remain identical.
prims=[a.doc['meshes'][a.nodes[next(i for i,n in enumerate(a.nodes) if n.get('name')=='Nightmare')]['mesh']]['primitives'][0] for a in [old,new]]
assert np.array_equal(old.accessor(prims[0]['indices']),new.accessor(prims[1]['indices']))
for attr in ['POSITION','NORMAL','TEXCOORD_0','WEIGHTS_0']:
 assert np.array_equal(old.accessor(prims[0]['attributes'][attr]),new.accessor(prims[1]['attributes'][attr])),attr
jnames=[np.array([a.nodes[i]['name'] for i in a.doc['skins'][0]['joints']]) for a in [old,new]]
assert np.array_equal(*[names[a.accessor(p['attributes']['JOINTS_0'])] for a,p,names in zip([old,new],prims,jnames)])
clips=[{n:(c,start,end) for n,c,start,end in a.clips()} for a in [old,new]]
for name,(clip,start,end) in clips[1].items():
 times=np.linspace(start,end,round(end*120)+1)
 poses=[a.pose(cs[name][0],times) for a,cs in zip([old,new],clips)]
 selected=[b for b in bones if name!='Attack' or not b.startswith('Eye')]
 difference=max(float(abs(poses[0][:,nodes[0][b]]-poses[1][:,nodes[1][b]]).max()) for b in selected)
 assert difference<1e-6,(name,difference)
 report['clips'][name]={'unaffected_bone_max_matrix_delta':difference,'duration':float(end-start)}
 if name=='Attack':
  for eye in [f'Eye{k}_Tip' for k in range(5)]:
   p,q=[v[:,ns[eye],:3,3] for v,ns in zip(poses,nodes)]
   old_travel=float(np.linalg.norm(np.diff(p,axis=0),axis=1).sum())
   new_travel=float(np.linalg.norm(np.diff(q,axis=0),axis=1).sum())
   displacement=float(np.linalg.norm(q-p,axis=1).max())
   assert .001<displacement<.012,(eye,displacement)
   assert np.max(abs(p[[0,-1]]-q[[0,-1]]))<1e-6
   report['eye_tips'][eye]={'old_travel_m':old_travel,'new_travel_m':new_travel,'max_displacement_m':float(np.linalg.norm(q-p,axis=1).max())}
final_old,final_new=[G['Glb'](P/n) for n in ['work/attack_revision_base/mm8_m600.glb','export/mm8_m600.glb']]
old_meshes={m['name']:m for m in final_old.doc['meshes']}
for mesh in final_new.doc['meshes']:
 p=mesh['primitives'][0];q=old_meshes[mesh['name']]['primitives'][0]
 for key in ['POSITION','NORMAL','TEXCOORD_0','WEIGHTS_0']:
  assert np.array_equal(final_old.accessor(q['attributes'][key]),final_new.accessor(p['attributes'][key])),(mesh['name'],key)
 assert np.array_equal(final_old.accessor(q['indices']),final_new.accessor(p['indices']))
 names=[np.array([g.nodes[i]['name'] for i in g.doc['skins'][0]['joints']]) for g in [final_old,final_new]]
 assert np.array_equal(names[0][final_old.accessor(q['attributes']['JOINTS_0'])],names[1][final_new.accessor(p['attributes']['JOINTS_0'])])
report['all_colour_shadow_lods_unchanged']=True
report['final_sha256']=hashlib.sha256((P/'export/mm8_m600.glb').read_bytes()).hexdigest()
report['unchanged']='Body geometry, UVs, normals, weights, six other clips and non-eye Attack bones'
out=P/'review/attack_subtle';out.mkdir(exist_ok=True)
(out/'invariants.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
