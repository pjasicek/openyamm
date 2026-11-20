"""dress_clear.py on a runtime GLB (no piece attribute): skirt = LOD0 vertices mostly on Dress_* bones, right fist =
vertices mostly on B_R_Hand/B_R_Finger*, plus the Dagger node's blade line (the engine attaches the dagger there;
glTF rest transform from the JSON as in render_carry.py). Args: -- <glb> [action ...]"""
import bpy, sys, json, struct
import numpy as np
from mathutils import Vector, Matrix, Quaternion
a = sys.argv[sys.argv.index('--') + 1:]; glb = a[0]; acts = a[1:] or ['Standing', 'Walking', 'Running', 'Hit', 'Fidget']
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene; sc.render.fps = 30
bpy.ops.import_scene.gltf(filepath=glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == 'M428')
names = [g.name for g in body.vertex_groups]
def share(v, pred): return sum(e.weight for e in v.groups if pred(names[e.group]))
skirt = [v.index for v in body.data.vertices if share(v, lambda n: n.startswith('Dress_')) > 0.5]
hand = [v.index for v in body.data.vertices if share(v, lambda n: n.startswith('B_R_Hand') or n.startswith('B_R_Finger')) > 0.5]
raw = open(glb, 'rb').read(); doc = json.loads(raw[20:20 + struct.unpack_from('<I', raw, 12)[0]])
parent = {c: i for i, n in enumerate(doc['nodes']) for c in n.get('children', [])}
def trs(n):
    r = n.get('rotation', [0, 0, 0, 1]); s_ = n.get('scale', [1, 1, 1])
    return Matrix.Translation(n.get('translation', [0, 0, 0])) @ Quaternion((r[3], r[0], r[1], r[2])).to_matrix().to_4x4() @ Matrix.Diagonal((s_[0], s_[1], s_[2], 1))
i = next(k for k, n in enumerate(doc['nodes']) if n.get('name') == 'Dagger'); N = Matrix()
while i is not None: N = trs(doc['nodes'][i]) @ N; i = parent.get(i)
C = Matrix.Rotation(1.5707963267948966, 4, 'X'); NREST = C @ N @ C.inverted()
def hull(pts):
    pts = sorted(map(tuple, pts))
    def cr(o, p, q): return (p[0]-o[0])*(q[1]-o[1]) - (p[1]-o[1])*(q[0]-o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cr(hi[-2], hi[-1], p) <= 0: hi.pop()
        hi.append(p)
    return np.array(lo[:-1] + hi[:-1])
def depth(poly, q):
    d = []
    for k in range(len(poly)):
        p0, p1 = poly[k], poly[(k + 1) % len(poly)]; e = p1 - p0; n = np.array([e[1], -e[0]]); n /= np.linalg.norm(n) + 1e-12
        d.append((q - p0) @ n)
    return -max(d)
print('GLBCLEAR skirt verts', len(skirt), 'hand verts', len(hand))
for name in acts:
    act = next(x for x in bpy.data.actions if x.name == name or x.name.split('|')[0] == name)
    rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    worst, wf, bad = -1e9, None, []
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
        sc.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        co = np.array([(body.matrix_world @ v.co)[:] for v in m.vertices]); ev.to_mesh_clear()
        pb = rig.pose.bones['Dagger']
        D = rig.matrix_world @ pb.matrix @ pb.bone.matrix_local.inverted() @ rig.matrix_world.inverted() @ NREST
        # dagger blade along the node's +Y (glTF), i.e. +Y in the converted node frame before conversion
        samples = list(co[hand]) + [np.array((D @ (C @ Vector((0, y, 0))))[:]) for y in np.linspace(-0.06, 0.32, 20)]
        sk = co[skirt]; hit = False
        for q in samples:
            band = sk[np.abs(sk[:, 2] - q[2]) < 0.015]
            if len(band) < 6: continue
            dd = depth(hull(band[:, :2]), q[:2])
            if dd > worst: worst, wf = dd, f
            hit |= dd > 0.002
        if hit: bad.append(f)
    print('GLBCLEAR', name, 'deepest', round(worst * 100, 2), 'cm at frame', wf, '| frames inside', bad)
