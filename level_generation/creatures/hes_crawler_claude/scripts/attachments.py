"""Tier attachments, built procedurally: work/anim_base_w.blend (weights_fix.py) -> work/anim_base.blend:
  Pods    (Brood Crawler, B)    a cluster of seven glossy yellow egg pods on the back (Abdomen plates), concept upper left
  Sacs_F / Sacs_M / Sacs_R  (Crawler Matron, C)  six swollen glowing acid sacs on the flanks between the legs, three
                                bones so each pair rides its own body segment (Thorax, Body, Abdomen)
Each attachment is geometry joined into the Crawler mesh with its own material (Crawler_Pods, Crawler_Sacs; small own
textures textures/hcr_pods.png, hcr_sacs.png) and weighted 100 % to its own non-animated child bone, so
tools/split_attachment.py can cut it out of the runtime GLB into a rigid attachment on that node (actors.yml
`attachments`). Positions come from ray casts onto the rest mesh (plate tops for the pods, the flank from inside the
body for the sacs, 2 cm embedded)."""
import bpy, bmesh, os, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_base_w.blend'))
mesh = bpy.data.objects['Crawler']; rig = bpy.data.objects['Crawler_Rig']
BONES = {'Pods': 'Abdomen', 'Sacs_F': 'Thorax', 'Sacs_M': 'Body', 'Sacs_R': 'Abdomen'}

# ---- clean previous attachments
if len(mesh.data.materials) > 1 or any(b in rig.data.bones for b in BONES):
    bm = bmesh.new(); bm.from_mesh(mesh.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index > 0], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(mesh.data); bm.free()
    while len(mesh.data.materials) > 1:
        mesh.data.materials.pop()
    for g in [g for g in mesh.vertex_groups if g.name in BONES]:
        mesh.vertex_groups.remove(g)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    for b in BONES:
        if b in rig.data.edit_bones:
            rig.data.edit_bones.remove(rig.data.edit_bones[b])
    bpy.ops.object.mode_set(mode='OBJECT')
if not mesh.data.materials:
    mesh.data.materials.append(bpy.data.materials.new('Crawler_A'))

bm0 = bmesh.new(); bm0.from_mesh(mesh.data); bvh = BVHTree.FromBMesh(bm0)


def ray(origin, direction, dist=2.0):
    loc, nrm, idx, d = bvh.ray_cast(Vector(origin), Vector(direction).normalized(), dist)
    return loc, nrm


# ---- textures (numpy written through bpy images so no PIL dependency inside Blender)
def write_png(name, rgb):
    h, w, _ = rgb.shape
    img = bpy.data.images.new(name, w, h, alpha=False)
    px = np.concatenate([rgb[::-1], np.ones((h, w, 1))], -1).astype(np.float32).ravel()
    img.pixels.foreach_set(px)
    img.filepath_raw = os.path.join(T, name); img.file_format = 'PNG'; img.save()
    return img


rng = np.random.default_rng(7)
N = 256
v = np.linspace(1, 0, N)[:, None] * np.ones((1, N))            # v = 1 top (north pole) .. 0 bottom
u = np.ones((N, 1)) * np.linspace(0, 1, N)[None]
# egg pods: pale yellow translucent shell, darker olive base, a soft highlight band and small dark embryo specks
top = np.array([0.98, 0.92, 0.55]); bot = np.array([0.62, 0.55, 0.16])
pods = bot + (top - bot) * (v[..., None] ** 0.7)
pods += 0.25 * np.exp(-((v - 0.78) / 0.06) ** 2)[..., None] * np.array([1, 1, 0.8])
spot = np.zeros((N, N))
for _ in range(40):
    cy, cx, r = rng.uniform(0.2, 0.7), rng.uniform(0, 1), rng.uniform(0.01, 0.03)
    spot = np.maximum(spot, np.exp(-(((v - cy) / r) ** 2 + ((u - cx) / (r * 2)) ** 2)))
