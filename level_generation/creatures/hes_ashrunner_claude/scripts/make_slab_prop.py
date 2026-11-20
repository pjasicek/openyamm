"""A side-view gun as a low hard-surface prop (modelling guidelines: a few hundred triangles, hard edges between parts):
the reference's outline (work/<name>_profile.json, prop_profile.py) filled with its holes and extruded to +-hw, glow
windows as quads 0.8 mm proud of both sides (material <Name>_Glow, emissive), optional round tubes (a handguard for
the left fist), glow tubes (an emitter) and a straight pistol grip along +Z with its UVs sheared onto the reference's
raked grip. UVs: planar side projection onto textures/props/<name>.png (the reference's alpha box).
Prop space (the hand frames of seat_props.py): origin = the grip centre, +Z up the grip (thumb side), +Y along the
barrel, +X = Y x Z. Image px map into it by scale S = length_m / outline width and a rotation:
- 'pistol': the grip axis (grip_centre_px -> grip_top_px) becomes +Z (the whole gun follows the rake);
- 'carbine' (two-handed, shares the rifle frame of rifle_fit.py): the grip-centre -> foregrip direction is turned onto
  the rifle frame's handguard direction, so the left fist closes on the carbine's foregrip where it closes on the
  rifle's handguard; the raked grip is cut from the outline and replaced by a straight octagon along +Z.
Writes work/<name>.blend (object <Name>; custom props muzzle, uv_box). Args: -- <name>"""
import bpy, bmesh, os, sys, json, math
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
name = sys.argv[sys.argv.index('--') + 1]
CF = json.load(open(os.path.join(HERE, 'scripts', 'props.json')))[name]
PR = json.load(open(os.path.join(HERE, 'work', f'{name}_profile.json')))
BOX = PR['box']; NAME = name.capitalize()
outline_w = max(p[0] for l in PR['loops'] for p in l) - min(p[0] for l in PR['loops'] for p in l)
S = CF['length_m'] / outline_w
gc = Vector(CF['grip_centre_px'])
img = lambda c, r: Vector(((c - gc.x) * S, (gc.y - r) * S))          # image px -> unrotated (y, z)
if 'foregrip_px' in CF:
    FR = json.load(open(os.path.join(HERE, 'work', 'rifle_frame.json')))
    want = Vector(FR['left_centre_rifle'][1:]).normalized()
    have = img(*CF['foregrip_px']).normalized()
    ang = math.atan2(want.y, want.x) - math.atan2(have.y, have.x)
else:
    ax = (img(*CF['grip_top_px'])).normalized()                     # the grip axis -> +Z
    ang = math.pi / 2 - math.atan2(ax.y, ax.x)
ca, sa = math.cos(ang), math.sin(ang)
rot = lambda v: Vector((ca * v.x - sa * v.y, sa * v.x + ca * v.y))
inv = lambda v: Vector((ca * v.x + sa * v.y, -sa * v.x + ca * v.y))
P2 = lambda c, r: rot(img(c, r))                                     # image px -> prop (y, z)
def to_px(y, z):
    u = inv(Vector((y, z))); return u.x / S + gc.x, gc.y - u.y / S
HW = CF['hw']
bpy.ops.wm.read_factory_settings(use_empty=True)
bm = bmesh.new(); MAT = {}


def face(vs, glow=False):
    f = bm.faces.new(vs); MAT[f] = 1 if glow else 0; return f


# the outline slab: fill both sides (scanfill keeps the holes), then walls
side = {}
for sx in (-1, 1):
    edges = []
    for lp in PR['loops']:
        vs = [bm.verts.new((sx * HW, *P2(*p))) for p in lp]
        side.setdefault(sx, []).append(vs)
        for i in range(len(vs)):
            edges.append(bm.edges.new((vs[i], vs[(i + 1) % len(vs)])))
    res = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges)
    for f in res['geom']:
        if isinstance(f, bmesh.types.BMFace):
            MAT[f] = 0
for la, lb in zip(side[-1], side[1]):
    for i in range(len(la)):
        j = (i + 1) % len(la)
        face((la[i], la[j], lb[j], lb[i]))


def tube(y0, y1, r0, r1, zc, seg=12, glow=False):
    rings = [[bm.verts.new((r * math.cos(2 * math.pi * k / seg), y, zc + r * math.sin(2 * math.pi * k / seg)))
              for k in range(seg)] for y, r in ((y0, r0), (y1, r1))]
    for k in range(seg):
        a, b = k, (k + 1) % seg
        face((rings[0][a], rings[1][a], rings[1][b], rings[0][b]), glow)
    face(rings[0], glow); face(list(reversed(rings[1])), glow)


