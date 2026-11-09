"""Fast exported grip check before the full animated LOD audit."""
import runpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];g=runpy.run_path(str(P.parent/'claude_shared/gates/run_gates.py'),run_name='probe');cfg=json.loads((P/'gates.json').read_text());r=g['Report'](cfg);a=g['Glb'](P/'export/mm8_m576.glb');props=g['load_props'](cfg,P,a,r);clip=next(c for n,c,s,e in a.clips() if n=='Standing');pose=a.pose(clip,np.array([0.]))[0]
for m in g['load_meshes'](a):
 g['configure_mesh'](m,cfg,r);m.grip_samples={};g['mesh_sample'](m,m.posed(pose),pose,0,'Standing',cfg,r,props,[],{})
rows=[row for row in r.rows.values() if row['gate'].startswith('grip')]
for row in rows:
 if row['status']!='PASS':print(row,flush=True)
(P/'review/lod_grip_contacts.json').write_text(json.dumps(rows,indent=2)+'\n')
assert all(row['status']=='PASS' for row in rows)
print('ALL LOD GRIP CONTACTS PASS',len(rows),flush=True)
