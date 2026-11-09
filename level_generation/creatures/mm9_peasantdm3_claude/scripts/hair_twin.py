"""Hair thickness for the lengthened curtain (see-through gate r3: from the side, with the head turned, the view met the
inside of the hair shell at the nape, back faces culled in the game). Hair faces below rest z Z_MAX are duplicated
OFFSET behind themselves, flipped, with the same UVs (hair paint), weights and attributes, so the hair's inside shows hair.
Args (Blender): -- <in blend> <out blend> [Z_MAX 0.44] [OFFSET 0.002]"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parts_lib as L
a = sys.argv[sys.argv.index('--') + 1:]
Z_MAX = float(a[2]) if len(a) > 2 else 0.44
OFFSET = float(a[3]) if len(a) > 3 else 0.002
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
co = L.rest_coords(body); lab = L.loose_parts(me)
hair = lab[np.argmax(co[:, 2])]
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
dl = bm.verts.layers.deform.active
ilay = {n: bm.faces.layers.int[n] for n in ('head', 'hand', 'lined') if n in bm.faces.layers.int}
uvl = [bm.loops.layers.uv[u.name] for u in me.uv_layers]
sel = [f for f in bm.faces if lab[f.verts[0].index] == hair and f.calc_center_median().z < Z_MAX]
normal = {}
for f in sel:
    for v in f.verts:
        normal[v] = normal.get(v, Vector()) + f.normal * f.calc_area()
vmap = {}
for v, n in normal.items():
    nv = bm.verts.new(v.co - n.normalized() * OFFSET)
    for g, w in v[dl].items(): nv[dl][g] = w
    vmap[v] = nv
for f in sel:
    loops = list(f.loops)[::-1]
    g = bm.faces.new([vmap[l.vert] for l in loops])
    g.material_index = f.material_index; g.smooth = f.smooth
    for k, lay in ilay.items(): g[lay] = f[lay]
    for gl, sl in zip(g.loops, loops):
        for lay in uvl: gl[lay].uv = sl[lay].uv
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('HAIRTWIN', json.dumps({'faces': len(sel), 'z_max': Z_MAX}))
