import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as S
g=S.Glb(P/'export/mm6_natm.glb');a=next(a for a in g.doc['animations']if a['name']=='Attack');m=S.load_meshes(g)[0];cfg=json.loads((P/'gates.json').read_text());S.configure_mesh(m,cfg,S.Report(cfg));pm=S.load_meshes(S.Glb(P/'review/round4_dense_spear.glb'))[0];surf=S.Surface(m,m.solid&~m.regions['hand_R']);bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_lod0.blend'));r=bpy.data.objects['Rig']
for f in [53,60,61,62,63]:
 C.activate('Attack',f/48);po=g.pose(a,np.array([f/48]))[0];bp=g.rest.copy()
 for b in r.pose.bones:
  if b.name in g.names:bp[g.names[b.name]]=np.array(b.matrix)
 print('DIFF',f,sorted([(n,float(abs(bp[i]-po[i]).max()))for n,i in g.names.items()if n.startswith('B_')],key=lambda x:-x[1])[:8])
 for label,p in [('glb',po),('blend',bp)]:
  points=m.posed(p);pp=S.transform(p[g.names['Spear']]@np.linalg.inv(S.C),pm.rest);print(label,S.penetration(surf.build(points),pp),p[g.names['B_L_Hand']][:3,3].tolist())
