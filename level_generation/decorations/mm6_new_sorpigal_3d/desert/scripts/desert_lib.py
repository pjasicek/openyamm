"""Blender-side helpers for the desert palms: a mesh builder with per-vertex shading normals and tints, primitives
(tubes, bent cards, pleated fan leaves, folded blade strips), proxy-volume sky occlusion into COLOR_0, materials and
export. Blender is Z-up (the glTF export converts to Y-up); every plant stands on z = 0 round the origin."""
import bpy, math, os, sys
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desert_common as dc

BARK, LEAVES = 0, 1
UP = Vector((0, 0, 1))


def frame(axis):
    axis = Vector(axis).normalized()
    helper = Vector((0, 0, 1)) if abs(axis.z) < 0.95 else Vector((1, 0, 0))
    a = helper.cross(axis).normalized()
    return a, axis.cross(a), axis


def rotate_toward(d, target, angle):
    """rotate unit vector d toward target by angle (radians), stopping at target"""
    d = Vector(d).normalized(); target = Vector(target).normalized()
    axis = d.cross(target)
    if axis.length < 1e-6:
        return d
    full = d.angle(target)
    return (Matrix.Rotation(min(angle, full), 3, axis.normalized()) @ d).normalized()


class MeshBuilder:
    def __init__(self):
        self.co, self.nrm, self.tint, self.faces, self.uvs, self.mats = [], [], [], [], [], []

    def v(self, co, n, tint):
        self.co.append(tuple(co)); self.nrm.append(tuple(Vector(n).normalized())); self.tint.append(tuple(tint))
        return len(self.co) - 1

    def f(self, idx, uvs, mat):
        """uvs in atlas image space (v down)"""
        self.faces.append(tuple(idx)); self.uvs.append([(u, 1.0 - v) for u, v in uvs]); self.mats.append(mat)

    def triangles(self):
        return sum(len(f) - 2 for f in self.faces)

    def to_object(self, name, materials, occlusion):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.co, [], self.faces)
        uv = me.uv_layers.new(name='UVMap')
        flat = [c for face in self.uvs for c in face]
        uv.data.foreach_set('uv', np.array(flat, np.float32).ravel())
        for p, m in zip(me.polygons, self.mats):
            p.material_index = m; p.use_smooth = True
        for m in materials:
            me.materials.append(m)
        me.normals_split_custom_set_from_vertices(self.nrm)
        colours = np.array(self.tint) * np.asarray(occlusion)[:, None]
        attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
        attr.data.foreach_set('color', np.hstack([np.clip(colours, 0, 1), np.ones((len(colours), 1))]).astype(np.float32).ravel())
        me.color_attributes.active_color = attr
        obj = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(obj)
        return obj


