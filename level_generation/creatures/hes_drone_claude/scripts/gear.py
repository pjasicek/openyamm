"""Tier gear and the thrust glow on the rigged master: work/rig_v1.blend -> work/gear_v1.blend.

Parts (face attribute 'part', all in mesh HDR, UVs in the reserved strip v < 0.125, painted by compose_hdr.py):
  5 twin emitter barrel (tier B): a 16-sided ceramic barrel with gold collars (smooth, hard only at the front bevel) on the drone's left flank (+X) beside
    the lens, its front end STICK cm ahead of the casing; 6 its glowing lens disc (glow material)
  7 shield emitter ring (tier C): a belt round the middle at lens height, fitted per angle to the casing (+GAP);
    8 its glowing cells (glow material)
  Bound 100 % to GearEmitter (5) / GearEmitterGlow (6) / GearRing (7) / GearRingGlow (8); split into attachment GLBs at export (tools/split_attachment.py).
Thrust glow: separate mesh HDR_Thrust (alpha-blended, unlit), an open 12-sided cone under the vent ring on bone
Thrust; its texture textures/hdr_thrust.png is a vertical gradient (compose_hdr.py).
Socket_Muzzle2: the twin emitter's muzzle (non-deforming child of GearEmitter)."""
import bpy, bmesh, os, json, math
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
mesh = bpy.data.objects['HDR']; rig = bpy.data.objects['HDR_Rig']
R = json.load(open(os.path.join(HERE, 'work', 'rig_info.json')))
STRIP = 0.125
co = np.array([tuple(v.co) for v in mesh.data.vertices])
part_f = np.zeros(len(mesh.data.polygons), int); mesh.data.attributes['part'].data.foreach_get('value', part_f)
pv = np.zeros(len(co), int)
for p in mesh.data.polygons:
    for v in p.vertices:
        pv[v] = part_f[p.index]
body = co[pv == 0]
lens_z = R['lens_base'][2]


def px(u, v):                       # strip pixel (2048 x 2048 atlas) -> Blender UV
    return (u / 2048.0, v / 2048.0)


new_faces = []                      # (verts, uvs, part)


def quad_strip(rings, u0, u1, v0, v1, part, closed=True):
    """rings: list of vertex lists (same count); UV u along the ring, v across the rings."""
    n = len(rings[0]); m = len(rings)
    for i in range(m - 1):
        for j in range(n if closed else n - 1):
            a, b = rings[i][j], rings[i][(j + 1) % n]
            c, d = rings[i + 1][(j + 1) % n], rings[i + 1][j]
            ua, ub = u0 + (u1 - u0) * j / n, u0 + (u1 - u0) * (j + 1) / n
            va, vb = v0 + (v1 - v0) * i / (m - 1), v0 + (v1 - v0) * (i + 1) / (m - 1)
            new_faces.append(((a, b, c), (px(ua, va), px(ub, va), px(ub, vb)), part))
            new_faces.append(((a, c, d), (px(ua, va), px(ub, vb), px(ua, vb)), part))


# ---------------------------------------------------------------- twin emitter (tier B), +X flank beside the lens
RAD, SIDES = 0.038, 16
band = body[(np.abs(body[:, 2] - (lens_z - 0.01)) < 0.03) & (body[:, 1] < -0.18) & (body[:, 0] > 0)]
ex = float(np.percentile(band[:, 0], 90)) + 0.2 * RAD
ez = lens_z - 0.015
near = body[(np.abs(body[:, 0] - ex) < RAD) & (np.abs(body[:, 2] - ez) < RAD)]
y_front = min(float(near[:, 1].min()) - 0.04, R['apex'][1] + 0.01)
LEN = 0.15
emit_rings = []
# profile along +Y from the front: (y offset, radius scale)
PROFILE = [(0.0, 0.80), (0.004, 1.0), (0.025, 1.0), (0.03, 1.12), (0.05, 1.12), (0.055, 1.0), (0.11, 1.0),
           (0.115, 1.12), (0.135, 1.12), (0.14, 0.95), (LEN, 0.9)]
