"""Closed low-poly organic components and a procedurally painted texture atlas for small ground items.

Every component is a closed solid with its own UVs mapped into one cell of a 4x4 atlas (512 px, 128 px per cell,
4 px gutters; a cell may span several grid units). Cells are painted with numpy: base colour, a height field that
becomes an OpenGL tangent-space normal map, roughness and binary metalness. One single-sided material per model.
"""
import math

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

ATLAS = 512
GRID = 4
GUTTER = 4


class Builder:
    def __init__(self, name):
        self.name = name
        self.vertices = []
        self.faces = []
        self.uvs = []
        self.cells = {}

    # ---- atlas -------------------------------------------------------------------------------------------------
    def cell(self, key, rect, painter, **params):
        """Reserve atlas cell `key` at rect (gx, gy, gw, gh) in grid units, painted by painter(u, v, **params)."""
        self.cells[key] = (rect, painter, params)

    def cell_uv(self, key, u, v):
        (gx, gy, gw, gh), _, _ = self.cells[key]
        size = ATLAS / GRID
        x0, y0 = gx * size + GUTTER, gy * size + GUTTER
        w, h = gw * size - 2 * GUTTER, gh * size - 2 * GUTTER
        u = min(1.0, max(0.0, u))
        v = min(1.0, max(0.0, v))
        # Image row 0 is the top; glTF/Blender UV v=0 is the bottom.
        return ((x0 + u * w) / ATLAS, 1 - (y0 + (1 - v) * h) / ATLAS)

    # ---- geometry ----------------------------------------------------------------------------------------------
    def add(self, vertices, faces, uvs, key):
        offset = len(self.vertices)
        self.vertices.extend(Vector(v) for v in vertices)
        for face in faces:
            self.faces.append(tuple(i + offset for i in face))
            self.uvs.append([self.cell_uv(key, *uvs[i]) for i in face])

    def blade(self, key, base, direction, side, length, width, thickness, rings=6, ring=6, cup=0.0, bend=0.0,
              profile=None, twist=0.0):
        """Closed leaf/petal/feather: elliptical cross-sections along a (bent) spine, pointed tip.
        profile(t) -> relative width; cup lifts the edges towards `normal`; bend curls the spine towards `normal`."""
        direction = Vector(direction).normalized()
        side = Vector(side)
        side = (side - direction * side.dot(direction)).normalized()
        normal = direction.cross(side).normalized()
        profile = profile or (lambda t: math.sin(math.pi * min(1.0, 0.08 + 0.92 * t)) ** 0.75)
        vertices, uvs, faces = [], [], []
        point = Vector(base)
        heading = direction.copy()
        step = length / rings
        stations = []
        for i in range(rings + 1):
            t = i / rings
            stations.append((point.copy(), heading.copy(), t))
            heading = (heading + normal * bend * step * 2).normalized()
            point = point + heading * step
        tip = stations[-1][0]
        for centre, heading, t in stations[:-1]:
            angle = twist * t
            s = side * math.cos(angle) + normal * math.sin(angle)
            n = heading.cross(s).normalized()
            s = n.cross(heading).normalized()
            w = max(width * profile(t), width * 0.04)
            h = thickness * (1 - 0.6 * t)
            for k in range(ring):
                a = 2 * math.pi * k / ring
                x, y = math.cos(a), math.sin(a)
                lift = cup * w * x * x * (1 - t * t)
                vertices.append(centre + s * (w / 2) * x + n * ((h / 2) * y + lift))
                uvs.append(((1 - x) / 2, t))
        count = len(stations) - 1
        for i in range(count - 1):
            for k in range(ring):
                a, b = i * ring + k, i * ring + (k + 1) % ring
                faces.append((a, b, b + ring, a + ring))
        base_centre = len(vertices)
        vertices.append(stations[0][0] - stations[0][1] * thickness * 0.3)
        uvs.append((0.5, 0.0))
        apex = len(vertices)
        vertices.append(tip)
        uvs.append((0.5, 1.0))
        for k in range(ring):
            faces.append(((k + 1) % ring, k, base_centre))
            last = (count - 1) * ring
            faces.append((last + k, last + (k + 1) % ring, apex))
        self.add(vertices, faces, uvs, key)

    def slab(self, key, centre, axis, x_axis, outline, thickness, cup=0.0):
        """Closed flat shape from a 2D outline that is star-shaped about the origin (heart leaflets, petals);
        planar UVs across its box; cup lifts the rim along `axis`."""
        axis = Vector(axis).normalized()
        x_axis = Vector(x_axis)
        x_axis = (x_axis - axis * x_axis.dot(axis)).normalized()
        y_axis = axis.cross(x_axis)
        xs = [p[0] for p in outline]
        ys = [p[1] for p in outline]
        span = max(max(xs) - min(xs), max(ys) - min(ys))
        radius = max(math.hypot(x, y) for x, y in outline)
        middle = ((0 - min(xs)) / span, (0 - min(ys)) / span)
        self._lens(key, Vector(centre), axis, thickness,
                   [(x_axis * x + y_axis * y + axis * (cup * (x * x + y * y) / radius),
                     ((x - min(xs)) / span, (y - min(ys)) / span)) for x, y in outline], middle)

    def _lens(self, key, centre, axis, thickness, rim, middle):
        """Top and bottom fans from two centre points meeting on one shared outline: a closed thin solid without
        sliver rim strips. rim: [(offset from centre, uv)]."""
        vertices = [centre + axis * thickness / 2, centre - axis * thickness / 2]
        uvs = [middle, middle]
        for offset, uv in rim:
            vertices.append(centre + offset)
            uvs.append(uv)
        faces = []
        n = len(rim)
        for k in range(n):
            a, b = 2 + k, 2 + (k + 1) % n
            faces.append((0, a, b))
            faces.append((1, b, a))
        self.add(vertices, faces, uvs, key)

    def tube(self, key, points, radii, ring=6, closed_ends=True):
        """Closed tube along a polyline (stems, rods); radii per point."""
        points = [Vector(p) for p in points]
        vertices, uvs, faces = [], [], []
        total = sum((points[i + 1] - points[i]).length for i in range(len(points) - 1))
        travelled = 0.0
        previous_side = None
        for i, point in enumerate(points):
            if i:
                travelled += (point - points[i - 1]).length
            tangent = (points[min(i + 1, len(points) - 1)] - points[max(i - 1, 0)]).normalized()
            reference = previous_side or (Vector((0, 0, 1)) if abs(tangent.z) < 0.9 else Vector((1, 0, 0)))
            side = (reference - tangent * reference.dot(tangent)).normalized()
            previous_side = side
            other = tangent.cross(side)
            for k in range(ring):
                a = 2 * math.pi * k / ring
                vertices.append(point + (side * math.cos(a) + other * math.sin(a)) * radii[i])
                uvs.append(((1 - math.cos(a)) / 2, travelled / max(total, 1e-6)))
        for i in range(len(points) - 1):
            for k in range(ring):
                a, b = i * ring + k, i * ring + (k + 1) % ring
                faces.append((a, b, b + ring, a + ring))
        start = len(vertices)
        vertices.append(points[0] - (points[1] - points[0]).normalized() * radii[0] * 0.5)
        uvs.append((0.5, 0.0))
        end = len(vertices)
        vertices.append(points[-1] + (points[-1] - points[-2]).normalized() * radii[-1] * 0.5)
        uvs.append((0.5, 1.0))
        last = (len(points) - 1) * ring
        for k in range(ring):
            faces.append(((k + 1) % ring, k, start))
            faces.append((last + k, last + (k + 1) % ring, end))
        self.add(vertices, faces, uvs, key)

    def torus(self, key, centre, axis, radius, minor, segments=24, ring=6):
        axis = Vector(axis).normalized()
        a1 = (Vector((1, 0, 0)) if abs(axis.x) < 0.9 else Vector((0, 1, 0))).cross(axis).normalized()
        a2 = axis.cross(a1)
        vertices, uvs, faces = [], [], []
        for i in range(segments):
            s = 2 * math.pi * i / segments
            radial = a1 * math.cos(s) + a2 * math.sin(s)
            for k in range(ring):
                a = 2 * math.pi * k / ring
                vertices.append(Vector(centre) + radial * (radius + minor * math.cos(a)) + axis * minor * math.sin(a))
                uvs.append(((1 - math.cos(a)) / 2, 1 - abs(2 * i / segments - 1)))
        for i in range(segments):
            for k in range(ring):
                j = (i + 1) % segments
                faces.append((i * ring + k, j * ring + k, j * ring + (k + 1) % ring, i * ring + (k + 1) % ring))
        self.add(vertices, faces, uvs, key)

    def ellipsoid(self, key, centre, radii, axes=None, segments=10, rings=6, planar=False):
        axes = axes or (Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)))
        vertices, uvs, faces = [], [], []
        for j in range(1, rings):
            phi = math.pi * j / rings
            for i in range(segments):
                theta = 2 * math.pi * i / segments
                x, y, z = math.sin(phi) * math.cos(theta), math.sin(phi) * math.sin(theta), math.cos(phi)
                vertices.append(Vector(centre) + axes[0] * x * radii[0] + axes[1] * y * radii[1]
                                + axes[2] * z * radii[2])
                uvs.append(((x + 1) / 2, (y + 1) / 2) if planar else ((1 - math.cos(theta)) / 2, j / rings))
        top = len(vertices)
        vertices.append(Vector(centre) + axes[2] * radii[2])
        uvs.append((0.5, 0.5) if planar else (0.5, 0.0))
        bottom = len(vertices)
        vertices.append(Vector(centre) - axes[2] * radii[2])
        uvs.append((0.5, 0.5) if planar else (0.5, 1.0))
        for j in range(rings - 2):
            for i in range(segments):
                a, b = j * segments + i, j * segments + (i + 1) % segments
                faces.append((a, a + segments, b + segments, b))
        last = (rings - 2) * segments
        for i in range(segments):
            faces.append((top, i, (i + 1) % segments))
            faces.append((bottom, last + (i + 1) % segments, last + i))
        self.add(vertices, faces, uvs, key)

    def star(self, key, centre, axis, points, outer, inner, thickness, cup=0.0, phase=0.0, round_tips=1):
        """Closed star-shaped disc (a small flower or a rosette); planar UVs across the disc."""
        axis = Vector(axis).normalized()
        a1 = (Vector((1, 0, 0)) if abs(axis.x) < 0.9 else Vector((0, 1, 0))).cross(axis).normalized()
        a2 = axis.cross(a1)
        outline = []
        steps = points * 2 * round_tips
        for k in range(steps):
            a = phase + 2 * math.pi * k / steps
            local = (k % (2 * round_tips))
            r = outer if local < round_tips else inner
            if round_tips > 1 and local < round_tips:
                r = outer * (0.85 + 0.15 * math.cos(math.pi * (local - (round_tips - 1) / 2) / round_tips))
            outline.append((math.cos(a) * r, math.sin(a) * r))
        self._lens(key, Vector(centre), axis, thickness,
                   [(a1 * x + a2 * y + axis * (cup * (x * x + y * y) / max(outer, 1e-6)),
                     (0.5 + x / (2 * outer), 0.5 + y / (2 * outer))) for x, y in outline], (0.5, 0.5))

    def shell(self, key, axis_points, radius, thickness, segments=30, lobe=None):
        """Thick surface of revolution (a trumpet flower): radius(t, theta) along axis points, closed at both ends."""
        axis_points = [Vector(p) for p in axis_points]
        m = len(axis_points)
        vertices, uvs, faces = [], [], []
        frames = []
        previous = None
        for i, p in enumerate(axis_points):
            tangent = (axis_points[min(i + 1, m - 1)] - axis_points[max(i - 1, 0)]).normalized()
            reference = previous or (Vector((0, 0, 1)) if abs(tangent.z) < 0.9 else Vector((1, 0, 0)))
            side = (reference - tangent * reference.dot(tangent)).normalized()
            previous = side
            frames.append((side, tangent.cross(side)))
        for layer, offset in ((0, 0.0), (1, -thickness)):
            for i, p in enumerate(axis_points):
                t = i / (m - 1)
                side, other = frames[i]
                for k in range(segments):
                    theta = 2 * math.pi * k / segments
                    r = max(radius(t, theta) + offset, thickness * 0.3)
                    vertices.append(p + (side * math.cos(theta) + other * math.sin(theta)) * r)
                    uvs.append((1 - abs(2 * k / segments - 1), t))
        inner = m * segments
        for i in range(m - 1):
            for k in range(segments):
                a, b = i * segments + k, i * segments + (k + 1) % segments
                faces.append((a, b, b + segments, a + segments))
                faces.append((inner + a, inner + a + segments, inner + b + segments, inner + b))
        last = (m - 1) * segments
        for k in range(segments):
            a, b = k, (k + 1) % segments
            faces.append((inner + a, inner + b, b, a))
            faces.append((last + a, last + b, inner + last + b, inner + last + a))
        self.add(vertices, faces, uvs, key)

    # ---- finish ------------------------------------------------------------------------------------------------
    def build(self):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        mesh = bpy.data.meshes.new(self.name)
        mesh.from_pydata([tuple(v) for v in self.vertices], [], self.faces)
        mesh.update()
        layer = mesh.uv_layers.new(name='UVMap')
        for polygon, face_uvs in zip(mesh.polygons, self.uvs):
            for loop, uv in zip(polygon.loop_indices, face_uvs):
                layer.data[loop].uv = uv
        obj = bpy.data.objects.new(self.name, mesh)
        bpy.context.collection.objects.link(obj)
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='BEAUTY', ngon_method='BEAUTY')
        bm.to_mesh(mesh)
        bm.free()
        # Ground and centre the footprint.
        low = Vector([min(v.co[i] for v in mesh.vertices) for i in range(3)])
        high = Vector([max(v.co[i] for v in mesh.vertices) for i in range(3)])
        shift = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
        for v in mesh.vertices:
            v.co -= shift
        for polygon in mesh.polygons:
            polygon.use_smooth = True
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
        obj.data.materials.append(self.material())
        return obj

    def material(self):
        colour = np.zeros((ATLAS, ATLAS, 3), np.float32) + 0.3
        height = np.zeros((ATLAS, ATLAS), np.float32)
        rough = np.zeros((ATLAS, ATLAS), np.float32) + 0.6
        metal = np.zeros((ATLAS, ATLAS), np.float32)
        size = ATLAS // GRID
        for key, ((gx, gy, gw, gh), painter, params) in self.cells.items():
            x0, y0, w, h = gx * size, gy * size, gw * size, gh * size
            # Paint the whole cell including gutters (u, v extrapolate slightly beyond 0..1).
            ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
            u = (xs + 0.5 - GUTTER) / (w - 2 * GUTTER)
            v = 1 - (ys + 0.5 - GUTTER) / (h - 2 * GUTTER)
            rng = np.random.default_rng(abs(hash(key)) % (2 ** 32))
            c, hgt, r, m = painter(u, v, rng, **params)
            colour[y0:y0 + h, x0:x0 + w] = c
            height[y0:y0 + h, x0:x0 + w] = hgt
            rough[y0:y0 + h, x0:x0 + w] = r
            metal[y0:y0 + h, x0:x0 + w] = m
        gy, gx = np.gradient(height)
        normal = np.stack([-gx * 3.0, gy * 3.0, np.ones_like(gx)], -1)
        normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
        mr = np.stack([np.ones_like(rough), rough, (metal > 0.5).astype(np.float32)], -1)
        images = {}
        for kind, data, space in (('basecolor', colour, 'sRGB'), ('mr', mr, 'Non-Color'),
                                  ('normal', normal * 0.5 + 0.5, 'Non-Color')):
            image = bpy.data.images.new(f'{self.name}_{kind}', ATLAS, ATLAS, alpha=False)
            image.colorspace_settings.name = space
            rgba = np.concatenate([np.clip(data, 0, 1), np.ones((ATLAS, ATLAS, 1), np.float32)], -1)
            image.pixels[:] = rgba[::-1].ravel()
            image.file_format = 'PNG'
            image.pack()
            images[kind] = image
        material = bpy.data.materials.new(self.name)
        material.use_nodes = True
        material.use_backface_culling = True
        nodes, links = material.node_tree.nodes, material.node_tree.links
        bsdf = nodes['Principled BSDF']
        base = nodes.new('ShaderNodeTexImage')
        base.image = images['basecolor']
        links.new(base.outputs['Color'], bsdf.inputs['Base Color'])
        mr_node = nodes.new('ShaderNodeTexImage')
        mr_node.image = images['mr']
        separate = nodes.new('ShaderNodeSeparateColor')
        links.new(mr_node.outputs['Color'], separate.inputs['Color'])
        links.new(separate.outputs['Green'], bsdf.inputs['Roughness'])
        links.new(separate.outputs['Blue'], bsdf.inputs['Metallic'])
        normal_node = nodes.new('ShaderNodeTexImage')
        normal_node.image = images['normal']
        normal_map = nodes.new('ShaderNodeNormalMap')
        links.new(normal_node.outputs['Color'], normal_map.inputs['Color'])
        links.new(normal_map.outputs['Normal'], bsdf.inputs['Normal'])
        return material


