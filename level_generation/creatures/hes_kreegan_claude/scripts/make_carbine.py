"""The Kreegan pulse carbine, v2 (armour pass 2026-10-22: the concept fam_troopers.png gun is a large bone-and-resin
weapon about forearm-to-shoulder long; v1 was a slim 0.79 m rod that read small). Built locally as a hard-surface
prop. Prop space = the rifle frame of rifle_fit.py: origin at the right fist's grip-tunnel centre, +Z up the grip,
+Y along the barrel, +X = Y x Z.
Parts:
- the main loft (SEG superellipse sides per station): a tall bone stock with a shoulder pad, a big receiver (amber
  resin between ivory side plates), the barrel housing at the receiver's height with raised gold rib rings, a flared
  bone emitter at the muzzle; its bottom clears the right fist (z >= 0.07 over the grip) and the left fist under it;
- the fore-grip: a slim wrapped bar under the barrel where the left fist holds (support_hand.py: tunnel centre at
  y in [Y_LO, Y_HI], z = HG_Z), joined to the barrel by a front and a rear strut;
- the pistol grip (8 sides, raked toward the stock, inside the right fist's tunnel) and a trigger guard;
- a bone spine fin along the top of the receiver;
- glow (material Rifle_Glow, emissive): the core channel on both receiver sides, the round lens on top, glow bands
  between the barrel ribs on both sides, the muzzle bore.
UVs: the main loft u = around (0..0.75 of the atlas), v = along (Y0 -> Y1); the grip, the fore-grip bar, the struts,
the fin and the caps their own strips (carbine_texture.py paints them from work/carbine_layout.json).
Writes work/rifle.blend (object 'Rifle', custom props muzzle, butt) and work/carbine_layout.json. Args: none"""
import bpy, bmesh, os, json, math
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FR = json.load(open(os.path.join(HERE, 'work', 'rifle_frame.json')))
HG_Y, HG_Z = FR['left_centre_rifle'][1], FR['left_centre_rifle'][2]
HG_R = float(os.environ.get('HG_R', '0.020'))
GRIP_R = float(os.environ.get('GRIP_R', '0.019'))
Y_LO, Y_HI = float(os.environ.get('Y_LO', '0.20')), float(os.environ.get('Y_HI', '0.34'))
BZ = float(os.environ.get('BARREL_Z', '0.165'))          # barrel axis height: its bottom clears the left fist
# main loft stations: y, half width (x), half height (z), centre z
ST = [(-0.265, 0.030, 0.060, 0.115), (-0.255, 0.040, 0.075, 0.115), (-0.215, 0.042, 0.074, 0.118),
      (-0.160, 0.034, 0.056, 0.128), (-0.100, 0.040, 0.060, 0.138), (-0.050, 0.060, 0.082, 0.150),
      (0.010, 0.068, 0.090, 0.155), (0.080, 0.068, 0.088, 0.157), (0.130, 0.058, 0.070, 0.160),
      (0.165, 0.042, 0.042, BZ), (Y_HI + 0.06, 0.040, 0.038, BZ)]
RIBS = [Y_HI + 0.09 + 0.075 * k for k in range(4)]        # raised gold rings along the barrel housing (4: budget pass)
for y in RIBS:
    ST += [(y - 0.006, 0.040, 0.038, BZ), (y, 0.048, 0.046, BZ), (y + 0.012, 0.048, 0.046, BZ), (y + 0.018, 0.040, 0.038, BZ)]
YM = RIBS[-1] + 0.05
ST += [(YM, 0.042, 0.040, BZ), (YM + 0.03, 0.058, 0.056, BZ), (YM + 0.075, 0.066, 0.064, BZ), (YM + 0.09, 0.058, 0.056, BZ)]
SEG = 10                                      # budget pass: 12 -> 10 sides
EXP = 2.6                                     # superellipse exponent (rounded box)
bpy.ops.wm.read_factory_settings(use_empty=True)
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
mat_of = {}; uv_of = {}
Y0, Y1 = ST[0][0], ST[-1][0]
GLOWUV = (0.97, 0.97)


def sect(k):
    t = 2 * math.pi * k / SEG
    c, s = math.cos(t), math.sin(t)
    return math.copysign(abs(c) ** (2 / EXP), c), math.copysign(abs(s) ** (2 / EXP), s)


def loft(stations, u_range, v_of, seg=SEG, close0=True, cap_uv=(0.80, 0.02)):
    rings = []
    for y, hw, hh, cz in stations:
        rings.append([bm.verts.new((hw * sect(k)[0] if seg == SEG else hw * math.cos(2 * math.pi * k / seg), y,
                                    cz + (hh * sect(k)[1] if seg == SEG else hh * math.sin(2 * math.pi * k / seg)))) for k in range(seg)])
    for i in range(len(stations) - 1):
        for k in range(seg):
            a, b = k, (k + 1) % seg
            f = bm.faces.new((rings[i][a], rings[i + 1][a], rings[i + 1][b], rings[i][b])); mat_of[f] = 0
            v0, v1 = v_of(i), v_of(i + 1)
            u0 = u_range[0] + (u_range[1] - u_range[0]) * k / seg; u1 = u_range[0] + (u_range[1] - u_range[0]) * (k + 1) / seg
            uv_of[f] = [(u0, v0), (u0, v1), (u1, v1), (u1, v0)]
    if close0:
        f = bm.faces.new(list(reversed(rings[0]))); mat_of[f] = 0; uv_of[f] = [cap_uv] * seg
    return rings


