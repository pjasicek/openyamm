"""Stage 1 (Blender): a statue's high and low pieces. The source creature is posed and baked into a static mesh; the
built parts (flames, robe and wings, seat, jar and stream, the fire statue's plinth) are made around it; everything is
scaled so the figure's top stands `figure_top` model metres over its base and moved so the base's centre is the origin.
Model units: metres = game units / 100; front toward Blender -Y (glTF +Z).
Saves work/<id>/high.blend with collections High (normal-bake sources: the posed creature with its own materials and
the built parts' detailed versions) and Low (LOD0 pieces, each with the custom property part: 0 figure, 1 plinth or
seat, 2 built detail). Usage: blender -b --python build_high.py -- <id>"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..'))
sys.path.insert(0, HERE)
import posing  # noqa: E402
import shapes  # noqa: E402

sid = sys.argv[sys.argv.index('--') + 1]
cfg = json.load(open(os.path.join(HERE, 'statues.json')))[sid]
work = os.path.join(PROJECT, 'work', sid)
os.makedirs(work, exist_ok=True)
R = shapes.rng(cfg.get('seed', 7))

arm, bodies = posing.import_creature(os.path.join(REPO, cfg['source']), cfg['mesh'], cfg['materials'])
posing.apply_pose(arm, cfg['pose'])
BONE = {pb.name: (arm.matrix_world @ pb.head, arm.matrix_world @ pb.tail) for pb in arm.pose.bones}
fig = posing.bake_static(arm, bodies, 'HighFigure')
bm = bmesh.new()
bm.from_mesh(fig.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
bm.to_mesh(fig.data)
bm.free()
bulk = cfg.get('bulk', [1.0, 1.0])
fv = [v.co.copy() for v in fig.data.vertices]
ground = min(p.z for p in fv)

scene = bpy.context.scene
high_col = bpy.data.collections.new('High')
low_col = bpy.data.collections.new('Low')
scene.collection.children.link(high_col)
scene.collection.children.link(low_col)
scene.collection.objects.unlink(fig)
high_col.objects.link(fig)
plain = bpy.data.materials.new('BuiltStone')
built = []          # (high bmesh object, low target triangles or None, part)


def add_built(bm_, name, low_tris, part=2, remesh=None, smooth=0):
    ob = shapes.to_object(bm_, name, plain, high_col)
    if remesh:
        mod = ob.modifiers.new('rm', 'REMESH')
        mod.mode = 'VOXEL'
        mod.voxel_size = remesh
        if smooth:
            sm = ob.modifiers.new('sm', 'SMOOTH')
            sm.factor = 0.6
            sm.iterations = smooth
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        ob.modifiers.clear()
        old = ob.data
        ob.data = me
        bpy.data.meshes.remove(old)
        me.materials.append(plain)
    built.append((ob, low_tris, part))
    return ob


def tongue(bm_, root, direction, length, r0, side=None, wiggle=0.12, phase=0.0, curl=None, sides=8, flat=0.8):
    d = Vector(direction).normalized()
    side = (side or d.cross(Vector((0, 0, 1))) if abs(d.z) < 0.95 else Vector((1, 0, 0)))
    side = (side - d * side.dot(d)).normalized()
    other = d.cross(side)
    ctrl = []
    for i in range(7):
        s = i / 6
        p = root + d * (length * s) + side * (wiggle * length * math.sin(2 * math.pi * 0.85 * s + phase) * s) \
            + other * (0.5 * wiggle * length * math.sin(2 * math.pi * 0.6 * s + phase * 1.7) * s)
        if curl is not None:
            p += Vector(curl) * (length * s * s)
        ctrl.append(p)
    pts = shapes.catmull(ctrl, per=3)
    n = len(pts)
    radii = [r0 * (1 - i / (n - 1)) ** 0.85 for i in range(n)]
    shapes.tube(bm_, pts, radii, sides=sides, flat=flat, up=other)


def b(name, end=0):
    return BONE[name][end].copy()


# ------------------------------------------------------------------------------------- figure-space built parts
if sid == 'fire':
    feet = [p for p in fv if p.z < ground + 0.12]
    fc = Vector(((min(p.x for p in feet) + max(p.x for p in feet)) / 2, (min(p.y for p in feet) + max(p.y for p in feet)) / 2, ground))
    hips = b('Hips')
    fl = bmesh.new()
    # 1. the column: tongues from a ring round the feet, leaning in over the legs and licking up past the hips
    n_ring = 11
    for k in range(n_ring):
        a = 2 * math.pi * k / n_ring + R.uniform(-0.1, 0.1)
        rr = (0.40 + R.uniform(-0.05, 0.05), 0.30 + R.uniform(-0.04, 0.04))
        root = fc + Vector((math.cos(a) * rr[0], math.sin(a) * rr[1], -0.03))
        inward = (Vector((hips.x, hips.y, root.z)) - root)
        dirn = Vector((0, 0, 1)) + inward.normalized() * 0.22
        L = R.uniform(0.75, 1.25) * (1.15 if abs(math.cos(a)) > 0.6 else 1.0)
        tongue(fl, root, dirn, L, R.uniform(0.17, 0.22), wiggle=0.13, phase=R.uniform(0, 6.28),
               curl=(-inward.normalized() * 0.10))
    # inner ring: shorter, fatter tongues close to the legs
    for k in range(7):
        a = 2 * math.pi * (k + 0.5) / 7
        root = fc + Vector((math.cos(a) * 0.22, math.sin(a) * 0.15, -0.03))
        tongue(fl, root, (0, 0, 1), R.uniform(0.95, 1.35), R.uniform(0.17, 0.21), wiggle=0.12,
               phase=R.uniform(0, 6.28))
    # 2. flanks: from the hips up the sides of the torso
    for sx in (1, -1):
        for j in range(3):
            root = hips + Vector((sx * (0.11 + 0.02 * j), R.uniform(-0.05, 0.08), -0.05 + 0.12 * j))
            tongue(fl, root, (sx * 0.25, 0.1, 1), R.uniform(0.5, 0.75), 0.11, wiggle=0.12, phase=R.uniform(0, 6.28))
    # 3. the back and shoulders: rising up and back above the head
    sp = b('Spine2')
    for j, (dx, L) in enumerate(((-0.14, 0.75), (-0.05, 0.95), (0.05, 0.9), (0.14, 0.75), (0.0, 0.6))):
        root = sp + Vector((dx, 0.07, 0.05 - 0.08 * (j == 4)))
        tongue(fl, root, (dx * 1.2, 0.35, 1), L, 0.13, wiggle=0.1, phase=R.uniform(0, 6.28))
    # 4. hair: tongues from the crown streaming up and back
    hd, ht = b('Head'), b('Head', 1)
    crown = hd + (ht - hd).normalized() * 0.14
    for j, (dx, dy, L) in enumerate(((0, 0.0, 0.55), (-0.06, 0.04, 0.45), (0.06, 0.04, 0.45), (-0.04, 0.07, 0.4),
                                    (0.04, 0.07, 0.4), (0.0, 0.08, 0.5))):
        tongue(fl, crown + Vector((dx, dy - 0.02, -0.03)), (dx * 2, 0.45 + dy * 2, 1), L, 0.08, wiggle=0.16,
               phase=R.uniform(0, 6.28), sides=7)
    # 5. arms and hands: tongues along the outer forearms and out of the palms
    for side, sx in (('Left', 1), ('Right', -1)):
        fa0, fa1 = b(side + 'ForeArm'), b(side + 'ForeArm', 1)
        for t, L in ((0.3, 0.32), (0.7, 0.36)):
            root = fa0.lerp(fa1, t) + Vector((sx * 0.03, 0.02, 0))
            tongue(fl, root, (sx * 0.5, 0.15, 1), L, 0.065, wiggle=0.12, phase=R.uniform(0, 6.28), sides=7)
        hand = b(side + 'Hand', 1)
        tongue(fl, hand + Vector((0, 0, 0.04)), (sx * 0.2, 0.05, 1), 0.5, 0.085, wiggle=0.12, phase=R.uniform(0, 6.28),
               sides=7)
    add_built(fl, 'HighFlames', cfg['lod0_built_tris'], remesh=0.014, smooth=6)

if sid == 'air':
    feet = [p for p in fv if p.z < ground + 0.05]
    cx = (min(p.x for p in feet) + max(p.x for p in feet)) / 2
    cy = (min(p.y for p in feet) + max(p.y for p in feet)) / 2
    rx0 = (max(p.x for p in feet) - min(p.x for p in feet)) / 2
    ry0 = (max(p.y for p in feet) - min(p.y for p in feet)) / 2
    top = ground + 0.10
    rc = cfg['robe']
    rings = []
    N = 72
    steps = 22
    for i in range(steps + 1):
        t = i / steps                                   # 0 at the waist (top), 1 on the ground
        z = top + (0.0 - top) * t
        grow = t ** rc.get('flare_pow', 1.6)
        rx = rx0 * 0.97 + (rc['bottom_r'] - rx0) * grow
        ry = ry0 * 0.97 + (rc['bottom_r'] * 0.85 - ry0) * grow
        ccx = cx + rc.get('sway', 0.05) * math.sin(math.pi * t)
        ccy = cy + rc['stream_back'] * t ** 1.5
        amp = 0.010 + rc['fold_amp'] * t ** 1.2
        ph = rc['twist'] * t
        ring = []
        for j in range(N):
            a = 2 * math.pi * j / N
            f = math.cos(rc['folds'] * a + ph) + 0.35 * math.cos(2 * rc['folds'] * a - ph * 0.5)
            # the back of the robe streams further out than the front
            back = 1.0 + rc.get('back_bias', 0.25) * max(0.0, math.sin(a)) * t
            ring.append(Vector((ccx + math.cos(a) * (rx * back + amp * f), ccy + math.sin(a) * (ry * back + amp * f), z)))
        rings.append(ring)
    rb = bmesh.new()
    shapes.loft(rb, rings[::-1], cap_bottom=True, cap_top=True)
    add_built(rb, 'HighRobe', cfg['lod0_robe_tris'], remesh=0.012)
    # wings: rows of feathers (flattened ellipsoids) hung from a leading edge, fused by a voxel remesh
    wc = cfg['wings']
    sp = b('Spine2')
    for sx in (1, -1):
        wb = bmesh.new()
        root = Vector((sx * wc['root'][0], sp.y + wc['root'][1], wc['root'][2]))
        out = Vector((sx * math.cos(math.radians(wc['back_deg'])), math.sin(math.radians(wc['back_deg'])), 0.0))
        up = Vector((0, math.sin(math.radians(wc['tilt_deg'])), math.cos(math.radians(wc['tilt_deg']))))
        up = (up - out * up.dot(out)).normalized()
        nrm = out.cross(up) * sx
        edge2d = [Vector(p) * wc.get('scale', 1.0) for p in wc['edge']]
        edge = shapes.catmull(edge2d, per=8)

        def to3(p, lift=0.0):
            return root + out * p.x + up * p.y + nrm * lift

        shapes.tube(wb, [to3(p) for p in edge], [0.07 - 0.04 * (i / (len(edge) - 1)) for i in range(len(edge))],
                    sides=10, flat=0.6)
        for row in wc['rows']:
            count = row['count']
            for k in range(count):
                s = row['s0'] + (row['s1'] - row['s0']) * k / (count - 1)
                idx = min(len(edge) - 1, int(s * (len(edge) - 1)))
                p = edge[idx]
                ang = math.radians(row['a0'] + (row['a1'] - row['a0']) * s ** 1.2)
                d2 = Vector((math.sin(ang), -math.cos(ang)))          # hanging down, fanning outward
                L = (row['l0'] + (row['l1'] - row['l0']) * s ** row.get('lpow', 1.0)) * wc.get('scale', 1.0)
                c2 = p + d2 * (L * 0.5 - row.get('inset', 0.04))
                d3 = (out * d2.x + up * d2.y).normalized()
                w3 = nrm.cross(d3).normalized()
                m = Matrix((w3, nrm, d3)).transposed()
                shapes.ellipsoid(wb, to3(c2, row.get('lift', 0.0) + 0.004 * k), m,
                                 (row['w'], row.get('t', 0.022), L * 0.5), segs=10, rings=6)
        add_built(wb, 'HighWing%s' % ('L' if sx > 0 else 'R'), cfg['lod0_wing_tris'], remesh=0.011)

if sid == 'earth':
    seat_top = min(b('B_L_Thigh').z, b('B_R_Thigh').z) - cfg['seat']['below_hip']
    sb = bmesh.new()
    shapes.rough_block(sb, (-cfg['seat']['half_x'], cfg['seat']['y'][0], ground - 0.02),
                       (cfg['seat']['half_x'], cfg['seat']['y'][1], seat_top), cuts=7, amp=0.025, seed=3,
                       scale=4.0, chamfer=0.07)
    add_built(sb, 'HighSeat', cfg['lod0_seat_tris'], part=1)
    print('SEAT top %.3f ground %.3f' % (seat_top, ground))

JAR = None
if sid == 'water':
    jc = cfg['jar']
    h0, h1 = b('R_Hand'), b('R_Hand', 1)
    axis = Vector(jc['axis']).normalized()
    belly = h1 + Vector(jc['offset'])
    prof = [(r * jc['scale'], z * jc['scale']) for r, z in jc['profile']]
    zb = max(prof, key=lambda q: q[0])[1]                         # the belly's height on the jar's axis
    ref = Vector((0, 0, 1)) if abs(axis.z) < 0.9 else Vector((1, 0, 0))
    ax1 = ref.cross(axis).normalized()
    ax2 = axis.cross(ax1)
    m3 = Matrix((ax1, ax2, axis)).transposed()
    base = belly - axis * zb
    jb = bmesh.new()
    shapes.lathe(jb, prof, segments=24, centre=base, axis_matrix=m3, cap_top=True)
    # two handles from the shoulder to the neck
    for sgn in (1, -1):
        sh = base + axis * (prof[-6][1]) + ax1 * sgn * prof[-6][0] * 0.95
        nk = base + axis * (prof[-3][1]) + ax1 * sgn * prof[-3][0] * 0.9
        midp = (sh + nk) / 2 + ax1 * sgn * 0.07 * jc['scale'] / 0.9
        pts = shapes.catmull([sh, midp, nk], per=5)
        shapes.tube(jb, pts, [0.016 * jc['scale'] / 0.9] * len(pts), sides=8)
    add_built(jb, 'HighJar', cfg['lod0_jar_tris'])
    JAR = (base + axis * prof[-1][1], axis)

# ------------------------------------------------------------------------------------------ scale and origin
objs = [fig] + [o for o, _, _ in built]
allv = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
zmin = min(p.z for p in allv)
zmax = max(p.z for p in allv)
if cfg.get('centre') == 'bounds':
    base_pts = [p for p in allv if p.z < zmin + cfg.get('centre_band', 0.3)]
else:
    base_pts = [p for p in allv if p.z < zmin + 0.12]
cx = (min(p.x for p in base_pts) + max(p.x for p in base_pts)) / 2 + cfg.get('centre_shift', [0, 0])[0]
cy = (min(p.y for p in base_pts) + max(p.y for p in base_pts)) / 2 + cfg.get('centre_shift', [0, 0])[1]
plinth_h = cfg.get('plinth', {}).get('height', 0.0)
scale = cfg['figure_top'] / (zmax - zmin)
M = Matrix.Translation((0, 0, plinth_h - cfg.get('sink', 0.02))) @ Matrix.Scale(scale, 4) @ \
    Matrix.Diagonal((bulk[0], bulk[1], 1.0, 1.0)) @ Matrix.Translation((-cx, -cy, -zmin))
for o in objs:
    o.data.transform(M)
    o.matrix_world = Matrix.Identity(4)
if JAR:
    JAR = (M @ JAR[0], (M.to_3x3() @ JAR[1]).normalized())
print('FIGURE scale %.3f height %.3f centre (%.3f, %.3f)' % (scale, zmax - zmin, cx, cy))

# ------------------------------------------------------------------------------------------ model-space parts
if sid == 'water':
    sc = cfg['stream']
    m0, a = JAR
    m0 = m0 + a * 0.02
    ah = Vector((a.x, a.y, 0))
    dirh = ah.normalized()
    start_d = Vector((m0.x, m0.y, 0)).dot(dirh)
    h = max(sc['land_r'] - start_d, sc.get('min_reach', 0.45))
    g = 9.8
    slope = a.z / ah.length
    denom = 2 * ah.length ** 2 * (m0.z + slope * h - sc['end_z'])
    v = math.sqrt(g * h * h / denom)
    T = h / (ah.length * v)
    pts = []
    for i in range(25):
        t = T * i / 24
        pts.append(m0 + Vector((a.x * v * t, a.y * v * t, a.z * v * t - 0.5 * g * t * t)))
    pts.append(pts[-1] + Vector((0, 0, -0.12)))
    n = len(pts)
    radii = [sc['r0'] * (0.75 + 0.6 * min(1.0, i / (n - 2))) for i in range(n)]
    lateral = Vector((-dirh.y, dirh.x, 0.0))
    stb = bmesh.new()
    shapes.tube(stb, pts, radii, sides=14, flat=sc.get('flat', 0.5), cap_start=True, cap_end=True, up=lateral)
    # the splash: a low ring and a crown of droplets where the stream meets the basin
    land = pts[-2]
    ring = [Vector((land.x + math.cos(2 * math.pi * k / 24) * 0.16, land.y + math.sin(2 * math.pi * k / 24) * 0.16,
                    sc['end_z'] + 0.02)) for k in range(25)]
    for k in range(7):
        aa = 2 * math.pi * k / 7 + 0.3
        root = Vector((land.x + math.cos(aa) * 0.1, land.y + math.sin(aa) * 0.1, sc['end_z'] - 0.05))
        tongue(stb, root, (math.cos(aa) * 0.8, math.sin(aa) * 0.8, 1), R.uniform(0.16, 0.24), 0.035, wiggle=0.05,
               sides=7, flat=0.8)
    shapes.tube(stb, ring, [0.045] * len(ring), sides=8, cap_start=False, cap_end=False)
    add_built(stb, 'HighStream', cfg['lod0_stream_tris'])
    print('STREAM start (%.2f, %.2f, %.2f) land (%.2f, %.2f) r %.2f' % (m0.x, m0.y, m0.z, land.x, land.y,
                                                                        Vector((land.x, land.y)).length))

if cfg.get('plinth'):
    pc = cfg['plinth']
    w, hgt = pc['width'], pc['height']
    hw = w / 2
    f = hgt / 0.96
    rings_ = [(hw, 0.0), (hw, 0.17 * f), (hw - 0.07, 0.24 * f), (hw - 0.12, 0.25 * f), (hw - 0.12, 0.74 * f),
              (hw - 0.05, 0.80 * f), (hw - 0.03, 0.88 * f), (hw - 0.09, hgt)]

    def square(r):
        cs = [(-r, -r), (r, -r), (r, r), (-r, r)]
        out = []
        for k in range(4):
            p, q = cs[k], cs[(k + 1) % 4]
            for s in range(3):
                out.append((p[0] + (q[0] - p[0]) * s / 3, p[1] + (q[1] - p[1]) * s / 3))
        return out

    pb_ = bmesh.new()
    loops = [[pb_.verts.new((x, y, z)) for x, y in square(r)] for r, z in rings_]
    for la, lb in zip(loops, loops[1:]):
        for i in range(12):
            j = (i + 1) % 12
            pb_.faces.new((la[i], la[j], lb[j], lb[i]))
    topl, r_ = loops[-1], rings_[-1][0]
    inner = [pb_.verts.new((x, y, hgt)) for x, y in square(r_ / 3)[::3]]
    gg = [[topl[0], topl[1], topl[2], topl[3]], [topl[11], inner[0], inner[1], topl[4]],
          [topl[10], inner[3], inner[2], topl[5]], [topl[9], topl[8], topl[7], topl[6]]]
    for j in range(3):
        for i in range(3):
            pb_.faces.new((gg[j][i], gg[j][i + 1], gg[j + 1][i + 1], gg[j + 1][i]))
    # the plaque: a raised panel on the front (-Y) face of the die
    pw, pz0, pz1, proud = pc['plaque']
    face_y = -(hw - 0.12)
    geom = bmesh.ops.create_cube(pb_, size=1.0)
    bmesh.ops.transform(pb_, matrix=Matrix.Translation((0, face_y - proud / 2 + 0.01, (pz0 + pz1) / 2 * f))
                        @ Matrix.Diagonal((pw, proud + 0.02, (pz1 - pz0) * f, 1.0)), verts=geom['verts'])
    bmesh.ops.recalc_face_normals(pb_, faces=pb_.faces)
    plo = shapes.to_object(pb_, 'HighPlinth', plain, high_col)
    if max(plo.data.polygons, key=lambda p: p.center.z).normal.z < 0:
        plo.data.flip_normals()
    built.append((plo, None, 1))

# ------------------------------------------------------------------------------------------ LOD0 pieces
def tris(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def low_copy(ob, target, name, part):
    tmp = bpy.data.objects.new('tmp', ob.data.copy())
    scene.collection.objects.link(tmp)
    if target and tris(tmp.data) > target:
        mod = tmp.modifiers.new('dec', 'DECIMATE')
        mod.decimate_type = 'COLLAPSE'
        mod.ratio = target / tris(tmp.data)
        mod.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp, do_unlink=True)
    lo = bpy.data.objects.new(name, me)
    low_col.objects.link(lo)
    lo['part'] = part
    print('LOW', name, 'tris', tris(me))
    return lo


low_copy(fig, cfg['lod0_figure_tris'], 'LowFigure', 0)
for ob, target, part in built:
    low_copy(ob, target, 'Low' + ob.name[4:], part)
allv = [v.co for o in low_col.objects for v in o.data.vertices]
lo = Vector([min(p[i] for p in allv) for i in range(3)])
hi = Vector([max(p[i] for p in allv) for i in range(3)])
print('BOUNDS', tuple(round(x, 3) for x in lo), tuple(round(x, 3) for x in hi))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'high.blend'))

# previews (workbench) of the LOD0 pieces
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (0.55, 0.55, 0.57)
scene.display.shading.show_cavity = True
scene.render.resolution_x, scene.render.resolution_y = 480, 640
high_col.hide_render = True
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
scene.camera = cam
cam.data.lens = 50
centre = Vector((0, 0, (lo.z + hi.z) / 2))
dist = (hi.z - lo.z) * 2.3
for view, az in (('front', 0), ('q', 35), ('side', 90), ('back', 160)):
    a = math.radians(az)
    eye = Vector((math.sin(a) * dist, -math.cos(a) * dist, 1.7))
    cam.location = eye
    cam.rotation_euler = (centre - eye).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(work, f'high_{view}.png')
    bpy.ops.render.render(write_still=True)
print('HIGH_DONE')
