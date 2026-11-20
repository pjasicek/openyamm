"""Blender helpers for the MM6 succulents: a small geometry accumulator (positions, faces with per-loop texture
coordinates and normals, per-vertex occlusion), ribbed sweeps for cactus columns and barrels, bulged prickly-pear
pads, foliage cards, ray-traced vertex occlusion into the 'Color' attribute (glTF COLOR_0), materials from
succulents/textures and the LOD export. Blender is Z-up (the glTF export converts to Y-up); every model is built
round its base centre on the ground (z = 0). Texture coordinates are given in image space (v down) and flipped on
output."""
import bpy, math, os
import numpy as np
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, 'textures')
WORK = os.path.join(ROOT, 'work')


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def frame(axis):
    axis = Vector(axis).normalized()
    helper = Vector((0, 0, 1)) if abs(axis.z) < 0.95 else Vector((1, 0, 0))
    a = helper.cross(axis).normalized()
    return a, axis.cross(a), axis


class Geo:
    """Mesh accumulator. Loop normals: None = smooth vertex normal, 'flat' = the face normal, or a Vector."""

    def __init__(self):
        self.v, self.occ, self.faces, self.uvs, self.norms, self.mats, self.solid = [], [], [], [], [], [], []
        self.proxy = []              # extra occluder triangles (cards and pads occlude through these)
        self.ao_normal = {}          # vertex -> normal used for its occlusion hemisphere

    def vert(self, p, occ=1.0):
        self.v.append(Vector(p)); self.occ.append(occ)
        return len(self.v) - 1

    def face(self, idx, uvs, normals=None, mat=0, solid=True):
        self.faces.append(tuple(idx)); self.uvs.append([(u, 1.0 - v) for u, v in uvs])
        self.norms.append(normals if normals is not None else [None] * len(idx))
        self.mats.append(mat); self.solid.append(solid)

    def triangles(self):
        return sum(len(f) - 2 for f in self.faces)

    # -------------------------------------------------------------- normals
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
        return out, vn

    # -------------------------------------------------------------- occlusion
    def occlusion(self, rays=40, distance=0.5, strength=0.8, floor=True, seed=3, extra_bvh=None):
        """Per-vertex hemisphere occlusion against the solid faces, the proxies and the ground plane; multiplies the
        analytic occlusion already stored per vertex."""
        loops, vn = self.loop_normals()
        tris = []
        for f, s in zip(self.faces, self.solid):
            if s:
                for k in range(1, len(f) - 1):
                    tris.append((f[0], f[k], f[k + 1]))
        verts = [tuple(p) for p in self.v]
        for tri in self.proxy:
            base = len(verts); verts += [tuple(p) for p in tri]; tris.append((base, base + 1, base + 2))
        bvh = BVHTree.FromPolygons(verts, tris, epsilon=0.0) if tris else None
        rng = np.random.default_rng(seed)
        dirs = rng.normal(size=(rays, 3)); dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
        dirs = [Vector(d) for d in dirs]
        for i, p in enumerate(self.v):
            n = self.ao_normal.get(i, vn[i])
            origin = p + n * 0.004
            hit = 0
            for d in dirs:
                if d.dot(n) < 0:
                    d = -d
                if floor and d.z < 0 and origin.z + d.z * distance < 0:
                    hit += 1; continue
                if bvh is not None and bvh.ray_cast(origin, d, distance)[0] is not None:
                    hit += 1; continue
                if extra_bvh is not None and extra_bvh.ray_cast(origin, d, distance)[0] is not None:
                    hit += 1
            self.occ[i] *= 1.0 - strength * hit / rays

    def bvh(self):
        tris = []
        for f, s in zip(self.faces, self.solid):
            if s:
                for k in range(1, len(f) - 1):
                    tris.append((f[0], f[k], f[k + 1]))
        verts = [tuple(p) for p in self.v]
        for tri in self.proxy:
            base = len(verts); verts += [tuple(p) for p in tri]; tris.append((base, base + 1, base + 2))
        return BVHTree.FromPolygons(verts, tris, epsilon=0.0)

    # -------------------------------------------------------------- output
    def to_object(self, name, materials):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(p) for p in self.v], [], self.faces)
        me.validate(clean_customdata=False)
        uv = me.uv_layers.new(name='UVMap')
        flat_uv = [c for f in self.uvs for uvp in f for c in uvp]
        uv.data.foreach_set('uv', flat_uv)
        for m in materials:
            me.materials.append(m)
        me.polygons.foreach_set('material_index', self.mats)
        me.polygons.foreach_set('use_smooth', [True] * len(self.faces))
        loops, _ = self.loop_normals()
        me.normals_split_custom_set([tuple(n) for n in loops])
        attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
        attr.data.foreach_set('color', [x for o in self.occ for x in (o, o, o, 1.0)])
        me.color_attributes.active_color = attr
        obj = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(obj)
        return obj