rings = loft(ST, (0.0, 0.75), lambda i: (ST[i][0] - Y0) / (Y1 - Y0))
# the emitter: inset ring then the glowing bore disc
yb, _, _, czb = ST[-1]
inner = [bm.verts.new((0.62 * v.co.x, yb - 0.006, czb + 0.62 * (v.co.z - czb))) for v in rings[-1]]
for k in range(SEG):
    a, b = k, (k + 1) % SEG
    f = bm.faces.new((rings[-1][a], inner[a], inner[b], rings[-1][b])); mat_of[f] = 0; uv_of[f] = [(0.80, 0.98)] * 4
fb = bm.faces.new(inner); mat_of[fb] = 1; uv_of[fb] = [GLOWUV] * SEG
# the fore-grip bar (left fist) under the barrel, 8 sides, from just behind Y_LO to just past Y_HI
FG0, FG1 = Y_LO - 0.065, Y_HI + 0.065
fg = loft([(FG0, HG_R, HG_R, HG_Z), (FG1, HG_R, HG_R, HG_Z)], (0.88, 0.96), lambda i: 0.05 + 0.20 * i, seg=8,
          close0=True, cap_uv=(0.92, 0.04))
f = bm.faces.new(fg[1]); mat_of[f] = 0; uv_of[f] = [(0.92, 0.26)] * 8
# struts: the bar's ends up into the barrel housing (6 sides, 1.2 cm)
for ys in (FG0 + 0.012, FG1 - 0.012):
    lo = [bm.verts.new((0.012 * math.cos(2 * math.pi * k / 6), ys + 0.012 * math.sin(2 * math.pi * k / 6), HG_Z)) for k in range(6)]
    hi = [bm.verts.new((0.012 * math.cos(2 * math.pi * k / 6), ys + 0.012 * math.sin(2 * math.pi * k / 6), BZ - 0.02)) for k in range(6)]
    for k in range(6):
        a, b = k, (k + 1) % 6
        f = bm.faces.new((lo[a], lo[b], hi[b], hi[a])); mat_of[f] = 0; uv_of[f] = [(0.92, 0.32)] * 4
# grip: 8 sides, raked toward the stock (the butt end of the grip leans back)
RAKE = math.radians(float(os.environ.get('GRIP_RAKE', '20')))
gr = []
for z in (-0.075, 0.085):
    yo = z * math.tan(RAKE)                      # along the fist's tunnel axis (rifle_fit.py RIFLE_TILT = GRIP_RAKE)
    gr.append([bm.verts.new((GRIP_R * math.cos(2 * math.pi * (k + 0.5) / 8), yo + GRIP_R * 1.15 * math.sin(2 * math.pi * (k + 0.5) / 8), z)) for k in range(8)])
for k in range(8):
    a, b = k, (k + 1) % 8
    f = bm.faces.new((gr[0][a], gr[0][b], gr[1][b], gr[1][a])); mat_of[f] = 0
    uv_of[f] = [(0.78 + 0.08 * k / 8, 0.30), (0.78 + 0.08 * (k + 1) / 8, 0.30), (0.78 + 0.08 * (k + 1) / 8, 0.55), (0.78 + 0.08 * k / 8, 0.55)]
f = bm.faces.new(list(reversed(gr[0]))); mat_of[f] = 0; uv_of[f] = [(0.82, 0.28)] * 8
# trigger guard: a bar polyline in the y-z plane (from the grip's front to the receiver's belly)
pts = [(0.022, 0.045), (0.075, -0.005), (0.105, 0.030), (0.115, 0.080)]
prev = None
for k, (y, z) in enumerate(pts):
    a_, b_ = pts[max(k - 1, 0)], pts[min(k + 1, len(pts) - 1)]
    ty, tz = b_[0] - a_[0], b_[1] - a_[1]; L_ = math.hypot(ty, tz); ny, nz = -tz / L_, ty / L_
    cur = [bm.verts.new((x, y + ny * o, z + nz * o)) for (x, o) in ((-0.006, 0.0), (0.006, 0.0), (0.006, 0.007), (-0.006, 0.007))]
    if prev:
        for i in range(4):
            f = bm.faces.new((prev[i], prev[(i + 1) % 4], cur[(i + 1) % 4], cur[i])); mat_of[f] = 0; uv_of[f] = [(0.90, 0.40)] * 4
    prev = cur
# the spine fin along the receiver's top: a thin blade (two sides + top) rising 3.5 cm, swept back
fin = [(-0.090, 0.0), (-0.040, 0.030), (0.040, 0.036), (0.110, 0.022), (0.150, 0.0)]
top_of = lambda y: max(c + h for (yy, w, h, c) in ST if abs(yy - y) < 0.07)
FL, FR_ = [], []
for y, hgt in fin:
    zb = top_of(y) - 0.006
    FL.append((bm.verts.new((-0.006, y, zb)), bm.verts.new((-0.003, y, zb + hgt + 0.004))))
    FR_.append((bm.verts.new((0.006, y, zb)), bm.verts.new((0.003, y, zb + hgt + 0.004))))
