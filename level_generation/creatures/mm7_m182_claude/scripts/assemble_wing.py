"""v2: add the procedural wings (scripts/build_wing.py; left as built, right mirrored with reversed winding) to the
cleaned symmetric body (scripts/clean_shoulder.py). Wing vertices carry point attributes `wing_kind` (-1 body,
0/1 membrane top/bottom, 3 bone tube, 4 claw), `wing_side` (+1/-1) and `wing_param` (membrane: planform u, v in m;
tube/claw: arc length, angle fraction); their faces take material slot 2. The analytic wing weights are kept in
work/v2/wing_weights.npz (vertex index -> weights) for scripts/rig_v2.py.
Usage: assemble_wing.py -- <in.blend> <wing_left.npz> <out.blend>"""
import bpy, bmesh, json, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); o = bpy.data.objects['Body']; me = o.data
w = np.load(a[1]); co = w['co']; tris = w['tris']; kind = w['kind']; prm = w['param']; W = w['weights']; names = list(w['names'])
uvs = w['uv']; piece = w['piece']; layout = json.loads(str(w['layout']))
nb = len(me.vertices)
bm = bmesh.new(); bm.from_mesh(me)
uvl = bm.loops.layers.uv.get('UVMap') or bm.loops.layers.uv.new('UVMap')
pcl = bm.verts.layers.int.new('wing_piece')
for name, typ in [('wing_kind', 'INT'), ('wing_side', 'INT')]:
    if name not in bm.verts.layers.int: bm.verts.layers.int.new(name)
kl = bm.verts.layers.int['wing_kind']; sl = bm.verts.layers.int['wing_side']; pl = bm.verts.layers.int['part']
pu = bm.verts.layers.float.new('wing_pu'); pv = bm.verts.layers.float.new('wing_pv')
for v in bm.verts: v[kl] = -1; v[sl] = 0
index_map = {}
for side in (1, -1):
    base = len(bm.verts); vs = []
    for i, p in enumerate(co):
        v = bm.verts.new((p[0] * side, p[1], p[2])); v[kl] = int(kind[i]); v[sl] = side; v[pu] = float(prm[i, 0]); v[pv] = float(prm[i, 1]); v[pl] = 0
        vs.append(v)
    bm.verts.ensure_lookup_table()
    for t in tris:
        tt = t if side == 1 else t[::-1]
        f = bm.faces.new([vs[k] for k in tt]); f.material_index = 2; f.smooth = True
        # tube faces across the angle seam take angle + 1 on their low corners
        ang = [prm[k, 1] for k in tt]; tube = kind[tt[0]] == 3
        wrap = tube and max(ang) - min(ang) > .5
        for loop, k in zip(f.loops, tt):
            u, v = uvs[k]
            if wrap and prm[k, 1] < .5:
                t_ = [q for q in layout.values() if isinstance(q, dict) and 'height_uv' in q][piece[k] - 1]; v += t_['height_uv']
            loop[uvl].uv = (u, v)
    for i, v in enumerate(vs): v[pcl] = int(piece[i])
    index_map[side] = base
bm.to_mesh(me); bm.free(); me.update()
# analytic wing weights as temporary vertex groups 'wing:<bone>' (they survive reduction; scripts/rig_v2.py reads
# them, swaps L/R names on the -X side and removes them)
for side in (1, -1):
    start = index_map[side]; prefix = 'L' if side == 1 else 'R'
    for j, n in enumerate(names):
        bone = prefix + n if n.startswith('Wing') else n
        g = o.vertex_groups.get('wing:' + bone) or o.vertex_groups.new(name='wing:' + bone)
        for k in np.nonzero(W[:, j] > 1e-4)[0]: g.add([start + int(k)], float(W[k, j]), 'REPLACE')
side_names = lambda s: [('L' if s == 1 else 'R') + n if n.startswith('Wing') else n for n in names]
np.savez(a[2].replace('.blend', '_wing_weights.npz'), left_start=index_map[1], right_start=index_map[-1], count=len(co),
         weights=W, names_L=np.array(side_names(1)), names_R=np.array(side_names(-1)), bone_pts=w['bone_pts'], frame=w['frame'])
while len(me.materials) < 3:
    me.materials.append(bpy.data.materials.new(['DragonBody', 'DragonHead', 'DragonWings'][len(me.materials)]))
print('ASSEMBLED', len(me.vertices), len(me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=a[2])
