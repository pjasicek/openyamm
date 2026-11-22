"""Witch fork-staff, modelled from references_hd/05_staff.png (crystal head left, prongs right, 870 px = 1.29 m) and the
native sprite (held in the left gauntlet ~0.47 m below the crystal top, the fork pointing down).
Prop space: +Y toward the crystal, origin at the grip centre (the solved handle centre of work/grip_pose.json).
Parts (radii from the reference): white shaft r 1.5 cm with red bands (single, triple, single), red-wrapped lower grip
r 1.6 cm, dark metal collars, a claw cage of four curved spikes round a faceted magenta crystal (r 6 cm), a fork collar
and three prongs (5 cm apart, 24 cm long, the outer two splayed at the root). Every lathe part is mapped onto the
reference's centre row by its axial position (clean bands without the painting's baked shading); the crystal is
projected from the side so its facets keep the painted highlights.
Writes textures/staff_basecolor.png (1024 x 256 crop of the reference), textures/staff_emission_mask.png (crystal),
work/staff.blend (object 'StaffMesh', material 'Staff_A', UVMap) and prints the triangle count. Args: none"""
import bpy, bmesh, os, sys, math
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(HERE, *p)
TOP, BOT = 0.47, -0.82                      # crystal top / prong tips along +Y from the grip
S = (TOP - BOT) / 870.0                     # metres per reference pixel
X_TOP = 335.0                               # reference column of the crystal's far edge
CX0, CY0, CW, CH = 320, 400, 896, 224        # crop box of the reference -> 1024 x 256 texture
ROW = 512.0                                 # the staff's centre row in the reference


def ref_x(y):
    return X_TOP + (TOP - y) / S


def uv(x_px, y_px):
    return ((x_px - CX0) / CW, 1.0 - (y_px - CY0) / CH)


# ---------------------------------------------------------------- textures (PIL inside Blender's Python is absent: use bpy)
src = bpy.data.images.load(R('references_hd', '05_staff.png'))
W0, H0 = src.size
px = np.array(src.pixels[:]).reshape(H0, W0, 4)[::-1]          # top row first
crop = px[CY0:CY0 + CH, CX0:CX0 + CW]
ys = (np.arange(256) + 0.5) * CH / 256; xs = (np.arange(1024) + 0.5) * CW / 1024
tex = crop[ys.astype(int)][:, xs.astype(int)]
tex[..., 3] = 1.0
img = bpy.data.images.new('staff_basecolor', 1024, 256, alpha=False)
img.pixels = tex[::-1].ravel().tolist(); img.filepath_raw = R('textures', 'staff_basecolor.png'); img.file_format = 'PNG'
os.makedirs(R('textures'), exist_ok=True); img.save()
mask = np.zeros((256, 1024, 4)); mask[..., 3] = 1
u0, u1 = uv(ref_x(TOP), 0)[0], uv(ref_x(TOP - 0.135), 0)[0]
cu = (np.arange(1024) + 0.5) / 1024
m = (cu >= u0) & (cu <= u1)
mag = tex[..., 0] * 0.5 + tex[..., 2] * 0.5 - tex[..., 1]          # magenta = red + blue over green
mk = np.clip((mag - 0.15) / 0.35, 0, 1) * m[None, :]
mask[..., 0] = mask[..., 1] = mask[..., 2] = mk
mimg = bpy.data.images.new('staff_emission_mask', 1024, 256, alpha=False)
mimg.pixels = mask[::-1].ravel().tolist(); mimg.filepath_raw = R('textures', 'staff_emission_mask.png'); mimg.file_format = 'PNG'
mimg.save()

# ---------------------------------------------------------------- geometry
bm = bmesh.new()
uvl = bm.loops.layers.uv.new('UVMap')


def lathe(profile, seg=8, row=ROW):
    """profile: [(y, r)] bottom to top; rings of `seg` vertices, quads between, caps closed by the end rings' fans
    only where r > 0 at the ends (inner ring + strip for no high valence)."""
    rings = []
    for y, r in profile:
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / seg), y, r * math.sin(2 * math.pi * k / seg))) for k in range(seg)])
    faces = []
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(seg):
            faces.append(bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k])))
    for ring, flip in ((rings[0], True), (rings[-1], False)):
        f = bm.faces.new(ring[::-1] if flip else ring); faces.append(f)
    for f in faces:
        for l in f.loops:
            l[uvl].uv = uv(ref_x(l.vert.co.y), row)
    return faces