def export(obj, path):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True,
                              export_image_format='AUTO', export_yup=True)


# ---- cell painters: (u, v, rng, **params) -> colour HxWx3 (linear), height, roughness, metal -------------------------

def _noise(rng, shape, scale):
    h, w = shape
    small = rng.random((max(2, h // scale), max(2, w // scale))).astype(np.float32)
    ys = np.linspace(0, small.shape[0] - 1, h)
    xs = np.linspace(0, small.shape[1] - 1, w)
    y0 = np.floor(ys).astype(int).clip(0, small.shape[0] - 2)
    x0 = np.floor(xs).astype(int).clip(0, small.shape[1] - 2)
    fy = (ys - y0)[:, None]
    fx = (xs - x0)[None, :]
    a = small[y0][:, x0]
    b = small[y0][:, x0 + 1]
    c = small[y0 + 1][:, x0]
    d = small[y0 + 1][:, x0 + 1]
    return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy


def lin(rgb):
    return (np.array(rgb, np.float32) / 255.0) ** 2.2


def petal(u, v, rng, base, tip, veins=9, vein_dark=0.8, edge_dark=0.85, rough=0.55, streak=None):
    t = np.clip(v, 0, 1)[..., None]
    colour = lin(base) * (1 - t) + lin(tip) * t
    across = np.abs(u - 0.5) * 2
    vein = 0.5 + 0.5 * np.cos(u * math.pi * 2 * veins + _noise(rng, u.shape, 8) * 2)
    vein = vein ** 6
    colour = colour * (1 - (1 - vein_dark) * vein[..., None])
    colour = colour * (1 - (1 - edge_dark) * across[..., None] ** 3)
    if streak is not None:
        band = np.exp(-((u - 0.5) / 0.12) ** 2) * np.clip(1 - v * 1.6, 0, 1)
        colour = colour * (1 - band[..., None]) + lin(streak) * band[..., None]
    colour *= (0.92 + 0.16 * _noise(rng, u.shape, 6))[..., None]
    height = -vein * 0.35 + 0.2 * _noise(rng, u.shape, 4)
    return colour, height, np.full(u.shape, rough, np.float32), np.zeros(u.shape, np.float32)


def leaf(u, v, rng, colour, rib=(170, 200, 120), veins=7, rough=0.5, chevron=None):
    base = lin(colour)
    across = (u - 0.5) * 2
    tone = base[None, None, :] * (0.9 + 0.2 * _noise(rng, u.shape, 10))[..., None]
    midrib = np.exp(-(across / 0.06) ** 2)
    lateral = 0.5 + 0.5 * np.cos((v * veins * 2 - np.abs(across) * 2.2) * math.pi)
    lateral = lateral ** 10 * (np.abs(across) > 0.06)
    tone = tone * (1 - 0.25 * lateral[..., None])
    tone = tone * (1 - 0.3 * np.abs(across)[..., None] ** 4)
    tone = tone * (1 - midrib[..., None]) + lin(rib) * midrib[..., None]
    if chevron is not None:
        band = np.exp(-((v - 0.35 - 0.35 * np.abs(across)) / 0.05) ** 2) * (np.abs(across) < 0.8)
        tone = tone * (1 - 0.6 * band[..., None]) + lin(chevron) * 0.6 * band[..., None]
    height = midrib * 0.6 - lateral * 0.4 + 0.15 * _noise(rng, u.shape, 3)
    return tone, height, np.full(u.shape, rough, np.float32), np.zeros(u.shape, np.float32)


def stem(u, v, rng, colour, rough=0.55):
    streaks = _noise(rng, (u.shape[0], u.shape[1]), 3)
    tone = lin(colour)[None, None, :] * (0.85 + 0.25 * streaks)[..., None]
    return tone, streaks * 0.3, np.full(u.shape, rough, np.float32), np.zeros(u.shape, np.float32)


def radial(u, v, rng, centre, petal_colour, tip, centre_radius=0.18, rays=10, rough=0.55):
    x, y = u - 0.5, v - 0.5
    r = np.sqrt(x * x + y * y) * 2
    angle = np.arctan2(y, x)
    t = np.clip((r - centre_radius) / (1 - centre_radius), 0, 1)[..., None]
    tone = lin(petal_colour) * (1 - t) + lin(tip) * t
    ray = (0.5 + 0.5 * np.cos(angle * rays * 2)) ** 8 * (r > centre_radius)
    tone = tone * (1 - 0.18 * ray[..., None])
    inside = (r < centre_radius)[..., None]
    dots = _noise(rng, u.shape, 2)
    tone = np.where(inside, lin(centre)[None, None, :] * (0.7 + 0.5 * dots)[..., None], tone)
    height = np.where(r < centre_radius, 0.5 * dots, -ray * 0.3)
    return tone, height, np.full(u.shape, rough, np.float32), np.zeros(u.shape, np.float32)


def solid(u, v, rng, colour, rough=0.5, metal=0.0, grain=0.15, scale=4):
    n = _noise(rng, u.shape, scale)
    tone = lin(colour)[None, None, :] * (1 - grain + 2 * grain * n)[..., None]
    return tone, n * 0.4, np.full(u.shape, rough, np.float32) + 0.1 * (n - 0.5), np.full(u.shape, metal, np.float32)


def eye(u, v, rng):
    x, y = u - 0.5, v - 0.5
    r = np.sqrt(x * x + y * y) * 2
    angle = np.arctan2(y, x)
    t = np.clip(r, 0, 1)[..., None]
    tone = lin((255, 220, 60)) * (1 - t) + lin((215, 70, 10)) * t
    fibres = _noise(rng, (u.shape[0], u.shape[1]), 2)
    fibre = (0.5 + 0.5 * np.cos(angle * 60 + fibres * 6)) ** 4
    tone = tone * (1 - 0.25 * fibre[..., None])
    rim = np.clip((r - 0.86) / 0.14, 0, 1)[..., None]
    tone = tone * (1 - rim) + lin((60, 8, 4)) * rim
    slit = np.abs(x) < 0.07 * np.sqrt(np.clip(1 - (y / 0.42) ** 2, 0, 1))
    tone = np.where(slit[..., None], lin((8, 6, 5))[None, None, :], tone)
    height = -fibre * 0.15
    return tone, height, np.full(u.shape, 0.12, np.float32), np.zeros(u.shape, np.float32)
