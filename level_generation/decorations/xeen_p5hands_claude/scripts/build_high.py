"""Stage 1 (Blender): the high stone hand. Opens the Carnage Hand's rig_v1.blend (read only), poses the fingers open
and slightly cupped, bakes the pose, removes the palm mouth (face attribute part != 0) and closes the palm, turns the
hand palm up (fingers to the front, -Y), puts the palm centre (the mouth's centre) over the origin at palm_height,
adds a forearm swept from the plinth to the heel of the hand and a round stepped plinth, and voxel-remeshes the union
into one closed surface. Saves work/high.blend (object HighHand) and work/high_info.json.
Usage: blender -b --python build_high.py"""
import json, math, os, sys
import bpy, bmesh
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..'))
HAND = os.path.join(REPO, 'level_generation', 'creatures', 'xeen_hand_claude')
cfg = json.load(open(os.path.join(HERE, 'hand.json')))
work = os.path.join(PROJECT, 'work'); os.makedirs(work, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.join(HAND, 'work', 'rig_v1.blend'))
sys.path.insert(0, os.path.join(HAND, 'scripts'))
import handpose  # noqa: E402  (reads the hand project's rig_info.json)
sc = bpy.context.scene
rig = bpy.data.objects['Hand_Rig']; mesh = bpy.data.objects['Hand']
handpose.reset(rig)
handpose.hand(rig, {k: tuple(v) for k, v in cfg['flex'].items()}, spread=cfg['spread'])
dg = bpy.context.evaluated_depsgraph_get()
me = bpy.data.meshes.new_from_object(mesh.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
me.transform(mesh.matrix_world)
bm = bmesh.new(); bm.from_mesh(me)
part = bm.faces.layers.int.get('part')
mouth = [f for f in bm.faces if f[part] != 0]
rim = [f for f in bm.faces if f[part] == 1]
mouth_centre = sum((f.calc_center_median() for f in rim), Vector()) / len(rim)
n_palm = Vector(handpose.INFO['n']).normalized()      # out of the palm (the hand project's mouth frame)
bmesh.ops.delete(bm, geom=mouth, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
boundary = [e for e in bm.edges if e.is_boundary]
print('BOUNDARY edges', len(boundary))
res = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=boundary)
newf = [g for g in res['geom'] if isinstance(g, bmesh.types.BMFace)]
# relax the fill a little (boundary pinned) so the palm reads as one surface
fill_verts = {v for f in newf for v in f.verts}
for _ in range(6):
    bmesh.ops.smooth_vert(bm, verts=[v for v in fill_verts if not v.is_boundary], factor=0.5,
                          use_axis_x=True, use_axis_y=True, use_axis_z=True)
print('FILLED faces', len(newf))
bmesh.ops.triangulate(bm, faces=newf)
bm.normal_update()
# hand frame: palm normal n_palm, fingers up (+Z in the rest model), thumb +X
up = Vector((0, 0, 1))
f_dir = (up - n_palm * up.dot(n_palm)).normalized()
src = Matrix((n_palm, f_dir, n_palm.cross(f_dir))).transposed()
t = math.radians(cfg['palm_tilt_deg'])
p_t = Vector((0, -math.sin(t), math.cos(t)))          # palm faces up, tilted to the front
f_t = Vector((0, -math.cos(t), -math.sin(t)))         # fingers to the front
dst = Matrix((p_t, f_t, p_t.cross(f_t))).transposed()
R = (dst @ src.inverted()).to_4x4()
pc = mouth_centre.copy()
for v in bm.verts:
    v.co = R @ (v.co - pc)
bm.normal_update()
# palm centre now at the origin; raise to palm_height
H = cfg['palm_height']
for v in bm.verts:
    v.co.z += H
hand_me = bpy.data.meshes.new('HandPosed'); bm.to_mesh(hand_me); bm.free()
hand_ob = bpy.data.objects.new('HandPosed', hand_me); sc.collection.objects.link(hand_ob)
# heel: hand vertices furthest back along the fingers (+Y side, the -f_t direction)
co = [v.co.copy() for v in hand_me.vertices]
along = [c.dot(f_t) for c in co]
lo = min(along); hi = max(along)
heel = [c for c, a in zip(co, along) if a < lo + 0.06 * (hi - lo)]
heel_c = sum(heel, Vector()) / len(heel)
lat = Vector((1, 0, 0))
half_w = max(abs((c - heel_c).dot(lat)) for c in heel)
half_t = max(abs((c - heel_c).dot(p_t)) for c in heel)
# a wider section a little into the hand gives the wrist's real width
band = [c for c, a in zip(co, along) if lo + 0.08 * (hi - lo) < a < lo + 0.16 * (hi - lo)]
half_w, half_t = cfg['forearm']['wrist_half']
fa = cfg['forearm']
W = heel_c + f_t * fa['wrist_inset'] - p_t * fa.get('wrist_drop', 0.0)
B = Vector((0, fa['back'], 0))
print('HEEL', tuple(round(x, 3) for x in heel_c), 'half_w', round(half_w, 3), 'half_t', round(half_t, 3))
# forearm: a swept ellipse from the plinth top (vertical tangent) to the wrist (tangent along -f_t: into the heel)
pl = cfg['plinth']
z0 = pl['height']
P0 = Vector((B.x, B.y, 0.0)); P3 = W
T0 = Vector((0, 0, 1)); T3 = (-f_t * 0.35 + Vector((0, 0, 1)) * 0.65).normalized()
L = (P3 - P0).length
P1 = P0 + T0 * L * 0.4; P2 = P3 - T3 * L * 0.35
def bez(s):
    return (1 - s) ** 3 * P0 + 3 * (1 - s) ** 2 * s * P1 + 3 * (1 - s) * s * s * P2 + s ** 3 * P3
bm = bmesh.new()
rings = []
nr, ns = fa['rings'], fa['segments']
for i in range(nr + 1):
    s = i / nr
    c = bez(s)
    tan = (bez(min(1, s + 0.01)) - bez(max(0, s - 0.01))).normalized()
    x = (lat - tan * lat.dot(tan)).normalized()
    y = tan.cross(x)
    k = fa['base_scale'] + (fa['wrist_scale'] - fa['base_scale']) * (s ** 0.8)
    a, b = half_w * k, half_t * k
    ring = []
    for j in range(ns):
        th = 2 * math.pi * j / ns
        # superellipse (n 2.4): a squarer forearm section
        cs, sn = math.cos(th), math.sin(th)
        e = 2 / 2.4
        px = a * math.copysign(abs(cs) ** e, cs); py = b * math.copysign(abs(sn) ** e, sn)
        ring.append(bm.verts.new(c + x * px + y * py))
    rings.append(ring)
for i in range(nr):
    for j in range(ns):
        bm.faces.new((rings[i][j], rings[i][(j + 1) % ns], rings[i + 1][(j + 1) % ns], rings[i + 1][j]))
bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
base_r = max(half_w, half_t) * fa['base_scale']
# plinth: two stacked discs (stepped), 64 sides
R1 = base_r * pl['radius_scale']; R2 = R1 - pl['step']
for r, z_lo, z_hi in ((R1, 0.0, z0 * 0.55), (R2, z0 * 0.55 - 0.001, z0)):
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=64, radius1=r, radius2=r * 0.985, depth=z_hi - z_lo,
                                matrix=Matrix.Translation((0, 0, (z_lo + z_hi) / 2)))
