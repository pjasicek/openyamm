"""The guard's blaster rifle (HD prop reference references_hd/rifle.png, side view), built locally as a hard-surface
prop (modelling guidelines: a few hundred triangles, hard edges between parts). Prop space = the rifle frame of
rifle_fit.py: origin at the right fist's grip-tunnel centre, +Z up the pistol grip (thumb side), +Y along the barrel,
+X = Y x Z; reference pixels map as y = (col - X0) S, z = (Y0 - row) S (1455 px = 1.0 m; the handguard centre at the
left fist's tunnel, 0.064 m above the grip, 0.35 m ahead). Parts: stock + receiver as the extruded alpha profile, a
12-sided handguard for the left fist (the reference's vertical fore-grip and lower rail sit where that hand closes, so
they are left out), front body, gold gas tube, barrel, three cooling rings and a collar, the emitter tip and the two
power-cell windows (material Rifle_Glow, emissive), a non-raked pistol grip (the tunnel is perpendicular to the barrel;
its UVs are sheared onto the reference's raked grip), trigger guard, scope. UVs: planar side projection onto
textures/props/rifle.png (the reference's alpha box). Writes work/rifle.blend (object 'Rifle'; custom prop muzzle).
Args: none"""
import bpy, bmesh, os, json, math
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PR = json.load(open(os.path.join(HERE, 'work', 'rifle_profile.json'))); BOX = PR['box']; COLS = {int(k): v for k, v in PR['cols'].items()}
FR = json.load(open(os.path.join(HERE, 'work', 'rifle_frame.json')))
S = 1.0 / (BOX[1] - BOX[0]); X0 = 380.0
HG_Z = FR['left_centre_rifle'][2]; HG_Y = FR['left_centre_rifle'][1]
Y0 = 430.0 + HG_Z / S                     # the white handguard's centre row (430) at the left tunnel's height
RAKE = -0.47                              # reference grip: columns per row (bottom toward the stock)
bpy.ops.wm.read_factory_settings(use_empty=True)
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); GRIPV = set()
mat_of = {}
py = lambda col: (col - X0) * S
pz = lambda row: (Y0 - row) * S


def face(vs, glow=False):
    f = bm.faces.new(vs); mat_of[f] = 1 if glow else 0; return f


def ribbon(colrows, hw):
    """Extruded side profile: colrows = [(col, top row, bottom row)], half width hw (x)."""
    L, R = [], []
    for c, t, b in colrows:
        L.append((bm.verts.new((-hw, py(c), pz(t))), bm.verts.new((-hw, py(c), pz(b)))))
        R.append((bm.verts.new((hw, py(c), pz(t))), bm.verts.new((hw, py(c), pz(b)))))
    for i in range(len(colrows) - 1):
        face((L[i][0], L[i][1], L[i + 1][1], L[i + 1][0]))      # -x side
        face((R[i][0], R[i + 1][0], R[i + 1][1], R[i][1]))      # +x side
        face((L[i][0], L[i + 1][0], R[i + 1][0], R[i][0]))      # top
        face((L[i][1], R[i][1], R[i + 1][1], L[i + 1][1]))      # bottom
    face((L[0][0], R[0][0], R[0][1], L[0][1])); face((L[-1][0], L[-1][1], R[-1][1], R[-1][0]))


def tube(y0, y1, r0, r1, zc, seg=12, caps=(True, True), glow=False, xc=0.0):
    rings = [[bm.verts.new((xc + r * math.cos(2 * math.pi * k / seg), y, zc + r * math.sin(2 * math.pi * k / seg)))
              for k in range(seg)] for y, r in ((y0, r0), (y1, r1))]
    for k in range(seg):
        a, b = k, (k + 1) % seg
        face((rings[0][a], rings[1][a], rings[1][b], rings[0][b]), glow)
    if caps[0]:
        face(rings[0], glow)
    if caps[1]:
        face(list(reversed(rings[1])), glow)


def col_range(c0, c1, step, top_fn, bot_fn):
    return [(c, top_fn(c), bot_fn(c)) for c in list(range(c0, c1, step)) + [c1]]


T = lambda c: COLS.get(c, COLS[min(COLS, key=lambda k: abs(k - c))])
# stock + receiver (the scope above and the grip/trigger guard below are their own parts)
stock = col_range(BOX[0] + 2, 290, 25, lambda c: T(c)[0], lambda c: min(T(c)[1], 500) if c >= 250 else T(c)[1])
recv = col_range(290, 780, 25, lambda c: max(T(c)[0], 388) if 470 <= c <= 760 else T(c)[0],
                 lambda c: min(T(c)[1], 500 if c < 440 else 505))
