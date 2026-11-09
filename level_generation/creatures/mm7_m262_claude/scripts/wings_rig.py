"""Wing bone chains (from mm7_m150_claude, the angel; WRIST_FRAC for the harpy's steep wings) (wings are the separate 'Wings' object from step1_clean.py: P01 the upper coverts of
both wings joined across the shoulder blades, P06/P07 inner and P11/P12 outer feather sheets).

Per side, the LEADING EDGE is traced from the mesh: for |x| slices (2 cm) the highest vertex. Joints on that edge
(moved EDGE_IN m down into the coverts' thickness): root at |x| = ROOT_X (the shoulder blade), shoulder at |x| =
SHOULDER_X, wrist = the edge's highest point, tip = the vertex farthest out. Bones Wing_<s>_1 (root -> shoulder),
_2 (shoulder -> wrist), _3 (wrist -> tip), parent B_Spine2; roll: local Z = the wing's back normal (+Y).
Weights by the vertex's |x| along the chain (the feathers hang below the edge, so their span position, not their 3D
distance, says which bone carries them), smoothstep blends BLEND m wide at each joint; the coverts strap across the
back is B_Spine2 for |x| < SPINE_X, blending into Wing_<s>_1 by SPINE_X + BLEND. The Wings object is parented to the
rig with an armature modifier. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
src, out = sys.argv[sys.argv.index('--') + 1:]
E = lambda k, d: float(os.environ.get(k, d))
ROOT_X, SHOULDER_X, EDGE_IN, BLEND, SPINE_X = E('ROOT_X', 0.12), E('SHOULDER_X', 0.42), E('EDGE_IN', 0.03), E('BLEND', 0.08), E('SPINE_X', 0.07)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; wings = bpy.data.objects['Wings']; me = wings.data
co = np.array([tuple(wings.matrix_world @ v.co) for v in me.vertices])
chains = {}
for s, sg in (('L', 1.0), ('R', -1.0)):
    m = co[:, 0] * sg > 0.02
    ax = np.abs(co[:, 0])
    edge = []
    for x in np.arange(0.06, ax[m].max(), 0.02):
        sl = m & (np.abs(ax - x) < 0.01)
        if sl.sum():
            edge.append(co[sl][np.argmax(co[sl][:, 2])])
    edge = np.array(edge)
    def at(x):
        i = int(np.argmin(np.abs(np.abs(edge[:, 0]) - x)))
        return edge[i]
    root, sh = at(ROOT_X), at(SHOULDER_X)
    wr = edge[np.argmax(edge[:, 2])]
    tip = co[m][np.argmax(ax[m])]
    if os.environ.get('WRIST_FRAC'):                         # m262: a steep wing peaks at its tip; place the wrist
        tipe = edge[np.argmax(np.abs(edge[:, 0]))]           # by span fraction along the traced leading edge
        tip = co[m][np.argmax(co[m][:, 2])]
        wr = at(abs(root[0]) + (abs(tip[0]) - abs(root[0])) * float(os.environ['WRIST_FRAC']))
    pts = [root, sh, wr, tip]
    pts = [p - np.array([0, 0, EDGE_IN]) for p in pts[:3]] + [tip]
    chains[s] = [list(map(float, p)) for p in pts]
    print('WINGCHAIN', s, 'root', np.round(pts[0], 3), 'shoulder', np.round(pts[1], 3), 'wrist', np.round(pts[2], 3),
          'tip', np.round(pts[3], 3))
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
for s, pts in chains.items():
    parent = eb['B_Spine2']
    for i in range(3):
        b = eb.new(f'Wing_{s}_{i + 1}')
        b.head = Vector(pts[i]); b.tail = Vector(pts[i + 1])
        b.align_roll(Vector((0, 1, 0)))
        b.parent = parent; b.use_connect = i > 0
        b.use_deform = True
        parent = b
bpy.ops.object.mode_set(mode='OBJECT')


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


wings.vertex_groups.clear()
groups = {n: wings.vertex_groups.new(name=n) for n in ['B_Spine2'] + [f'Wing_{s}_{i}' for s in 'LR' for i in (1, 2, 3)]}
ax = np.abs(co[:, 0])
for s, sg in (('L', 1.0), ('R', -1.0)):
    xs = [abs(p[0]) for p in chains[s]]
    side = (co[:, 0] * sg >= 0)
    for vi in np.where(side)[0]:
        x = ax[vi]
        w = {}
        ws = 1 - smooth((x - SPINE_X) / BLEND)
        if ws > 0:
            w['B_Spine2'] = ws
        rest = 1 - ws
        # Wing_1 until the shoulder joint, Wing_2 to the wrist, Wing_3 beyond; blends centred on the joints
        b2 = smooth((x - (xs[1] - BLEND / 2)) / BLEND); b3 = smooth((x - (xs[2] - BLEND / 2)) / BLEND)
        w1 = rest * (1 - b2); w2 = rest * b2 * (1 - b3); w3 = rest * b2 * b3
        for k, v in ((1, w1), (2, w2), (3, w3)):
            if v > 1e-4:
                w[f'Wing_{s}_{k}'] = v
        for n, v in w.items():
            groups[n].add([int(vi)], float(v), 'REPLACE')
wings.parent = rig
for md in [m for m in wings.modifiers if m.type == 'ARMATURE']:
    wings.modifiers.remove(md)
md = wings.modifiers.new('Armature', 'ARMATURE'); md.object = rig
json.dump(chains, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'wing_chains.json'), 'w'), indent=1)
print('WINGRIG bones 6, vertices', len(co))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