for dy, s in PROFILE:
    emit_rings.append([Vector((ex + RAD * s * math.cos(2 * math.pi * j / SIDES), y_front + dy,
                               ez + RAD * s * math.sin(2 * math.pi * j / SIDES))) for j in range(SIDES)])
EMIT = {'u': (260, 900), 'v': (8, 120), 'disc': (260, 130, 380, 250)}
# smooth round the barrel and over its rounded collars; a profile corner sharper than 50 degrees (the front bevel)
# starts a new strip on its own copy of the ring, so the edge is hard
v_of = lambda i: EMIT['v'][0] + (EMIT['v'][1] - EMIT['v'][0]) * i / (len(PROFILE) - 1)
cuts = [0]
for i in range(1, len(PROFILE) - 1):
    d0 = np.subtract(PROFILE[i], PROFILE[i - 1]) * (1, RAD); d1 = np.subtract(PROFILE[i + 1], PROFILE[i]) * (1, RAD)
    if math.degrees(math.acos(np.clip(np.dot(d0, d1) / np.linalg.norm(d0) / np.linalg.norm(d1), -1, 1))) > 50:
        cuts.append(i)
cuts.append(len(PROFILE) - 1)
for i0, i1 in zip(cuts[:-1], cuts[1:]):
    run = [[v.copy() for v in emit_rings[i0]] if i0 else emit_rings[i0]] + emit_rings[i0 + 1:i1 + 1]
    quad_strip(run, EMIT['u'][0], EMIT['u'][1], v_of(i0), v_of(i1), 5)
# front lens disc (glow): an inner ring at 0.45 and a centre, recessed 6 mm
c0 = Vector((ex, y_front + 0.006, ez))
inner = [Vector((ex + RAD * 0.45 * math.cos(2 * math.pi * j / SIDES), y_front + 0.003,
                 ez + RAD * 0.45 * math.sin(2 * math.pi * j / SIDES))) for j in range(SIDES)]
du0, dv0, du1, dv1 = EMIT['disc']; cu, cv, hr = (du0 + du1) / 2, (dv0 + dv1) / 2, (du1 - du0) / 2
rim = emit_rings[0]
for j in range(SIDES):
    a0 = 2 * math.pi * j / SIDES; a1 = 2 * math.pi * (j + 1) / SIDES
    uo = lambda a, r: px(cu + hr * r * math.cos(a), cv + hr * r * math.sin(a))
    new_faces.append(((rim[(j + 1) % SIDES], rim[j], inner[j]), (uo(a1, 1), uo(a0, 1), uo(a0, 0.45)), 6))
    new_faces.append(((rim[(j + 1) % SIDES], inner[j], inner[(j + 1) % SIDES]), (uo(a1, 1), uo(a0, 0.45), uo(a1, 0.45)), 6))
    new_faces.append(((inner[(j + 1) % SIDES], inner[j], c0), (uo(a1, 0.45), uo(a0, 0.45), px(cu, cv)), 6))
# back cap (inside the flank)
back = [v.copy() for v in emit_rings[-1]]; bc = Vector((ex, y_front + LEN, ez))
for j in range(SIDES):
    new_faces.append(((back[j], back[(j + 1) % SIDES], bc), (px(300, 110), px(310, 110), px(305, 115)), 5))

# ---------------------------------------------------------------- shield ring (tier C): belt at lens height
N, GAP, H, T = 48, 0.012, 0.022, 0.012
zc = lens_z
slab = co[(pv == 0) & (np.abs(co[:, 2] - zc) < 0.03)]
ang = np.arctan2(slab[:, 1], slab[:, 0]); rad = np.hypot(slab[:, 0], slab[:, 1])
radii = []
for j in range(N):
    a = 2 * math.pi * j / N
    d = np.abs((ang - a + math.pi) % (2 * math.pi) - math.pi)
    sel = d < math.radians(7)
    radii.append(float(np.percentile(rad[sel], 92)) if sel.any() else 0.3)
