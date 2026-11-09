"""G5 for the grafted MPFB hands (2026-10-30): finger weights from MPFB's own hand weights instead of the connectivity
fit (finger_weights.py). MPFB's groups (MP_<bone>, kept on the step1 Body by prep_forad.py) map to our chains:
wrist and metacarpal1-4 -> B_<s>_Hand, finger<f>-<j> -> B_<s>_Finger<f-1>, <f-1>1, <f-1>2 (right thumb quirk names),
lowerarm -> the vertex's existing (Meshy + twist) forearm weights. Blend per vertex by the graft factor graft_s
(0 in the forearm stub under the bracer .. 1 on the hand): new = s * mapped + (1 - s) * existing. Side by x
(the character's left is +X). Prints per-side counts. Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
V2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Body']; me = body.data; nv = len(me.vertices)
with bpy.data.libraries.load(os.path.join(V2, 'work', 'step1.blend')) as (s_, d_):
    d_.objects = ['Body']
ref = d_.objects[0]
assert len(ref.data.vertices) == nv, 'topology changed since step1'
mpn = {g.index: g.name[3:] for g in ref.vertex_groups if g.name.startswith('MP_')}
MP = [dict() for _ in range(nv)]
for v in ref.data.vertices:
    for e in v.groups:
        if e.group in mpn and e.weight > 1e-4:
            MP[v.index][mpn[e.group]] = e.weight
s = np.zeros(nv); me.attributes['graft_s'].data.foreach_get('value', s)
hand = np.zeros(nv, bool)
for i in range(nv):
    hand[i] = bool(MP[i])
names = [g.name for g in body.vertex_groups]; gi = {n: i for i, n in enumerate(names)}
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])


def target(side, b):
    if b == 'wrist' or b.startswith('metacarpal'):
        return f'B_{side}_Hand'
    if b.startswith('finger'):
        f, j = int(b[6]), int(b[8])
        i = f - 1
        if side == 'R' and i == 0:
            return ['B_R_Finger0', 'B_R_Finger0.001', 'B_R_Finger0.002'][j - 1]
        return f'B_{side}_Finger{i}' + ('' if j == 1 else str(j - 1))
    return None                                     # lowerarm: keep the existing forearm weights


count = {'L': 0, 'R': 0}
for v in me.vertices:
    i = v.index
    if not hand[i]:
        continue
    side = 'L' if co[i, 0] > 0 else 'R'
    ex = np.zeros(len(names))
    for e in v.groups:
        ex[e.group] = e.weight
    ex /= max(ex.sum(), 1e-9)
    mp = np.zeros(len(names)); keep = 0.0
    tot = sum(MP[i].values())
    for b, w in MP[i].items():
        t = target(side, b)
        if t is None:
            keep += w / tot
        else:
            mp[gi[t]] += w / tot
    new = s[i] * (mp + keep * ex) + (1 - s[i]) * ex
    new /= max(new.sum(), 1e-9)
    for g in list(v.groups):
        body.vertex_groups[g.group].remove([i])
    for j in np.nonzero(new > 1e-4)[0]:
        body.vertex_groups[int(j)].add([i], float(new[j]), 'REPLACE')
    count[side] += 1
fing = {sd: sorted({n for n in names if n.startswith(f'B_{sd}_Finger')}) for sd in 'LR'}
print('MPFINGERS hand vertices', count, 'finger groups', {k: len(v) for k, v in fing.items()})
bpy.data.objects.remove(ref, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
