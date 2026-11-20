import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as G
cfg=json.loads((P/'gates.json').read_text());doc=G.Glb(P/'export/mm6_mfp.glb');meshes=G.load_meshes(doc);cfg['lod_regions']={}
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/round1/lod{level}.blend'));b=bpy.data.objects['Body'];pv=[v.value for v in b.data.attributes['piece'].data];tree=KDTree(len(b.data.vertices))
 for v in b.data.vertices:tree.insert(v.co,v.index)
 tree.balance()
 for mesh in [m for m in meshes if m.label.endswith(str(level))]:
  ids=[];waist=[v.co.copy()for v in b.data.vertices if pv[v.index]==1 and .97<v.co.z<1.06]
  angles=np.array([np.arctan2(v.y+.03,v.x)for v in waist]);heights=np.array([v.z for v in waist])
  for i,co in enumerate(mesh.rest):
   point,vi,d=tree.find(co)
   angle=np.arctan2(point.y+.03,point.x);near=np.abs(np.arctan2(np.sin(angles-angle),np.cos(angles-angle)))<.15;top=max(heights[near])if near.any()else .98
   if pv[vi]==0 and point.z<top-.004:ids.append(i)
  cfg['lod_regions'][mesh.label.split('/')[-1]]={'under_skirt':{'vertices':ids},'waist_skin':{'vertices':[i for i in ids if mesh.rest[i,2]>.85]},'leg_skin_L':{'vertices':[i for i in ids if mesh.rest[i,2]<=.85 and mesh.rest[i,0]>0]},'leg_skin_R':{'vertices':[i for i in ids if mesh.rest[i,2]<=.85 and mesh.rest[i,0]<0]}}
  print('REGION',mesh.label,len(ids),flush=True)
prop=G.Glb(P/'export/mm6_mfp_knife.glb');pm=G.load_meshes(prop)[0];print('PROP_BOUNDS',pm.rest.min(0),pm.rest.max(0))
(P/'gates.json').write_text(json.dumps(cfg,indent=2))
