import bpy,bmesh,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/step1.blend'))
m=bpy.data.objects['Body'].data;bm=bmesh.new();bm.from_mesh(m);pv=bm.verts.layers.int['piece']
bm.verts.ensure_lookup_table()
S=set(v for v in bm.verts if v[pv]==1 and v.is_boundary)
while S:
 v=S.pop();c={v};st=[v]
 while st:
  v=st.pop()
  for e in v.link_edges:
   w=e.other_vert(v)
   if e.is_boundary and w in S:S.remove(w);c.add(w);st.append(w)
 co=np.array([tuple(v.co) for v in c]);print('BOUNDARY',len(c),'bounds',co.min(0),co.max(0))
near=[v for v in bm.verts if v[pv]==1 and abs(v.co.x+.028)<.012 and abs(v.co.z-1.484)<.012 and v.co.y<-.025]
for v in near:print('NOSEVERT',v.index,tuple(v.co),'boundary',v.is_boundary,'faces',len(v.link_faces),[(f.index,len(f.verts),tuple(f.normal)) for f in v.link_faces])
