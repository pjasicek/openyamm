import runpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];g=runpy.run_path(str(P.parent/'claude_shared/gates/run_gates.py'),run_name='probe');cfg=json.loads((P/'gates.json').read_text());r=g['Report'](cfg);a=g['Glb'](P/'export/mm8_m576.glb');prop=g['load_props'](cfg,P,a,r)[0];c=next(c for n,c,s,e in a.clips() if n=='Standing');pose=a.pose(c,np.array([0.]))[0]
for m in g['load_meshes'](a)[:4]:
 g['configure_mesh'](m,cfg,r);v=m.posed(pose);tri,bary,_,_=g['grip_points'](m,'L',cfg);samples=np.einsum('sk,tkj->tsj',bary,v[tri]).reshape(-1,3);local=g['transform'](g['C']@np.linalg.inv(pose[a.names['Trident']]),samples)
 print(m.label,[float(-s.signed(local)[0].min()*1000) for s in prop['solid_surfaces']],flush=True)