radii = np.array(radii)
radii = np.max([np.roll(radii, k) for k in (-1, 0, 1)], axis=0)          # no dips between samples
for _ in range(4):                                                          # a smooth belt, no kinks
    radii = (np.roll(radii, -1) + 2 * radii + np.roll(radii, 1)) / 4
radii = np.maximum(radii, np.max([np.roll(radii, k) for k in (-1, 0, 1)], axis=0) * 0.0) + GAP
# at the front the belt runs into the lens collar, behind the dome (never across the lens)
front_lim = -R['lens_base'][1] + 0.004 - T
for j in range(N):
    a = 2 * math.pi * j / N
    if math.sin(a) < -0.3:
        radii[j] = min(radii[j], front_lim / max(-math.sin(a), 1e-3))


def ring(r_off, z):
    return [Vector(((radii[j] + r_off) * math.cos(2 * math.pi * j / N), (radii[j] + r_off) * math.sin(2 * math.pi * j / N), z))
            for j in range(N)]


# section: outer face (2 rings), top, inner, bottom: a closed rectangular tube
# each face of the section gets its own vertices: smooth round the ring, hard at the section's corners
RING = {'u': (920, 2040)}
quad_strip([ring(T, zc - H), ring(T, zc + H)], RING['u'][0], RING['u'][1], 8, 60, 7)   # outer band
quad_strip([ring(T, zc + H), ring(0, zc + H)], RING['u'][0], RING['u'][1], 64, 80, 7)  # top
quad_strip([ring(0, zc + H), ring(0, zc - H)], RING['u'][0], RING['u'][1], 84, 110, 7)  # inner
quad_strip([ring(0, zc - H), ring(T, zc - H)], RING['u'][0], RING['u'][1], 112, 126, 7)  # bottom
# glowing cells: 10 small quads 2 mm proud of the outer face
CELLS = 10
for c in range(CELLS):
    j0 = int(round((c + 0.2) * N / CELLS)); j1 = j0 + 2
    q = []
    for j, z in ((j0, zc - H * 0.45), (j1, zc - H * 0.45), (j1, zc + H * 0.45), (j0, zc + H * 0.45)):
        a = 2 * math.pi * (j % N) / N; r = radii[j % N] + T + 0.002
        q.append(Vector((r * math.cos(a), r * math.sin(a), z)))
    uvs = [px(930, 134), px(990, 134), px(990, 166), px(930, 166)]
    new_faces.append(((q[0], q[1], q[2]), (uvs[0], uvs[1], uvs[2]), 8))
    new_faces.append(((q[0], q[2], q[3]), (uvs[0], uvs[2], uvs[3]), 8))

# ---------------------------------------------------------------- append to HDR, bind rigidly
bm = bmesh.new(); bm.from_mesh(mesh.data)
uvl = bm.loops.layers.uv.active; partl = bm.faces.layers.int.get('part')
dl = bm.verts.layers.deform.verify()
gi = {g.name: g.index for g in mesh.vertex_groups}
for name in ('GearEmitter', 'GearRing', 'GearEmitterGlow', 'GearRingGlow'):
    if name not in gi:
        gi[name] = mesh.vertex_groups.new(name=name).index
cache = {}
added = []
for verts, uvs, part in new_faces:
    vs = []
    for v in verts:
        key = (id(v), part)
        if key not in cache:
            nv = bm.verts.new(v); cache[key] = nv
            nv[dl][gi[{5: 'GearEmitter', 6: 'GearEmitterGlow', 7: 'GearRing', 8: 'GearRingGlow'}[part]]] = 1.0
        vs.append(cache[key])
    try:
        f = bm.faces.new(vs)
    except ValueError:
        continue
    f[partl] = part; f.smooth = True
    for l, uv in zip(f.loops, uvs):
        l[uvl].uv = uv
    added.append(f)