for t in CF.get('tubes', []):                                        # tubes along the barrel axis (prop +Y)
    a, b = P2(t['px'][0], t['row']), P2(t['px'][1], t['row'])
    tube(a.x, b.x, t['r'], t['r'], (a.y + b.y) / 2)
for t in CF.get('glow_tubes', []):
    a, b = P2(t['px'][0], t['row']), P2(t['px'][1], t['row'])
    tube(a.x, b.x, t['r0'], t['r1'], (a.y + b.y) / 2, glow=True)
GRIPV = set()
if 'grip_box' in CF:                                                  # straight octagon grip along +Z
    r = CF['grip_box']['r']; z0, z1 = CF['grip_box']['z']; n0 = len(bm.verts)
    rings = [[bm.verts.new((r * math.cos(2 * math.pi * (k + 0.5) / 8), r * math.sin(2 * math.pi * (k + 0.5) / 8), z))
              for k in range(8)] for z in (z0, z1)]
    for k in range(8):
        a, b = k, (k + 1) % 8; face((rings[0][a], rings[0][b], rings[1][b], rings[1][a]))
    face(list(reversed(rings[0])))
    bm.verts.ensure_lookup_table(); GRIPV = {v.index for v in bm.verts[n0:]}
GLOWF = []
for c0, r0, c1, r1 in CF.get('glow_rects', []):                       # glow windows, 0.8 mm proud of both sides
    for sx in (-1, 1):
        q = [bm.verts.new((sx * (HW + 0.0008), *P2(c, r))) for c, r in ((c0, r1), (c1, r1), (c1, r0), (c0, r0))]
        GLOWF.append(face(q if sx > 0 else list(reversed(q)), glow=True))
bm.normal_update()
bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f not in GLOWF])
for f in GLOWF:
    if f.normal.x * f.verts[0].co.x < 0:
        f.normal_flip()
# UVs: planar side projection; the straight grip samples the raked reference grip (its axis in the image)
uvl = bm.loops.layers.uv.new('UVMap'); bm.verts.ensure_lookup_table()
gax = (Vector(CF['grip_top_px']) - gc).normalized()   # image px: up the grip
gpe = Vector((-gax.y, gax.x)) if Vector((-gax.y, gax.x)).x > 0 else Vector((gax.y, -gax.x))
for f in bm.faces:
    for l in f.loops:
        v = l.vert; c = v.co
        if v.index in GRIPV:
            px = gc + gax * (c.z / S) + gpe * (c.y / S)
            col, row = px.x, px.y
        else:
            col, row = to_px(c.y, c.z)
        l[uvl].uv = ((col - BOX[0]) / (BOX[1] - BOX[0]), 1.0 - (row - BOX[2]) / (BOX[3] - BOX[2]))
me = bpy.data.meshes.new(NAME); bm.to_mesh(me)
mats = [MAT.get(f, 0) for f in bm.faces]
bm.free()
ob = bpy.data.objects.new(NAME, me); bpy.context.scene.collection.objects.link(ob)
tex = os.path.join(HERE, 'textures', 'props', f'{name}.png')
emit = (0.55, 0.8, 1.0) if CF['glow'] == 'blue' else (1.0, 0.55, 0.15)
for mname, e in ((f'{NAME}_A', None), (f'{NAME}_Glow', emit)):
    mat = bpy.data.materials.new(mname); mat.use_nodes = True
    n = mat.node_tree.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(tex)
    bsdf = next(x for x in mat.node_tree.nodes if x.type == 'BSDF_PRINCIPLED')
    mat.node_tree.links.new(n.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.45; bsdf.inputs['Metallic'].default_value = 0.0
    if e:
        bsdf.inputs['Emission Color'].default_value = (*e, 1.0); bsdf.inputs['Emission Strength'].default_value = 1.0
    me.materials.append(mat)
for p, gi in zip(me.polygons, mats):
    p.material_index = gi; p.use_smooth = False
mz = P2(*CF['muzzle_px'])
ob['muzzle'] = [0.0, mz.x, mz.y]
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', f'{name}.blend'))
ys = [v.co.y for v in me.vertices]
print('SLAB', name, 'tris', sum(len(p.vertices) - 2 for p in me.polygons), 'length m', round(max(ys) - min(ys), 3),
      'rotation deg', round(math.degrees(ang), 1), 'muzzle', [round(x, 3) for x in ob['muzzle']], 'scale mm/px', round(S * 1000, 3))