fore_me = bpy.data.meshes.new('ForearmPlinth'); bm.to_mesh(fore_me); bm.free()
fore_ob = bpy.data.objects.new('ForearmPlinth', fore_me); sc.collection.objects.link(fore_ob)
# union by voxel remesh
for o in list(sc.objects):
    if o not in (hand_ob, fore_ob):
        bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
hand_ob.select_set(True); fore_ob.select_set(True)
bpy.context.view_layer.objects.active = hand_ob
bpy.ops.object.join()
high = bpy.context.view_layer.objects.active
high.name = 'HighHand'
for a in [a for a in high.data.attributes if a.name == 'part']:
    high.data.attributes.remove(a)
mod = high.modifiers.new('remesh', 'REMESH'); mod.mode = 'VOXEL'; mod.voxel_size = cfg['voxel']; mod.adaptivity = 0.0
bpy.ops.object.modifier_apply(modifier='remesh')
mod = high.modifiers.new('smooth', 'CORRECTIVE_SMOOTH'); mod.iterations = 3; mod.factor = 0.5
mod.smooth_type = 'SIMPLE'
bpy.ops.object.modifier_apply(modifier='smooth')
high.data.shade_smooth()
v = [high.matrix_world @ x.co for x in high.data.vertices]
lo = Vector(map(min, *v)); hi = Vector(map(max, *v))
info = {'palm_centre': [0.0, 0.0, H], 'palm_normal': list(p_t), 'fingers': list(f_t), 'heel': list(heel_c),
        'base_radius': R1, 'bounds': [list(lo), list(hi)], 'high_tris': len(high.data.polygons) * 2}
json.dump(info, open(os.path.join(work, 'high_info.json'), 'w'), indent=1)
print('HIGH', info)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'high.blend'))
print('HIGH_DONE')
