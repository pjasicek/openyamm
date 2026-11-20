import bpy,bmesh,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sel=json.loads((P/'review/reduction/selection.json').read_text())
for e in [{'blend':'work/reduction_master.blend'}]+sel['body']:
 path=P/e['blend'];bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(o.data);part=bm.verts.layers.int['piece'];df=bm.verts.layers.deform.active
 for pid in [8,9]:
  roots={v for v in bm.verts if v[part]==pid and abs(v.co.x)<.185 and v.co.z>1.18};targets={}
  for v in roots:
   outside=[e.other_vert(v)for e in v.link_edges if e.other_vert(v)not in roots]
   if outside:targets[v]=min(outside,key=lambda q:(q.co.y-v.co.y)**2+(q.co.z-v.co.z)**2).co.copy()
  for v,t in targets.items():
   v.co.y=t.y;v.co.z=t.z;v[df].clear();v[df][o.vertex_groups['B_Spine2'].index]=1
 faces=[f for f in bm.faces if all(v[part]in[8,9]for v in f.verts)];bmesh.ops.recalc_face_normals(bm,faces=faces);bm.to_mesh(o.data);bm.free();bpy.ops.wm.save_as_mainfile(filepath=str(path))
