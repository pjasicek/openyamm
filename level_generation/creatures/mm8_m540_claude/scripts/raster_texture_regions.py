"""Rasterise the selected body and rebaked head UVs and their shared neck seam."""
from pathlib import Path
import bpy,bmesh,runpy,sys,json
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
def run(name,args):
 s=p/'scripts'/name;sys.argv=[str(s),'--']+[str(x) for x in args];runpy.run_path(str(s),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_uv.blend'))
body=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(body.data);hd=bm.faces.layers.int['head'];uv=bm.loops.layers.uv['HeadUV'];buv=bm.loops.layers.uv['UVMap'];rows=[]
for e in bm.edges:
 if len(e.link_faces)!=2 or e.link_faces[0][hd]==e.link_faces[1][hd]:continue
 b,h=sorted(e.link_faces,key=lambda f:f[hd])
 for t in [0,.25,.5,.75,1]:
  row={'pos':list(e.verts[0].co.lerp(e.verts[1].co,t))}
  for name,f,u in [('body',b,buv),('head',h,uv)]:
   ls=[next(l for l in f.loops if l.vert==v) for v in e.verts];centre=sum((l[u].uv for l in f.loops),Vector((0,0)))/len(f.loops)
   row[name]=list(ls[0][u].uv.lerp(ls[1][u].uv,t).lerp(centre,.025))
  rows.append(row)
bm.free();assert len(rows)>50
(p/'work/seam_samples.json').write_text(json.dumps(rows)+'\n')
for layer in ['UVMap','HeadUV']:run('uv_raster.py',[p/'work/rig_uv.blend',layer,1024])
