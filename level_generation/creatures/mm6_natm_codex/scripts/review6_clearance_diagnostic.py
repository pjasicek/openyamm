"""Authoring distance detail using the unmodified shared evaluator; production paired shared collision gates are separate. Gripping/releasing hands are measured separately."""
import sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as S
g=S.Glb(P/'export/mm6_natm.glb');cfg=json.loads((P/'gates.json').read_text());ms=S.load_meshes(g)[:4];pm=S.load_meshes(S.Glb(P/'review/round5_dense_spear.glb'));a=next(a for a in g.doc['animations']if a['name']=='Attack');times=np.arange(56)/48;poses=g.pose(a,times);rows=[]
for level,m in enumerate(ms):
 S.configure_mesh(m,cfg,S.Report(cfg));surf=S.Surface(m,m.solid&~m.regions['hand_L']&~m.regions['hand_R']);minimum=1e9;maximum=0;frame=0
 for f,pose in enumerate(poses):
  pp=S.transform(pose[g.names['Spear']]@np.linalg.inv(S.C),pm[level].rest);surf.build(m.posed(pose));depth,_=S.penetration(surf,pp);gap=surf.gap(pp)*1000;maximum=max(maximum,depth)
  if gap<minimum:minimum=gap;frame=f
 rows.append({'lod':level,'samples':56,'max_penetration_mm':maximum,'minimum_surface_distance_mm':minimum,'minimum_distance_frame_48hz':frame})
(P/'review/round6_clearance_diagnostic.json').write_text(json.dumps({'classification':__doc__,'source_sha256':g.sha256,'rows':rows},indent=2));print('SHAFT_BODY_DISTANCE',rows,flush=True)
