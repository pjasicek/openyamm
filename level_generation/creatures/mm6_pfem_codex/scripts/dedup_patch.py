import bpy,bmesh
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/uv_ready.blend'))
o=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(o.data);piece=bm.verts.layers.int['piece']
groups={}
for f in bm.faces:
 if all(v[piece]==100 for v in f.verts):
  key=tuple(sorted(tuple(round(x,7) for x in v.co) for v in f.verts));groups.setdefault(key,[]).append(f)
drop=[]
for key,fs in groups.items():
 if len(fs)>1:
  fs.sort(key=lambda f:f.normal.x*f.calc_center_median().x+f.normal.y*f.calc_center_median().y,reverse=True)
  drop.extend(fs[1:])
print('DUPLICATE SKIRT PATCH faces removed',len(drop))
bmesh.ops.delete(bm,geom=drop,context='FACES_ONLY');bm.to_mesh(o.data);bm.free();o.data.update()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/uv_ready.blend'))
