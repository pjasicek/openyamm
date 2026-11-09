"""Weights of the jacket on the UV master, safe to re-run: no UV moves; only the front chain's bones. Arm chain only inside a tube round the arm axis (the arm axis runs down and out, so the low chest
projects onto it and took arm weights: the X of needles on the chest). Shoulder blend wide, the MM9 clips lift the arms over the head.
Args: <in blend> <out blend>"""
import bpy, sys, json, os
import numpy as np
A = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=A[0])
body = bpy.data.objects['Body']; arm = body.parent
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
J = {b.name: np.array(arm.matrix_world @ b.head_local) for b in arm.data.bones}
me = body.data
mw = body.matrix_world
CO = np.array([tuple(mw @ v.co) for v in me.vertices])
n = len(me.polygons)
part = np.zeros(n, np.int32); me.attributes['part'].data.foreach_get('value', part)
hand = np.zeros(n, np.int32); me.attributes['hand'].data.foreach_get('value', hand)
F = np.array([p.vertices[:] for p in me.polygons])
up = np.zeros(len(CO), bool); up[F[(part == 0) & (hand == 0)].ravel()] = True
up[F[hand == 1].ravel()] = False
sho = J['Zarmpiv01']; wr = J['Zhand01']; L = np.linalg.norm(wr - sho); u = (wr - sho) / L
e = np.linalg.norm(J['Zarm01'] - sho)


def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


sp = [(k, J[k][2]) for k in ('XCENTER', 'Xspine', 'Xspine1', 'Xspine2')]
gi = {g.name: g.index for g in body.vertex_groups}
changed = 0
for i in np.where(up)[0]:
    p = CO[i]
    side = 1 if p[0] > 0 else -1
    tag = '01' if side > 0 else ''
    Ms = np.array([side, 1, 1.0])
    uu = u * Ms; s0 = sho * Ms
    al = float((p - s0) @ uu)
    rad = float(np.linalg.norm(p - s0 - uu * al))
    tube = 1 - ss(0.085 + 0.25 * max(0.0, -al), 0.135 + 0.25 * max(0.0, -al), rad)
    arm_t = ss(-0.10, 0.05, al) * tube if abs(p[0]) > 0.09 else 0.0
    z = p[2]
    if z <= sp[1][1]:
        f = ss(sp[0][1], sp[1][1], z); tw = [('XCENTER', 1 - f), ('Xspine', f)]
    elif z <= sp[2][1]:
        f = ss(sp[1][1], sp[2][1], z); tw = [('Xspine', 1 - f), ('Xspine1', f)]
    elif z <= sp[3][1]:
        f = ss(sp[2][1], sp[3][1], z); tw = [('Xspine1', 1 - f), ('Xspine2', f)]
    else:
        tw = [('Xspine2', 1.0)]
    w = {}
    for k, x in tw:
        w[k] = w.get(k, 0) + x * (1 - arm_t)
    if arm_t > 0:
        base = 1 - ss(-0.03, 0.12, al)
        w['Zarmbase' + tag] = arm_t * base
        rest = arm_t * (1 - base)
        f = ss(e - 0.045, e + 0.045, al)
        h = 0.0     # sleeve and cuff stay on the forearm: MM9 turns the wrist up to 90 deg and a ring shared with the hand folds; the hand turns inside the cuff
        w['Zarmpiv' + tag] = rest * (1 - f)
        w['Zarm' + tag] = rest * f * (1 - h)
        w['Zhand' + tag] = rest * f * h
    top = sorted([(k, x) for k, x in w.items() if x > 1e-4], key=lambda t: -t[1])[:4]
    tot = sum(x for _, x in top)
    v = me.vertices[int(i)]
    for g in list(v.groups):
        body.vertex_groups[g.group].remove([int(i)])
    for k, x in top:
        body.vertex_groups[k].add([int(i)], x / tot, 'REPLACE')
    changed += 1
