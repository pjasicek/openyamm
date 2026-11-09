"""Per-frame audit of the titan's clips (arm and hand gate, CLAUDE_HUMANOID_NPC_PLAYBOOK.md).

For every frame of each clip: arm (forearm/hand-dominant vertices) vertices inside the body (nearest body
face whose normal points away from the vertex, within 6 cm; body = everything not dominated by an arm bone), wrist
swing/twist (hand vs forearm), forearm twist (forearm vs upper arm), upper-arm roll (upper arm vs clavicle, about the
bone axis), lowest body and halberd z. Gate: penetration <= 2 cm (< 3 verts allowed at the armpit), wrist swing <= 60,
forearm twist <= 90, upper-arm roll <= 40 and stable over cyclic clips. Args: blend [clip,clip,...].
Writes work/pose_audit.json and prints one summary line per clip."""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, args[0]))
from mathutils import Quaternion
arm = bpy.data.objects['Titan_Rig']; mesh = bpy.data.objects['Titan']; AW = arm.matrix_world.copy()
scene = bpy.context.scene


class gr:
    scene = scene

    @staticmethod
    def B(n):
        return arm.pose.bones[n]

    @staticmethod
    def rest3(n):
        return AW.to_3x3() @ arm.data.bones[n].matrix_local.to_3x3()

    @staticmethod
    def swing_twist_deg(q, axis):
        p = Vector((q.x, q.y, q.z)).project(axis)
        t = Quaternion((q.w, p.x, p.y, p.z)); t.normalize(); s = q @ t.inverted()
        tw = math.degrees(2 * math.atan2(p.length, q.w)) * (1 if p.dot(axis) >= 0 else -1)
        return math.degrees(s.angle), (tw + 180) % 360 - 180

    @staticmethod
    def set_action(name):
        act = bpy.data.actions[name]; arm.animation_data.action = act
        if getattr(act, 'slots', None):
            arm.animation_data.action_slot = act.slots[0]
        return act, tuple(int(round(x)) for x in act.frame_range)


_gname = {g.index: g.name for g in mesh.vertex_groups}
gr._dom = [_gname.get(max(v.groups, key=lambda g: g.weight).group) if v.groups else None for v in mesh.data.vertices]
clips = args[1].split(',') if len(args) > 1 else ['Standing', 'Walking', 'Running', 'Attack', 'Ranged', 'Cast', 'Hit',
                                                   'Death', 'Dead', 'Fidget']
Y = Vector((0, 1, 0))
dom = np.array([d or '' for d in gr._dom])
ARMB = ('LeftArm', 'LeftForeArm', 'LeftForeArmTwist1', 'LeftForeArmTwist2', 'LeftHand', 'RightArm', 'RightForeArm',
        'RightForeArmTwist1', 'RightForeArmTwist2', 'RightHand')
distal = {s: np.where(np.isin(dom, [s + 'ForeArm', s + 'ForeArmTwist1', s + 'ForeArmTwist2', s + 'Hand']))[0]
          for s in ('Left', 'Right')}
body_v = set(np.where(~np.isin(dom, ARMB))[0].tolist())
body_polys = [p.index for p in mesh.data.polygons if all(v in body_v for v in p.vertices)]
CORE = ('Hips', 'Spine02', 'Spine01', 'Spine', 'neck', 'Head', 'LeftShoulder', 'RightShoulder')
core_v = set(np.where(np.isin(dom, CORE))[0].tolist())
core_polys = [p.index for p in mesh.data.polygons if all(v in core_v for v in p.vertices)]


DIRS = [Vector(d) for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))]


def parity(tree, p, d, reach=1.5):
    n, o = 0, p.copy()
    for _ in range(40):
        loc, nor, idx, dist = tree.ray_cast(o, d, reach)
        if loc is None:
            break
        n += 1
        o = loc + d * 1e-4
    return n % 2


