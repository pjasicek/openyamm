"""MM7 Chicken rig (quadruped playbook's own-rig route with two legs; bird legs as the cockatrice,
mm6_ckt_claude): joints measured on work/step1.blend (forward -Y, up +Z, left +X, toes at z = 0; shell = piece 0,
tail feather cards = pieces 1-8, eyes 9-10, flakes 11+ dropped).
Bones: Body (root, hips -> chest) - Chest - Neck1 - Neck2 - Head (to the beak tip); Tail1 (rump -> tail tip, the
feather cards rigid on it); per side Thigh (hip -> knee, inside the body) - Shin (knee -> hock) - Tarsus (hock -> ankle)
- Foot (ankle -> toe tip); Wing1 / Wing2 per side along the folded wing.
Joints: read off horizontal and vertical slices of the shell (see the block below; a traced-leg measure failed on the
short feathered legs): hock at the top of the bare shank, knee and hip inside the feathers, the neck and head on the
midline, the tail up into the feather cards. Wings: the folded wing is part of the shell (|x| > WING_X at its height);
Wing1 / Wing2 follow it from front-top to rear-bottom.
The feet are fused at the inner toe tips: the bridge faces between them are deleted after weighting.
Weights: Blender heat weights on a voxel proxy of the shell with the wing bones excluded; then the folded wing takes
the wing bones (outward ramp over 2 cm, by position along the wing), feather cards rigid on Tail1, eyes rigid on
Head, the feet below 1.5 cm and the toes rigid on Foot.
Writes work/joints.json and work/rig_v1.blend. Args: none"""
import bpy, bmesh, os, sys, json, math
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOXEL = float(os.environ.get('VOXEL', '0.006'))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'step1.blend'))
body = bpy.data.objects['Body']; me = body.data
# drop the flakes (pieces 11+: 3-6 vertex surface splinters)
bm = bmesh.new(); bm.from_mesh(me); pl = bm.verts.layers.int['piece']
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[pl] >= 11], context='VERTS'); bm.to_mesh(me); bm.free()
co = np.array([tuple(v.co) for v in me.vertices]); nv = len(co)
pv = np.zeros(nv, np.int32); me.attributes['piece'].data.foreach_get('value', pv)
S = co[pv == 0]; H = S[:, 2].max()
# ---------------------------------------------------------------- joints (read off the shell's slices: work/joints.json)
# legs: the bare shank runs from the foot (z < 2.5 cm) to z 9 cm where the feathered thigh starts; the stance is
# staggered (left foot 4 cm ahead). Body z 0.11-0.32, widest (the folded wing) at z 0.19-0.25 between y -0.12 and +0.06.
J = {'L': {'hip': (0.045, 0.0, 0.20), 'knee': (0.060, -0.060, 0.15), 'hock': (0.051, -0.045, 0.09),
           'ankle': (0.056, -0.060, 0.022), 'toe': (0.071, -0.146, 0.01)},
     'R': {'hip': (-0.045, 0.0, 0.20), 'knee': (-0.058, -0.035, 0.15), 'hock': (-0.046, -0.020, 0.09),
           'ankle': (-0.053, -0.020, 0.022), 'toe': (-0.057, -0.110, 0.01)}}
J = {k: {kk: np.array(vv) for kk, vv in v.items()} for k, v in J.items()}
hips = np.array((0.0, 0.0, 0.20)); chest = np.array((0.0, -0.09, 0.24)); neck_base = np.array((0.0, -0.12, 0.31))
neck_mid = np.array((0.0, -0.14, 0.36)); head_base = np.array((0.0, -0.145, 0.405)); beak = np.array((0.0, -0.222, 0.41))
tail_root = np.array((0.0, 0.10, 0.27)); tail_tip = np.array((0.0, 0.20, 0.36))
WING_X = 0.075                                         # the folded wing: |x| beyond this, y -0.13 .. +0.10, z 0.15 .. 0.31
wings = {sd: {'root': np.array((sg * 0.085, -0.10, 0.26)), 'mid': np.array((sg * 0.10, -0.01, 0.23)),
              'tip': np.array((sg * 0.08, 0.08, 0.21))} for sd, sg in (('L', 1), ('R', -1))}
