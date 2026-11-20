"""Tier gear as rigid props (seat_props.py parents them): tier B's salvage chest plate and tier C's buckler emitter.
- Chest plate (references_hd/chest_plate.png, front view): a GRID x GRID lattice over the plate's alpha box, PLATE_W wide,
  centred on the sternum (x of B_Spine2) with its top TOP_Z; each lattice point is ray-cast from the front onto the torso
  shell (garment 1, strips included) and lifted OFFSET in front of the hit; cells inside the alpha mask become quads
  (UVs = the front projection), plus a back face. Object ChestPlate (material ChestPlate_A), on B_Spine2.
- Buckler (references_hd/buckler.png, face-on): a SEG-gon disc of radius R and depth D on the outer side of the left
  forearm (FA_T of the way from the elbow to the wrist, its face normal = the forearm's outward lateral direction, the
  disc centre forearm radius + GAP out); front face UVs = the face-on projection, rim and back from the rim texels; the
  orange rings and centre (radial bins of the reference where most texels glow) as annuli 1 mm proud of the face,
  material Buckler_Glow (emissive), on bone BucklerGlow. Object Buckler (Buckler_A), on B_L_Forearm.
Writes work/chest_plate.blend, work/buckler.blend and textures har_chest_plate_*, har_buckler_*. Args: -- <rig blend>"""
import bpy, bmesh, os, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures'); os.makedirs(os.path.join(T, 'props'), exist_ok=True)
GRID, PLATE_W, TOP_Z, OFFSET = 14, float(os.environ.get('PLATE_W', '0.40')), float(os.environ.get('TOP_Z', '1.46')), float(os.environ.get('OFFSET', '0.03'))
R, D, SEG, FA_T, GAP = 0.16, 0.035, 24, 0.55, 0.02
blend = sys.argv[sys.argv.index('--') + 1]


def load_rgba(name):
    img = bpy.data.images.load(os.path.join(HERE, 'references_hd', name))
    w, h = img.size; px = np.array(img.pixels[:]).reshape(h, w, 4)[::-1]      # row 0 = top
    return img, px


def crop_tex(px, box, out_name, size):
    """the alpha box, transparent texels filled with the nearest opaque colour (simple dilation), saved as a PNG"""
    x0, x1, y0, y1 = box; c = px[y0:y1, x0:x1].copy(); a = c[..., 3] > 0.5
    rgb = c[..., :3].copy()
    for _ in range(40):                                                 # grow colour into the transparent texels
        if a.all():
            break
        acc = np.zeros_like(rgb); cnt = np.zeros(a.shape)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sa = np.roll(a, (dy, dx), (0, 1)); sr = np.roll(rgb, (dy, dx), (0, 1))
            acc += sr * sa[..., None]; cnt += sa
        new = ~a & (cnt > 0); rgb[new] = acc[new] / cnt[new][:, None]; a = a | new
    im = bpy.data.images.new(out_name, rgb.shape[1], rgb.shape[0])
    im.pixels = np.dstack([rgb, np.ones(a.shape)])[::-1].ravel().tolist()
    im.scale(*size); im.filepath_raw = os.path.join(T, 'props', out_name + '.png'); im.file_format = 'PNG'; im.save()
    return im


def material(name, tex, emit=None):
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    n = mat.node_tree.nodes.new('ShaderNodeTexImage'); n.image = tex
    bsdf = next(x for x in mat.node_tree.nodes if x.type == 'BSDF_PRINCIPLED')
    mat.node_tree.links.new(n.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.45; bsdf.inputs['Metallic'].default_value = 0.0
    if emit:
        bsdf.inputs['Emission Color'].default_value = (*emit, 1.0); bsdf.inputs['Emission Strength'].default_value = 1.0
    return mat


bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
co = np.array([v.co[:] for v in me.vertices]); gv = np.array([a.value for a in me.attributes['garment'].data])
J = lambda n: Vector(rig.data.bones[n].head_local)
for o in list(bpy.data.objects):
    if o.name not in ('Rig', 'Body'):
        bpy.data.objects.remove(o, do_unlink=True)
out_objs = {}
# ---------------------------------------------------------------- chest plate
img, px = load_rgba('chest_plate.png')
al = px[..., 3] > 0.5; ys, xs = np.nonzero(al); box = (int(xs.min()), int(xs.max()) + 1, int(ys.min()), int(ys.max()) + 1)
bw, bh = box[1] - box[0], box[3] - box[2]; S = PLATE_W / bw; H_M = bh * S
tex = crop_tex(px, box, 'chest_plate', (512, 512))   # power of two (split_attachment.py)
tor = [tuple(f.vertices) for f in me.polygons if all(gv[i] == 1 for i in f.vertices)]
tree = BVHTree.FromPolygons(co.tolist(), tor)
cx = J('B_Spine2').x
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); grid = {}
for j in range(GRID + 1):
    for i in range(GRID + 1):
        u, v = i / GRID, j / GRID
        x = cx + (u - 0.5) * PLATE_W; z = TOP_Z - v * H_M
        loc, n, fi, d = tree.ray_cast(Vector((x, -1.0, z)), Vector((0, 1, 0)), 2.0)
        if loc is None:
            continue
        grid[(i, j)] = (bm.verts.new((x, loc.y - OFFSET, z)), (u, 1 - v))
