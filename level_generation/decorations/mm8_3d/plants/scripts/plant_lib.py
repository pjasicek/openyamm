"""Blender helpers for the MM8 plants (run inside Blender). Adapted from the MM6 succulents' `succ_lib.py` (geometry
accumulator, ribbed sweeps) and the MM6 flowers (cards, lathed heads, clump normals).

Geometry is accumulated in a `Geo` (positions, faces with per-loop texture coordinates and shading normals, per-vertex
RGB colour = tint x occlusion), then turned into one Blender object per LOD. Blender is Z-up; the glTF export turns
it Y-up. Every model stands on its base centre (origin) on the ground. Texture coordinates are image space (v down)
and flipped on output.

Parts (all take a Geo, an Atlas and placement in metres):
  leaf()   a strip along a drooping spine, its width fitted to the painted leaf's outline in the atlas cell
           (`<atlas>_layout.json` half-width profile), so little transparent area is drawn; across=2 folds it along
           the midrib. segs=1, across=1 gives a plain card over the whole cell (the card cutter trims it later).
  card()   a quad over a cell (sprays, tufts, flowers seen side on).
  head()   a lathed flower head mapped radially from a face-on painted flower cell: flat discs, cups, goblets.
  tube()   a swept tube (stems, trunks) mapped either onto an atlas strip or a tiling texture.
LODs are built by the recipes from one seeded layout with a keep priority per part."""
import bpy, json, math, os
import numpy as np
from mathutils import Vector, Matrix, Quaternion

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(HERE, 'textures')
WORK = os.path.join(HERE, 'work')
REVIEW = os.path.join(HERE, 'review')
UP = Vector((0, 0, 1))


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def frame(axis):
    axis = Vector(axis).normalized()
    helper = Vector((0, 0, 1)) if abs(axis.z) < 0.95 else Vector((1, 0, 0))
    a = helper.cross(axis).normalized()
    return a, axis.cross(a), axis


def rot(v, axis, angle):
    return Quaternion(Vector(axis).normalized(), angle) @ Vector(v)


class Atlas:
    def __init__(self, name):
        self.name = name
        with open(os.path.join(TEX, f'{name}_layout.json')) as fh:
            self.meta = json.load(fh)
        self.cells = self.meta['cells']

    def rect(self, cell):
        return self.cells[cell]['rect']

    def half(self, cell, t):
        """Relative half width of the painted shape at t (0 base .. 1 tip of the cell), conservative."""
        prof = self.cells[cell]['half']
        n = len(prof)
        x = min(max(t * n - 0.5, 0), n - 1)
        i = int(x)
        lo, hi = max(i - 1, 0), min(i + 2, n - 1)
        return max(prof[lo:hi + 1])


class Geo:
    """Mesh accumulator. Loop normals: None = smooth vertex normal, 'flat' = face normal, or a Vector."""

    def __init__(self):
        self.v, self.col, self.faces, self.uvs, self.norms, self.mats = [], [], [], [], [], []

    def vert(self, p, colour=(1.0, 1.0, 1.0)):
        self.v.append(Vector(p)); self.col.append(tuple(colour))
        return len(self.v) - 1

    def face(self, idx, uvs, normals=None, mat=0):
        self.faces.append(tuple(idx)); self.uvs.append([(u, 1.0 - v) for u, v in uvs])
        self.norms.append(normals if normals is not None else [None] * len(idx)); self.mats.append(mat)

    def triangles(self):
        return sum(len(f) - 2 for f in self.faces)

    def face_normal(self, f):
        n = Vector((0, 0, 0)); pts = [self.v[i] for i in f]
        for a, b in zip(pts, pts[1:] + pts[:1]):
            n += a.cross(b)
        return n.normalized() if n.length > 1e-12 else Vector((0, 0, 1))

    def loop_normals(self):
        fn = [self.face_normal(f) for f in self.faces]
        vn = [Vector((0, 0, 0)) for _ in self.v]
        for f, n, ns in zip(self.faces, fn, self.norms):
            for i, spec in zip(f, ns):
                if spec is None:
                    vn[i] += n
        vn = [n.normalized() if n.length > 1e-9 else Vector((0, 0, 1)) for n in vn]
        out = []
        for f, n, ns in zip(self.faces, fn, self.norms):
            for i, spec in zip(f, ns):
                out.append(vn[i] if spec is None else (n if spec == 'flat' else Vector(spec).normalized()))
        return out

    def bounds(self):
        a = np.array([tuple(p) for p in self.v])
        return a.min(0), a.max(0)

    def to_object(self, name, materials):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(p) for p in self.v], [], self.faces)
        me.validate(clean_customdata=False)
        uv = me.uv_layers.new(name='UVMap')
        uv.data.foreach_set('uv', [c for f in self.uvs for uvp in f for c in uvp])
        for m in materials:
            me.materials.append(m)
        me.polygons.foreach_set('material_index', self.mats)
        me.polygons.foreach_set('use_smooth', [True] * len(self.faces))
        me.normals_split_custom_set([tuple(n) for n in self.loop_normals()])
        attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
        attr.data.foreach_set('color', [x for c in self.col for x in (min(c[0], 1.0), min(c[1], 1.0),
                                                                         min(c[2], 1.0), 1.0)])
        me.color_attributes.active_color = attr
        obj = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(obj)
        return obj


