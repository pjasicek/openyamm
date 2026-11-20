import runpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];g=runpy.run_path(str(P.parent/'claude_shared/gates/run_gates.py'),run_name='probe');a=g['Glb'](P/'export/mm8_m576_lod0.glb');cfg=json.loads((P/'gates.json').read_text());r=g['Report'](cfg)
# Measure the shaft point nearest the palm centre. The reverse-grip axis crosses the palm diagonally.
clip=next(c for n,c,s,e in a.clips() if n=='Standing');p=a.pose(clip,np.array([0.]))[0];H=a.names['B_L_Hand'];T=a.names['Trident'];f=[a.names[f'B_L_Finger{i}'] for i in range(5)];origin=.5*(p[H,:3,3]+p[f,:3,3].mean(0));local=np.linalg.inv(p[T])@np.r_[origin,1];print('PALM CENTRE IN SHAFT SPACE',local.tolist())
for n,c,s,e in a.clips():
 t=g['sample_grid'](s,e,48);pose=a.pose(c,t);g['bone_gates'](a,pose,t,n,cfg,r,cfg['props']);g['prop_timing'](dict(cfg['props'][0],meshes=g['load_meshes'](g['Glb'](P/'export/mm8_m576_trident.glb'))),pose,t,a,n,cfg,r)
for row in r.rows.values():
 if row['status'] in ('FAIL','UNVERIFIED','ERROR'):print(row)
(P/'review/quick_rig_probe.json').write_text(json.dumps(list(r.rows.values()),indent=2)+'\n')

assert not [row for row in r.rows.values() if row['status'] in ('FAIL','UNVERIFIED','ERROR')], 'Rig/impact probe failed'