bmesh.ops.recalc_face_normals(bm, faces=[f for f in added if f[partl] in (5, 6)])
bm.to_mesh(mesh.data); bm.free()
pa = np.zeros(len(mesh.data.polygons), int); mesh.data.attributes['part'].data.foreach_get('value', pa)
flips = []
# simpler: per face, outward = away from the tube's centreline (radius + T/2, zc)
for p in mesh.data.polygons:
    if pa[p.index] in (7, 8):
        c = p.center; a = math.atan2(c.y, c.x)
        j = (a % (2 * math.pi)) / (2 * math.pi) * N
        r_mid = np.interp(j, np.arange(N + 1), np.append(radii, radii[0])) + T / 2
        centre_line = Vector((r_mid * math.cos(a), r_mid * math.sin(a), zc))
        if p.normal.dot(c - centre_line) < 0:
            flips.append(p.index)
bm = bmesh.new(); bm.from_mesh(mesh.data); bm.faces.ensure_lookup_table()
for i in flips:
    bm.faces[i].normal_flip()
bm.to_mesh(mesh.data); bm.free()
print('GEAR emitter at', round(ex, 3), round(y_front, 3), round(ez, 3), 'ring radii', radii.min().round(3), radii.max().round(3),
      'flipped', len(flips))

# the second muzzle (tier B's twin emitter): non-deforming child of GearEmitter, 3 cm in front of its disc
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
if 'Socket_Muzzle2' in eb:
    eb.remove(eb['Socket_Muzzle2'])
sb = eb.new('Socket_Muzzle2'); sb.head = (ex, y_front - 0.03, ez); sb.tail = (ex, y_front - 0.08, ez)
sb.parent = eb['GearEmitter']; sb.use_deform = False; sb.align_roll(Vector((0, 0, 1)))
bpy.ops.object.mode_set(mode='OBJECT')

# ---------------------------------------------------------------- thrust glow (own mesh node, blended)
th = Vector(R['thrust'])
vent = body[(np.abs(body[:, 2] - th.z) < 0.04) & (np.hypot(body[:, 0] - th.x, body[:, 1] - th.y) < 0.2)]
TR0 = 0.6 * float(np.percentile(np.hypot(vent[:, 0] - th.x, vent[:, 1] - th.y), 60))
tb = bmesh.new(); tuv = tb.loops.layers.uv.new('UVMap')
S2 = 12
rings_t = []
for k, (dz, rr) in enumerate(((0.004, TR0), (-0.03, TR0 * 0.75), (-0.065, TR0 * 0.4))):
    rings_t.append([tb.verts.new((th.x + rr * math.cos(2 * math.pi * j / S2), th.y + rr * math.sin(2 * math.pi * j / S2), th.z + dz))
                    for j in range(S2)])
for i in range(2):
    for j in range(S2):
        a, b = rings_t[i][j], rings_t[i][(j + 1) % S2]; c, d = rings_t[i + 1][(j + 1) % S2], rings_t[i + 1][j]
        for tri, uvs in (((a, b, c), ((j / S2, 1 - i / 2), ((j + 1) / S2, 1 - i / 2), ((j + 1) / S2, 1 - (i + 1) / 2))),
                         ((a, c, d), ((j / S2, 1 - i / 2), ((j + 1) / S2, 1 - (i + 1) / 2), (j / S2, 1 - (i + 1) / 2)))):
            f = tb.faces.new(tri)
            for l, uv in zip(f.loops, uvs):
                l[tuv].uv = uv
tme = bpy.data.meshes.new('HDR_Thrust'); tb.to_mesh(tme); tb.free()
thr = bpy.data.objects.new('HDR_Thrust', tme); bpy.context.scene.collection.objects.link(thr)
thr.parent = rig; g = thr.vertex_groups.new(name='Thrust'); g.add(list(range(len(tme.vertices))), 1.0, 'REPLACE')
m = thr.modifiers.new('Armature', 'ARMATURE'); m.object = rig
print('THRUST radius', round(TR0, 3), 'at', tuple(round(c, 3) for c in th))
print('TRIS HDR', sum(len(p.vertices) - 2 for p in mesh.data.polygons), 'thrust', len(tme.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'gear_v1.blend'))
print('SAVED gear_v1.blend')