# ------------------------------------------------------------------ shading helpers
class Clump:
    """Analytic occlusion and volume normals for a plant: an ellipsoid (centre, radii) that is the foliage volume.
    occ(p) darkens toward the ground and deep inside the volume; normal(own, p) blends a face's own normal (turned
    outward) with the direction out of the volume, so cards shade as one mass."""

    def __init__(self, centre, radii, floor=0.35, ground=0.3, depth=0.55, blend=0.55, height=None):
        self.c = Vector(centre); self.r = Vector(radii); self.floor = floor; self.ground = ground
        self.depth = depth; self.blend = blend; self.H = height or (self.c.z + self.r.z)

    def local(self, p):
        d = p - self.c
        return Vector((d.x / self.r.x, d.y / self.r.y, d.z / self.r.z))

    def outward(self, p):
        q = self.local(p)
        n = Vector((q.x / self.r.x, q.y / self.r.y, q.z / self.r.z))
        return n.normalized() if n.length > 1e-6 else Vector((0, 0, 1))

    def occ(self, p):
        q = self.local(p).length
        inner = max(0.0, 1.0 - q)                      # 0 at the surface, 1 at the centre
        z = max(p.z, 0.0) / max(self.H, 1e-6)
        g = self.ground + (1 - self.ground) * min(1.0, z / 0.35) ** 0.8
        return max(self.floor, (1 - self.depth * inner ** 0.8) * g)

    def normal(self, own, p):
        out = self.outward(p)
        own = own if own.dot(out) >= 0 else -own
        return (own * (1 - self.blend) + out * self.blend).normalized()


def tinted(tint, o):
    return (tint[0] * o, tint[1] * o, tint[2] * o)


# ------------------------------------------------------------------ parts
def spine_points(base, direction, length, droop, segs, curl=0.0, curl_axis=None):
    """Points along a leaf that starts along `direction` and bends down by `droop` radians over its length
    (gravity), optionally curling sideways."""
    d0 = Vector(direction).normalized()
    horiz = Vector((d0.x, d0.y, 0))
    bend_axis = horiz.cross(UP).normalized() if horiz.length > 1e-4 else Vector((1, 0, 0))
    pts = [Vector(base)]; dirs = []
    step = length / segs
    p = Vector(base)
    for k in range(segs):
        t = (k + 0.5) / segs
        d = rot(d0, bend_axis, -droop * t)
        if curl and curl_axis is not None:
            d = rot(d, curl_axis, curl * t)
        dirs.append(d)
        p = p + d * step
        pts.append(p)
    dirs.append(dirs[-1])
    return pts, dirs


