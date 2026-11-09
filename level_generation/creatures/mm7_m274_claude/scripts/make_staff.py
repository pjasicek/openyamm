"""The Mage's staff, modelled from the native sprite (m274sa0/sa1: a slender dark red-brown wooden shaft with gold
bands, a gold butt cap, and at the top a vertical gold ring holding a large red faceted gem), not by Meshy (a thin
1.8 m prop is beyond Smart Topology; cle/m460 lesson). Proportions from the native front frame (creature.json
"staff": length, shaft radius, ring radius, gem radius, band heights as fractions of the length).
Staff space: +Z from the butt (z = 0) to the top, the ring in the X-Z plane (faces +-Y). UVs on a 3-swatch atlas
(textures/<prefix>_staff_basecolor.png: wood, gold, gem) written by staff_texture.py.
Writes work/staff.blend (object 'Staff', custom props: length, grip_z, head_z) . Args: none"""
import bpy, bmesh, sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg, common
S = cfg.C['staff']
L = S['length']; RS = S['shaft_r']; RR = S['ring_r']; RT = S['ring_tube']; RG = S['gem_r']
bpy.ops.wm.read_factory_settings(use_empty=True)
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
# swatch rectangles in the atlas (u0, v0, u1, v1)
SW = {'wood': (0.0, 0.0, 0.333, 1.0), 'gold': (0.333, 0.0, 0.666, 1.0), 'gem': (0.666, 0.0, 1.0, 1.0)}


def lathe(profile, sides, swatch, closed_bottom=True, closed_top=True):
    """profile: list of (z, r). A tube of rings; UV u around, v along the profile inside the swatch."""
    u0, v0, u1, v1 = SW[swatch]
    rings = []
    for z, r in profile:
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / sides), r * math.sin(2 * math.pi * k / sides), z)) for k in range(sides)])
    n = len(profile)
    for i in range(n - 1):
        for k in range(sides):
            j = (k + 1) % sides
            f = bm.faces.new((rings[i][k], rings[i][j], rings[i + 1][j], rings[i + 1][k]))
            for lp, (kk, ii) in zip(f.loops, ((k, i), (k + 1, i), (k + 1, i + 1), (k, i + 1))):
                lp[uvl].uv = (u0 + (u1 - u0) * kk / sides, v0 + (v1 - v0) * ii / (n - 1))
    for idx, ok in ((0, closed_bottom), (n - 1, closed_top)):
        if ok:
            f = bm.faces.new(list(reversed(rings[idx])) if idx == 0 else rings[idx])
            for lp in f.loops:
                lp[uvl].uv = ((u0 + u1) / 2, (v0 + v1) / 2)


# shaft with gold bands: wood between, gold rings at the band fractions
bands = S.get('bands', [0.0, 0.03, 0.30, 0.33, 0.62, 0.65, 0.92])
lathe([(0.0, RS * 0.8), (L * 0.012, RS * 1.25)], 10, 'gold', True, False)                   # butt cap
z0 = L * 0.012
for b in range(len(bands) - 1):
    za, zb = max(L * bands[b], z0), L * bands[b + 1]
    if zb <= za:
        continue
    gold_band = (zb - za) < 0.06 * L                 # the short segments are the gold bands, the long ones wood
    r = RS * (1.25 if gold_band else 1.0)
    lathe([(za, r), (zb, r)], 10, 'gold' if gold_band else 'wood', False, False)
# collar under the ring
zc = L * bands[-1]
lathe([(zc, RS * 1.0), (zc + L * 0.02, RS * 1.6), (L - 2 * RR + RT, RS * 1.2)], 10, 'gold', False, True)
# ring: torus in the X-Z plane around the gem centre
gz = L - RR
NS, NT = 28, 8
grid = []
for i in range(NS):
    a = 2 * math.pi * i / NS
    cx, cz = RR * math.cos(a), gz + RR * math.sin(a)
    row = []
    for j in range(NT):
        b = 2 * math.pi * j / NT
        rr = RR + RT * math.cos(b)
        row.append(bm.verts.new((rr * math.cos(a), RT * math.sin(b), gz + rr * math.sin(a))))
    grid.append(row)
u0, v0, u1, v1 = SW['gold']
for i in range(NS):
    for j in range(NT):
        a, b = grid[i][j], grid[(i + 1) % NS][j]; c, d = grid[(i + 1) % NS][(j + 1) % NT], grid[i][(j + 1) % NT]
        f = bm.faces.new((a, b, c, d))
        for lp, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
            lp[uvl].uv = (u0 + (u1 - u0) * ii / NS, v0 + (v1 - v0) * jj / NT)
# gem: a faceted sphere in the ring
gem = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=RG)
for v in gem['verts']:
    v.co.z += gz
gu0, gv0, gu1, gv1 = SW['gem']
for f in {f for v in gem['verts'] for f in v.link_faces}:
    for lp in f.loops:
        lp[uvl].uv = (gu0 + (gu1 - gu0) * (0.5 + lp.vert.co.x / (2.2 * RG)), gv0 + (gv1 - gv0) * (0.5 + (lp.vert.co.z - gz) / (2.2 * RG)))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new('Staff'); bm.to_mesh(me); bm.free()
for p in me.polygons:
    p.use_smooth = True
ob = bpy.data.objects.new('Staff', me); bpy.context.scene.collection.objects.link(ob)
ob['length'] = L; ob['grip_z'] = L * S['grip_frac']; ob['head_z'] = gz
print('STAFF tris', sum(len(p.vertices) - 2 for p in me.polygons), 'length', L, 'grip z', round(L * S['grip_frac'], 3), 'gem z', round(gz, 3))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'staff.blend'))
