"""Keep the rifle and the right fist out of the armoured torso (gate G6: the source mannequin's chest is slimmer than
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
if 'solid_garments' in cfg.C:   # har: closed shells only (the cloak, scarf strips and belt gear are open or loose)
    solid = ~arm & np.isin(gv, cfg.C['solid_garments']) & ~np.isin(pv, cfg.C.get('uniform_pieces', []))
    if 'strip' in me.attributes:
        solid &= np.array([x.value for x in me.attributes['strip'].data]) == 0
else:
    solid = ~arm & (gv != 2) & ~np.isin(pv, (6, 8))            # the shoulder plates ride the arm
faces = [tuple(f.vertices) for f in me.polygons if all(solid[i] for i in f.vertices)]


def evaluated(ob):
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); ev.to_mesh_clear()
    return co.reshape(-1, 3) @ np.array(ob.matrix_world.to_3x3()).T + np.array(ob.matrix_world.translation)


def depth():
    bc = evaluated(body); tree = BVHTree.FromPolygons(bc.tolist(), faces)
    pts = np.vstack([evaluated(gun), bc[rhand]]); best = 0.0
    for p in pts:
        loc, n, fi, d = tree.find_nearest(Vector(p), 0.12)
        if loc is not None and (Vector(p) - loc).dot(n) < -0.7 * d:
            if d > best and os.environ.get('DEBUG'):
                WORST[:] = [round(d * 100, 1), [round(x, 2) for x in p], int(pv[faces[fi][0]]), int(gv[faces[fi][0]])]
            best = max(best, d)
    return best


WORST = []


rep = {}
for name in acts:
    act = bpy.data.actions[name]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); fr = list(range(f0, f1 + 1))
    first = None
    for it in range(PASSES):
        need = []
        for f in fr:
            sc.frame_set(f); need.append(depth())
            if os.environ.get('DEBUG') and WORST:
                print('DEEP', name, f, WORST); WORST.clear()
        need = np.array(need)
        if first is None:
            first = float(need.max())
        push = np.where(need > 0, need + MARGIN, 0.0)
        k = np.exp(-0.5 * (np.arange(-5, 6) / SIG) ** 2); k /= k.sum()
        push = np.maximum(np.convolve(np.pad(push, 5, mode='edge'), k, mode='valid'), push)
        if push.max() <= 0:
            break
        keys = {}
        for f, d in zip(fr, push):
            sc.frame_set(f)
            if d <= 0:
                continue
            C = AW @ rig.pose.bones['B_Spine2'].matrix
            fwd = C.to_3x3() @ Vector((0, 0, -1)) if False else None
            sp = AW @ rig.pose.bones['B_Spine2'].matrix; pe = AW @ rig.pose.bones['B_Pelvis'].matrix
            # the chest's forward: perpendicular to the shoulder line, horizontal, toward the rifle's muzzle side
            sh = (AW @ rig.pose.bones['B_L_UpperArm'].matrix).translation - (AW @ rig.pose.bones['B_R_UpperArm'].matrix).translation
            fwd = Vector((0, 0, 1)).cross(sh); fwd.z = 0; fwd.normalize()
            if fwd.dot(Vector((0, -1, 0))) < 0:
                fwd = -fwd
            H = AW @ rig.pose.bones['B_R_Hand'].matrix
            armik.solve(rig, 'R', H.translation + fwd * float(d), hand_rot=H.to_3x3().normalized())
            keys[f] = {n: rig.pose.bones[n].matrix_basis.to_quaternion() for n in ('B_R_UpperArm', 'B_R_Forearm', 'B_R_Hand')}
        prev = {}
        for f in fr:
            if f not in keys:
                continue
            for n, q in keys[f].items():
                pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
                if n in prev and q.dot(prev[n]) < 0: q = -q
                prev[n] = q; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
    last = []
    for f in fr:
        sc.frame_set(f); last.append(depth())
    rep[name] = {'before_cm': round(first * 100, 1), 'after_cm': round(float(max(last)) * 100, 1)}
    print('RIFLECLEAR', name, json.dumps(rep[name]))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