def leaf(g, atlas, cell, base, direction, length, clump, tint=(1, 1, 1), droop=0.0, roll=0.0, segs=3, across=2,
         fold=0.25, width=1.0, mat=0, curl=0.0, normal_up=0.0, shade=1.0):
    """Leaf strip fitted to the painted outline of `cell` (base at the cell's bottom centre). width scales the
    painted aspect. roll turns the blade about its first direction (0 = blade plane contains the up axis)."""
    u0, v0, u1, v1 = atlas.rect(cell)
    info = atlas.cells[cell]
    t0, t1 = info.get('t0', 0.0), info.get('t1', 1.0)
    d0 = Vector(direction).normalized()
    side0 = UP.cross(d0)
    if side0.length < 1e-4:
        side0 = Vector((1, 0, 0))
    side0 = rot(side0.normalized(), d0, roll)
    curl_axis = d0
    pts, dirs = spine_points(base, d0, length, droop, segs, curl, curl_axis)
    full_w = length / max(t1 - t0, 1e-3) * info['aspect'] * width       # physical width of the whole cell
    card_mode = segs == 1 and across == 1
    rows = []
    side = side0
    for k, (p, d) in enumerate(zip(pts, dirs)):
        if k:
            q = dirs[k - 1].rotation_difference(d); side = (q @ side)
            side = (side - d * side.dot(d)).normalized()
        t = t0 + (t1 - t0) * k / segs
        h = 1.0 if card_mode else min(1.0, atlas.half(cell, t) + 0.05)
        if not card_mode and k == segs:
            h = max(h, 0.08)
        hw = h * full_w * 0.5
        v = v1 + (v0 - v1) * t
        blade_n = side.cross(d).normalized()
        if blade_n.z < 0 and abs(blade_n.z) > 0.05:
            pass
        row = []
        cols = [(-1, 0.0), (1, 0.0)] if across == 1 else [(-1, 0.0), (0, 1.0), (1, 0.0)]
        for s, lift in cols:
            pos = p + side * (s * hw) + blade_n * (lift * fold * hw)
            pos.z = max(pos.z, 0.003)
            n = (blade_n * (1 - 0.35 * abs(s) * 0) - side * (s * fold * 0.8)).normalized()
            n = (n + UP * normal_up).normalized()
            n = clump.normal(n, pos) if clump else n
            o = clump.occ(pos) * shade if clump else shade
            uc = (u0 + u1) * 0.5 + s * h * (u1 - u0) * 0.5
            row.append((g.vert(pos, tinted(tint, o)), (uc, v), n))
        rows.append(row)
    for k in range(segs):
        a, b = rows[k], rows[k + 1]
        for c in range(len(a) - 1):
            quad = [a[c], a[c + 1], b[c + 1], b[c]]
            g.face([q[0] for q in quad], [q[1] for q in quad], [q[2] for q in quad], mat)


def card(g, atlas, cell, base, right, up, clump, tint=(1, 1, 1), mat=0, shade=1.0, normal=None, sub=None):
    """Quad: base - right/2 .. base + right/2 + up over the whole cell (or `sub` = (u0, v0, u1, v1) fractions)."""
    u0, v0, u1, v1 = atlas.rect(cell)
    if sub:
        su0, sv0, su1, sv1 = sub
        u0, u1 = u0 + (u1 - u0) * su0, u0 + (u1 - u0) * su1
        v0, v1 = v0 + (v1 - v0) * sv0, v0 + (v1 - v0) * sv1
    base, right, up = Vector(base), Vector(right), Vector(up)
    pts = [base - right * 0.5, base + right * 0.5, base + right * 0.5 + up, base - right * 0.5 + up]
    for p in pts:
        p.z = max(p.z, 0.0)
    uvs = [(u0, v1), (u1, v1), (u1, v0), (u0, v0)]
    own = right.cross(up).normalized()
    nrm = []
    for p in pts:
        n = normal if normal is not None else (clump.normal(own, p) if clump else own)
        nrm.append(n)
    idx = [g.vert(p, tinted(tint, (clump.occ(p) if clump else 1.0) * shade)) for p in pts]
    g.face(idx, uvs, nrm, mat)


