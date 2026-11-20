"""New cleric hands from an MPFB (MakeHuman, CC0) male: relaxed right hand, left fist solved around the staff.

1. MPFB human with the `default` rig (wrist, metacarpals, three joints per finger; finger1 = thumb).
2. Per hand, anatomical frame from the rest joints: h = wrist -> middle knuckle, t = pinky -> index knuckle (thumb
   side), palm normal n (right: n = t x h, left: n = h x t). A finger joint flexes toward n; the sign of each bone's
   local X rotation is chosen by that test.
3. Right: relaxed curl (more toward the pinky), thumb slightly opposed. Left: a cylinder of the staff's radius (scaled
   into MPFB units) across the palm, slightly diagonal, its surface just above the palm; each finger is curled until its
   vertices reach the cylinder surface, then the thumb wraps over it.
4. Each hand (hand-bone weight > 0.5, plus a forearm stub reaching STUB metres above the wrist, which sits in the
   cuff) is cut from the posed mesh; UVs (MakeHuman layout) are kept.
Writes hands/mpfb_hands.blend (objects HandL, HandR in MPFB space, with frames as custom properties) and
hands/mpfb_frames.json. Args: -- <measure.json>"""
import bpy, bmesh, json, math, os, sys
import addon_utils
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(sys.argv[sys.argv.index('--') + 1]))
addon_utils.enable("bl_ext.blender_org.mpfb", default_set=True)
from bl_ext.blender_org.mpfb.services.humanservice import HumanService
bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("bl_ext.blender_org.mpfb", default_set=True)
h = HumanService.create_human()
rig = HumanService.add_builtin_rig(h, "default")
# the helper geometry (clothes/hair helpers) is hidden by a Mask modifier; keep evaluated indices equal to the mesh's
mask = next(m for m in h.modifiers if m.type == 'MASK')
MASK_GROUP, MASK_INV = mask.vertex_group, mask.invert_vertex_group
mask.show_viewport = False; mask.show_render = False
dg = lambda: bpy.context.evaluated_depsgraph_get()


def posed_verts():
    bpy.context.view_layer.update()
    ev = h.evaluated_get(dg()); me = ev.to_mesh()
    P = np.array([(h.matrix_world @ v.co)[:] for v in me.vertices]); ev.to_mesh_clear()
    return P


def J(name, tail=False):
    pb = rig.pose.bones[name]
    return rig.matrix_world @ (pb.tail if tail else pb.head)


P0 = posed_verts()
height = P0[:, 2].max() - P0[:, 2].min()
S = 1.578 / height                                     # MPFB -> cleric scale (same body height)
R_STAFF = M['staff']['radius_near_grip'] / S
names = {g.index: g.name for g in h.vertex_groups}
nv = len(h.data.vertices)
W = {}
for v in h.data.vertices:
    for g in v.groups:
        W.setdefault(names[g.group], np.zeros(nv))[v.index] = g.weight
FING = {1: ['finger1-1', 'finger1-2', 'finger1-3'], 2: ['finger2-1', 'finger2-2', 'finger2-3'],
        3: ['finger3-1', 'finger3-2', 'finger3-3'], 4: ['finger4-1', 'finger4-2', 'finger4-3'],
        5: ['finger5-1', 'finger5-2', 'finger5-3']}


def frame(sfx):
    w = J('wrist' + sfx); m3 = J('finger3-1' + sfx); i2 = J('finger2-1' + sfx); p5 = J('finger5-1' + sfx)
    hd = (m3 - w).normalized(); t = (i2 - p5); t = (t - hd * t.dot(hd)).normalized()
    n = t.cross(hd) if sfx == '.R' else hd.cross(t)
    return w, hd, t, n.normalized()


def finger_vids(sfx, f):
    acc = sum(W.get(b + sfx, 0) for b in FING[f])
    body = W.get(MASK_GROUP, np.zeros(nv)) > .5
    return np.where((acc > 0.4) & (~body if MASK_INV else body))[0]


def flex_sign(bone, n):
    """+1 if a positive local-X rotation moves the bone's tail toward n"""
    pb = rig.pose.bones[bone]; pb.rotation_mode = 'XYZ'
    t0 = J(bone, True); pb.rotation_euler = (0.3, 0, 0); bpy.context.view_layer.update()
    t1 = J(bone, True); pb.rotation_euler = (0, 0, 0); bpy.context.view_layer.update()
    return 1.0 if (t1 - t0).dot(n) > 0 else -1.0


def curl(sfx, f, c, n, split=(1.0, 1.15, 0.8)):
    for b, k in zip(FING[f], split):
        pb = rig.pose.bones[b + sfx]; pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (SIGN[b + sfx] * c * k, 0, 0)


SIGN = {}
frames = {}
for sfx in ('.L', '.R'):
    w, hd, t, n = frame(sfx)
    frames[sfx] = (w, hd, t, n)
    for f in FING:
        for b in FING[f]:
            SIGN[b + sfx] = flex_sign(b + sfx, n)

# right hand: relaxed (degrees per finger: MCP base; PIP x1.15, DIP x0.8); the thumb stays open so it never rings
w, hd, t, n = frames['.R']
for f, deg in ((2, 8), (3, 14), (4, 20), (5, 26)):
    curl('.R', f, math.radians(deg), n)
th = rig.pose.bones['finger1-1.R']; th.rotation_mode = 'XYZ'
th.rotation_euler = (math.radians(-10), 0, math.radians(18))   # out of the palm, alongside the index (no ring)
for b, a in (('finger1-2.R', 6), ('finger1-3.R', 8)):
    rig.pose.bones[b].rotation_mode = 'XYZ'; rig.pose.bones[b].rotation_euler = (SIGN[b] * math.radians(a), 0, 0)

