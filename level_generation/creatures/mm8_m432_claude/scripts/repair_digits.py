"""Remove the confirmed extra outer digit and close its root into the glove's ulnar edge."""
import bpy,bmesh,json,sys
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
import common
src=P/'work/body_before_digit_repair.blend'
if not src.exists():
    import shutil
    shutil.copyfile(P/'work/body_clean.blend',src)
bpy.ops.wm.open_mainfile(filepath=str(src))
o=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table()
co=np.array([v.co[:] for v in bm.verts]);remove=set()
for side in ['R','L']:
    pieces=json.loads((P/f'work/extra_fingers_{side}.json').read_text())['fingers']
    extra=max(pieces,key=lambda ids:co[ids,1].mean())
    remove.update(extra)
old_boundary=set(e for e in bm.edges if e.is_boundary)
bmesh.ops.delete(bm,geom=[bm.verts[i] for i in sorted(remove)],context='VERTS')
new_boundary=[e for e in bm.edges if e.is_boundary and e not in old_boundary]
ring=set(v for e in new_boundary for v in e.verts)
for v in ring:
    v.co.y-=.012
    v.co.z+=.014
bmesh.ops.holes_fill(bm,edges=new_boundary,sides=0)
smooth=ring|{e.other_vert(v) for v in ring for e in v.link_edges}
for _ in range(5):
    bmesh.ops.smooth_vert(bm,verts=list(smooth),factor=.4,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3])
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
assert len(remove)==80
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/body_clean.blend'))
common.workbench_clay(bpy.context.scene)
for side,x in [('R',-.61),('L',.61)]:
    common.render_views(str(P/f'review/digits_fixed_{side}'),1.07,.25,views=('front','left','right'),resolution=(700,700),target=(x,-.05))
(P/'work/digit_repair.json').write_text(json.dumps({'removed_vertices':sorted(remove),'count_per_hand':40,'remaining_digits':5,'closed_root':True},indent=1))
