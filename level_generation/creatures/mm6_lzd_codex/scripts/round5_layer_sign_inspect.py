import sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared/gates'))
from run_gates import *
g=Glb(P/'export/mm6_lzd.glb');m=load_meshes(g)[0];cfg=json.loads((P/'gates.layers.json').read_text());idx=cfg['lod_regions']['colour0']['outer_layers']['vertices'][384];data=json.loads((P/'work/round5/lod0_pieces.json').read_text());co=np.array(data['positions']);parts=np.array(data['pieces'])[np.linalg.norm(m.rest[:,None,:]-co,axis=2).argmin(1)]
pose=g.pose(next(a for a in g.doc['animations']if a['name']=='Attack'),np.array([.22916666666666666]))[0];points=m.posed(pose);p=points[[idx]];print('OUTER',parts[idx],m.rest[idx],p,flush=True)
for part in [2,10,15]:
 for cap in [False,True]:
  surface=Surface(m,parts==part,cap=cap).build(points,pose);ds,face=surface.signed(p,containment=True)
  print('SURFACE',part,cap,'closed',surface.closed,'loops',len(surface.loops),'signed',ds,'face',face,'capHit',int(face[0])in surface.caps,flush=True)
  if surface.loops:print('BOUNDARIES',[m.rest[m.weld_first[loop]].mean(0).tolist()for loop in surface.loops],flush=True)