nq = 0
for j in range(GRID):
    for i in range(GRID):
        cs = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
        if not all(c in grid for c in cs):
            continue
        uc, vc = (i + 0.5) / GRID, (j + 0.5) / GRID
        if not al[int(box[2] + vc * bh), int(box[0] + uc * bw)]:
            continue
        f = bm.faces.new([grid[c][0] for c in reversed(cs)])
        for l, c in zip(f.loops, reversed(cs)):
            l[uvl].uv = grid[c][1]
        nq += 1
front = list(bm.faces)
ret = bmesh.ops.duplicate(bm, geom=front)                      # back face (the plate's edge shows from the side)
back = [g for g in ret['geom'] if isinstance(g, bmesh.types.BMFace)]
for f in back:
    for v in f.verts:
        v.co.y += 0.006
bmesh.ops.reverse_faces(bm, faces=back)
bm.normal_update()
mesh = bpy.data.meshes.new('ChestPlate'); bm.to_mesh(mesh); bm.free()
ob = bpy.data.objects.new('ChestPlate', mesh); mesh.materials.append(material('ChestPlate_A', tex))
for p in mesh.polygons:
    p.use_smooth = True
out_objs['chest_plate'] = ob
print('GEAR chest plate quads', nq, 'tris', sum(len(p.vertices) - 2 for p in mesh.polygons), 'size m', round(PLATE_W, 3), round(H_M, 3))
# ---------------------------------------------------------------- buckler
img, px = load_rgba('buckler.png')
al = px[..., 3] > 0.5; ys, xs = np.nonzero(al); box = (int(xs.min()), int(xs.max()) + 1, int(ys.min()), int(ys.max()) + 1)
tex = crop_tex(px, box, 'buckler', (512, 512))
c = px[box[2]:box[3], box[0]:box[1]]; hh, ww = c.shape[:2]
yy, xx = np.mgrid[0:hh, 0:ww]; rr = np.hypot((xx - ww / 2) / (ww / 2), (yy - hh / 2) / (hh / 2))
rgb = c[..., :3]
glow = (rgb[..., 0] > 0.8) & (rgb[..., 1] > 0.25) & (rgb[..., 1] < 0.85) & (rgb[..., 2] < 0.45)
bins = np.linspace(0, 1, 41); share = np.array([glow[(rr >= a) & (rr < b)].mean() if ((rr >= a) & (rr < b)).any() else 0 for a, b in zip(bins[:-1], bins[1:])])
rings, cur = [], None
for k, s in enumerate(share):
    if s > 0.45 and cur is None:
        cur = bins[k]
    if s <= 0.45 and cur is not None:
        rings.append((cur, bins[k])); cur = None
if cur is not None:
    rings.append((cur, 1.0))
fa, wr = J('B_L_Forearm'), J('B_L_Hand'); ax = (wr - fa).normalized()
lat = Vector((1, 0, 0)); lat = (lat - ax * lat.dot(ax)).normalized()           # outward (the left side is +x)
ring_pts = [co[i] for i in range(len(co)) if gv[i] == 1 and abs((Vector(co[i]) - fa).dot(ax) - FA_T * (wr - fa).length) < 0.02
            and (Vector(co[i]) - fa).dot(lat) > 0]
cen_axis = fa + ax * FA_T * (wr - fa).length
rad = max([(Vector(p) - cen_axis - ax * (Vector(p) - cen_axis).dot(ax)).length for p in ring_pts] or [0.045])
centre = cen_axis + lat * (rad + GAP + D / 2)
up = ax; side = lat.cross(up).normalized()                                        # the disc plane spans (up, side)
bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap'); MAT = {}