JJ = {'legs': {k: {kk: list(map(float, vv)) for kk, vv in v.items()} for k, v in J.items()},
      'hips': list(map(float, hips)), 'chest': list(map(float, chest)), 'neck_base': list(map(float, neck_base)),
      'neck_mid': list(map(float, neck_mid)), 'head_base': list(map(float, head_base)), 'beak': list(map(float, beak)),
      'tail_root': list(map(float, tail_root)), 'tail_tip': list(map(float, tail_tip)),
      'wings': {k: {kk: list(map(float, vv)) for kk, vv in v.items()} for k, v in wings.items()}}
json.dump(JJ, open(os.path.join(HERE, 'work', 'joints.json'), 'w'), indent=1)
# ---------------------------------------------------------------- armature
V = lambda a: Vector(tuple(a))
ad = bpy.data.armatures.new('Rig'); rig = bpy.data.objects.new('Rig', ad)
bpy.context.scene.collection.objects.link(rig); bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT'); eb = ad.edit_bones


def bone(n, h, t, parent=None, connect=False, roll_up=Vector((0, 0, 1))):
    b = eb.new(n); b.head = V(h); b.tail = V(t); b.align_roll(roll_up); b.parent = eb[parent] if parent else None
    b.use_connect = connect; return b


bone('Body', hips, chest)
bone('Chest', chest, neck_base, 'Body', True)
bone('Neck1', neck_base, neck_mid, 'Chest', True)
bone('Neck2', neck_mid, head_base, 'Neck1', True)
bone('Head', head_base, beak, 'Neck2', True)
bone('Tail1', tail_root, tail_tip, 'Body')
for sd in 'LR':
    L = J[sd]
    bone(f'Thigh_{sd}', L['hip'], L['knee'], 'Body', roll_up=Vector((0, -1, 0)))
    bone(f'Shin_{sd}', L['knee'], L['hock'], f'Thigh_{sd}', True, roll_up=Vector((0, -1, 0)))
    bone(f'Tarsus_{sd}', L['hock'], L['ankle'], f'Shin_{sd}', True, roll_up=Vector((0, -1, 0)))
    bone(f'Foot_{sd}', L['ankle'], L['toe'], f'Tarsus_{sd}', True)
    W_ = wings[sd]
    bone(f'Wing1_{sd}', W_['root'], W_['mid'], 'Chest')
    bone(f'Wing2_{sd}', W_['mid'], W_['tip'], f'Wing1_{sd}', True)
bpy.ops.object.mode_set(mode='OBJECT')
names = [b.name for b in ad.bones]
# ---------------------------------------------------------------- heat weights on a voxel proxy of the shell (wings excluded)
pm = me.copy(); proxy = bpy.data.objects.new('Proxy', pm); bpy.context.scene.collection.objects.link(proxy)
bmp = bmesh.new(); bmp.from_mesh(pm); lay = bmp.verts.layers.int.get('piece')
bmesh.ops.delete(bmp, geom=[v for v in bmp.verts if v[lay] != 0], context='VERTS'); bmp.to_mesh(pm); bmp.free()
r = proxy.modifiers.new('Remesh', 'REMESH'); r.mode = 'VOXEL'; r.voxel_size = VOXEL
rm = bpy.data.meshes.new_from_object(proxy.evaluated_get(bpy.context.evaluated_depsgraph_get())); proxy.modifiers.clear(); proxy.data = rm
for b in ad.bones:
    b.use_deform = not b.name.startswith('Wing')
