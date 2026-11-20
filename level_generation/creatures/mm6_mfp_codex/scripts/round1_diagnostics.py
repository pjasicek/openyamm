import sys,json,numpy as np,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as G
cfg=json.loads((P/'gates.json').read_text());g=G.Glb(P/'export/mm6_mfp.glb');meshes=G.load_meshes(g);report=G.Report(cfg);data=json.loads((P/'review/round1/shared_gates_v3/gates.json').read_text());clips={n:a for n,a,s,e in g.clips()}
for m in meshes:
 if m.label not in ['PeasantF3/colour0','PeasantF3/shadow1']:continue
 G.configure_mesh(m,cfg,report)
 for clip in ['Standing','Hit','Attack','Death']:
  row=next(x for x in data['gates']if x['gate']=='cloth_penetration_mm'and x['clip']==clip and x['lod']==m.label);ids=np.flatnonzero(m.select('under_skirt'));vi=ids[row['detail']['sample_vertex']];pose=g.pose(clips[clip],np.array([row['time_s']]))[0];print('CLOTH_WITNESS',m.label,clip,'rest',m.rest[vi].tolist(),'posed',m.posed(pose)[vi].tolist(),'mm',row['worst'],flush=True)
node=g.names['Knife'];pose=g.pose(clips['Attack'],np.array([.416666666667,.4375]));tip=np.array(cfg['props'][0]['tip']);world=np.array([G.transform(p[node],tip)for p in pose]);v=(world[1]-world[0])/(.4375-.416666666667);R=pose[0,node,:3,:3];vl=np.linalg.inv(R)@v;e=np.array(cfg['props'][0]['edge_axis']);delta=math.degrees(math.atan2(vl[1],vl[0])-math.atan2(e[1],e[0]));print('EDGE_ROLL_DELTA',delta,'velocity_local',vl.tolist(),flush=True)
