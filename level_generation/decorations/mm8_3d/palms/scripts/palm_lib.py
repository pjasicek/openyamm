"""Blender-side helpers for the MM8 palms, adapted from ../../mm6_new_sorpigal_3d/desert/scripts/desert_lib.py: a mesh
builder with per-vertex shading normals and tints, tubes, the pinnate frond strip, proxy-volume sky occlusion into
COLOR_0, materials. Blender is Z-up (the glTF export converts to Y-up); every palm stands on z = 0 at the origin."""
import bpy, json, math, os, sys
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palm_common as pc

BARK, LEAVES = 0, 1
UP = Vector((0, 0, 1))
DOWN = Vector((0, 0, -1))
ENV = json.load(open(pc.ENV))


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
        self.base, self.current_base = [], None     # each vertex's undarkened tint (for the darkening floor)

    def v(self, co, n, tint):
        self.co.append(tuple(co)); self.nrm.append(tuple(Vector(n).normalized())); self.tint.append(tuple(tint))
        self.base.append(tuple(self.current_base) if self.current_base is not None else tuple(tint))
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
def tube(mb, pts, radii, sides, tint, u_repeat=1.0, v_per_m=1.0, cap=False, mat=BARK, uv_cell=None, u_inset=0.0):
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
        for s in range(sides + 1):                      # a seam column: u runs 0..1 round the tube
            a = 2 * math.pi * s / sides
            radial = N * math.cos(a) + B * math.sin(a)
            nn = (radial - tangents[i] * dr).normalized()
            ring.append(mb.v(pts[i] + radial * radii[i], nn, col))
        rings.append(ring)

    def uv(s, i):
        if uv_cell:
            u0, v0, u1, v1 = uv_cell
            return (u0 + (u1 - u0) * s / sides, v1 - (v1 - v0) * lengths[i] / total)
        return (u_inset + (1 - 2 * u_inset) * s / sides * u_repeat, -lengths[i] * v_per_m)
    for i in range(n - 1):
        for s in range(sides):
            mb.f((rings[i][s], rings[i][s + 1], rings[i + 1][s + 1], rings[i + 1][s]),
                 (uv(s, i), uv(s + 1, i), uv(s + 1, i + 1), uv(s, i + 1)), mat)
    if cap:
        col = tint(n - 1) if callable(tint) else tint
        c = mb.v(pts[-1] + tangents[-1] * radii[-1] * 0.3, tangents[-1], col)
        for s in range(sides):
            mb.f((rings[-1][s], rings[-1][s + 1], c), (uv(s, n - 1), uv(s + 1, n - 1), uv(s + 0.5, n - 1)), mat)


def cell_uv(cell, x, y):
    """cell-relative (x 0..1 right, y 0..1 down) -> atlas image uv"""
    return (cell[0] + (cell[2] - cell[0]) * x, cell[1] + (cell[3] - cell[1]) * y)


def spine(start, direction, length, bends, steps=48):
    """fine polyline from start along direction; bends(u, d) -> new direction after a step at fraction u"""
    pts = [Vector(start)]; d = Vector(direction).normalized(); dirs = [d]
    for k in range(steps):
        pts.append(pts[-1] + d * length / steps)
        d = bends((k + 0.5) / steps, d)
        dirs.append(d)
    return pts, dirs


def resample(pts, n):
    """n points evenly spaced by arc length along the polyline pts"""
    seg = [(b - a).length for a, b in zip(pts, pts[1:])]
    cum = np.concatenate([[0], np.cumsum(seg)]); total = cum[-1]
    out = []
    for k in range(n):
        s = total * k / (n - 1)
        i = min(int(np.searchsorted(cum, s, side='right')) - 1, len(seg) - 1)
        f = (s - cum[i]) / max(seg[i], 1e-9)
        out.append(pts[i].lerp(pts[i + 1], min(max(f, 0.0), 1.0)))
    return out


def env_at(cell_name, t0, t1):
    """painted leaflet reach (fraction of the cell half-width) over the rachis span t0..t1 (max)"""
    env = ENV[cell_name]
    k0 = max(0, int(math.floor(min(t0, t1) * 128))); k1 = min(128, int(math.ceil(max(t0, t1) * 128)))
    return max(env[k0:k1 + 1])