# ------------------------------------------------------------------------------------------------ primitives
def tube(mb, pts, radii, sides, tint, u_repeat=1.0, v_per_m=1.0, cap=False, twist=0.0, mat=BARK, uv_cell=None,
         normal_blend=None):
    """Tube along the polyline pts with ring radii; parallel-transported rings; u around, v along (metres x v_per_m).
    uv_cell maps the whole tube into one atlas cell instead (u across the cell, v from its bottom to its top).
    tint: rgb or a callable(index along) -> rgb."""
    pts = [Vector(p) for p in pts]; n = len(pts)
    tangents = []
    for i in range(n):
        d = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        tangents.append(d.normalized())
    N0, B0, _ = frame(tangents[0])
    frames = [(N0, B0)]
    for i in range(1, n):
        N = frames[-1][0]
        N = (N - tangents[i] * N.dot(tangents[i])).normalized()
        frames.append((N, tangents[i].cross(N)))
    lengths = [0.0]
    for a, b in zip(pts, pts[1:]):
        lengths.append(lengths[-1] + (b - a).length)
    total = max(lengths[-1], 1e-6)
    rings = []
    for i in range(n):
        N, B = frames[i]; ring = []
        dr = (radii[min(i + 1, n - 1)] - radii[max(i - 1, 0)]) / max(lengths[min(i + 1, n - 1)] - lengths[max(i - 1, 0)], 1e-6)
        col = tint(i) if callable(tint) else tint
        for s in range(sides):
            a = 2 * math.pi * s / sides + twist * i
            radial = N * math.cos(a) + B * math.sin(a)
            nn = (radial - tangents[i] * dr).normalized()
            if normal_blend is not None:
                nn = (nn * (1 - normal_blend[1]) + normal_blend[0](pts[i]) * normal_blend[1]).normalized()
            ring.append(mb.v(pts[i] + radial * radii[i], nn, col))
        rings.append(ring)

    def uv(s, i):
        if uv_cell:
            u0, v0, u1, v1 = uv_cell
            return (u0 + (u1 - u0) * s / sides, v1 - (v1 - v0) * lengths[i] / total)
        return (s / sides * u_repeat, -lengths[i] * v_per_m)
    for i in range(n - 1):
        for s in range(sides):
            s2 = (s + 1) % sides
            mb.f((rings[i][s], rings[i][s2], rings[i + 1][s2], rings[i + 1][s]),
                 (uv(s, i), uv(s + 1, i), uv(s + 1, i + 1), uv(s, i + 1)), mat)
    if cap:
        col = tint(n - 1) if callable(tint) else tint
        c = mb.v(pts[-1] + tangents[-1] * radii[-1] * 0.3, tangents[-1], col)
        for s in range(sides):
            s2 = (s + 1) % sides
            mb.f((rings[-1][s], rings[-1][s2], c), (uv(s, n - 1), uv(s + 1, n - 1), uv(s + 0.5, n - 1)), mat)


def cell_uv(cell, x, y):
    """cell-relative (x 0..1 right, y 0..1 down) -> atlas image uv"""
    return (cell[0] + (cell[2] - cell[0]) * x, cell[1] + (cell[3] - cell[1]) * y)


def card(mb, base, direction, roll_side, width, length, cell, segments, droop, tint, outward=None, hanging=False,
         own_weight=0.45, gravity=Vector((0, 0, -1))):
    """Foliage card from base along direction (bending toward gravity by droop radians in total), width across
    roll_side. The cell's bottom edge sits at the base (hanging: its top edge). Each segment is a quad over an
    axis-aligned sub-rectangle of the cell (cut_foliage_cards.py trims it to the texels). Shading normals blend
    the card's own normal (turned toward outward) with outward."""
    d = Vector(direction).normalized(); side = Vector(roll_side)
    side = (side - d * side.dot(d)).normalized()
    spine, sides = [Vector(base)], []
    step = length / segments
    for k in range(segments + 1):
        sides.append((side - d * side.dot(d)).normalized())
        if k < segments:
            spine.append(spine[-1] + d * step)
            d = rotate_toward(d, gravity, droop / segments)
    rows = []
    for k, (p, sd) in enumerate(zip(spine, sides)):
        frac = k / segments
        nxt = (spine[min(k + 1, segments)] - spine[max(k - 1, 0)]).normalized()
        own = sd.cross(nxt).normalized()
        o = outward(p) if outward else own
        if own.dot(o) < 0:
            own = -own
        nrm = (own * own_weight + o * (1 - own_weight)).normalized()
        y = frac if hanging else 1.0 - frac
        rows.append(((mb.v(p - sd * width * 0.5, nrm, tint), cell_uv(cell, 0.0, y)),
                     (mb.v(p + sd * width * 0.5, nrm, tint), cell_uv(cell, 1.0, y))))
    for k in range(segments):
        (a, ua), (b, ub) = rows[k]; (c, uc), (e, ue) = rows[k + 1]
        mb.f((a, b, e, c), (ua, ub, ue, uc), LEAVES)
    return spine