PROFILES = {
    # (radial distance, axial height) in head radii; texture radius follows the arc length
    'flat': [(0.0, 0.0), (1.0, 0.12)],
    'dish': [(0.0, 0.0), (0.4, 0.06), (1.0, 0.3)],
    'cup': [(0.0, 0.0), (0.35, 0.12), (0.75, 0.45), (1.0, 0.85)],
    'trumpet': [(0.0, -0.35), (0.18, -0.05), (0.55, 0.12), (1.0, 0.32)],
    'goblet': [(0.0, 0.0), (0.45, 0.18), (0.8, 0.7), (0.85, 1.25), (0.62, 1.7)],
    'dome': [(0.0, 0.62), (0.55, 0.52), (0.9, 0.18), (0.95, -0.12)],
    'star': [(0.0, 0.0), (0.3, 0.1), (1.0, 0.45)],
}


def head(g, atlas, cell, centre, axis, radius, clump, tint=(1, 1, 1), profile='dish', segments=8, rings=None,
         mat=0, shade=1.0, turn=None, rng=None, tex_scale=1.0, open_normals=0.5):
    """Lathed flower head round `axis`, texture mapped radially from the face-on painted flower (centre of the cell =
    the flower's centre, the painted petal tips at the outermost profile point). rings: subset of the profile points
    for coarser levels."""
    prof = PROFILES[profile] if isinstance(profile, str) else profile
    if rings is not None:
        idx = sorted(set([0, len(prof) - 1] + [i for i in rings if 0 < i < len(prof) - 1]))
        prof = [prof[i] for i in idx]
    u0, v0, u1, v1 = atlas.rect(cell)
    cu, cv = (u0 + u1) * 0.5, (v0 + v1) * 0.5
    ru, rv = (u1 - u0) * 0.5 * atlas.cells[cell]['radius'] * tex_scale, (v1 - v0) * 0.5 * atlas.cells[cell]['radius'] * tex_scale
    arcs = [0.0]
    for (r0, h0), (r1, h1) in zip(prof, prof[1:]):
        arcs.append(arcs[-1] + math.hypot(r1 - r0, h1 - h0))
    taus = [a / arcs[-1] for a in arcs]
    a, b, n = frame(axis)
    t0 = turn if turn is not None else (rng.uniform(0, 2 * math.pi) if rng is not None else 0.0)
    ring_ids = []
    for i, ((r, hgt), tau) in enumerate(zip(prof, taus)):
        ids = []
        count = 1 if r < 1e-6 else segments
        for k in range(count):
            ang = t0 + 2 * math.pi * k / segments
            radial = a * math.cos(ang) + b * math.sin(ang)
            pos = Vector(centre) + radial * (r * radius) + n * (hgt * radius)
            pos.z = max(pos.z, 0.003)
            if i + 1 < len(prof):
                dr, dh = prof[i + 1][0] - r, prof[i + 1][1] - hgt
            else:
                dr, dh = r - prof[i - 1][0], hgt - prof[i - 1][1]
            surf = (radial * dh - n * dr)           # normal of the profile curve (outer side)
            nn = (n * (1 - open_normals) + (n if surf.length < 1e-6 else -surf.normalized()) * open_normals)
            nn = (nn + radial * 0.15).normalized()
            o = (clump.occ(pos) if clump else 1.0) * shade
            uv = (cu + math.cos(ang) * tau * ru, cv + math.sin(ang) * tau * rv)
            ids.append((g.vert(pos, tinted(tint, o)), uv, nn, ang))
        ring_ids.append(ids)
    for i in range(len(ring_ids) - 1):
        A, B = ring_ids[i], ring_ids[i + 1]
        for k in range(segments):
            k2 = (k + 1) % segments
            if len(A) == 1:
                # centre: triangle per segment, the centre's texture coordinate is the cell centre
                c = A[0]
                g.face([c[0], B[k][0], B[k2][0]], [(cu, cv), B[k][1], _wrap(B, k2, k, cu, cv, ru, rv, taus[i + 1])],
                       [n, B[k][2], B[k2][2]], mat)
            else:
                g.face([A[k][0], B[k][0], B[k2][0], A[k2][0]],
                       [A[k][1], B[k][1], B[k2][1], A[k2][1]], [A[k][2], B[k][2], B[k2][2], A[k2][2]], mat)