def disc_pt(r_, a_, depth):
    return centre + (up * math.cos(a_) + side * math.sin(a_)) * r_ + lat * depth


def uv_of(r_, a_):
    return (0.5 + 0.5 * r_ / R * math.sin(a_), 0.5 + 0.5 * r_ / R * math.cos(a_))


angs = [2 * math.pi * k / SEG for k in range(SEG)]
fr = [bm.verts.new(disc_pt(R, a_, D / 2)) for a_ in angs]; fi_ = [bm.verts.new(disc_pt(R * 0.55, a_, D / 2 + 0.004)) for a_ in angs]
bk = [bm.verts.new(disc_pt(R * 0.92, a_, -D / 2)) for a_ in angs]
cf = bm.verts.new(centre + lat * (D / 2 + 0.008))


def put(f, uvs, m=0):
    for l, u in zip(f.loops, uvs):
        l[uvl].uv = u
    MAT[f] = m


for k in range(SEG):
    n_ = (k + 1) % SEG
    put(bm.faces.new((fr[k], fr[n_], fi_[n_], fi_[k])), [uv_of(R, angs[k]), uv_of(R, angs[n_]), uv_of(R * .55, angs[n_]), uv_of(R * .55, angs[k])])
    put(bm.faces.new((fi_[k], fi_[n_], cf)), [uv_of(R * .55, angs[k]), uv_of(R * .55, angs[n_]), (0.5, 0.5)])
    put(bm.faces.new((bk[k], bk[n_], fr[n_], fr[k])), [uv_of(R * .97, angs[k]), uv_of(R * .97, angs[n_]), uv_of(R, angs[n_]), uv_of(R, angs[k])])
put(bm.faces.new(list(reversed(bk))), [uv_of(R * .9, a_) for a_ in reversed(angs)])
bm.normal_update(); bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
gseg = 24
for r0, r1 in rings:                                                              # glow annuli, 1 mm proud
    a0, a1 = max(r0, 0.0) * R, min(r1, 0.98) * R
    zf = lambda r_: D / 2 + 0.001 + (0.004 * (R - r_) / (0.45 * R) if r_ >= 0.55 * R else 0.004 + 0.004 * (0.55 * R - r_) / (0.55 * R))
    if a0 < 1e-4:
        ring = [bm.verts.new(disc_pt(a1, a_, zf(a1))) for a_ in angs]; cc = bm.verts.new(centre + lat * (zf(0) + 0.001))
        for k in range(SEG):
            put(bm.faces.new((ring[k], ring[(k + 1) % SEG], cc)), [uv_of(a1, angs[k]), uv_of(a1, angs[(k + 1) % SEG]), (0.5, 0.5)], 1)
        continue
    o = [bm.verts.new(disc_pt(a1, a_, zf(a1))) for a_ in angs]; i_ = [bm.verts.new(disc_pt(a0, a_, zf(a0))) for a_ in angs]
    for k in range(SEG):
        n_ = (k + 1) % SEG
        put(bm.faces.new((o[k], o[n_], i_[n_], i_[k])), [uv_of(a1, angs[k]), uv_of(a1, angs[n_]), uv_of(a0, angs[n_]), uv_of(a0, angs[k])], 1)
bm.normal_update()
for f in bm.faces:                                                                # glow annuli face outward (+lat)
    if MAT.get(f) == 1 and f.normal.dot(lat) < 0:
        f.normal_flip()
mesh = bpy.data.meshes.new('Buckler'); mats = [MAT.get(f, 0) for f in bm.faces]; bm.to_mesh(mesh); bm.free()
ob = bpy.data.objects.new('Buckler', mesh)
mesh.materials.append(material('Buckler_A', tex)); mesh.materials.append(material('Buckler_Glow', tex, (1.0, 0.55, 0.15)))
for p, m in zip(mesh.polygons, mats):
    p.material_index = m; p.use_smooth = False
out_objs['buckler'] = ob
print('GEAR buckler rings', [(round(a, 2), round(b, 2)) for a, b in rings], 'forearm radius cm', round(rad * 100, 1),
      'tris', sum(len(p.vertices) - 2 for p in mesh.polygons), 'centre', [round(x, 3) for x in centre])
for key, ob in out_objs.items():
    bpy.data.libraries.write(os.path.join(HERE, 'work', f'{key}.blend'), {ob}, fake_user=True)