def fan(mb, centre, forward, normal, radius, rays, rings, cell, tint, span=math.radians(128), pleat=0.05,
        droop=0.25, sag=0.15, outward=None, own_weight=0.6):
    """Pleated fan leaf: rays from the petiole tip over +-span about forward, in the plane with the given normal;
    alternate rays lifted/lowered (pleats), the outer part bent back along -normal (droop) and down (sag).
    UVs map polar coordinates into the cell (texture fan painted with its petiole at the bottom)."""
    f = Vector(forward).normalized(); n = Vector(normal); n = (n - f * n.dot(f)).normalized(); side = n.cross(f)
    ring_ids = []
    centre_v = None
    for ri, rr in enumerate(rings):
        if rr == 0:
            o = outward(Vector(centre)) if outward else n
            nn = n if n.dot(o) >= 0 else -n
            centre_v = (mb.v(centre, (nn * own_weight + o * (1 - own_weight)), tint), cell_uv(cell, 0.5, 0.5))
            ring_ids.append(None); continue
        ids = []
        for k in range(rays):
            phi = -span + 2 * span * k / (rays - 1)
            lift = pleat * rr * (1 if k % 2 else -1) if 0 < k < rays - 1 else 0.0
            p = Vector(centre) + (f * math.cos(phi) + side * math.sin(phi)) * radius * rr
            p += n * (lift - droop * rr * rr) * radius
            p.z -= sag * rr * rr * radius
            tilt = (side * math.cos(phi) - f * math.sin(phi)) * (0.35 if k % 2 else -0.35) if 0 < k < rays - 1 else Vector()
            own = (n + tilt).normalized()
            o = outward(p) if outward else own
            if own.dot(o) < 0:
                own = -own
            nn = (own * own_weight + o * (1 - own_weight)).normalized()
            uv = cell_uv(cell, 0.5 + math.sin(phi) * rr * 0.5, 0.5 - math.cos(phi) * rr * 0.5)
            ids.append((mb.v(p, nn, tint), uv))
        ring_ids.append(ids)
    for ri in range(1, len(rings)):
        inner, outer = ring_ids[ri - 1], ring_ids[ri]
        for k in range(rays - 1):
            if inner is None:
                (c, uc) = centre_v; (a, ua), (b, ub) = outer[k], outer[k + 1]
                mb.f((c, a, b), (uc, ua, ub), LEAVES)
            else:
                (a, ua), (b, ub) = inner[k], inner[k + 1]; (c, uc), (e, ue) = outer[k], outer[k + 1]
                mb.f((a, c, e, b), (ua, uc, ue, ub), LEAVES)


def blade(mb, spine, widths, ups, cell, tint, fold=0.3, across=3, outward=None, own_weight=0.6, mat=LEAVES):
    """Leaf strip along spine (widths: half-widths; ups: blade surface normals), 'across' vertices per row
    (3: edges + midrib, folded by fold x width along up; 5: also curls the edges down; 2: flat).
    A zero width at the end becomes a single tip vertex. The texture spans the cell width at every row."""
    n = len(spine)
    lengths = [0.0]
    for a, b in zip(spine, spine[1:]):
        lengths.append(lengths[-1] + (Vector(b) - Vector(a)).length)
    total = max(lengths[-1], 1e-6)
    rows = []
    for i in range(n):
        p = Vector(spine[i]); t = (Vector(spine[min(i + 1, n - 1)]) - Vector(spine[max(i - 1, 0)])).normalized()
        up = Vector(ups[i]); up = (up - t * up.dot(t)).normalized(); side = t.cross(up)
        w = widths[i]; y = 1.0 - lengths[i] / total
        o = outward(p) if outward else up
        if w <= 1e-6:
            nn = up if up.dot(o) >= 0 else -up
            rows.append([(mb.v(p, nn * own_weight + o * (1 - own_weight), tint), cell_uv(cell, 0.5, y))])
            continue
        if across == 2:
            offs = [(-1, 0.0), (1, 0.0)]
        elif across == 3:
            offs = [(-1, 0.0), (0, fold), (1, 0.0)]
        else:
            offs = [(-1, -fold * 0.6), (-0.5, fold * 0.6), (0, fold), (0.5, fold * 0.6), (1, -fold * 0.6)]
        row = []
        for s, lift in offs:
            q = p + side * s * w + up * lift * w
            slope = -fold * (1 if s > 0 else -1 if s < 0 else 0)
            own = (up + side * slope * 0.8).normalized()
            if own.dot(o) < 0:
                own = -own
            row.append((mb.v(q, own * own_weight + o * (1 - own_weight), tint), cell_uv(cell, 0.5 + s * 0.5, y)))
        rows.append(row)
    for i in range(n - 1):
        a, b = rows[i], rows[i + 1]
        if len(b) == 1:
            for k in range(len(a) - 1):
                mb.f((a[k][0], a[k + 1][0], b[0][0]), (a[k][1], a[k + 1][1], b[0][1]), mat)
        else:
            for k in range(len(a) - 1):
                mb.f((a[k][0], a[k + 1][0], b[k + 1][0], b[k][0]), (a[k][1], a[k + 1][1], b[k + 1][1], b[k][1]), mat)


