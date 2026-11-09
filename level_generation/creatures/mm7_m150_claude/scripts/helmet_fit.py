"""Fit the Meshy helmet (work/props.blend 'HelmetMesh', facing -Y) onto the angel's head, in place on the textured
master (work/rig_v6.blend), once (flag on the rig):
- skull: Body vertices mostly on B_Head (skin, eyes, hair) above the brow (eye centre + BROW m); its centre (x, y)
  at the brow, half widths along x and y, and the top;
- helmet cavity: rays from a point inside the bowl toward +-x, +-y and +z give the inner half widths and the inner top;
- scale so the cavity clears the skull by CLEAR on both axes, then place the cavity centre over the skull centre and
  its inner top CLEAR above the skull top; the placement is written to work/helmet_fit.json for export_runtime.py;
- scalp and hair vertices that would still poke out of the cavity (above the brow - 1 cm) are moved inward along the
  ray from the skull centre to PUSH inside the helmet's inner surface (the Smart Topology hair is full on top);
- a 'Helmet' bone (child of B_Head) at the skull centre.
Args: -- <blend>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = lambda k, d: float(os.environ.get(k, d))
BROW, CLEAR, PUSH = E('BROW', 0.035), E('CLEAR', 0.012), E('PUSH', 0.008)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
if rig.get('helmet_fit_applied'):
    print('HELMETFIT already applied'); raise SystemExit
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
gi = body.vertex_groups['B_Head'].index
hw = np.array([sum(e.weight for e in v.groups if e.group == gi) for v in me.vertices])
pv = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
eye = co[np.isin(pv, [15, 16])].mean(0)
brow = float(eye[2] + BROW)
head = (hw > 0.5) & (co[:, 2] > brow)
sk = co[head]
c_h = np.array([np.median(sk[:, 0]), (sk[:, 1].max() + sk[:, 1].min()) / 2])
ring = sk[np.abs(sk[:, 2] - (brow + 0.02)) < 0.015]
wx = float(np.abs(ring[:, 0] - c_h[0]).max()); wy = float(np.abs(ring[:, 1] - c_h[1]).max()); top = float(sk[:, 2].max())
print('HELMETFIT skull: brow z', round(brow, 3), 'centre', np.round(c_h, 3), 'half widths', round(wx, 3), round(wy, 3), 'top', round(top, 3))

with bpy.data.libraries.load(os.path.join(HERE, 'work', 'props.blend'), link=False) as (src, dst):
    dst.objects = ['HelmetMesh']
hm = dst.objects[0]; bpy.context.scene.collection.objects.link(hm)
H = np.array([tuple(v.co) for v in hm.data.vertices])
bm = bmesh.new(); bm.from_mesh(hm.data); tree = BVHTree.FromBMesh(bm); bm.free()
# a point inside the bowl: x centre of the mesh, y/z from the front-opening region's centre, refined by rays
cx = float(np.median(H[:, 0])); z0 = float(H[:, 2].min() + 0.45 * np.ptp(H[:, 2])); y0 = float(np.median(H[:, 1]))
p0 = Vector((cx, y0, z0))


def hit(d):
    r = tree.ray_cast(p0, Vector(d))
    return (r[0] - p0).length if r[0] is not None else None


dxp, dxm, dyp, dym, dzp = hit((1, 0, 0)), hit((-1, 0, 0)), hit((0, 1, 0)), hit((0, -1, 0)), hit((0, 0, 1))
print('HELMETFIT cavity rays +x', dxp, '-x', dxm, '+y', dyp, '-y', dym, '+z', dzp)
# re-centre the probe in the cavity and measure again
p0 = Vector((cx + (dxp - dxm) / 2 if dxp and dxm else cx, y0 + (dyp - (dym or dyp)) / 2 if dyp else y0, z0))
dxp, dxm, dyp, dym, dzp = hit((1, 0, 0)), hit((-1, 0, 0)), hit((0, 1, 0)), hit((0, -1, 0)), hit((0, 0, 1))
ihx = min(dxp, dxm); ihy = min(dyp, dym or dyp)
# per-axis scale (user review of v3: too wide, the ears showed): the cavity is long front to back, so one uniform
# scale fitted to the depth left the sides 25 % too wide; width and depth fit separately, height their geometric mean
sx, sy = (wx + CLEAR) / ihx, (wy + CLEAR) / ihy
# the Meshy shell is thick (brow band, rims): an inner fit leaves the outside ~2 cm wide of the head; SX_TIGHT narrows
# the width further and the scalp / ears are pushed inside below
sx *= E('SX_TIGHT', 0.88)
sz = float(np.sqrt(sx * sy)); s = sz
S3 = Vector((sx, sy, sz))
# placement: cavity centre (p0 x, y) over the skull centre; inner top (p0.z + dzp) CLEAR above the skull top
off = Vector((c_h[0], c_h[1], top + CLEAR)) - Vector((p0.x * sx, p0.y * sy, (p0.z + dzp) * sz))
M = Matrix.Translation(off) @ Matrix.Diagonal((sx, sy, sz, 1))
json.dump({'scale': [sx, sy, sz], 'offset': list(off)}, open(os.path.join(HERE, 'work', 'helmet_fit.json'), 'w'), indent=1)
print('HELMETFIT scale x/y/z', round(sx, 4), round(sy, 4), round(sz, 4), 'offset', np.round(list(off), 3), 'helmet height m', round(float(np.ptp(H[:, 2])) * sz, 3))
hm.data.transform(M)
# cheek guards (user review of v2: they stood off the face): below the brow the helmet is bent inward about its centre
# line so its inner surface sits CHEEK_GAP outside the face at cheek height (eye - 3 cm); the bend ramps in over the
# 6 cm below the brow, the bowl above stays as fitted
CHEEK_GAP = E('CHEEK_GAP', 0.006)
bm = bmesh.new(); bm.from_mesh(hm.data); tree = BVHTree.FromBMesh(bm); bm.free()
zc = float(eye[2] - 0.03)
face = co[(hw > 0.5) & (pv == 0) & (np.abs(co[:, 2] - zc) < 0.01) & (co[:, 1] < c_h[1] + 0.02)]   # skin, not hair
face_hw = float(np.abs(face[:, 0] - c_h[0]).max()) if len(face) else wx
cheek_y = float(face[np.argmax(np.abs(face[:, 0] - c_h[0])), 1]) if len(face) else c_h[1]
probe = Vector((c_h[0], cheek_y, zc))
gx = []
for sgn in (1, -1):
    r = tree.ray_cast(probe, Vector((sgn, 0, 0)), 0.4)
    gx.append((r[0] - probe).length if r[0] is not None else None)
inner = min(g for g in gx if g) if any(gx) else None
if inner and inner > face_hw + CHEEK_GAP:
    k = (face_hw + CHEEK_GAP) / inner
    for v in hm.data.vertices:
        t = min(max((brow - v.co.z) / 0.06, 0.0), 1.0); t = t * t * (3 - 2 * t)
        if t > 0:
            v.co.x = c_h[0] + (v.co.x - c_h[0]) * (1 - t * (1 - k))
    hm.data.update()
    print('HELMETFIT cheek guards: face half width', round(face_hw, 3), 'guard inner', round(inner, 3), '-> bent by', round(k, 3))
else:
    print('HELMETFIT cheek guards: face half width', round(face_hw, 3), 'guard inner', inner, '(no bend)')
bm = bmesh.new(); bm.from_mesh(hm.data); tree = BVHTree.FromBMesh(bm); bm.free()
# push the scalp / hair inside the cavity
centre = Vector((c_h[0], c_h[1], brow))
inv = body.matrix_world.inverted(); moved = 0; worst = 0.0
for i in np.where((hw > 0.3) & (co[:, 2] > zc - 0.06))[0]:   # scalp, the hair and the ears under the guards (the open face is not hit)
    p = Vector(co[i]); d = p - centre
    if d.length < 1e-4:
        continue
    r = tree.ray_cast(centre, d.normalized(), 0.4)
    if r[0] is None:
        continue
    lim = (r[0] - centre).length - PUSH
    if d.length > lim:
        worst = max(worst, d.length - lim)
        me.vertices[i].co = inv @ (centre + d.normalized() * lim); moved += 1
me.update()
print('HELMETFIT scalp/hair vertices pushed inside', moved, 'worst push cm', round(worst * 100, 1))
# keep the fitted helmet (world space, rest pose) in the master for export_runtime.py
hm.name = hm.data.name = 'HelmetFitted'; hm.hide_render = True; hm.hide_viewport = True
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones.new('Helmet'); eb.head = centre; eb.tail = centre + Vector((0, 0, 0.12)); eb.parent = rig.data.edit_bones['B_Head']
eb.align_roll(Vector((0, -1, 0)))
bpy.ops.object.mode_set(mode='OBJECT')
rig['helmet_fit_applied'] = 1
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(blend))