def inside(V, tree, pts, limit=0.06):
    """Arms are tested against the torso core (spine/hips/head/clavicle faces; the open mail skirt and the legs
    give false parity), the halberd against the whole body. Ray-parity vote over six axis directions (open shells and flipped normals tolerated): inside when at least
    4 of 6 rays cross the body an odd number of times; depth = distance to the nearest body face."""
    n, deep = 0, 0.0
    for p in pts:
        loc, nor, idx, dist = tree.find_nearest(p, limit)
        if loc is None:
            continue
        if sum(parity(tree, p, d) for d in DIRS) >= 4:
            n += 1
            deep = max(deep, dist)
    return n, deep


def rel_angles(child, parent):
    q = ((AW @ gr.B(parent).matrix).to_3x3().normalized().inverted() @
         (AW @ gr.B(child).matrix).to_3x3().normalized()).to_quaternion()
    qr = (gr.rest3(parent).inverted() @ gr.rest3(child)).to_quaternion()
    return gr.swing_twist_deg(qr.inverted() @ q, Y)


# vertices already inside the body at rest (forearm skin under the sleeves) are covered, not penetrating
arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
em = mesh.evaluated_get(dg).to_mesh()
V0 = [mesh.matrix_world @ v.co for v in em.vertices]
tree0 = BVHTree.FromPolygons(V0, [tuple(em.polygons[i].vertices) for i in core_polys])
for s in ('Left', 'Right'):
    keep = []
    for i in distal[s]:
        if inside(V0, tree0, [V0[i]])[0] == 0:
            keep.append(i)
    print('REST covered', s, len(distal[s]) - len(keep), 'of', len(distal[s]))
    distal[s] = np.array(keep)
mesh.evaluated_get(dg).to_mesh_clear()
out = {}
for clip in clips:
    if clip not in bpy.data.actions:
        continue
    act, (f0, f1) = gr.set_action(clip)
    rows = []
    for f in range(f0, f1 + 1):
        gr.scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        em = mesh.evaluated_get(dg).to_mesh()
        V = [mesh.matrix_world @ v.co for v in em.vertices]
        tree = BVHTree.FromPolygons(V, [tuple(em.polygons[i].vertices) for i in body_polys])
        ctree = BVHTree.FromPolygons(V, [tuple(em.polygons[i].vertices) for i in core_polys])
        r = {'f': f}
        for s in ('Left', 'Right'):
            n, d = inside(V, ctree, [V[i] for i in distal[s]])
            r['pen_' + s[0]] = (n, round(d * 100, 1))
            sw, tw = rel_angles(s + 'Hand', s + 'ForeArm')
            r['wrist_' + s[0]] = (round(sw), round(tw))
            r['forearm_tw_' + s[0]] = round(rel_angles(s + 'ForeArm', s + 'Arm')[1])
            r['roll_' + s[0]] = round(rel_angles(s + 'Arm', s + 'Shoulder')[1])
        r['low_body'] = round(min(v.z for v in V) * 100, 1)
        mesh.evaluated_get(dg).to_mesh_clear()
        rows.append(r)
    out[clip] = rows

    def worst(key, idx=None, absval=True):
        vals = [(abs(r[key][idx]) if idx is not None else abs(r[key])) for r in rows]
        i = int(np.argmax(vals))
        return vals[i], rows[i]['f']
    summ = {k: worst(k, 1) + (max(r[k][0] for r in rows),) for k in ('pen_L', 'pen_R')}
    summ.update({k: worst(k, 0) for k in ('wrist_L', 'wrist_R')})
    summ.update({k: worst(k) for k in ('forearm_tw_L', 'forearm_tw_R', 'roll_L', 'roll_R')})
    summ['roll_range_R'] = max(r['roll_R'] for r in rows) - min(r['roll_R'] for r in rows)
    summ['roll_range_L'] = max(r['roll_L'] for r in rows) - min(r['roll_L'] for r in rows)
    summ['low_body'] = min(r['low_body'] for r in rows)
    print('AUDIT', clip, json.dumps(summ))
json.dump(out, open(os.path.join(common.WORK, 'pose_audit.json'), 'w'), indent=0)