# ------------------------------------------------------------------------------------------------ occlusion
def hemisphere(count, seed):
    rng = np.random.default_rng(seed)
    d = rng.normal(size=(count * 3, 3)); d /= np.linalg.norm(d, axis=1, keepdims=True)
    return d[:count * 2]


def proxy_occlusion(co, nrm, spheres, rays=40, seed=11, ground=0.75, up_bias=0.8):
    """Sky visibility per vertex: rays over the hemisphere about normalize(normal + up_bias x up), each attenuated by
    exp(-density x chord) through every proxy sphere (centre, radius, density); rays below the horizon count as
    blocked by the ground (ground = how much). Returns visibility 0..1."""
    co = np.asarray(co); nrm = np.asarray(nrm)
    dirs = hemisphere(rays, seed)
    axis = nrm + np.array([0, 0, up_bias]); axis /= np.maximum(np.linalg.norm(axis, axis=1, keepdims=True), 1e-6)
    vis = np.zeros(len(co))
    if spheres:
        C = np.array([s[0] for s in spheres]); R = np.array([s[1] for s in spheres]); D = np.array([s[2] for s in spheres])
    for d in dirs:
        dd = np.where((axis @ d < 0)[:, None], -d, d)              # (V, 3) flipped into each vertex's hemisphere
        w = np.ones(len(co))
        if spheres:
            oc = co[:, None, :] - C[None]                           # (V, S, 3)
            b = np.einsum('vsk,vk->vs', oc, dd)
            c = np.einsum('vsk,vsk->vs', oc, oc) - R[None] ** 2
            disc = b * b - c
            sq = np.sqrt(np.maximum(disc, 0))
            t0 = np.maximum(-b - sq, 0); t1 = np.maximum(-b + sq, 0)
            chord = np.where(disc > 0, t1 - t0, 0)
            w *= np.exp(-(chord * D[None]).sum(1))
        below = dd[:, 2] < 0
        w = np.where(below, w * (1 - ground * np.clip(-dd[:, 2] * 3, 0, 1)), w)
        vis += w
    return vis / len(dirs)


# ------------------------------------------------------------------------------------------------ materials
def load_image(path, colorspace):
    img = bpy.data.images.load(path, check_existing=True); img.colorspace_settings.name = colorspace
    return img


def material(name, base_path, normal_path, wind, leaves, roughness):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tb = nt.nodes.new('ShaderNodeTexImage'); tb.image = load_image(base_path, 'sRGB')
    nt.links.new(tb.outputs['Color'], bsdf.inputs['Base Color'])
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = load_image(normal_path, 'Non-Color')
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = roughness; bsdf.inputs['Metallic'].default_value = 0.0
    m['openyamm_wind'] = wind
    if leaves:
        nt.links.new(tb.outputs['Alpha'], bsdf.inputs['Alpha'])
        m.use_backface_culling = False; m.surface_render_method = 'DITHERED'
        m['openyamm_specular'] = dc.SPECULAR; m['openyamm_translucency'] = dc.TRANSLUCENCY
    else:
        m.use_backface_culling = True
    return m


def materials(sid, wind):
    _, _, _, atlas, bark = dc.MODELS_SPEC[sid]
    b = material('Bark', os.path.join(dc.TEX, f'{bark}_basecolor.png'), os.path.join(dc.TEX, f'{bark}_normal.png'),
                 wind, False, 0.95)
    l = material('Leaves', os.path.join(dc.TEX, f'{atlas}_basecolor.png'), os.path.join(dc.TEX, f'{atlas}_normal.png'),
                 wind, True, 0.8)
    return [b, l]


def srgb_to_linear(c):
    c = np.asarray(c, np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