pods *= (1 - 0.35 * spot)[..., None]
pods_img = write_png('hcr_pods.png', np.clip(pods, 0.02, 0.95) ** 2.2)   # pixels are linear in Blender images
# acid sacs: lime glow, brighter at the bulge, darker green veins
sacs = np.array([0.30, 0.45, 0.04]) + np.array([0.55, 0.50, 0.12]) * (np.sin(np.pi * v) ** 1.5)[..., None]
vein = np.zeros((N, N))
for _ in range(14):
    x0, ph, f = rng.uniform(0, 1), rng.uniform(0, 6.3), rng.uniform(3, 8)
    path = x0 + 0.04 * np.sin(v * f + ph)
    vein = np.maximum(vein, np.exp(-((u - path) / 0.006) ** 2) * (0.6 + 0.4 * np.sin(v * 9 + ph)))
sacs *= (1 - 0.45 * vein)[..., None]
sacs_img = write_png('hcr_sacs.png', np.clip(sacs, 0.02, 0.95) ** 2.2)


def material(name, img, emissive=(0, 0, 0)):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type == 'TEX_IMAGE':
            nt.nodes.remove(n)
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img
    nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.3; bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Emission Color'].default_value = (*emissive, 1); bsdf.inputs['Emission Strength'].default_value = 1.0
    return m


mesh.data.materials.append(material('Crawler_Pods', pods_img))
mesh.data.materials.append(material('Crawler_Sacs', sacs_img, (0.10, 0.17, 0.02)))
MAT = {'Pods': 1, 'Sacs_F': 2, 'Sacs_M': 2, 'Sacs_R': 2}

# ---- placements
items = []                                                     # (bone, centre, radii, rotation)
pod_xy = [(0.0, 0.14), (0.048, 0.12), (-0.046, 0.128), (0.03, 0.185), (-0.032, 0.19), (0.062, 0.168), (0.005, 0.235)]
for i, (x, y) in enumerate(pod_xy):
    r = (0.034, 0.03, 0.028, 0.031, 0.029, 0.024, 0.026)[i]
    hit, n = ray((x, y, 1.0), (0, 0, -1))
    c = hit + Vector((0, 0, r * 0.55))
    items.append(('Pods', c, (r, r * 1.08, r * 0.92), Matrix.Rotation(rng.uniform(-0.3, 0.3), 4, 'X')))
for bone, y in (('Sacs_F', -0.245), ('Sacs_M', -0.058), ('Sacs_R', 0.128)):
    for sgn in (1, -1):
        hit, n = ray((0, y, 0.175), (sgn, 0, -0.15))
        rx, ry, rz = 0.040, 0.064, 0.05
        c = hit + Vector((sgn * (rx - 0.02), 0, 0))
        items.append((bone, c, (rx, ry, rz), Matrix.Rotation(sgn * 0.25, 4, 'Y')))

# ---- bones (non-animated children; head at the item cluster centre)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
for b, parent in BONES.items():
    cs = [c for (bn, c, _, _) in items if bn == b]
    cen = sum(cs, Vector()) / len(cs)
    nb = eb.new(b); nb.head = cen; nb.tail = cen + Vector((0, 0, 0.06)); nb.parent = eb[parent]
    nb.align_roll(Vector((0, -1, 0)))
bpy.ops.object.mode_set(mode='OBJECT')

# ---- geometry
bm = bmesh.new(); bm.from_mesh(mesh.data)
uvl = bm.loops.layers.uv.active
deform = bm.verts.layers.deform.verify()
groups = {b: mesh.vertex_groups.new(name=b) for b in BONES}
for bone, c, (rx, ry, rz), rot in items:
    seg, rings = (10, 6) if bone == 'Pods' else (10, 6)
    res = bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0, calc_uvs=True,
                                    matrix=Matrix.Translation(c) @ rot @ Matrix.Diagonal((rx, ry, rz, 1)))
    vs = res['verts']
    faces = {f for v_ in vs for f in v_.link_faces}
    for f in faces:
        f.material_index = MAT[bone]; f.smooth = True
    gi = groups[bone].index
    for v_ in vs:
        v_[deform].clear(); v_[deform][gi] = 1.0
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if f.material_index > 0 and len(f.verts) > 3])
bm.to_mesh(mesh.data); bm.free()
mesh.data.calc_loop_triangles()
counts = np.bincount([p.material_index for p in mesh.data.polygons])
print('ATTACHMENTS', {b: sum(1 for it in items if it[0] == b) for b in BONES}, 'triangles per material', counts.tolist())
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_base.blend'))