# ------------------------------------------------------------------ builders
def transport_frames(centres):
    """Rotation-minimising frames along a polyline: (tangent, side, other) per point."""
    n = len(centres)
    tangents = []
    for i in range(n):
        a = centres[max(i - 1, 0)]; b = centres[min(i + 1, n - 1)]
        t = (b - a); tangents.append(t.normalized() if t.length > 1e-9 else Vector((0, 0, 1)))
    side, _, _ = frame(tangents[0])
    frames = []
    for i, t in enumerate(tangents):
        if i:
            q = tangents[i - 1].rotation_difference(t); side = q @ side
            side = (side - t * side.dot(t)).normalized()
        frames.append((t, side, t.cross(side)))
    return frames


def ribbed(g, centres, radii, ribs, depth, vpr, v_scale, mat=0, phase=0.0, twist=0.0, occ=None, u_rib=1.0,
           crest_round=0.35, apex=True, solid=True, normal_fn=None, rib_v=None):
    """Ribbed sweep along `centres` (Vectors) with ring radii `radii` (the last may be 0: apex). vpr = vertices per
    rib: 1 (crest only, rounded polygon), 2 (valley, crest) or 4 (valley, flank, crest, flank). u repeats once per
    rib (valley at whole numbers), v = surface length x v_scale. Valleys are creased (face normals); returns the
    per-ring crest data [(position, outward normal)] per rib for spine placement."""
    centres = [Vector(c) for c in centres]
    if apex and radii[-1] <= 1e-6:
        ring_count = len(centres) - 1
    else:
        ring_count = len(centres)
    frames = transport_frames(centres)
    prof = {1: [1.0], 2: [1.0 - depth, 1.0], 4: [1.0 - depth, 1.0 - depth * crest_round, 1.0, 1.0 - depth * crest_round]}[vpr]
    ustep = {1: [0.5], 2: [0.0, 0.5], 4: [0.0, 0.25, 0.5, 0.75]}[vpr]
    N = ribs * vpr
    rings, vcoord, crest = [], [], []
    length = 0.0
    for i in range(ring_count):
        if i:
            length += math.hypot((centres[i] - centres[i - 1]).length, radii[i] - radii[i - 1])
        vcoord.append(length * v_scale)
        t, a, b = frames[i]
        ring = []; crest.append([])
        for k in range(ribs):
            for j in range(vpr):
                ang = phase + twist * i + 2 * math.pi * (k + ustep[j]) / ribs
                d = a * math.cos(ang) + b * math.sin(ang)
                p = centres[i] + d * radii[i] * prof[j]
                o = occ(p, i, j == 0 and vpr > 1) if occ else 1.0
                ring.append(g.vert(p, o))
                if ustep[j] == 0.5:
                    crest[-1].append((p, d))
        rings.append(ring)
    uvals = [(k + ustep[j]) * u_rib for k in range(ribs) for j in range(vpr)]
    valley = [vpr > 1 and j == 0 for k in range(ribs) for j in range(vpr)]
    for i in range(ring_count - 1):
        for s in range(N):
            s2 = (s + 1) % N
            u0, u1 = uvals[s], (uvals[s2] if s2 else ribs * u_rib)
            idx = (rings[i][s], rings[i][s2], rings[i + 1][s2], rings[i + 1][s])
            dv = rib_v[s // vpr] if rib_v is not None and vpr > 1 else 0.0       # per-rib texture offset
            uv = [(u0, vcoord[i] + dv), (u1, vcoord[i] + dv), (u1, vcoord[i + 1] + dv), (u0, vcoord[i + 1] + dv)]
            nrm = ['flat' if valley[x] else None for x in (s, s2, s2, s)]
            if normal_fn is not None:
                nrm = [normal_fn(g.v[x]) for x in idx]
            g.face(idx, uv, nrm, mat, solid)
    if apex and radii[-1] <= 1e-6:
        top = centres[-1]
        length += math.hypot((top - centres[ring_count - 1]).length, radii[ring_count - 1])
        tip = g.vert(top, occ(top, ring_count, False) if occ else 1.0)
        g.ao_normal[tip] = frames[-1][0]
        for s in range(N):
            s2 = (s + 1) % N
            u0, u1 = uvals[s], (uvals[s2] if s2 else ribs * u_rib)
            dv = rib_v[s // vpr] if rib_v is not None and vpr > 1 else 0.0
            g.face((rings[-1][s], rings[-1][s2], tip), [(u0, vcoord[-1] + dv), (u1, vcoord[-1] + dv), ((u0 + u1) / 2, length * v_scale + dv)],
                   ['flat' if valley[s] else None, 'flat' if valley[s2] else None, frames[-1][0]]
                   if normal_fn is None else [normal_fn(g.v[x]) for x in (rings[-1][s], rings[-1][s2], tip)], mat, solid)
    return crest


def card(g, base, right, up, uv_rect, normal_fn, occ_fn, mat=0):
    """Quad from base - right/2 .. base + right/2 + up; uv_rect = (u0, v0, u1, v1) image space with v0 at the top."""
    pts = [base - right * 0.5, base + right * 0.5, base + right * 0.5 + up, base - right * 0.5 + up]
    u0, v0, u1, v1 = uv_rect
    uvs = [(u0, v1), (u1, v1), (u1, v0), (u0, v0)]
    nrm = [normal_fn(p) for p in pts]
    if sum(nrm, Vector((0, 0, 0))).dot(right.cross(up)) < 0:      # wind toward the shading side
        pts, uvs, nrm = pts[::-1], uvs[::-1], nrm[::-1]
    idx = [g.vert(p, occ_fn(p)) for p in pts]
    for i, n in zip(idx, nrm):
        g.ao_normal[i] = n
    g.face(idx, uvs, nrm, mat, solid=False)


PAD_GRIDS = {4: [-1.0, -1 / 3, 1 / 3, 1.0], 3: [-1.0, 0.0, 1.0], 2: [-1.0, 1.0]}


def pad(g, attach, up, normal, width, height, cell, oval, grid, bulge, mat=0, occ_fn=None, tilt_normals=0.6):
    """Prickly-pear pad: a cell-sized quad grid whose texture oval (cell-local semi-axes oval = (rx, ry) round
    (0.5, 0.52)) has the physical size width x height, the oval's lowest point at `attach`. grid 4/3: both faces
    bulged (lens), grid 2: one flat double-sided quad. Shading normals lean out toward the rim; an oval proxy
    occludes for the vertex occlusion."""
    up = Vector(up).normalized(); normal = Vector(normal); normal = (normal - up * normal.dot(up)).normalized()
    right = up.cross(normal).normalized()
    rx, ry = oval
    qw, qh = width / (2 * rx), height / (2 * ry)                  # quad size
    centre = attach + up * (height * 0.5)                          # oval centre
    qcentre = centre + up * (qh * (0.52 - 0.5))                    # oval centre sits 0.02 cell below quad centre
    cu, cv = (cell % 2) * 0.5, (cell // 2) * 0.5
    coords = PAD_GRIDS[grid]

    def point(s, t, side):
        p = qcentre + right * (s * qw * 0.5) + up * (-t * qh * 0.5)
        lx = (s * qw * 0.5) / (width * 0.5); ly = (-t * qh * 0.5 + (qcentre - centre).dot(up)) / (height * 0.5)
        rr = min(lx * lx + ly * ly, 1.0)
        b = bulge * (1 - rr) if grid > 2 else 0.0
        return p + normal * b * side, lx, ly

    def uv(s, t):
        return (cu + (s + 1) * 0.25, cv + (t + 1) * 0.25)
    sides = (1, -1) if grid > 2 else (1,)
    for side in sides:
        idx = {}
        for a, s in enumerate(coords):
            for b, t in enumerate(coords):
                edge = a in (0, len(coords) - 1) or b in (0, len(coords) - 1)
                p, lx, ly = point(s, t, side)
                if edge and side < 0:
                    # the rim lies in the transparent margin: the back face gets its own rim vertices, 0.5 mm
                    # behind, so no tool pairs a front and a back triangle across it into one card
                    p = p - normal * 0.0005
                o = occ_fn(p) if occ_fn else 1.0
                i = g.vert(p, o); idx[(a, b)] = i
                g.ao_normal[i] = normal * side
        n = len(coords)
        for a in range(n - 1):
            for b in range(n - 1):
                quad = [(a, b), (a + 1, b), (a + 1, b + 1), (a, b + 1)]
                if side > 0:
                    quad = quad[::-1]           # wind each face toward its own side
                nrm = []
                for (qa, qb) in quad:
                    s, t = coords[qa], coords[qb]
                    _, lx, ly = point(s, t, side)
                    radial = right * lx + up * ly
                    nrm.append((normal * side + radial * tilt_normals * min(math.hypot(lx, ly), 1.2)).normalized())
                g.face([idx[q] for q in quad], [uv(coords[qa], coords[qb]) for qa, qb in quad], nrm, mat, solid=False)
    # oval proxy for occlusion
    ring = [centre + right * math.cos(t) * width * 0.48 + up * math.sin(t) * height * 0.48
            for t in np.linspace(0, 2 * math.pi, 11)[:-1]]
    for k in range(len(ring)):
        g.proxy.append((centre, ring[k], ring[(k + 1) % len(ring)]))
    return centre, right


def ellipsoid(g, centre, axis, radius, length, segments, rings, uv_rect, mat=0, occ_fn=None):
    """Small closed ellipsoid (fruit) round `axis`: lat-long mapped into uv_rect."""
    a, b, n = frame(axis)
    u0, v0, u1, v1 = uv_rect
    grid = []
    for r in range(rings + 1):
        th = math.pi * r / rings
        row = []
        for s in range(segments):
            ph = 2 * math.pi * s / segments
            p = centre + n * (-math.cos(th) * length) + (a * math.cos(ph) + b * math.sin(ph)) * math.sin(th) * radius
            row.append(g.vert(p, occ_fn(p) if occ_fn else 1.0))
            if r in (0, rings):
                break
        grid.append(row)
    for r in range(rings):
        for s in range(segments):
            s2 = (s + 1) % segments
            uva = lambda ss, rr: (u0 + (u1 - u0) * ss / segments, v0 + (v1 - v0) * rr / rings)
            if r == 0:
                g.face([grid[0][0], grid[1][s2], grid[1][s]], [uva(s + 0.5, 0), uva(s + 1, 1), uva(s, 1)], None, mat)
            elif r == rings - 1:
                g.face([grid[r][s], grid[r][s2], grid[r + 1][0]], [uva(s, r), uva(s + 1, r), uva(s + 0.5, r + 1)], None, mat)
            else:
                g.face([grid[r][s], grid[r][s2], grid[r + 1][s2], grid[r + 1][s]],
                       [uva(s, r), uva(s + 1, r), uva(s + 1, r + 1), uva(s, r + 1)], None, mat)


# ------------------------------------------------------------------ materials
_images = {}


def image(name, colorspace):
    key = (name, colorspace)
    if key not in _images:
        img = bpy.data.images.load(os.path.join(TEX, name)); img.colorspace_settings.name = colorspace
        _images[key] = img
    return _images[key]


def material(name, texture, cutout=False, roughness=0.6, extras=None, extension='REPEAT'):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tb = nt.nodes.new('ShaderNodeTexImage'); tb.image = image(f'{texture}_basecolor.png', 'sRGB'); tb.extension = extension
    nt.links.new(tb.outputs['Color'], bsdf.inputs['Base Color'])
    if cutout:
        nt.links.new(tb.outputs['Alpha'], bsdf.inputs['Alpha'])
        m.surface_render_method = 'DITHERED'; m.use_backface_culling = False
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = image(f'{texture}_normal.png', 'Non-Color'); tn.extension = extension
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = roughness; bsdf.inputs['Metallic'].default_value = 0.0
    for k, v in (extras or {}).items():
        m[k] = v
    return m


def export(objects, name):
    os.makedirs(WORK, exist_ok=True)
    for o in bpy.data.objects:
        o.select_set(o in objects)
    bpy.context.view_layer.objects.active = objects[0]
    path = os.path.join(WORK, f'{name}_export.glb')
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_format='GLB', export_yup=True,
                              export_extras=True, export_normals=True, export_vertex_color='ACTIVE',
                              export_tangents=False, export_animations=False, export_skins=False,
                              export_morph=False, export_image_format='AUTO')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f'{name}.blend'))
    print('EXPORTED', path, 'LOD triangles', [sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objects])
    return path