ribbon(stock, 0.017); ribbon(recv, 0.021)
HG0, HG1 = py(780), py(985)
tube(HG0, HG1, 0.022, 0.022, HG_Z)                                          # handguard (left fist)
ribbon(col_range(985, 1195, 30, lambda c: 395, lambda c: 465), 0.020)     # front body
tube(py(1040), py(1180), 0.012, 0.012, pz(487), seg=8)                     # gold gas tube
BZ = pz(451)
tube(py(1195), py(1420), 0.025, 0.025, BZ)                                 # barrel
for c0, c1 in ((1215, 1262), (1272, 1310), (1320, 1368)):
    tube(py(c0), py(c1), 0.050, 0.050, BZ, seg=16)                         # cooling rings
tube(py(1380), py(1420), 0.034, 0.034, BZ)                                 # collar
tube(py(1420), py(1496), 0.025, 0.012, BZ, glow=True)                      # emitter tip
tube(py(480), py(620), 0.013, 0.013, pz(366), seg=10)                      # scope
tube(py(620), py(750), 0.005, 0.005, pz(362), seg=6)                       # scope rod
# pistol grip: an octagon (radius 0.019, inside the fist's 21 mm tunnel) straight along Z
n0 = len(bm.verts)
rings = [[bm.verts.new((0.019 * math.cos(2 * math.pi * (k + 0.5) / 8), 0.019 * math.sin(2 * math.pi * (k + 0.5) / 8), z))
          for k in range(8)] for z in (-0.088, 0.035)]
for k in range(8):
    a, b = k, (k + 1) % 8; face((rings[0][a], rings[0][b], rings[1][b], rings[1][a]))
face(list(reversed(rings[0])))
bm.verts.ensure_lookup_table(); GRIPV = {v.index for v in bm.verts[n0:]}
# trigger guard: a bar along a polyline (image points)
pts = [(py(c), pz(r)) for c, r in ((432, 482), (440, 540), (470, 560), (520, 560), (560, 505))]
prev = None
for k, (y, z) in enumerate(pts):
    a_, b_ = pts[max(k - 1, 0)], pts[min(k + 1, len(pts) - 1)]
    ty, tz = b_[0] - a_[0], b_[1] - a_[1]; L_ = math.hypot(ty, tz); ny, nz = -tz / L_, ty / L_
    cur = [bm.verts.new((x, y + ny * o, z + nz * o)) for (x, o) in ((-0.004, 0.0), (0.004, 0.0), (0.004, 0.004), (-0.004, 0.004))]
    if prev:
        for i in range(4):
            face((prev[i], prev[(i + 1) % 4], cur[(i + 1) % 4], cur[i]))
    prev = cur
# power-cell windows on both receiver sides (glow), 0.8 mm proud of the receiver
WINDOWS = []
for sx in (-1, 1):
    x = sx * (0.021 + 0.0008)
    q = [bm.verts.new((x, py(c), pz(r))) for c, r in ((490, 400), (640, 400), (640, 445), (490, 445))]
    WINDOWS.append(face(q if sx > 0 else list(reversed(q)), glow=True))
bm.normal_update()
bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f not in WINDOWS])   # closed parts outward
for f in WINDOWS:                                                                     # windows face away from the gun
    if f.normal.x * f.verts[0].co.x < 0:
        f.normal_flip()
bm.verts.ensure_lookup_table()
for f in bm.faces:
    for l in f.loops:
        v = l.vert; c = v.co
        col, row = c.y / S + X0, Y0 - c.z / S
        if v.index in GRIPV:
            col += (row - 523.0) * RAKE + (380.0 - X0)
        l[uvl].uv = ((col - BOX[0]) / (BOX[1] - BOX[0]), 1.0 - (row - BOX[2]) / (BOX[3] - BOX[2]))
me = bpy.data.meshes.new('Rifle'); bm.to_mesh(me)
glow_idx = [mat_of[f] for f in bm.faces]
bm.free()
ob = bpy.data.objects.new('Rifle', me); bpy.context.scene.collection.objects.link(ob)
tex = os.path.join(HERE, 'textures', 'props', 'rifle.png')
for name, emit in (('Rifle_A', None), ('Rifle_Glow', (0.55, 0.8, 1.0))):
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    n = mat.node_tree.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(tex)
    bsdf = next(x for x in mat.node_tree.nodes if x.type == 'BSDF_PRINCIPLED')
    mat.node_tree.links.new(n.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.45; bsdf.inputs['Metallic'].default_value = 0.0
    if emit:
        bsdf.inputs['Emission Color'].default_value = (*emit, 1.0); bsdf.inputs['Emission Strength'].default_value = 1.0
    me.materials.append(mat)
for p, gi in zip(me.polygons, glow_idx):
    p.material_index = gi; p.use_smooth = False
ob['muzzle'] = [0.0, py(1496), BZ]
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rifle.blend'))
print('RIFLE tris', sum(len(p.vertices) - 2 for p in me.polygons), 'length m', round(py(BOX[1]) - py(BOX[0]), 3),
      'handguard y', round(HG0, 3), round(HG1, 3), 'z', round(HG_Z, 3), 'muzzle', [round(x, 3) for x in ob['muzzle']])