# shaft (white with bands) and the red-wrapped grip below it, one lathe so bands come from the texture
lathe([(-0.524, 0.016), (-0.33, 0.016), (-0.325, 0.015), (0.30, 0.015)])
# collars (dark metal)
lathe([(0.295, 0.022), (0.305, 0.027), (0.335, 0.027), (0.345, 0.020)], row=ROW)
lathe([(-0.578, 0.020), (-0.565, 0.028), (-0.535, 0.028), (-0.522, 0.019)], row=ROW)
# crystal: faceted ball, projected from the side
cc = Vector((0, TOP - 0.063, 0))
ico = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.062, matrix=Matrix.Translation(cc))
cverts = set(ico['verts'])
for f in {f for v in cverts for f in v.link_faces}:
    f.smooth = False
    for l in f.loops:
        l[uvl].uv = uv(ref_x(l.vert.co.y), ROW - l.vert.co.z / S * 0.9)
# claw cage: four curved spikes from the upper collar over the crystal
for k in range(4):
    ang = math.pi / 4 + k * math.pi / 2
    d = Vector((math.cos(ang), 0, math.sin(ang)))
    pts = [Vector((0, 0.335, 0)) + d * 0.024, cc + d * 0.055 + Vector((0, -0.03, 0)), cc + d * 0.05 + Vector((0, 0.012, 0)),
           cc + d * 0.032 + Vector((0, 0.04, 0))]
    rad = [0.007, 0.006, 0.004, 0.0005]
    prev = None
    for i, (p, r) in enumerate(zip(pts, rad)):
        t = (pts[min(i + 1, 3)] - pts[max(i - 1, 0)]).normalized(); s1 = t.cross(d).normalized(); s2 = t.cross(s1)
        ring = [bm.verts.new(p + (s1 * math.cos(j * math.pi / 2) + s2 * math.sin(j * math.pi / 2)) * r) for j in range(4)]
        if prev:
            for j in range(4):
                f = bm.faces.new((prev[j], prev[(j + 1) % 4], ring[(j + 1) % 4], ring[j]))
                for l in f.loops:
                    l[uvl].uv = uv(ref_x(0.325), ROW)
        prev = ring
# prongs: three tines in the X-Y plane, 5 cm apart, the outer two splayed from the collar
for xoff in (-0.05, 0.0, 0.05):
    pts = [Vector((xoff * 0.35, -0.575, 0)), Vector((xoff, -0.63, 0)), Vector((xoff, -0.79, 0)), Vector((xoff * 1.02, BOT, 0))]
    rad = [0.006, 0.005, 0.0045, 0.0005]
    row = ROW + xoff / 0.05 * 34
    prev = None
    for i, (p, r) in enumerate(zip(pts, rad)):
        t = (pts[min(i + 1, 3)] - pts[max(i - 1, 0)]).normalized(); s1 = t.cross(Vector((0, 0, 1))).normalized(); s2 = t.cross(s1)
        ring = [bm.verts.new(p + (s1 * math.cos(j * math.pi / 2) + s2 * math.sin(j * math.pi / 2)) * r) for j in range(4)]
        if prev:
            for j in range(4):
                f = bm.faces.new((prev[j], prev[(j + 1) % 4], ring[(j + 1) % 4], ring[j]))
                for l in f.loops:
                    l[uvl].uv = uv(ref_x(min(l.vert.co.y, -0.60)), row)
        prev = ring
bmesh.ops.triangulate(bm, faces=bm.faces[:])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new('StaffMesh'); bm.to_mesh(me); bm.free()
for p in me.polygons:
    if p.use_smooth is not False:
        pass
ob = bpy.data.objects.new('StaffMesh', me); bpy.context.scene.collection.objects.link(ob)
for p in me.polygons:
    c = sum((me.vertices[v].co for v in p.vertices), Vector()) / len(p.vertices)
    p.use_smooth = (c - cc).length > 0.07                          # crystal flat-faceted, the rest smooth
mat = bpy.data.materials.new('Staff_A'); mat.use_nodes = True
bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
t = mat.node_tree.nodes.new('ShaderNodeTexImage'); t.image = img
mat.node_tree.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
bsdf.inputs['Roughness'].default_value = 0.55; bsdf.inputs['Metallic'].default_value = 0.0
me.materials.append(mat)
print('STAFF tris', len(me.polygons), 'length m', round(TOP - BOT, 3), 'crystal u', round(u0, 3), round(u1, 3),
      'mask texels', int((mk > 0.5).sum()))
bpy.ops.wm.save_as_mainfile(filepath=R('work', 'staff.blend'))
