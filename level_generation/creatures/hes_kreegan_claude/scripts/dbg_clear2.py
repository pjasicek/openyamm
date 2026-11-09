"""hkr copy of rifle_clear.py with the torso plates (Arm_* on B_Spine2 / B_Pelvis) as obstacles and the right arm plates as movers.
Keep the rifle and the right fist out of the armoured torso (gate G6: the source mannequin's chest is slimmer than
the guard's chest plate, so the aim pressed the stock and the fist up to 8 cm into it). Per frame of the listed clips:
the evaluated torso, plates, head and legs (not the arms, not the skirt) as a BVH; the deepest point of the rifle and
of the right fist inside it (nearest-surface test, as gates.py) plus MARGIN; the right hand moves by that depth along
the chest's horizontal forward axis (smoothed over time, kept at least the depth on the frames that need it), the
right arm re-solved with armik (hand rotation kept). The left hand is re-seated afterwards by support_hand.py.
PASSES rounds. Args: -- <in blend> <out blend> <Action> [...]"""
import bpy, sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armik, cfg
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
src, out, acts = a[0], a[1], a[2:]
MARGIN, PASSES, SIG = float(os.environ.get('MARGIN', '0.012')), int(os.environ.get('PASSES', '2')), 1.5
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; gun = bpy.data.objects['Rifle']; sc = bpy.context.scene; AW = rig.matrix_world
me = body.data; nv = len(me.vertices)
gv = np.array([x.value for x in me.attributes['garment'].data]); pv = np.array([x.value for x in me.attributes['piece'].data])
names = [g.name for g in body.vertex_groups]; W = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight
arm = W[:, [i for i, n in enumerate(names) if any(t in n for t in ('UpperArm', 'Forearm', 'Hand'))]].sum(1) > 0.2
P0 = np.array([v.co[:] for v in me.vertices]); JB = lambda n: np.array(rig.data.bones[n].head_local)
rhand = cfg.hand_mask(P0, pv, 'R', JB('B_R_Hand'), JB('B_R_Forearm'), 0.0)
tail = W[:, [i for i, n in enumerate(names) if n.startswith('Bone_0') and n not in ('Bone_024', 'Bone_023', 'Bone_025')]].sum(1) > 0.5
solid = ~arm & ~tail                                       # hkr: the whole body but the arms and the tail
faces = [tuple(f.vertices) for f in me.polygons if all(solid[i] for i in f.vertices)]


def evaluated(ob):
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); ev.to_mesh_clear()
    return co.reshape(-1, 3) @ np.array(ob.matrix_world.to_3x3()).T + np.array(ob.matrix_world.translation)


OBST = [o for o in bpy.data.objects if o.name.startswith('Arm_') and o.get('bone') in ('B_Spine2', 'B_Pelvis')]
MOVERS = [o for o in bpy.data.objects if o.name.startswith('Arm_') and o.get('bone') in ('B_R_Forearm', 'B_R_UpperArm')]


DIRS = [Vector((0.0123, 0.0217, 1.0)).normalized(), Vector((0.71, -0.33, -0.62)).normalized(), Vector((-0.55, 0.81, 0.2)).normalized()]


def parity(tree, p, maxd=1.0):
    votes = 0
    for d in DIRS:
        o = Vector(p); n = 0; tr = 0.0
        while tr < maxd:
            loc, nrm, fi, dist = tree.ray_cast(o, d, maxd - tr)
            if loc is None: break
            n += 1; tr += dist + 1e-5; o = loc + d * 1e-5
        votes += n % 2
    return votes >= 2


HANDV = W[:, [i for i, n in enumerate(names) if n.endswith('_Hand') or 'Finger' in n]].sum(1) > 0.5
FULL = [tuple(f.vertices) for f in me.polygons if not all(HANDV[k] for k in f.vertices)]   # the fists hold the gun (G5)


def depth():
    """deepest point of the carbine inside the body (closed skin, parity) or a torso plate, and of the right arm's
    plates inside a torso plate (nearest distance of the inside points)"""
    bc = evaluated(body); best = 0.0
    trees = [BVHTree.FromPolygons(bc.tolist(), FULL)]
    for o in OBST:
        e = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh()
        trees.append(BVHTree.FromPolygons([tuple(o.matrix_world @ v.co) for v in m.vertices], [tuple(p.vertices) for p in m.polygons if p.material_index == 0])); e.to_mesh_clear()
    G = evaluated(gun)
    for k, tree in enumerate(trees):
        pts = G if k == 0 else np.vstack([G] + [evaluated(o) for o in MOVERS])
        for p in pts:
            loc, n, fi, d = tree.find_nearest(Vector(p), 0.15)
            if loc is None or d <= best: continue
            if (Vector(p) - loc).dot(n) < 0 and parity(tree, p, 0.6): best = d
    return best



GI = {g.index: g.name for g in body.vertex_groups}
DOMB = [GI[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in me.vertices]
for clip, fr in (('Standing', 5), ('Walking', 10), ('Attack', 20)):
    rig.animation_data.action = bpy.data.actions[clip]; rig.animation_data.action_slot = bpy.data.actions[clip].slots[0]
    sc.frame_set(fr)
    bc = evaluated(body); tree = BVHTree.FromPolygons(bc.tolist(), FULL)
    G = evaluated(gun); res = []
    for k, p in enumerate(G):
        loc, n, fi, d = tree.find_nearest(Vector(p), 0.15)
        if loc is None: continue
        if (Vector(p) - loc).dot(n) < 0 and parity(tree, p, 0.6):
            res.append((round(d * 100, 1), DOMB[FULL[fi][0]], k))
    res.sort(reverse=True)
    print('DBGC', clip, fr, res[:6])