def _wrap(B, k2, k, cu, cv, ru, rv, tau):
    return B[k2][1]


def tube(g, pts, radii, sides, clump=None, tint=(1, 1, 1), mat=0, uv_rect=None, tile=None, cap=False, shade=1.0,
         occ_floor=None):
    """Swept tube along pts (Vectors) with radii; uv_rect = (u0, v0, u1, v1) atlas strip (u round, v along, the
    whole length stretched over the strip) or tile = (u repeats round, metres per v repeat) for a tiling texture."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    tang = []
    for i in range(n):
        d = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        tang.append(d.normalized() if d.length > 1e-9 else Vector((0, 0, 1)))
    side, _, _ = frame(tang[0])
    length = [0.0]
    for i in range(1, n):
        length.append(length[-1] + (pts[i] - pts[i - 1]).length)
    rings = []
    for i in range(n):
        if i:
            q = tang[i - 1].rotation_difference(tang[i]); side = (q @ side)
            side = (side - tang[i] * side.dot(tang[i])).normalized()
        other = tang[i].cross(side)
        ring = []
        for k in range(sides + 1):
            ang = 2 * math.pi * k / sides
            d = side * math.cos(ang) + other * math.sin(ang)
            p = pts[i] + d * radii[i]
            o = (clump.occ(p) if clump else 1.0) * shade
            if occ_floor is not None:
                o = max(o, occ_floor)
            if uv_rect is not None:
                u0, v0, u1, v1 = uv_rect
                uv = (u0 + (u1 - u0) * k / sides, v1 + (v0 - v1) * length[i] / max(length[-1], 1e-9))
            else:
                uv = (tile[0] * k / sides, length[i] / tile[1])
            ring.append((g.vert(p, tinted(tint, o)) if k < sides else None, uv, d))
        ring[sides] = (ring[0][0], ring[sides][1], ring[sides][2])
        rings.append(ring)
    for i in range(n - 1):
        for k in range(sides):
            A, B = rings[i], rings[i + 1]
            g.face([A[k][0], A[k + 1][0], B[k + 1][0], B[k][0]], [A[k][1], A[k + 1][1], B[k + 1][1], B[k][1]],
                   [None] * 4, mat)
    return rings


# ------------------------------------------------------------------ materials
_images = {}


def image(path, colorspace):
    key = (path, colorspace)
    if key not in _images:
        img = bpy.data.images.load(path); img.colorspace_settings.name = colorspace
        _images[key] = img
    return _images[key]


def material(name, stem, cutout=True, roughness=0.75, extras=None, extension='EXTEND', normal=True):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tb = nt.nodes.new('ShaderNodeTexImage'); tb.image = image(os.path.join(TEX, f'{stem}_basecolor.png'), 'sRGB')
    tb.extension = extension
    nt.links.new(tb.outputs['Color'], bsdf.inputs['Base Color'])
    if cutout:
        nt.links.new(tb.outputs['Alpha'], bsdf.inputs['Alpha'])
        m.surface_render_method = 'DITHERED'
    m.use_backface_culling = not cutout
    if normal:
        tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = image(os.path.join(TEX, f'{stem}_normal.png'), 'Non-Color')
        tn.extension = extension
        nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = roughness; bsdf.inputs['Metallic'].default_value = 0.0
    for k, v in (extras or {}).items():
        m[k] = v
    return m


def export(objects, sid):
    work = os.path.join(WORK, sid); os.makedirs(work, exist_ok=True)
    for o in bpy.data.objects:
        o.select_set(o in objects)
    bpy.context.view_layer.objects.active = objects[0]
    path = os.path.join(work, 'export.glb')
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format='GLB', export_yup=True,
                              export_extras=True, export_normals=True, export_vertex_color='ACTIVE',
                              export_tangents=False, export_animations=False, export_skins=False,
                              export_morph=False, export_image_format='AUTO')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(work, 'plant.blend'))
    print('EXPORTED', path, 'LOD triangles', [sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objects])
    return path


# ------------------------------------------------------------------ review renders
def review_renders(objects, sid, res=440):
    """Eevee, orthographic: base colour x COLOR_0, alpha clipped at 0.5, specular scaled by openyamm_specular as the
    engine does. LOD0 front / three-quarter / side, every LOD front (no shadows for the LOD row)."""
    sc = bpy.context.scene
    for engine in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
        try:
            sc.render.engine = engine; break
        except TypeError:
            continue
    sc.view_settings.view_transform = 'Standard'; sc.render.film_transparent = True
    try:
        sc.eevee.taa_render_samples = 8
    except AttributeError:
        pass
    sc.render.resolution_x = sc.render.resolution_y = res
    world = bpy.data.worlds.new('W'); sc.world = world; world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (0.55, 0.6, 0.68, 1); bg.inputs['Strength'].default_value = 0.6
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
    sun.data.energy = 3.4; sun.data.color = (1.0, 0.96, 0.88)
    sun.rotation_euler = (math.radians(40), 0, math.radians(-35))
    for m in bpy.data.materials:
        nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
        link = bsdf.inputs['Base Color'].links
        if not link:
            continue
        tex = link[0].from_node
        attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_type = 'GEOMETRY'; attr.attribute_name = 'Color'
        mul = nt.nodes.new('ShaderNodeVectorMath'); mul.operation = 'MULTIPLY'
        nt.links.new(tex.outputs['Color'], mul.inputs[0]); nt.links.new(attr.outputs['Color'], mul.inputs[1])
        nt.links.new(mul.outputs[0], bsdf.inputs['Base Color'])
        if bsdf.inputs['Alpha'].links:
            clip = nt.nodes.new('ShaderNodeMath'); clip.operation = 'GREATER_THAN'; clip.inputs[1].default_value = 0.5
            nt.links.new(tex.outputs['Alpha'], clip.inputs[0]); nt.links.new(clip.outputs[0], bsdf.inputs['Alpha'])
        plain = nt.nodes.new('ShaderNodeBsdfPrincipled'); plain.inputs['Specular IOR Level'].default_value = 0.0
        for nm in ('Base Color', 'Alpha', 'Normal'):
            if bsdf.inputs[nm].links:
                nt.links.new(bsdf.inputs[nm].links[0].from_socket, plain.inputs[nm])
        for nm in ('Roughness', 'Metallic'):
            plain.inputs[nm].default_value = bsdf.inputs[nm].default_value
        bsdf.inputs['Specular IOR Level'].default_value = 0.5
        mix = nt.nodes.new('ShaderNodeMixShader'); mix.inputs['Fac'].default_value = m.get('openyamm_specular', 1.0)
        out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        nt.links.new(plain.outputs['BSDF'], mix.inputs[1]); nt.links.new(bsdf.outputs['BSDF'], mix.inputs[2])
        nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'
    pts = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
    H = max(p.z for p in pts)
    W = max(max(abs(p.x), abs(p.y)) for p in pts)
    cam.data.ortho_scale = max(2.15 * W, 1.12 * H)
    cam.data.clip_end = 100
    out_dir = os.path.join(REVIEW, sid, 'renders'); os.makedirs(out_dir, exist_ok=True)
    views = {'front': (0.0, 6.0), 'three_quarter': (45.0, 22.0), 'side': (90.0, 6.0), 'top': (20.0, 70.0)}
    for li, o in enumerate(objects):
        for x in objects:
            x.hide_render = x is not o
        for view, (yaw, pitch) in views.items():
            if li and view != 'front':
                continue
            d = 10.0
            cam.location = (math.sin(math.radians(yaw)) * d * math.cos(math.radians(pitch)),
                            -math.cos(math.radians(yaw)) * d * math.cos(math.radians(pitch)),
                            H * 0.5 + d * math.sin(math.radians(pitch)))
            cam.rotation_euler = (Vector((0, 0, H * 0.5)) - Vector(cam.location)).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = os.path.join(out_dir, f'lod{li}_{view}.png')
            bpy.ops.render.render(write_still=True)
    print('RENDERED', out_dir)