# left hand: fist around the staff cylinder, wrapped joint by joint (knuckle, middle, tip)
w, hd, t, n = frames['.L']
bpy.context.view_layer.update()
P = posed_verts()
body_v = W.get(MASK_GROUP, np.zeros(nv)) > .5
if MASK_INV:
    body_v = ~body_v
m3 = J('finger3-1.L')
palm = np.where(body_v & (sum(W.get(b + '.L', 0) for b in ('metacarpal1', 'metacarpal2', 'metacarpal3', 'metacarpal4', 'wrist')) > .5))[0]
rel = P[palm] - np.array(m3[:])
near = np.abs(rel @ np.array(hd[:]) + 0.02 / S) < 0.01 / S   # palm band 2 cm behind the knuckle line
near &= np.abs(rel @ np.array(t[:])) < 0.02 / S                  # central palm, not the thenar/hypothenar pads
surf = np.percentile(rel[near] @ np.array(n[:]), 70)
ax = (t + hd * 0.2).normalized()                       # slightly diagonal: staff runs toward the wrist on the pinky side
ax = (ax - n * ax.dot(n)).normalized()
centre = m3 - hd * (0.02 / S) + n * (surf + R_STAFF - 0.002 / S)
TOL = R_STAFF + 0.0008 / S


def axis_dist(Q):
    d = Q - np.array(centre[:]); along = d @ np.array(ax[:])
    return np.linalg.norm(d - np.outer(along, ax[:]), axis=1)


def seg_vids(bones):
    acc = sum(W.get(b, 0) for b in bones)
    return np.where((acc > 0.4) & body_v)[0]


def wrap(chain, limits, start=(0, 0, 0)):
    """flex each joint in turn until its own and the distal segments reach the cylinder"""
    got = []
    for j, (bone, lim) in enumerate(zip(chain, limits)):
        vids = seg_vids(chain[j:]); pb = rig.pose.bones[bone]; pb.rotation_mode = 'XYZ'
        lo, hi = math.radians(start[j]), math.radians(lim)
        for _ in range(12):
            mid = (lo + hi) / 2; pb.rotation_euler = (SIGN[bone] * mid, 0, 0)
            if axis_dist(posed_verts()[vids]).min() < TOL:
                hi = mid
            else:
                lo = mid
        pb.rotation_euler = (SIGN[bone] * lo, 0, 0); got.append(round(math.degrees(lo), 1))
    return got


curls = {}
for f in (2, 3, 4, 5):
    curls[f] = wrap([b + '.L' for b in FING[f]], (95, 105, 80))
for b, a in (('finger1-1.L', -35), ('finger1-2.L', -10), ('finger1-3.L', 0)):   # swing the thumb clear first
    rig.pose.bones[b].rotation_mode = 'XYZ'; rig.pose.bones[b].rotation_euler = (SIGN[b] * math.radians(a), 0, 0)
curls[1] = wrap([b + '.L' for b in FING[1]], (60, 70, 70), start=(-35, -10, 0))
print('CURLS', curls, 'scale', round(S, 4), 'r_mpfb', round(R_STAFF, 4))

# cut each hand out of the posed, helper-free mesh
bpy.context.view_layer.update()
ev = h.evaluated_get(dg())
STUB = 0.035 / S
out = {}
for sfx, obj_name in (('.L', 'HandL'), ('.R', 'HandR')):
    w, hd, t, n = frame(sfx)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg())
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    handw = sum(W.get(b + sfx, 0) for b in ['wrist'] + [f'metacarpal{i}' for i in range(1, 5)] + sum(FING.values(), []))
    keepv = set()
    body = W.get(MASK_GROUP, np.zeros(nv)) > .5
    if MASK_INV:
        body = ~body
    for v in bm.verts:
        if v.index >= nv or not body[v.index]:
            continue
        p = h.matrix_world @ v.co
        along = (p - w).dot(hd)
        if handw[v.index] > .5 or (along > -STUB and handw[v.index] > 0.02):
            keepv.add(v.index)
    dead = [f for f in bm.faces if not all(v.index in keepv for v in f.verts)]
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    # largest connected piece only (drops stray bits of the forearm)
    bm.faces.ensure_lookup_table()
    comp = {}; cid = 0
    for f in bm.faces:
        if f.index in comp: continue
        st = [f]; comp[f.index] = cid
        while st:
            x = st.pop()
            for e in x.edges:
                for y in e.link_faces:
                    if y.index not in comp: comp[y.index] = cid; st.append(y)
        cid += 1
    big = max(range(cid), key=lambda c: sum(1 for v in comp.values() if v == c))
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if comp[f.index] != big], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.transform(h.matrix_world)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(obj_name, me); bpy.context.scene.collection.objects.link(o)
    o.vertex_groups.clear()
    out[obj_name] = dict(wrist=list(w), h=list(hd), t=list(t), n=list(n), faces=len(me.polygons),
                         tris=sum(len(p.vertices) - 2 for p in me.polygons))
    if sfx == '.L':
        out[obj_name].update(axis=list(ax), centre=list(centre), r=R_STAFF, curls=curls)
out['scale'] = S
for o in list(bpy.data.objects):
    if o.name not in ('HandL', 'HandR'):
        bpy.data.objects.remove(o, do_unlink=True)
json.dump(out, open(os.path.join(HERE, 'mpfb_frames.json'), 'w'), indent=1)
print('HANDS', {k: (v['faces'], v['tris']) for k, v in out.items() if isinstance(v, dict)})
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'mpfb_hands.blend'))
