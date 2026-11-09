import sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parent/'claude_shared/gates'));import run_gates as shared
cfg=json.loads((p/'gates.json').read_text());glb=shared.Glb(p/'export/mm6_mep.glb');m=shared.load_meshes(glb)[3];c=cfg['cloth'][2]
ids=np.flatnonzero(m.select(c['samples'])&~m.select(c['surface']));idx=int(ids[115]);a=next(a for n,a,st,en in glb.clips() if n=='Death');pose=glb.pose(a,np.array([1.25]))[0];points=m.posed(pose)
surface=shared.Surface(m,m.select(c['surface']),cap=True,opening=c['opening']).build(points,pose)
loc,normal,face,distance=surface.tree.find_nearest(Vector(points[idx]));delta=np.array(loc)+np.array(normal)*.006-points[idx]
def skinmat(world):return sum((world[m.skin_nodes[j]]@m.bind[j])*w for j,w in zip(m.joints[idx],m.weights[idx]))
rest_delta=skinmat(glb.rest)[:3,:3]@np.linalg.solve(skinmat(pose)[:3,:3],delta)
record={'lod':3,'point':m.rest[idx].tolist(),'delta':rest_delta.tolist(),'closest_is_cap':face in surface.caps,'authoring_pose':'Death 1.25 s','source_report':'review/round1/iteration13_gates/gates.json'}
assert np.linalg.norm(rest_delta)<.04
(p/'work/round1_hem_fix.json').write_text(json.dumps(record,indent=2));print('AUTHORING_CONTACT_FIT',record,flush=True)
