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


def depth():
    bc = evaluated(body); trees = [BVHTree.FromPolygons(bc.tolist(), faces)]
    for o in OBST:
        e = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh()
        trees.append(BVHTree.FromPolygons([tuple(o.matrix_world @ v.co) for v in m.vertices], [tuple(p.vertices) for p in m.polygons if p.material_index == 0])); e.to_mesh_clear()
    pts = np.vstack([evaluated(gun), bc[rhand]] + [evaluated(o) for o in MOVERS]); best = 0.0
    for tree in trees:
        for p in pts:
            loc, n, fi, d = tree.find_nearest(Vector(p), 0.12)
            if loc is not None and (Vector(p) - loc).dot(n) < -0.5 * d:
                best = max(best, d)
    return best



rig.animation_data.action = bpy.data.actions['Standing']; rig.animation_data.action_slot = bpy.data.actions['Standing'].slots[0]
sc.frame_set(0)
bc = evaluated(body); trees = [('body', BVHTree.FromPolygons(bc.tolist(), faces))]
for o in OBST:
    e = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh()
    trees.append((o.name, BVHTree.FromPolygons([tuple(o.matrix_world @ v.co) for v in m.vertices], [tuple(p.vertices) for p in m.polygons if p.material_index == 0]))); e.to_mesh_clear()
groups = [('gun', evaluated(gun)), ('rhand', bc[rhand])] + [(o.name, evaluated(o)) for o in MOVERS]
for tn, tree in trees:
    for gn, pts in groups:
        best = (0, None)
        for p in pts:
            loc, n, fi, d = tree.find_nearest(Vector(p), 0.12)
            if loc is not None and (Vector(p) - loc).dot(n) < -0.5 * d and d > best[0]:
                best = (d, [round(x, 3) for x in p])
        if best[0] > 0: print('DBGCLEAR', tn, gn, round(best[0] * 100, 1), best[1])
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
full = BVHTree.FromPolygons(bc.tolist(), [tuple(f.vertices) for f in me.polygons])
for gn, pts in (('gun', evaluated(gun)),):
    ins = [p for p in pts if parity(full, p)]
    print('DBGPAR', gn, len(ins), 'of', len(pts), [ [round(x,3) for x in p] for p in ins[:5]])