# ---- robe: MM9's rings as hat functions, as fit_ghost.py, with two changes. The chain's tip bone carries no skin: it has no child, MM9 turns it freely, and vertices off its column swing round it
# (the front tip folded over in Standing). The belt rings are one rigid band on XCENTER; the waist bends in the rows under it, from XCENTER through Ydress to the chain roots.
rep = json.load(open(os.path.join(os.path.dirname(A[0]), 'fit_v1.json')))
col, rows = rep['columns'], {k: [int(x) for x in v] for k, v in rep['rows'].items()}
CH = {'f': ['Yfront', 'YfA', 'YfB', 'YfC'], 'fl': ['Yfrontleft', 'YflA', 'YflB', 'YflC'], 'l': ['Yleft', 'YlA', 'YlB', 'YlC'],
      'bl': ['YblA', 'YblB', 'YblC'], 'b': ['Yback', 'YbA', 'YbB', 'YbC'], 'br': ['YbrA', 'YbrB', 'YbrC'],
      'r': ['Yrit', 'YrA', 'YrB', 'YrC'], 'fr': ['Yfrontrit', 'YfrA', 'YfrB', 'YfrC']}
fr = np.nonzero(part == 1)[0]
v0 = int(F[fr].min())
Nt = 40; Ns = 21
col['f'] = 0.0                                 # the nearest-joint search left it 2.3 columns off the centre line
assert int(F[fr].max()) - v0 + 1 == Nt * Ns
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects:
    o.select_set(o == arm)
bpy.ops.object.mode_set(mode='EDIT')
inv = arm.matrix_world.inverted()
for n_, r_ in zip(['Yfront', 'YfA', 'YfB', 'YfC', 'YfD'], rows['f']):
    b = arm.data.edit_bones[n_]; off = b.tail - b.head
    b.use_connect = False
    b.head = inv @ (mw @ me.vertices[v0 + r_ * Nt].co); b.tail = b.head + off
bpy.ops.object.mode_set(mode='OBJECT')
cols = sorted((col[c], c) for c in CH)
for i in range(Ns):
    for k in range(Nt):
        q = None
        for a in range(len(cols)):
            c0, n0 = cols[a]; c1, n1 = cols[(a + 1) % len(cols)]
            c1w = c1 + (Nt if c1 < c0 else 0)
            kk = k + (Nt if k < c0 else 0)
            if c0 <= kk <= c1w:
                q = (n0, n1, (kk - c0) / (c1w - c0)); break
        n0, n1, f = q
        w = {}
        for c, cw in ((n0, 1 - f), (n1, f)):
            rr = rows[c][:len(CH[c])]; bs = CH[c]
            if i <= 3:
                w['XCENTER'] = w.get('XCENTER', 0) + cw
                continue
            if i < rr[0]:
                g_ = (i - 3) / max(rr[0] - 3, 1)
                a_, b_ = ('XCENTER', 'Ydress') if g_ < 0.5 else ('Ydress', bs[0])
                h_ = g_ * 2 if g_ < 0.5 else g_ * 2 - 1
                w[a_] = w.get(a_, 0) + cw * (1 - h_); w[b_] = w.get(b_, 0) + cw * h_
                continue
            for a in range(len(rr) - 1):
                if rr[a] <= i < rr[a + 1]:
                    g_ = (i - rr[a]) / (rr[a + 1] - rr[a])
                    w[bs[a]] = w.get(bs[a], 0) + cw * (1 - g_); w[bs[a + 1]] = w.get(bs[a + 1], 0) + cw * g_
                    break
            else:
                w[bs[-1]] = w.get(bs[-1], 0) + cw
        top = sorted(w.items(), key=lambda t: -t[1])[:4]
        tot = sum(x for _, x in top)
        idx_ = v0 + i * Nt + k
        v = me.vertices[idx_]
        for g in list(v.groups):
            body.vertex_groups[g.group].remove([idx_])
        for n_, x in top:
            if x > 1e-4:
                body.vertex_groups[n_].add([idx_], x / tot, 'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=A[1])
print('RIGFIX', changed, 'jacket vertices', Nt * Ns, 'robe vertices')
