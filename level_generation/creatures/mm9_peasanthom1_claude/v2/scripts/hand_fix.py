"""Hands and sleeves for a real arm (Honk third pass, user 2026-10-31: "the hands are ultra strange ... weird proportions ... not straight as the arm ... bad graft").
Args (Blender): <in blend> <out blend> <report json> scale=<k> [centre=1]
- Hand size: the grafted hands were 12.7 cm (female) and 16.2 cm (male) against MM9's 16.8 and 17.9. Every hand-flag vertex and every bone under the Hand bone scales about the wrist
  by `scale`. Bone rest rotations do not change, only their positions, so the clips still apply.
- Sleeve centred on the forearm: the bell's opening sat about 10 cm off the forearm line, with the arm in its upper edge. The sleeve moves, not the arm, so hand paths and the gates
  built on them stay: body vertices on the forearm side slide across the forearm line, none at the elbow, all at the cuff, so the opening's centre lands on the line.
Run on fix_v1, before sleeve_lining.py."""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = a[:3]
opt = dict(x.split('=', 1) for x in a[3:])
K = float(opt['scale'])
bpy.ops.wm.open_mainfile(filepath=IN)
b = bpy.data.objects['Body']; rig = b.parent
if rig.animation_data:
    rig.animation_data.action = None
for p in rig.pose.bones:
    p.matrix_basis.identity()
bpy.context.view_layer.update()
me = b.data; M = b.matrix_world; Mi = M.inverted()
names = [g.name for g in b.vertex_groups]
rep = {}
wr = {s: rig.matrix_world @ rig.data.bones[f'Bip01 {s} Hand'].head_local for s in 'LR'}
el = {s: rig.matrix_world @ rig.data.bones[f'Bip01 {s} Forearm'].head_local for s in 'LR'}
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
dl = bm.verts.layers.deform.active
lh, lk = bm.faces.layers.int['head'], bm.faces.layers.int['hand']


def side_of(v):
    return 'L' if (M @ v.co - wr['L']).length < (M @ v.co - wr['R']).length else 'R'


hv = {v for f in bm.faces if f[lk] for v in f.verts}
for v in hv:
    s = side_of(v)
    v.co = Mi @ (wr[s] + (M @ v.co - wr[s]) * K)
rep['hand_verts'] = len(hv)
# sleeve
if opt.get('centre', '1') == '1':
    for s in 'LR':
        fa = (wr[s] - el[s]).normalized()
        L = (wr[s] - el[s]).length
        tok = f' {s} '

        def arm(v):
            w = v[dl]
            if not len(w):
                return False
            g = max(w.items(), key=lambda kv: kv[1])[0]
            return tok in names[g] and any(k in names[g] for k in ('Forearm', 'Hand', 'UpperArm'))

        vs = [v for v in bm.verts if v not in hv and arm(v) and not any(f[lh] or f[lk] for f in v.link_faces)]
        al = np.array([(M @ v.co - el[s]).dot(fa) for v in vs])
        cut = np.percentile(al, 88)
        far = [v for v, x in zip(vs, al) if x >= cut]
        u = fa.orthogonal().normalized(); w_ = fa.cross(u).normalized()
        pu = np.array([(M @ v.co - wr[s]).dot(u) for v in far]); pw = np.array([(M @ v.co - wr[s]).dot(w_) for v in far])
        cu, cw = (pu.max() + pu.min()) / 2, (pw.max() + pw.min()) / 2
        d = u * float(cu) + w_ * float(cw)
        for v, x in zip(vs, al):
            t = min(1.0, max(0.0, (x - 0.02) / (cut - 0.02)))
            t = t * t * (3 - 2 * t)
            v.co = Mi @ ((M @ v.co) - d * t)
        rep['sleeve_' + s] = {'verts': len(vs), 'shift_cm': round(d.length * 100, 1), 'open_radius_cm': [round(float(pu.max() - pu.min()) * 50, 1), round(float(pw.max() - pw.min()) * 50, 1)]}
bm.to_mesh(me); bm.free(); me.update()
# bones under the hand
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
ebs = rig.data.edit_bones
Ri = rig.matrix_world.inverted()
n = 0
for s in 'LR':
    root = ebs[f'Bip01 {s} Hand']
    w_ = Ri @ wr[s]
    tail = root.tail.copy()
    chain = [root] + list(root.children_recursive)
    moves = {x.name: (x.head.copy(), x.tail.copy()) for x in chain}
    for x in chain:
        h0, t0 = moves[x.name]
        conn = x.use_connect
        x.use_connect = False
        if x is not root:
            x.head = w_ + (h0 - w_) * K
        x.tail = w_ + (t0 - w_) * K
        n += 1
bpy.ops.object.mode_set(mode='OBJECT')
rep['bones_scaled'] = n
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('HAND_FIX', json.dumps(rep))
json.dump(rep, open(REP, 'w'), indent=1)