def frond(mb, rachis, side0, width, cell_name, tint, hang_in, hang_out, roll=0.0, across=5, outward=None,
          own_weight=0.65, grow=1.0, mat=LEAVES, edge_shade=1.0, sun=None):
    """Pinnate frond strip along the rachis points (base -> tip). At every row the leaflets leave the rachis on both
    sides: across 5 = rachis, mid and edge on each side, the inner half sloping hang_in(t) and the outer half
    hang_out(t) radians below the frond's own side plane (the leaflets arch down: a curved inverted V); across 3 =
    one straight slope (the mean). The half-width follows the painted reach of the cell (ENV), and the texture maps
    by that reach, so geometry hugs the texels. side0: the horizontal side direction of the frond; roll(t) radians
    twists the frond about its rachis. edge_shade scales the tint at the hanging leaflet tips (1 at the rachis, the
    mean of both at mid-leaflet): the shade under the frond's own arch. sun = (top rgb, under rgb): tint multipliers
    for leaflet surfaces facing the sky and those hanging or facing down (by the surface normal's z), the sunlit
    yellow-green tops against darker undersides of the sprites."""
    cell = pc.ATLAS[cell_name]
    n = len(rachis)
    rows = []
    for i in range(n):
        t = i / (n - 1)
        p = Vector(rachis[i])
        T = (Vector(rachis[min(i + 1, n - 1)]) - Vector(rachis[max(i - 1, 0)])).normalized()
        S = Vector(side0); S = (S - T * S.dot(T)).normalized()
        r = roll(t) if callable(roll) else roll
        S = Matrix.Rotation(r, 3, T) @ S
        U = T.cross(S).normalized()                           # upper surface (S stays on one side: no flips)
        span = 0.5 / (n - 1)
        e = env_at(cell_name, t - span, t + span)
        w = width * e * grow
        o = outward(p) if outward else U
        hi, ho = hang_in(t), hang_out(t)
        row = []
        if across == 5:
            offs = [(-1.0, -1), (-0.5, -1), (0.0, 0), (0.5, 1), (1.0, 1)]
        else:
            offs = [(-1.0, -1), (0.0, 0), (1.0, 1)]
        for s, sd in offs:
            if sd == 0:
                q = p; own = U
            else:
                Si = S * sd
                if across == 5:
                    d_in = Si * math.cos(hi) - U * math.sin(hi)
                    d_out = Si * math.cos(ho) - U * math.sin(ho)
                    q = p + d_in * w * 0.5 if abs(s) < 0.75 else p + d_in * w * 0.5 + d_out * w * 0.5
                    dd = d_in if abs(s) < 0.75 else (d_in + d_out).normalized()
                else:
                    hm = 0.5 * (hi + ho)
                    dd = Si * math.cos(hm) - U * math.sin(hm)
                    q = p + dd * w * math.cos(0.5 * (ho - hi))
                own = dd.cross(T).normalized()
                if own.dot(U) < 0:
                    own = -own
            upz = own.z
            if own.dot(o) < -0.2:
                own = -own
            nn = (own * own_weight + o * (1 - own_weight)).normalized()
            shade = np.full(3, 1.0 + (edge_shade - 1.0) * abs(s) ** 1.3)
            if sun is not None:
                f = min(max((upz - 0.15) / 0.7, 0.0), 1.0); f = f * f * (3 - 2 * f)
                shade = shade * (np.asarray(sun[1]) + (np.asarray(sun[0]) - np.asarray(sun[1])) * f)
            row.append((mb.v(q, nn, tuple(np.asarray(tint) * shade)), cell_uv(cell, 0.5 + 0.5 * s * e, 1.0 - t)))
        rows.append(row)
    for i in range(n - 1):
        a, b = rows[i], rows[i + 1]
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
        dd = np.where((axis @ d < 0)[:, None], -d, d)
        w = np.ones(len(co))
        if spheres:
            oc = co[:, None, :] - C[None]
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


def material(name, base_path, normal_path, wind, leaves, roughness, specular=None):
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
        m['openyamm_specular'] = pc.SPECULAR if specular is None else specular
        m['openyamm_translucency'] = pc.TRANSLUCENCY
    else:
        m.use_backface_culling = True
    return m


def materials(sid, wind):
    bark = pc.SPECIES[sid]['bark']
    b = material('Bark', os.path.join(pc.TEX, f'{bark}_basecolor.png'), os.path.join(pc.TEX, f'{bark}_normal.png'),
                 wind, False, 0.95)
    l = material('Leaves', os.path.join(pc.TEX, 'tropical_basecolor.png'), os.path.join(pc.TEX, 'tropical_normal.png'),
                 wind, True, pc.LEAF_ROUGHNESS, pc.SPECIES[sid].get('specular', pc.SPECULAR))
    return [b, l]
