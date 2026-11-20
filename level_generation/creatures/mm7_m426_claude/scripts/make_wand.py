"""The Warlock's wand, modelled from the native sprite (m426sa1, aligned_2x: a ~0.45 m bronze-gold rod with a wrapped
ornament, a gold knob at the butt, a crown of curling gold prongs at the top holding a pale turquoise crystal), not
by Meshy. Same object/bone contract as the Mage's staff (object 'Staff', +Z from the butt, custom props length,
grip_z, head_z; seat_staff.py seats it; the attachment is still split on bone 'Staff'). UVs on the 3-swatch atlas of
staff_texture.py (swatch 'wood' = the bronze rod, 'gold', 'gem'). Settings: creature.json "staff". Args: none"""
import bpy, bmesh, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg, common
S = cfg.C['staff']
L = S['length']; RS = S['shaft_r']; RG = S['gem_r']
bpy.ops.wm.read_factory_settings(use_empty=True)
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
SW = {'wood': (0.0, 0.0, 0.333, 1.0), 'gold': (0.333, 0.0, 0.666, 1.0), 'gem': (0.666, 0.0, 1.0, 1.0)}


def lathe(profile, sides, swatch, close0=True, close1=True):
    u0, v0, u1, v1 = SW[swatch]; rings = []
    for z, r in profile:
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / sides), r * math.sin(2 * math.pi * k / sides), z)) for k in range(sides)])
    n = len(profile)
    for i in range(n - 1):
        for k in range(sides):
            j = (k + 1) % sides
            f = bm.faces.new((rings[i][k], rings[i][j], rings[i + 1][j], rings[i + 1][k]))
            for lp, (kk, ii) in zip(f.loops, ((k, i), (k + 1, i), (k + 1, i + 1), (k, i + 1))):
                lp[uvl].uv = (u0 + (u1 - u0) * kk / sides, v0 + (v1 - v0) * ii / (n - 1))
    for idx, ok in ((0, close0), (n - 1, close1)):
        if ok:
            f = bm.faces.new(list(reversed(rings[idx])) if idx == 0 else rings[idx])
            for lp in f.loops:
                lp[uvl].uv = ((u0 + u1) / 2, (v0 + v1) / 2)


lathe([(0.0, RS * 0.6), (0.012, RS * 1.7), (0.03, RS * 1.5), (0.04, RS * 1.05)], 10, 'gold', True, False)   # butt knob
lathe([(0.04, RS * 1.05), (L * 0.55, RS)], 10, 'wood', False, False)                                      # grip rod
lathe([(L * 0.55, RS * 1.25), (L * 0.6, RS * 1.25), (L * 0.62, RS * 1.0), (L * 0.70, RS * 1.3)], 10, 'gold', False, False)
lathe([(L * 0.70, RS * 1.3), (L * 0.78, RS * 1.6), (L * 0.80, RS * 1.2)], 10, 'gold', False, True)        # crown base
gz = L - RG * 1.05
# five curling prongs from the crown base up round the gem
NP, SEG, PR = 5, 7, RS * 0.45
u0, v0, u1, v1 = SW['gold']
for p in range(NP):
    a = 2 * math.pi * p / NP
    pts = []
    for s in range(SEG + 1):
        t = s / SEG
        r = RS * 1.2 + (RG * 1.25) * math.sin(math.pi * 0.85 * t)
        z = L * 0.79 + (L - L * 0.79) * t
        ang = a + 0.5 * t
        pts.append((r * math.cos(ang), r * math.sin(ang), z))
    rings = []
    for s, c in enumerate(pts):
        nxt = pts[min(s + 1, SEG)]; prv = pts[max(s - 1, 0)]
        d = [nxt[i] - prv[i] for i in range(3)]; dl = math.sqrt(sum(x * x for x in d)) or 1
        d = [x / dl for x in d]
        ax = [-d[1], d[0], 0.0]; al = math.sqrt(sum(x * x for x in ax)) or 1; ax = [x / al for x in ax]
        bx = [d[1] * ax[2] - d[2] * ax[1], d[2] * ax[0] - d[0] * ax[2], d[0] * ax[1] - d[1] * ax[0]]
        rr = PR * (1 - 0.6 * s / SEG)
        rings.append([bm.verts.new(tuple(c[i] + rr * (math.cos(2 * math.pi * k / 5) * ax[i] + math.sin(2 * math.pi * k / 5) * bx[i]) for i in range(3))) for k in range(5)])
    for s in range(SEG):
        for k in range(5):
            j = (k + 1) % 5
            f = bm.faces.new((rings[s][k], rings[s][j], rings[s + 1][j], rings[s + 1][k]))
            for lp in f.loops:
                lp[uvl].uv = (u0 + (u1 - u0) * (p + 0.5) / NP, v0 + (v1 - v0) * s / SEG)
    f = bm.faces.new(rings[-1])
    for lp in f.loops:
        lp[uvl].uv = (u0 + (u1 - u0) * (p + 0.5) / NP, v1 - 0.01)
gem = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=RG)
for v in gem['verts']:
    v.co.z = v.co.z * 1.35 + gz
gu0, gv0, gu1, gv1 = SW['gem']
for f in {f for v in gem['verts'] for f in v.link_faces}:
    for lp in f.loops:
        lp[uvl].uv = (gu0 + (gu1 - gu0) * (0.5 + lp.vert.co.x / (2.2 * RG)), gv0 + (gv1 - gv0) * (0.5 + (lp.vert.co.z - gz) / (3.0 * RG)))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new('Staff'); bm.to_mesh(me); bm.free()
for p in me.polygons:
    p.use_smooth = True
ob = bpy.data.objects.new('Staff', me); bpy.context.scene.collection.objects.link(ob)
ob['length'] = L; ob['grip_z'] = L * S['grip_frac']; ob['head_z'] = gz
print('STAFF (wand) tris', sum(len(p.vertices) - 2 for p in me.polygons), 'length', L, 'grip z', round(L * S['grip_frac'], 3), 'gem z', round(gz, 3))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'staff.blend'))
