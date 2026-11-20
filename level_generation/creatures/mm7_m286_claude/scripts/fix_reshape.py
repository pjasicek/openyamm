"""v2a fix (user review 2026-10-21: "fix the abs ... and the shoulders"): replace the hard-edged reshape displacement
(reshape.apply + reshape.arm_apply, applied in step1_clean.py) on the rigged mesh by the smooth one
(reshape.apply_smooth + reshape.arm_delta_weighted with each vertex's B_<s>_UpperArm*/Forearm* weight):
co += new(orig_co) - old(orig_co). Topology, UVs, weights, joints and clips stay; works on any blend of this topology
(rig_v4 in rebuild.sh, rig_v6 the textured master). Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reshape
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
body = bpy.data.objects['Body']; me = body.data
if me.get('v2a_reshape_fixed'):
    raise SystemExit('FIXRESHAPE already applied to this mesh')
n = len(me.vertices)
oc = np.zeros(n * 3); me.attributes['orig_co'].data.foreach_get('vector', oc); oc = oc.reshape(-1, 3)
co = np.array([tuple(v.co) for v in me.vertices])
names = [g.name for g in body.vertex_groups]
w = {'L': np.zeros(n), 'R': np.zeros(n)}
for v in me.vertices:
    for e in v.groups:
        nm = names[e.group]
        for s in 'LR':
            if nm.startswith(f'B_{s}_UpperArm') or nm.startswith(f'B_{s}_Forearm'):
                w[s][v.index] += e.weight
old = reshape.arm_apply(reshape.apply(oc))
lo = reshape.apply_smooth(oc)
new = lo + reshape.arm_delta_weighted(oc, w)
d = new - old
co2 = co + d
for v, p in zip(me.vertices, co2):
    v.co = p
me['v2a_reshape_fixed'] = 1
E = np.array([tuple(e.vertices) for e in me.edges]); Lr = np.maximum(np.linalg.norm(oc[E[:, 0]] - oc[E[:, 1]], axis=1), 1e-4)
def grad(c):
    disp = c - oc
    return np.linalg.norm(disp[E[:, 0]] - disp[E[:, 1]], axis=1) / Lr
g0, g1 = grad(co), grad(co2)
print('FIXRESHAPE verts', n, 'moved mm max', round(float(np.linalg.norm(d, axis=1).max() * 1000), 1),
      'p99', round(float(np.percentile(np.linalg.norm(d, axis=1), 99) * 1000), 1),
      '| displacement gradient max', round(float(g0.max()), 2), '->', round(float(g1.max()), 2),
      'edges > 0.3:', int((g0 > 0.3).sum()), '->', int((g1 > 0.3).sum()))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