for o in bpy.data.objects:
    o.select_set(o in (proxy, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
pw = np.array([sum(g.weight for g in v.groups) for v in rm.vertices])
print('RIG proxy verts', len(rm.vertices), 'unweighted', int((pw < 1e-6).sum()), 'voxel', VOXEL)
for b in ad.bones:
    b.use_deform = True
body.vertex_groups.clear()
for n in names:
    body.vertex_groups.new(name=n)
dt = body.modifiers.new('DT', 'DATA_TRANSFER'); dt.object = proxy
dt.use_vert_data = True; dt.data_types_verts = {'VGROUP_WEIGHTS'}; dt.vert_mapping = 'POLYINTERP_NEAREST'
dt.layers_vgroup_select_src = 'ALL'; dt.layers_vgroup_select_dst = 'NAME'
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.ops.object.modifier_apply(modifier='DT')
gi = {n: i for i, n in enumerate(names)}
W = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight
bpy.data.objects.remove(proxy, do_unlink=True)
# feet: below 1.5 cm rigid on the nearer foot (by the ankle-to-toe segment: the inner toes reach across x = 0)
low = (pv == 0) & (co[:, 2] < 0.015)
dd = {}
for sd in 'LR':
    a, b = J[sd]['ankle'][:2], J[sd]['toe'][:2]; ab = b - a
    t = np.clip(((co[:, :2] - a) @ ab) / (ab @ ab), 0, 1)
    dd[sd] = np.linalg.norm(co[:, :2] - (a + t[:, None] * ab), axis=1)
for sd in 'LR':
    m = low & (dd[sd] <= dd['R' if sd == 'L' else 'L'])
    W[m] = 0; W[m, gi[f'Foot_{sd}']] = 1
# wings: the folded wing's surface ramps onto Wing1 / Wing2 (outward over 2 cm past WING_X), split along the wing
for sd, sg in (('L', 1), ('R', -1)):
    W_ = wings[sd]; a, b = W_['root'], W_['tip']; ab = b - a
    t = np.clip(((co - a) @ ab) / (ab @ ab), 0, 1)
    box = (pv == 0) & (co[:, 1] > -0.13) & (co[:, 1] < 0.10) & (co[:, 2] > 0.15) & (co[:, 2] < 0.31)
    wgt = np.clip((sg * co[:, 0] - WING_X) / 0.02, 0, 1) * box
    wgt *= np.clip(np.minimum(co[:, 1] + 0.13, 0.10 - co[:, 1]) / 0.03, 0, 1)    # fade at the wing's front and rear
    wgt *= np.clip(np.minimum(co[:, 2] - 0.15, 0.31 - co[:, 2]) / 0.03, 0, 1)
    move = wgt > 0
    W[move] *= (1 - wgt[move])[:, None]
    s2 = np.clip(2 * t[move] - 0.5, 0, 1)
    W[move, gi[f'Wing1_{sd}']] += wgt[move] * (1 - s2)
    W[move, gi[f'Wing2_{sd}']] += wgt[move] * s2
    print('RIG wing', sd, 'vertices', int((wgt > 0.5).sum()))
W[(pv >= 1) & (pv <= 8)] = 0; W[(pv >= 1) & (pv <= 8), gi['Tail1']] = 1
W[(pv == 9) | (pv == 10)] = 0; W[(pv == 9) | (pv == 10), gi['Head']] = 1
good = np.where(W.sum(1) > 0.5)[0]; lost = np.where(W.sum(1) <= 0.5)[0]
if len(lost):
    kd = KDTree(len(good))
    for i, g in enumerate(good):
        kd.insert(co[g], i)
    kd.balance()
    for i in lost:
        W[i] = W[good[kd.find(co[i])[1]]]
W /= np.maximum(W.sum(1, keepdims=True), 1e-9)
top4 = np.argsort(-W, 1)[:, :4]; W2 = np.zeros_like(W); rows = np.arange(nv)[:, None]
W2[rows, top4] = W[rows, top4]; W2 /= np.maximum(W2.sum(1, keepdims=True), 1e-9)
for g in list(body.vertex_groups):
    body.vertex_groups.remove(g)
for j, n in enumerate(names):
    g = body.vertex_groups.new(name=n)
    for i in np.nonzero(W2[:, j] > 1e-4)[0]:
        g.add([int(i)], float(W2[i, j]), 'REPLACE')
# the inner toe tips of both feet are fused at x = 0: delete the bridge faces between the feet (tiny holes under the toes)
fl, fr = gi['Foot_L'], gi['Foot_R']
bm = bmesh.new(); bm.from_mesh(me); dl = bm.verts.layers.deform.active
bridge = [f for f in bm.faces if any(dl and v[dl].get(fl, 0) > 0.5 for v in f.verts) and any(v[dl].get(fr, 0) > 0.5 for v in f.verts)]
bmesh.ops.delete(bm, geom=bridge, context='FACES')    # with the bridge edges only these faces use
cross = [e for e in bm.edges if (e.verts[0][dl].get(fl, 0) > 0.5 and e.verts[1][dl].get(fr, 0) > 0.5) or
         (e.verts[0][dl].get(fr, 0) > 0.5 and e.verts[1][dl].get(fl, 0) > 0.5)]
bmesh.ops.delete(bm, geom=cross, context='EDGES'); bm.to_mesh(me); bm.free()
print('RIG toe bridge edges left', len(cross))
print('RIG toe bridge faces deleted', len(bridge))
body.parent = rig
m = body.modifiers.new('Armature', 'ARMATURE'); m.object = rig
print('RIG bones', len(names), 'filled', len(lost))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
