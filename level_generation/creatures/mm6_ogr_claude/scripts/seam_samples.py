"""Record matching UVs along the shared neck boundary for a local colour transition."""
from pathlib import Path
import bpy,bmesh,json
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v6.blend'))
bm=bmesh.new();bm.from_mesh(bpy.data.objects['Body'].data);head=bm.faces.layers.int['head'];rows=[]
for e in bm.edges:
 if len(e.link_faces)!=2 or e.link_faces[0][head]==e.link_faces[1][head]:continue
 body,face=sorted(e.link_faces,key=lambda f:f[head]);buv=bm.loops.layers.uv['UVMap'];huv=bm.loops.layers.uv['HeadUV']
 for t in (0,.25,.5,.75,1):
  row={'pos':list(e.verts[0].co.lerp(e.verts[1].co,t))}
  for name,f,uv in [('body',body,buv),('head',face,huv)]:
   loops=[next(l for l in f.loops if l.vert==v) for v in e.verts]
   centre=sum((l[uv].uv for l in f.loops),loops[0][uv].uv*0)/len(f.loops)
   row[name]=list(loops[0][uv].uv.lerp(loops[1][uv].uv,t).lerp(centre,.025))
  rows.append(row)
assert rows;(p/'work/seam_samples.json').write_text(json.dumps(rows)+'\n');print('SEAM_SAMPLES',len(rows));bm.free()