for i in range(len(fin) - 1):
    for side, sgn in ((FL, -1), (FR_, 1)):
        q = (side[i][0], side[i + 1][0], side[i + 1][1], side[i][1])
        f = bm.faces.new(q if sgn > 0 else tuple(reversed(q))); mat_of[f] = 0; uv_of[f] = [(0.84, 0.70)] * 4
    f = bm.faces.new((FL[i][1], FL[i + 1][1], FR_[i + 1][1], FR_[i][1])); mat_of[f] = 0; uv_of[f] = [(0.84, 0.72)] * 4
# glow: core channels on both receiver sides (1 mm proud), the lens on top, bands between the barrel ribs
GLOW = []
for sx in (-1, 1):
    x = sx * (0.068 * 0.985 + 0.001)
    q = [bm.verts.new((x, y, z)) for y, z in ((-0.040, 0.140), (0.105, 0.142), (0.105, 0.166), (-0.040, 0.164))]
    f = bm.faces.new(q if sx > 0 else list(reversed(q))); mat_of[f] = 1; uv_of[f] = [GLOWUV] * 4; GLOW.append(f)
    for y in RIBS[:-1]:
        y0, y1 = y + 0.020, y + 0.039
        xb = sx * (0.040 * 0.985 + 0.0012)
        q = [bm.verts.new((xb, yy, BZ + dz)) for yy, dz in ((y0, -0.010), (y1, -0.010), (y1, 0.010), (y0, 0.010))]
        f = bm.faces.new(q if sx > 0 else list(reversed(q))); mat_of[f] = 1; uv_of[f] = [GLOWUV] * 4; GLOW.append(f)
lz = top_of(-0.06) + 0.001
lens = [bm.verts.new((0.022 * math.cos(2 * math.pi * k / 8), -0.065 + 0.022 * math.sin(2 * math.pi * k / 8), lz)) for k in range(8)]
f = bm.faces.new(lens); mat_of[f] = 1; uv_of[f] = [GLOWUV] * 8; GLOW.append(f)
bm.normal_update()
bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f not in GLOW])
for f in GLOW:
    c = f.calc_center_median()
    out = Vector((c.x, 0, 0)) if abs(c.x) > 0.02 else Vector((0, 0, 1))
    if f.normal.dot(out) < 0:
        f.normal_flip()
for f in bm.faces:
    uvs = uv_of[f]
    for l, uv in zip(f.loops, uvs if len(uvs) == len(f.loops) else [uvs[0]] * len(f.loops)):
        l[uvl].uv = uv
bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='SHORT_EDGE')
me = bpy.data.meshes.new('Rifle'); bm.to_mesh(me)
bm.free()
ob = bpy.data.objects.new('Rifle', me); bpy.context.scene.collection.objects.link(ob)
tex = os.path.join(HERE, 'textures', 'props', 'carbine.png')
for name, emit in (('Rifle_A', None), ('Rifle_Glow', (1.0, 0.45, 0.08))):
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    bsdf = next(x for x in mat.node_tree.nodes if x.type == 'BSDF_PRINCIPLED')
    if os.path.exists(tex) and not emit:
        n = mat.node_tree.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(tex)
        mat.node_tree.links.new(n.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.5; bsdf.inputs['Metallic'].default_value = 0.0
    if emit:
        bsdf.inputs['Base Color'].default_value = (*emit, 1.0)
        bsdf.inputs['Emission Color'].default_value = (*emit, 1.0); bsdf.inputs['Emission Strength'].default_value = 1.0
    me.materials.append(mat)
uvd = me.uv_layers[0].data
for p in me.polygons:
    u = sum(uvd[li].uv[0] for li in p.loop_indices) / len(p.loop_indices)
    v = sum(uvd[li].uv[1] for li in p.loop_indices) / len(p.loop_indices)
    p.material_index = 1 if (u > 0.95 and v > 0.95) else 0
    p.use_smooth = p.material_index == 0
ob['muzzle'] = [0.0, ST[-1][0] + 0.01, czb]
ob['butt'] = [0.0, ST[0][0], ST[0][3]]
json.dump({'Y0': Y0, 'Y1': Y1, 'stock_end': -0.07, 'receiver_end': 0.15, 'ribs': RIBS, 'muzzle_start': YM,
           'fore_grip': [FG0, FG1], 'barrel_z': BZ}, open(os.path.join(HERE, 'work', 'carbine_layout.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rifle.blend'))
print('CARBINE tris', len(me.polygons), 'glow tris', sum(1 for p in me.polygons if p.material_index == 1), 'length m',
      round(Y1 - Y0, 3), 'fore-grip y', round(FG0, 3), round(FG1, 3), 'z', round(HG_Z, 3), 'barrel z', BZ,
      'muzzle', [round(x, 3) for x in ob['muzzle']])
