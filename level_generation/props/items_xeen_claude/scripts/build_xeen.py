"""Builds the Xeen ground items (designs.json, every design `geometry: procedural`) from components: lying in their
resting pose, Blender Z up, longest horizontal side = the binding's length, lowest point at 0, origin at the centre of
the footprint. Writes work/procedural/<design>.glb, which codex_texture.py prep unwraps for the Codex paint +
material-mask bake (materials come from the mask, so the part classes here only colour the clay renders).
Copied from level_generation/props/items_mm9_claude/scripts/build_mm9.py (its component kit, auto_weapon and the
generic builders); MM9's own designs and Meshy hybrids removed, the Xeen custom builders added (build_<design>).

Long items (weapons, staves, wands) are built from their icon's silhouette (Silhouette, auto_weapon): the icon lies on
the ground (icon x -> X, icon up -> +Y, thickness along Z); the grip or haft is lathed, blades get a diamond section,
heads and guards are the band's outline extruded. Rocks, slabs, rings, amulets, books and vessels use the generic
builders with the parameters of design_overrides.yml.
Usage: blender --background --python build_xeen.py -- <design> [design ...]"""
import json
import math
import os
import sys

import bmesh
import numpy as np
import bpy
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(HERE, 'work')
PROCEDURAL = os.path.join(WORK, 'procedural')
DESIGNS = json.load(open(os.path.join(HERE, 'designs.json')))
# Surface class: (metallic, roughness, emission strength); hes_texture.py reads the same table.
CLASSES = {'ceramic': (0, 0.42, 0), 'gold': (1, 0.32, 0), 'steel': (1, 0.5, 0), 'copper': (1, 0.38, 0),
           'resin': (0, 0.3, 0), 'bone': (0, 0.5, 0), 'glass': (0, 0.08, 0.15), 'crystal': (0, 0.08, 0.35),
           'glow': (0, 0.2, 1.0), 'screen': (0, 0.12, 0.6), 'leather': (0, 0.65, 0), 'cloth': (0, 0.8, 0),
           'paper': (0, 0.85, 0), 'food': (0, 0.9, 0), 'string': (0, 0.75, 0)}
CLASSES['auto'] = (0, 0.4, 0)    # resolved per texel from the painted colour (hes_texture.py)
CLAY = {'gold': (0.75, 0.6, 0.3), 'steel': (0.5, 0.5, 0.52), 'copper': (0.7, 0.4, 0.25), 'resin': (0.2, 0.15, 0.22),
        'glow': (0.5, 0.8, 1.0), 'glass': (0.6, 0.75, 0.85), 'crystal': (0.6, 0.75, 0.9), 'screen': (0.15, 0.2, 0.3),
        'leather': (0.4, 0.28, 0.18), 'cloth': (0.6, 0.15, 0.12), 'paper': (0.85, 0.8, 0.7), 'food': (0.4, 0.45, 0.2)}

parts = []

CLASSES.update({'iron': (1, 0.55, 0), 'wood': (0, 0.7, 0), 'stone': (0, 0.85, 0), 'gem': (0, 0.1, 0)})
CLAY.update({'iron': (0.42, 0.42, 0.44), 'wood': (0.45, 0.3, 0.18), 'stone': (0.6, 0.58, 0.55), 'gem': (0.6, 0.1, 0.12)})


def material(name):
    if name not in bpy.data.materials:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        bsdf.inputs['Base Color'].default_value = (*CLAY.get(name, (0.85, 0.83, 0.78)), 1)
        bsdf.inputs['Metallic'].default_value = CLASSES[name][0]
        bsdf.inputs['Roughness'].default_value = CLASSES[name][1]
    return bpy.data.materials[name]


def place(bm, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    matrix = (Matrix.Translation(Vector(loc)) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()
              @ Matrix.Diagonal((*scale, 1)))
    bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)


def finish(bm, cls, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), bevel=0.0, segments=1):
    if bevel:
        edges = [e for e in bm.edges if e.calc_face_angle(0) > math.radians(50)]
        bmesh.ops.bevel(bm, geom=edges, offset=bevel, segments=segments, affect='EDGES', profile=0.5,
                        clamp_overlap=True)
    place(bm, loc, rot, scale)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(cls)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(material(cls))
    obj = bpy.data.objects.new(cls, mesh)
    bpy.context.scene.collection.objects.link(obj)
    parts.append(obj)
    return obj


def box(size, cls, loc=(0, 0, 0), rot=(0, 0, 0), bevel=0.0, segments=1):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    place(bm, scale=size)
    return finish(bm, cls, loc, rot, bevel=bevel, segments=segments)


def cyl(radius, depth, cls, loc=(0, 0, 0), rot=(0, 0, 0), sides=16, radius2=None, scale=(1, 1, 1), bevel=0.0):
    """A cylinder (or cone, radius2) along Z, centred."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=sides, radius1=radius,
                          radius2=radius if radius2 is None else radius2, depth=depth)
    place(bm, scale=scale)
    return finish(bm, cls, loc, rot, bevel=bevel)


def sphere(radius, cls, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), segments=16, rings=8):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius)
    place(bm, scale=scale)
    return finish(bm, cls, loc, rot)


def torus(major, minor, cls, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), segments=24, sides=8, section=(1, 1),
          arc=360.0, ripple=(0, 0.0)):
    """A torus round Z (section scales the tube: radial, height); arc < 360 leaves it open with capped ends;
    ripple (count, amount) swells the tube that many times round, as ribs."""
    bm = bmesh.new()
    closed = arc >= 360
    count = segments if closed else segments + 1
    rings = []
    for i in range(count):
        a = math.radians(arc) * i / segments
        centre = Vector((major * math.cos(a), major * math.sin(a), 0))
        out = Vector((math.cos(a), math.sin(a), 0))
        tube = minor * (1 + ripple[1] * math.cos(ripple[0] * a))
        rings.append([bm.verts.new(centre + out * tube * section[0] * math.cos(b) + Vector((0, 0, 1)) * tube
                                   * section[1] * math.sin(b))
                      for b in (2 * math.pi * j / sides for j in range(sides))])
    bridge(bm, rings, closed)
    if not closed:
        bm.faces.new(rings[0][::-1])
        bm.faces.new(rings[-1])
    return finish(bm, cls, loc, rot, scale)


def bridge(bm, rings, closed):
    for i in range(len(rings) - (0 if closed else 1)):
        a, b = rings[i], rings[(i + 1) % len(rings)]
        n = len(a)
        for j in range(n):
            bm.faces.new((a[j], a[(j + 1) % n], b[(j + 1) % n], b[j]))


def lathe(profile, cls, loc=(0, 0, 0), rot=(0, 0, 0), sides=20, scale=(1, 1, 1), closed=False):
    """Revolves (radius, z) points round Z; a radius of 0 at either end closes it with a pole; closed joins the last
    point back to the first (a ring band's cross-section) instead of capping."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r == 0:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(a), r * math.sin(a), z))
                          for a in (2 * math.pi * j / sides for j in range(sides))])
    for a, b in zip(rings, rings[1:] + (rings[:1] if closed else [])):
        if len(a) == 1:
            for j in range(sides):
                bm.faces.new((a[0], b[(j + 1) % sides], b[j]))
        elif len(b) == 1:
            for j in range(sides):
                bm.faces.new((a[j], a[(j + 1) % sides], b[0]))
        else:
            for j in range(sides):
                bm.faces.new((a[j], a[(j + 1) % sides], b[(j + 1) % sides], b[j]))
    if len(rings[0]) > 1 and not closed:
        bm.faces.new(rings[0][::-1])
    if len(rings[-1]) > 1 and not closed:
        bm.faces.new(rings[-1])
    return finish(bm, cls, loc, rot, scale)


def sweep(points, radii, cls, sides=8, closed=False, section=(1, 1), loc=(0, 0, 0), rot=(0, 0, 0), up=(0, 0, 1)):
    """A tube along points (radius per point, or one radius); section scales it across (side, up)."""
    points = [Vector(p) for p in points]
    radii = radii if isinstance(radii, (list, tuple)) else [radii] * len(points)
    bm = bmesh.new()
    rings = []
    count = len(points)
    for i, p in enumerate(points):
        ahead = points[(i + 1) % count] if closed or i + 1 < count else p
        behind = points[i - 1] if closed or i > 0 else p
        tangent = (ahead - behind).normalized()
        side = tangent.cross(Vector(up))
        if side.length < 1e-6:
            side = tangent.cross(Vector((1, 0, 0)))
        side.normalize()
        normal = side.cross(tangent).normalized()
        rings.append([bm.verts.new(p + side * radii[i] * section[0] * math.cos(a)
                                   + normal * radii[i] * section[1] * math.sin(a))
                      for a in (2 * math.pi * j / sides for j in range(sides))])
    bridge(bm, rings, closed)
    if not closed:
        bm.faces.new(rings[0][::-1])
        bm.faces.new(rings[-1])
    return finish(bm, cls, loc, rot)


def prism(outline, depth, cls, loc=(0, 0, 0), rot=(0, 0, 0), bevel=0.0, segments=1, taper=1.0):
    """An outline [(x, y)] extruded along Z from 0 to depth; taper scales the top face."""
    bm = bmesh.new()
    bottom = [bm.verts.new((x, y, 0)) for x, y in outline]
    top = [bm.verts.new((x * taper, y * taper, depth)) for x, y in outline]
    bm.faces.new(bottom[::-1])
    bm.faces.new(top)
    for j in range(len(outline)):
        k = (j + 1) % len(outline)
        bm.faces.new((bottom[j], bottom[k], top[k], top[j]))
    return finish(bm, cls, loc, rot, bevel=bevel, segments=segments)


def crystal(length, radius, cls, sides=6, tips=(0.3, 0.2), loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1),
            twist=0.0):
    """A pointed crystal along +Z from 0: a prism of `sides` with tips (fractions of the length) at both ends."""
    bm = bmesh.new()
    low, high = length * tips[1], length * (1 - tips[0])
    rings = []
    for z, turn in ((low, 0), (high, twist)):
        rings.append([bm.verts.new((radius * math.cos(a + turn), radius * math.sin(a + turn), z))
                      for a in (2 * math.pi * j / sides for j in range(sides))])
    bottom, top = bm.verts.new((0, 0, 0)), bm.verts.new((0, 0, length))
    for j in range(sides):
        k = (j + 1) % sides
        bm.faces.new((rings[0][j], rings[0][k], rings[1][k], rings[1][j]))
        bm.faces.new((rings[1][j], rings[1][k], top))
        bm.faces.new((rings[0][k], rings[0][j], bottom))
    place(bm, scale=scale)
    return finish(bm, cls, loc, rot)


def rounded_rect(width, height, radius, steps=3):
    points = []
    for cx, cy, start in ((width / 2 - radius, height / 2 - radius, 0), (-width / 2 + radius, height / 2 - radius, 90),
                          (-width / 2 + radius, -height / 2 + radius, 180),
                          (width / 2 - radius, -height / 2 + radius, 270)):
        for i in range(steps + 1):
            a = math.radians(start + 90 * i / steps)
            points.append((cx + radius * math.cos(a), cy + radius * math.sin(a)))
    return points


def slab(width, height, depth, radius, cls, loc=(0, 0, 0), rot=(0, 0, 0), bevel=0.0):
    return prism(rounded_rect(width, height, radius), depth, cls, loc, rot, bevel=bevel)


def chain(points, link=1.8, wire=0.32, cls='gold'):
    """Links along a polyline lying on the ground, alternately flat and on edge."""
    points = [Vector(p) for p in points]
    lengths = [(b - a).length for a, b in zip(points, points[1:])]
    total, step, i, travelled = sum(lengths), link * 0.95, 0, 0.0
    position, n = 0.0, 0
    while position < total:
        while i < len(lengths) - 1 and position > travelled + lengths[i]:
            travelled += lengths[i]
            i += 1
        t = (position - travelled) / lengths[i]
        p = points[i].lerp(points[i + 1], t)
        d = (points[i + 1] - points[i]).normalized()
        yaw = math.degrees(math.atan2(d.y, d.x))
        roll = 90 if n % 2 else 0
        torus(link / 2, wire, cls, (p.x, p.y, wire + (link / 2 * 0.62 - wire if roll else 0)),
              (roll, 0, yaw), scale=(1, 0.62, 1), segments=8, sides=4)
        position += step
        n += 1



RING_TILT = (32, 0, 0)


def ring_band(radius, width, thickness, cls, segments=32):
    lathe([(radius, -width / 2), (radius + thickness, -width / 2 + 0.3), (radius + thickness, width / 2 - 0.3),
           (radius, width / 2)], cls, sides=segments, closed=True)


def ring_group(builder):
    """Builds a ring lying flat (axis vertical), its setting at +Y, then tilts it so the setting faces up."""
    start = len(parts)
    builder()
    for obj in parts[start:]:
        obj.data.transform(Euler([math.radians(a) for a in RING_TILT]).to_matrix().to_4x4())


def pendant_chain(top, spread=13, drop=16):
    x, y = top
    chain([(x, y), (x - spread * 0.6, y + drop * 0.6), (x - spread * 0.3, y + drop), (x + spread * 0.3, y + drop),
           (x + spread * 0.6, y + drop * 0.6), (x, y)])




# --- Icon silhouettes ------------------------------------------------------------------------------------------
class Silhouette:
    """The design's x2 icon alpha, lying on the ground: icon x -> X (centred on `axis`, an icon column), icon rows
    up -> +Y (the bottom row at 0), scaled so the icon's longest side is the design's length."""

    def __init__(self, design, axis=None):
        entry = DESIGNS[design]
        image = bpy.data.images.load(entry['icon_path'], check_existing=False)
        width, height = image.size
        pixels = np.array(image.pixels[:], np.float32).reshape(height, width, 4)[::-1]
        bpy.data.images.remove(image)
        self.alpha = pixels[..., 3] > 0.5
        ys, xs = np.nonzero(self.alpha)
        self.top, self.bottom = ys.min(), ys.max() + 1
        self.left, self.right = xs.min(), xs.max() + 1
        self.scale = entry['length'] / max(self.bottom - self.top, self.right - self.left)
        self.axis = (self.left + self.right) / 2 if axis is None else axis

    def X(self, x):
        return (x - self.axis) * self.scale

    def Y(self, y):
        return (self.bottom - y) * self.scale

    def run(self, y, window=None):
        """The opaque run of row y (within window [x0, x1)) nearest the axis, as [left, right)."""
        lo, hi = window or (0, self.alpha.shape[1])
        xs = np.nonzero(self.alpha[int(y), lo:hi])[0] + lo
        if not len(xs):
            return None
        breaks = np.nonzero(np.diff(xs) > 1)[0]
        starts = np.concatenate([[xs[0]], xs[breaks + 1]])
        ends = np.concatenate([xs[breaks], [xs[-1]]]) + 1
        centre = self.axis if window is None else (lo + hi) / 2
        best = min(range(len(starts)), key=lambda i: 0 if starts[i] <= centre < ends[i]
                   else min(abs(starts[i] - centre), abs(ends[i] - centre)))
        return starts[best], ends[best]

    def rows(self, y0, y1, step, window=None):
        """(y, left, right) of each sampled row in [y0, y1], always including both ends."""
        ys = list(range(int(y0), int(y1), step)) + [int(y1)]
        result = []
        for y in ys:
            span = self.run(min(y, self.alpha.shape[0] - 1), window)
            if span:
                result.append((y, *span))
        return result

    def mask_outline(self, mask, epsilon=1.0):
        """The outer contour of the largest region of a mask (icon pixels), simplified, in world coordinates,
        counter-clockwise."""
        contour = trace(largest_component(mask))
        simplified = douglas_peucker(contour, epsilon)
        points = [(self.X(x), self.Y(y)) for x, y in simplified]
        area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(points, points[1:] + points[:1]))
        return points if area > 0 else points[::-1]

    def outline(self, y0, y1, window=None, epsilon=1.0):
        """The outer contour of the largest opaque region in rows [y0, y1) (and window), traced round its border and
        simplified (Douglas-Peucker, epsilon icon pixels), in world coordinates, counter-clockwise."""
        mask = np.zeros_like(self.alpha)
        lo, hi = window or (0, self.alpha.shape[1])
        mask[int(y0):int(y1), lo:hi] = self.alpha[int(y0):int(y1), lo:hi]
        labels = largest_component(mask)
        contour = trace(labels)
        simplified = douglas_peucker(contour, epsilon)
        points = [(self.X(x), self.Y(y)) for x, y in simplified]
        area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(points, points[1:] + points[:1]))
        return points if area > 0 else points[::-1]


def largest_component(mask):
    """The largest 4-connected component of a boolean mask."""
    seen = np.zeros_like(mask)
    best = None
    for start in zip(*np.nonzero(mask)):
        if seen[start]:
            continue
        stack, component = [start], []
        seen[start] = True
        while stack:
            y, x = stack.pop()
            component.append((y, x))
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        if best is None or len(component) > len(best):
            best = component
    result = np.zeros_like(mask)
    for y, x in best:
        result[y, x] = True
    return result


def trace(mask):
    """The outer boundary of a filled region as pixel-corner points (x, y): walk the edges between inside and outside
    pixels clockwise in image space."""
    padded = np.pad(mask, 1)
    edges = {}
    height, width = padded.shape
    for y in range(height - 1):
        for x in range(width - 1):
            if padded[y, x]:
                if not padded[y - 1, x]:
                    edges[(x, y)] = (x + 1, y)
                if not padded[y, x + 1]:
                    edges[(x + 1, y)] = (x + 1, y + 1)
                if not padded[y + 1, x]:
                    edges[(x + 1, y + 1)] = (x, y + 1)
                if not padded[y, x - 1]:
                    edges[(x, y + 1)] = (x, y)
    # The outer loop starts at the top-left-most corner; holes are separate loops and are ignored. Where two pixels
    # touch only at a corner, that corner has two outgoing edges and the walk can close a smaller loop that never
    # returns to the start: the walk is capped and such an outline falls back to the region's convex hull.
    start = min(edges, key=lambda p: (p[1], p[0]))
    loop, point = [start], edges[start]
    while point != start:
        loop.append(point)
        if len(loop) > len(edges):
            return convex_hull([(x - 1, y - 1) for x, y in edges])
        point = edges[point]
    return [(x - 1, y - 1) for x, y in loop]


def convex_hull(points):
    """The convex hull of 2D points (monotone chain), clockwise in image space like trace()."""
    points = sorted(set(points))
    if len(points) < 3:
        return points
    def half(sequence):
        chain = []
        for p in sequence:
            while len(chain) >= 2 and ((chain[-1][0] - chain[-2][0]) * (p[1] - chain[-2][1])
                                       - (chain[-1][1] - chain[-2][1]) * (p[0] - chain[-2][0])) <= 0:
                chain.pop()
            chain.append(p)
        return chain[:-1]
    return half(points) + half(points[::-1])


def douglas_peucker(points, epsilon):
    def simplify(chain):
        if len(chain) < 3:
            return chain
        a, b = np.array(chain[0], float), np.array(chain[-1], float)
        d = b - a
        norm = np.hypot(*d) or 1.0
        distances = [abs(d[0] * (p[1] - a[1]) - d[1] * (p[0] - a[0])) / norm for p in chain[1:-1]]
        index = int(np.argmax(distances)) + 1
        if distances[index - 1] <= epsilon:
            return [chain[0], chain[-1]]
        return simplify(chain[:index + 1])[:-1] + simplify(chain[index:])
    split = len(points) // 2
    return simplify(points[:split + 1])[:-1] + simplify(points[split:] + points[:1])[:-1]


def lathe_band(sil, y0, y1, cls, step=3, sides=12, window=None, squash=1.0, min_radius=0.4):
    """A round part revolved about the axis of each sampled row (grip, haft, pommel): radius = half the row's width."""
    rows = sil.rows(y0, y1, step, window)
    bm = bmesh.new()
    rings = []
    for y, left, right in rows:
        centre, radius = sil.X((left + right) / 2), max((right - left) / 2 * sil.scale, min_radius)
        rings.append([bm.verts.new((centre + radius * math.cos(a), sil.Y(y), radius * math.sin(a) * squash))
                      for a in (2 * math.pi * j / sides for j in range(sides))])
    bridge(bm, rings, False)
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    return finish(bm, cls)


def blade_band(sil, y0, y1, cls, step=3, thickness=0.14, window=None, tip=True):
    """A blade: each sampled row's run as a flat diamond section (edges at the run's ends, a ridge at its middle,
    thickness a fraction of its width); `tip` closes the first row to a point."""
    rows = sil.rows(y0, y1, step, window)
    bm = bmesh.new()
    rings = []
    for y, left, right in rows:
        half = (right - left) / 2 * sil.scale
        centre = sil.X((left + right) / 2)
        t = max(half * thickness, 0.25)
        rings.append([bm.verts.new((centre - half, sil.Y(y), 0)), bm.verts.new((centre, sil.Y(y), -t)),
                      bm.verts.new((centre + half, sil.Y(y), 0)), bm.verts.new((centre, sil.Y(y), t))])
    if tip:
        point = bm.verts.new((sil.X((rows[0][1] + rows[0][2]) / 2), sil.Y(rows[0][0] - step / 2), 0))
        for j in range(4):
            bm.faces.new((rings[0][(j + 1) % 4], rings[0][j], point))
    else:
        bm.faces.new(rings[0][::-1])
    bridge(bm, rings, False)
    bm.faces.new(rings[-1])
    return finish(bm, cls)


def slab_band(sil, y0, y1, cls, depth, window=None, bevel=0.0, epsilon=1.0, z=0.0):
    """A flat part (guard, axe blade, plate) with the band's outline, `depth` thick, centred on z."""
    outline = sil.outline(y0, y1, window, epsilon)
    return prism(outline, depth, cls, loc=(0, 0, z - depth / 2), bevel=bevel)


# --- Generic builders (the full pass) ---------------------------------------------------------------------------
# Every procedural design without a build_<design> of its own is built by family from its icon (generic()).
WEAPON_KINDS = {'sword': 'blade', 'sword2h': 'blade', 'dagger': 'blade', 'axe': 'hafted', 'axe2h': 'hafted',
                'mace': 'hafted', 'hammer': 'hafted', 'hammer2h': 'hafted', 'flail': 'hafted',
                'halberd': 'hafted', 'staff': 'hafted', 'spear': 'hafted', 'bow': 'bow', 'crossbow': 'hafted',
                'firearm': 'hafted'}
# Head depth (world units) as a fraction of the shaft width, per family: thin axe blades, thicker mace flanges and
# hammer blocks (hammers use the head's height instead, see auto_weapon).
HEAD_DEPTH = {'crossbow': 0.3, 'axe': 0.5, 'axe2h': 0.5, 'halberd': 0.45, 'mace': 0.7, 'staff': 0.6, 'flail': 0.6, 'firearm': 0.8,
              'spear': 0.45}


def components(mask, minimum=1):
    """The 8-connected components of a boolean mask with at least `minimum` pixels, largest first."""
    seen = np.zeros_like(mask)
    result = []
    height, width = mask.shape
    for start in zip(*np.nonzero(mask)):
        if seen[start]:
            continue
        stack, members = [start], []
        seen[start] = True
        while stack:
            y, x = stack.pop()
            members.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < height and 0 <= nx < width and mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
        if len(members) >= minimum:
            component = np.zeros_like(mask)
            ys, xs = zip(*members)
            component[list(ys), list(xs)] = True
            result.append(component)
    return sorted(result, key=lambda c: -c.sum())


def erode(mask, steps=1):
    for _ in range(steps):
        shrunk = mask.copy()
        shrunk[1:] &= mask[:-1]
        shrunk[:-1] &= mask[1:]
        shrunk[:, 1:] &= mask[:, :-1]
        shrunk[:, :-1] &= mask[:, 1:]
        mask = shrunk
    return mask


def dilate(mask, steps=1):
    for _ in range(steps):
        grown = mask.copy()
        grown[1:] |= mask[:-1]
        grown[:-1] |= mask[1:]
        grown[:, 1:] |= mask[:, :-1]
        grown[:, :-1] |= mask[:, 1:]
        mask = grown
    return mask


def track(sil, start, stop, centre):
    """Follows the opaque run nearest the previous row's centre from row `start` toward `stop` (either direction):
    {row: (left, right)}; ends where a row has no run within reach."""
    result = {}
    step = 1 if stop >= start else -1
    for y in range(start, stop + step, step):
        row = sil.alpha[y]
        xs = np.nonzero(row)[0]
        if not len(xs):
            break
        breaks = np.nonzero(np.diff(xs) > 1)[0]
        starts = np.concatenate([[xs[0]], xs[breaks + 1]])
        ends = np.concatenate([xs[breaks], [xs[-1]]]) + 1
        index = min(range(len(starts)), key=lambda i: 0 if starts[i] <= centre < ends[i]
                    else min(abs(starts[i] - centre), abs(ends[i] - centre)))
        if not (starts[index] - 6 <= centre <= ends[index] + 6):
            break
        result[y] = (int(starts[index]), int(ends[index]))
        centre = (starts[index] + ends[index]) / 2
    return result


def lathe_rows(sil, rows, cls, step=3, sides=10, min_radius=0.4):
    """Lathes the tracked runs of `rows` ({row: (left, right)}), one part per contiguous stretch."""
    keys = sorted(rows)
    stretches, current = [], [keys[0]] if keys else []
    for y in keys[1:]:
        if y == current[-1] + 1:
            current.append(y)
        else:
            stretches.append(current)
            current = [y]
    if current:
        stretches.append(current)
    for stretch in stretches:
        if len(stretch) < 2:
            continue
        sample = stretch[::step] + ([stretch[-1]] if (len(stretch) - 1) % step else [])
        bm = bmesh.new()
        rings = []
        for y in sample:
            left, right = rows[y]
            centre, radius = sil.X((left + right) / 2), max((right - left) / 2 * sil.scale, min_radius)
            rings.append([bm.verts.new((centre + radius * math.cos(a), sil.Y(y), radius * math.sin(a)))
                          for a in (2 * math.pi * j / sides for j in range(sides))])
        bridge(bm, rings, False)
        bm.faces.new(rings[0][::-1])
        bm.faces.new(rings[-1])
        finish(bm, cls)


def blade_rows(sil, rows, cls, step=3, thickness=0.16, tip=True):
    """A diamond-section blade over the tracked runs of `rows` (contiguous), the first row closed to a point."""
    keys = sorted(rows)
    sample = keys[::step] + ([keys[-1]] if (len(keys) - 1) % step else [])
    bm = bmesh.new()
    rings = []
    for y in sample:
        left, right = rows[y]
        half = (right - left) / 2 * sil.scale
        centre = sil.X((left + right) / 2)
        t = max(half * thickness, 0.25)
        rings.append([bm.verts.new((centre - half, sil.Y(y), 0)), bm.verts.new((centre, sil.Y(y), -t)),
                      bm.verts.new((centre + half, sil.Y(y), 0)), bm.verts.new((centre, sil.Y(y), t))])
    if tip:
        first = rows[sample[0]]
        point = bm.verts.new((sil.X((first[0] + first[1]) / 2), sil.Y(sample[0] - 2), 0))
        for j in range(4):
            bm.faces.new((rings[0][(j + 1) % 4], rings[0][j], point))
    else:
        bm.faces.new(rings[0][::-1])
    bridge(bm, rings, False)
    bm.faces.new(rings[-1])
    finish(bm, cls)


def mask_slab(sil, mask, depth, cls, epsilon=1.2, bevel=0.0):
    """Each component of a mask (icon pixels) extruded `depth` thick, centred on z = 0."""
    for component in components(mask, 24):
        outline = sil.mask_outline(component, epsilon)
        if len(outline) >= 3:
            prism(outline, depth, cls, loc=(0, 0, -depth / 2), bevel=bevel)


def row_mask(sil, rows):
    """The mask of the tracked runs of `rows`."""
    mask = np.zeros_like(sil.alpha)
    for y, (left, right) in rows.items():
        mask[y, left:right] = True
    return mask


def band_mask(sil, y0, y1):
    mask = np.zeros_like(sil.alpha)
    mask[y0:y1] = sil.alpha[y0:y1]
    return mask


def widths(rows):
    return {y: right - left for y, (left, right) in rows.items()}


def auto_weapon(design):
    """A weapon from its icon: the grip or haft found at the bottom and followed up and down (track); per family the
    blade, guard, head, limbs and leftovers (knuckle guards, chains, strings, crossbars) as parts. A hybrid design's
    Meshy part (`meshy_part`: head, hilt or weight) replaces its region of the icon."""
    entry = DESIGNS[design]
    family = entry['family']
    kind = WEAPON_KINDS.get(family, 'hafted')
    if family == 'throwing':
        kind = 'blade' if 'dagger' in entry['identity'].lower() or design in ('d10034', 'd10185') else 'hafted'
    sil = Silhouette(design)
    top, bottom = sil.top, sil.bottom - 1
    alpha = sil.alpha
    if kind == 'bow':
        start = (top + bottom) // 2
        xs = np.nonzero(alpha[start])[0]
        centre = xs.max() - 2 if len(xs) else (sil.left + sil.right) / 2
    else:
        # The grip or haft: the tallest opaque column of the lower half, from the lowest row that covers it.
        middle = (top + bottom) // 2
        centre = float(np.argmax(alpha[middle:bottom + 1].sum(axis=0)))
        start = max(y for y in range(middle, bottom + 1) if alpha[y, int(centre)])
        start = max(middle, start - max(2, (bottom - top) // 40))
    rows = {**track(sil, start, top, centre), **track(sil, start, bottom, centre)}
    if not rows:
        prism(sil.mask_outline(alpha), 2.0, 'steel')
        return
    sil.axis = float(np.median([(l + r) / 2 for l, r in rows.values()]))
    width = widths(rows)
    lower = [width[y] for y in rows if y > top + (bottom - top) * 0.55]
    shaft = float(np.median(lower)) if lower else float(np.median(list(width.values())))
    shaft_world = shaft * sil.scale
    used = np.zeros_like(alpha)
    meshy = None   # no Meshy parts (MM9's hybrids)
    region = None

    if kind == 'bow':
        lathe_rows(sil, rows, 'wood', step=3, sides=8)
        used |= dilate(row_mask(sil, rows), 2)
        rest = alpha & ~used
        mask_slab(sil, rest, max(shaft_world * 0.25, 0.4), 'string', epsilon=1.0)
        return finish_hybrid(sil, design, None)

    if kind == 'flat':
        prism(sil.mask_outline(alpha, 1.2), max(shaft_world * 0.35, 1.0), 'wood', loc=(0, 0, -shaft_world * 0.175))
        lathe_rows(sil, rows, 'wood', step=4, sides=8)
        return finish_hybrid(sil, design, None)

    if kind == 'blade':
        # The guard: from 30 % down, the first row clearly wider than the blade just above it and than the grip.
        guard = None
        ordered = sorted(rows)
        for y in ordered:
            if y < top + (bottom - top) * 0.3:
                continue
            above = [width[k] for k in range(y - 10, y - 3) if k in width]
            if above and width[y] >= 1.35 * float(np.median(above)) and width[y] >= 1.4 * shaft:
                guard = y
                break
        if guard is None:
            # No guard (a curved knife): the blade ends where the run narrows to the grip.
            guard = next((y for y in ordered if y > top + (bottom - top) * 0.45 and width[y] <= shaft * 1.15),
                         ordered[len(ordered) * 2 // 3])
        guard_end = guard
        while guard_end + 1 in width and width[guard_end + 1] >= 1.3 * shaft and guard_end - guard < 30:
            guard_end += 1
        blade = {y: rows[y] for y in ordered if y < guard}
        grip = {y: rows[y] for y in ordered if y > guard_end}
        if meshy == 'hilt':
            region = (guard - 2, bottom + 1)
        if blade:
            blade_rows(sil, blade, 'steel', step=3, thickness=0.16)
            used |= dilate(row_mask(sil, blade), 1)
        if meshy != 'hilt':
            guard_mask = band_mask(sil, guard - 1, guard_end + 2) & ~used
            mask_slab(sil, guard_mask, max(shaft_world * 0.8, 0.8), 'gold', epsilon=1.0)
            used |= dilate(guard_mask, 1)
            if grip:
                lathe_rows(sil, grip, 'leather', step=3, sides=10)
                used |= dilate(row_mask(sil, grip), 1)
        else:
            used[region[0]:region[1]] |= alpha[region[0]:region[1]]
        rest = alpha & ~used
        mask_slab(sil, rest, max(shaft_world * 0.5, 0.6), 'steel', epsilon=1.0)
        return finish_hybrid(sil, design, region)

    # Hafted: bands of rows (full width) clearly wider than the shaft are heads; the tracked run elsewhere is lathed.
    full = {y: (np.nonzero(alpha[y])[0].min(), np.nonzero(alpha[y])[0].max() + 1) for y in rows}
    if family == 'flail':
        # A flail's chain and weight hang beside the handle: its heads are only where the handle itself widens.
        full = dict(rows)
    wide = sorted(y for y in rows if (full[y][1] - full[y][0]) > 2.0 * shaft + 2)
    bands = []
    for y in wide:
        if bands and y <= bands[-1][1] + 3:
            bands[-1][1] = y
        else:
            bands.append([y, y])
    bands = [b for b in bands if b[1] - b[0] >= 3]
    if meshy == 'head' and bands:
        head = bands[0]
        region = (max(top, head[0] - 2), head[1] + 2)
        bands = bands[1:]
    for b0, b1 in bands:
        head_rows = {y: rows[y] for y in range(b0, b1 + 1) if y in rows}
        if family == 'spear' and b0 < top + (bottom - top) * 0.3 and head_rows:
            blade_rows(sil, head_rows, 'steel', step=2, thickness=0.2, tip=b0 <= top + 3)
            used |= dilate(row_mask(sil, head_rows), 1)
            continue
        if entry.get('head_lathe'):
            # A round head (a flanged mace seen from the side): revolved, the flanges painted (Xeen).
            band_rows = {y: full[y] for y in range(b0, b1 + 1) if y in full}
            lathe_rows(sil, band_rows, 'steel', step=2, sides=12)
            used |= dilate(band_mask(sil, b0, b1 + 1), 1)
            continue
        if family in ('hammer', 'hammer2h'):
            depth = max((b1 - b0) * sil.scale * 0.55, shaft_world)
        else:
            depth = max(shaft_world * HEAD_DEPTH.get(family, 0.5), 0.5)
        head_mask = band_mask(sil, b0, b1 + 1)
        if family == 'crossbow':
            # The string would close the bow into a filled half-disc: an opening removes it, the arms stay a strip.
            head_mask = dilate(erode(head_mask, 3), 3) & head_mask
        mask_slab(sil, head_mask, depth, 'steel', epsilon=1.2, bevel=min(depth * 0.2, 0.6))
        used |= dilate(head_mask, 1)
    shaft_rows = {y: r for y, r in rows.items() if not used[y, (r[0] + r[1]) // 2]
                  and not (region and region[0] <= y < region[1])}
    if shaft_rows:
        lathe_rows(sil, shaft_rows, 'wood', step=4, sides=10)
        used |= dilate(row_mask(sil, shaft_rows), 1)
    if region:
        used[region[0]:region[1]] |= alpha[region[0]:region[1]]
    rest = alpha & ~used
    leftovers = components(rest, 24)
    if family == 'flail':
        # Split each chain-and-weight leftover: rows at least 45 % of its widest row are the weight, the rest chain.
        split = []
        for component in leftovers:
            spans = component.sum(axis=1)
            weight = component & (spans >= 0.45 * spans.max())[:, None]
            split += [c for c in (weight, component & ~weight) if c.sum() >= 24]
        leftovers = sorted(split, key=lambda c: -c.sum())
        weights = [c for c in leftovers if np.ptp(np.nonzero(c)[1]) + 1 >= 0.6 * (np.ptp(np.nonzero(c)[0]) + 1)]
        if meshy == 'weight' and weights:
            ys, xs = np.nonzero(weights[0])
            region = (ys.min(), ys.max() + 1, xs.min(), xs.max() + 1)
            leftovers = [c for c in leftovers if c is not weights[0]]
    for component in leftovers:
        ys, xs = np.nonzero(component)
        h, w = ys.max() - ys.min() + 1, xs.max() - xs.min() + 1
        fill_ratio = component.sum() / (h * w)
        if family == 'flail' and 0.6 < h / w < 1.6 and fill_ratio > 0.4:
            # A flail's ball: a sphere at the component's centre.
            radius = (w + h) / 4 * sil.scale * 0.85
            centre = Vector((sil.X(xs.mean()), sil.Y(ys.mean()), 0))
            sphere(radius * 0.8, 'steel', centre, segments=14, rings=8)
            # Its spikes (Xeen): cones on the directions of an octahedron and a cube's corners.
            for direction in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1),
                              *((a, b, c) for a in (-1, 1) for b in (-1, 1) for c in (-1, 1))):
                d = Vector(direction).normalized()
                rotation = d.to_track_quat('Z', 'Y').to_euler()
                cyl(radius * 0.22, radius * 0.5, 'steel', centre + d * radius * 0.95,
                    tuple(math.degrees(a) for a in rotation), sides=6, radius2=0.02)
        else:
            outline = sil.mask_outline(component, 1.0)
            depth = max(shaft_world * 0.45, 0.5)
            if len(outline) >= 3:
                prism(outline, depth, 'steel', loc=(0, 0, -depth / 2))
    return finish_hybrid(sil, design, region)


def finish_hybrid(sil, design, region):
    """MM9's hybrid step (a Meshy head or hilt in its icon region); the Xeen designs have no Meshy parts."""
    return


def ring_generic(design):
    """A ring lying on its side, its setting turned up (Hesper's tilt); a plain band where the icon has no setting
    (an icon at most 0.8 as tall as it is wide)."""
    sil = Silhouette(design)
    aspect = (sil.bottom - sil.top) / (sil.right - sil.left)
    plain = aspect < 0.8 or DESIGNS[design].get('plain')

    def body():
        ring_band(8, 3.2 if plain else 2.6, 1.3 if plain else 1.0, 'gold')
        if not plain:
            cyl(3.0, 2.6, 'gold', (0, 9.6, 0), (90, 0, 0), sides=14)
            sphere(2.3, 'gem', (0, 11.0, 0), scale=(1, 0.55, 1), segments=14, rings=8)
    ring_group(body)


def amulet_generic(design):
    """A pendant lying flat: the icon's outline below its bail as a domed slab, the bail a small ring, and a chain
    loop above (as the MM6-MM8 amulets lie)."""
    sil = Silhouette(design)
    alpha = sil.alpha
    widest = max((int(np.ptp(np.nonzero(alpha[y])[0])) + 1 if alpha[y].any() else 0) for y in range(sil.top, sil.bottom))
    bail_end = sil.top
    for y in range(sil.top, sil.bottom):
        xs = np.nonzero(alpha[y])[0]
        if len(xs) and int(np.ptp(xs)) + 1 > 0.35 * widest:
            bail_end = y
            break
    body = band_mask(sil, bail_end, sil.bottom)
    width_world = widest * sil.scale
    depth = width_world * 0.14
    outline = sil.mask_outline(body, 1.2)
    prism(outline, depth, 'gold', bevel=depth * 0.3, taper=0.94)
    top_y = sil.Y(bail_end)
    cx = sil.X((sil.left + sil.right) / 2)
    if bail_end > sil.top + 2:
        torus(max((bail_end - sil.top) * sil.scale * 0.35, 1.0), 0.45, 'gold', (cx, top_y + (bail_end - sil.top)
                                                                                 * sil.scale * 0.45, depth * 0.5),
              (90, 0, 90), segments=10, sides=5)
    pendant_chain((cx, top_y + (bail_end - sil.top) * sil.scale + 0.5), spread=width_world * 0.7,
                  drop=width_world * 0.9)


def book_generic(design):
    """A closed book lying flat (or a loose manuscript: `manuscript` stacks a few slightly turned sheets)."""
    w, l, t = 34, 44, 9
    if DESIGNS[design].get('manuscript'):
        for k in range(5):
            box((w, l, 0.8), 'paper', (k * 0.6 - 1.2, k * 0.4, 0.4 + k * 0.85), (0, 0, k * 2.5 - 5), bevel=0.15)
        return
    box((w + 2, l + 2, 1.2), 'leather', (0.6, 0, 0.6), bevel=0.4)
    box((w + 2, l + 2, 1.2), 'leather', (0.6, 0, t - 0.6), bevel=0.4)
    box((w, l - 1.5, t - 2.2), 'paper', (1.2, 0, t / 2), bevel=0.2)
    cyl(t / 2, l + 2, 'leather', (-w / 2, 0, t / 2), (90, 0, 0), sides=12, scale=(0.5, 1, 1))


def vessel_upright(design):
    """A bottle, jar or potion standing up: the icon's rows revolved about its centre."""
    sil = Silhouette(design)
    rows = sil.rows(sil.top, sil.bottom - 1, 3)
    centre = sil.X((sil.left + sil.right) / 2)
    profile = [(0, sil.Y(sil.bottom - 1))]
    for y, left, right in sorted(rows, key=lambda r: -r[0]):
        profile.append(((right - left) / 2 * sil.scale, sil.Y(y)))
    profile.append((0, sil.Y(sil.top)))
    lathe([(r, z) for r, z in profile], 'glass', loc=(centre, 0, 0), sides=20)


def rock(design, roughness=0.18, flat=0.55, bottom=0.08):
    """A lump of rock or a smooth stone the icon's outline wide: a noise-displaced sphere, flattened, cut flat
    `bottom` (a fraction of its short side) below its middle: a stone sits low, a fruit or fur ball nearly whole."""
    sil = Silhouette(design)
    w = (sil.right - sil.left) * sil.scale
    h = (sil.bottom - sil.top) * sil.scale
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    seed = sum(ord(c) for c in design)
    for v in bm.verts:
        n = (math.sin(v.co.x * 3.1 + seed) * math.sin(v.co.y * 2.7 + seed * 0.3) * math.sin(v.co.z * 3.7 + seed * 0.7))
        n += 0.5 * math.sin(v.co.x * 7.3 + seed * 1.3) * math.sin(v.co.z * 6.1 + seed)
        v.co *= 1 + roughness * n
        v.co.x *= w / 2
        v.co.y *= h / 2
        v.co.z *= min(w, h) / 2 * flat
        v.co.z = max(v.co.z, -min(w, h) * bottom)
    finish(bm, 'stone')


def outline_slab(design, depth_fraction=0.12, cls='gold', bevel=0.3):
    """The icon's outline lying flat, `depth_fraction` of its width thick, with a bevelled edge."""
    sil = Silhouette(design)
    width = (sil.right - sil.left) * sil.scale
    depth = width * depth_fraction
    prism(sil.mask_outline(sil.alpha, 1.2), depth, cls, bevel=depth * bevel)


# --- Xeen designs ----------------------------------------------------------------------------------------------
def build_sphere(design):
    """Dragon Pharaoh's Orb: a polished orb."""
    sphere(12, 'gem', (0, 0, 12), segments=28, rings=16)


def build_disc(design):
    """Energy Disk: a thin disc, bevelled rim and a raised centre stone."""
    lathe([(0, 0), (15.2, 0), (16, 0.6), (16, 1.6), (15.2, 2.3), (6.0, 2.6), (5.0, 3.0), (0, 3.0)], 'steel', sides=36)
    sphere(3.6, 'gem', (0, 0, 3.0), scale=(1, 1, 0.5), segments=20, rings=10)


def gear(radius, depth, teeth, cls, loc=(0, 0, 0), rot=(0, 0, 0), tooth=0.18, hole=0.0):
    """A toothed wheel lying in XY, `depth` thick along Z from loc."""
    outline = []
    for i in range(teeth * 4):
        a = 2 * math.pi * i / (teeth * 4)
        r = radius * (1 + tooth) if i % 4 in (1, 2) else radius
        outline.append((r * math.cos(a), r * math.sin(a)))
    prism(outline, depth, cls, loc, rot)
    if hole:
        cyl(hole, depth * 1.6, 'steel', loc=Vector(loc) + Euler([math.radians(a) for a in rot]).to_matrix()
            @ Vector((0, 0, depth / 2)), rot=rot, sides=10)


def build_x12315():
    """Widget: a brass frame on a base plate (two side plates), a coil spring along its top, two gears on axles at
    its front and a crank out of the right side plate."""
    slab(30, 20, 1.6, 2.0, 'gold', bevel=0.3)
    for x in (-12.5, 10.5):
        box((1.6, 14, 15), 'gold', (x, 0, 9.0), bevel=0.3)
    # The coil spring between the side plates on top, round a steel rod.
    cyl(0.6, 23, 'steel', (-1, 1, 12.5), (0, 90, 0), sides=8)
    turns, start, end = 7, -11, 9
    coil = [(start + (end - start) * t / (turns * 2 * math.pi), 1 + 2.6 * math.cos(t), 12.5 + 2.6 * math.sin(t))
            for t in (i * 0.4 for i in range(int(turns * 2 * math.pi / 0.4) + 1))]
    sweep(coil, 0.5, 'steel', sides=6)
    # Two upright gears turning on axles at the front, and a small one flat on the plate.
    gear(5.5, 1.4, 12, 'gold', loc=(-5, -6.5, 8.0), rot=(90, 0, 0), hole=1.1)
    gear(3.6, 1.4, 9, 'gold', loc=(3.2, -6.0, 6.0), rot=(90, 0, 0), hole=0.9)
    cyl(0.6, 6, 'steel', (-5, -5.5, 8.0), (90, 0, 0), sides=8)
    cyl(0.6, 6, 'steel', (3.2, -5.0, 6.0), (90, 0, 0), sides=8)
    gear(2.6, 1.0, 8, 'gold', loc=(-9, 7, 1.6))
    # The crank: an axle out of the right plate, an arm and a wooden knob.
    cyl(0.7, 6, 'steel', (14, 0, 9), (0, 90, 0), sides=10)
    box((1.4, 1.2, 7), 'gold', (16.8, 0, 11.6), bevel=0.2)
    cyl(1.0, 3.5, 'wood', (16.8, -2.2, 14.4), (90, 0, 0), sides=10)

def build_x12192():
    """King's Megacredit: a thick gold coin with a raised rim (the stamped crown is painted)."""
    lathe([(0, 0), (19.2, 0), (20, 0.8), (20, 4.0), (19.2, 4.8), (16.8, 4.8), (16.0, 4.1), (0, 4.1)], 'gold',
          sides=40)


def build_x12313():
    """Crystals of Piezoelectricity: three pointed quartz prisms growing from a small rock base."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    for v in bm.verts:
        n = math.sin(v.co.x * 3.1 + 2) * math.sin(v.co.y * 2.7 + 1) * math.sin(v.co.z * 3.7)
        v.co *= 1 + 0.18 * n
        v.co.x, v.co.y, v.co.z = v.co.x * 9, v.co.y * 7, max(v.co.z * 4.5, -1.0) + 1.0
    finish(bm, 'stone')
    crystal(24, 3.6, 'crystal', loc=(-1, 0, 2.5), rot=(-8, 12, 0), tips=(0.22, 0.05))
    crystal(17, 2.8, 'crystal', loc=(-4, 1, 2.5), rot=(0, -38, 15), tips=(0.25, 0.05))
    crystal(14, 2.5, 'crystal', loc=(3.5, -1, 2.5), rot=(10, 40, -10), tips=(0.25, 0.05))


def build_x12352():
    """Caleb's Magnifying Glass, lying flat: a brass rim round a glass lens and a turned wooden handle."""
    torus(10, 1.3, 'gold', (0, 0, 1.3), segments=40, sides=10, section=(0.8, 1))
    cyl(9.8, 1.0, 'glass', (0, 0, 1.3), sides=40, scale=(1, 1, 1))
    lathe([(1.4, 0), (1.6, 2.5), (1.1, 4), (1.6, 6), (1.9, 12), (2.0, 18), (1.6, 22), (0, 22.6)], 'wood',
          loc=(0, -10.8, 1.6), rot=(90, 0, 0), sides=12)
    cyl(1.6, 2.6, 'gold', (0, -11.6, 1.6), (90, 0, 0), sides=12)


def chest(lid_dome=0.55):
    """A small iron-bound chest: a box with a half-cylinder lid, iron bands over both, corner fittings and a lock
    plate on the front (-Y)."""
    w, d, h = 30, 20, 13
    box((w, d, h), 'wood', (0, 0, h / 2), bevel=0.4)
    rise = d / 2 * lid_dome
    half = [(d / 2 * math.cos(a), rise * math.sin(a)) for a in (math.pi * i / 12 for i in range(13))]
    prism([(y, z) for y, z in half], w, 'wood', loc=(-w / 2, 0, h), rot=(90, 0, 90), bevel=0.3)
    for x in (-w / 2 + 3, w / 2 - 3):
        box((2.2, d + 0.6, h + 0.2), 'iron', (x, 0, h / 2), bevel=0.2)
        band = [(y * 1.04, z * 1.04 + 0.1) for y, z in half]
        prism(band, 2.2, 'iron', loc=(x - 1.1, 0, h), rot=(90, 0, 90))
    for x in (-w / 2, w / 2):
        for y in (-d / 2, d / 2):
            box((3.2, 3.2, 3.6), 'steel', (x * 0.98, y * 0.98, 1.8), bevel=0.4)
    box((6, 1.2, 6.5), 'steel', (0, -d / 2 - 0.4, h - 1.5), bevel=0.3)


def build_x12363():
    """Soul Box: the iron-bound chest."""
    chest()


def build_x12364():
    """Soul Box (Corak): the same chest (the light from its seam is painted)."""
    chest()


def build_x12365():
    """Cube of Power: a bevelled crystal cube, its twelve edges bound in silver bars between corner blocks."""
    s = 20
    box((s, s, s), 'crystal', (0, 0, s / 2), bevel=0.8, segments=2)
    edge = 1.6
    inset = s / 2 - edge / 2 + 0.3
    for axis in range(3):
        for a in (-1, 1):
            for b in (-1, 1):
                position = [0, 0, 0]
                others = [i for i in range(3) if i != axis]
                position[others[0]] = a * inset
                position[others[1]] = b * inset
                size = [edge, edge, edge]
                size[axis] = s - edge * 1.6
                box(size, 'steel', (position[0], position[1], position[2] + s / 2), bevel=0.25)
    for x in (-1, 1):
        for y in (-1, 1):
            for z in (-1, 1):
                box((edge * 1.4,) * 3, 'steel', (x * inset, y * inset, s / 2 + z * inset), bevel=0.3)

def build_x12527():
    """Jewel of Ages: a brilliant-cut diamond (twelve-sided lathe crown and pavilion, flat-shaded facets) lying on
    its side."""
    girdle, table = 10, 5.6
    profile = [(0, 0), (girdle, 8.6), (girdle, 9.4), (table + 1.6, 12.4), (table, 13.2), (0, 13.2)]
    lathe(profile, 'gem', loc=(0, -6.6, 0), rot=(-90, 0, 0), sides=12)

def build_x12522():
    """Ector's Ring: a heavy plain signet band with a flat square bezel."""
    def body():
        ring_band(7.5, 5.0, 2.4, 'steel')
        box((8.5, 3.4, 8.0), 'steel', (0, 10.2, 0), bevel=0.6)
    ring_group(body)


def build_x12510():
    """Last Flower of Summer: a gold band with a small enamel flower of five petals round a centre stone."""
    def body():
        ring_band(8, 2.6, 1.1, 'gold')
        cyl(2.4, 2.2, 'gold', (0, 9.6, 0), (90, 0, 0), sides=12)
        for k in range(5):
            a = 2 * math.pi * k / 5
            sphere(1.7, 'gem', (2.3 * math.cos(a), 10.9, 2.3 * math.sin(a)), (0, -math.degrees(a), 0),
                   scale=(1.2, 0.45, 0.85), segments=10, rings=6)
        sphere(1.0, 'gold', (0, 11.3, 0), scale=(1, 0.6, 1), segments=10, rings=6)
    ring_group(body)


def build_x12525():
    """Chalice of Protection: a hollow gold cup on a knotted stem and a broad foot (a lathe whose profile runs up
    the outside and back down the inside of the cup)."""
    lathe([(0, 0), (9.5, 0), (9.8, 0.8), (8.5, 1.8), (4.5, 3.0), (2.2, 5.0), (2.0, 7.0), (3.4, 8.6), (2.0, 10.2),
           (3.4, 11.8), (2.0, 13.4), (2.6, 15.0), (6.0, 17.0), (10.0, 20.5), (12.5, 25.5), (13.4, 29.5),
           (12.6, 29.5), (11.6, 25.6), (9.2, 21.2), (5.0, 18.6), (0, 18.2)], 'gold', sides=24)
    for k in range(10):
        a = 2 * math.pi * k / 10
        sphere(0.9, 'gem', (12.4 * math.cos(a), 12.4 * math.sin(a), 25.2), segments=8, rings=5)


def build_x12366():
    """Xeen's Scepter, lying flat: a turned iron handle with a ball pommel and a flared collar, the head a round
    clock face in a ring with eight spikes round it in the plane of the face."""
    lathe([(0, 0), (3.2, 0.6), (3.6, 2.4), (2.4, 4.6), (2.0, 6), (2.4, 9), (2.0, 12), (2.4, 15), (2.0, 18),
           (2.3, 30), (3.0, 34), (4.4, 38), (3.0, 40), (0, 40.5)], 'iron', rot=(-90, 0, 0), sides=12)
    centre = (0, 53, 0)
    cyl(11, 4.0, 'iron', centre, sides=32)
    torus(11.4, 1.6, 'iron', centre, segments=32, sides=8)
    for k in range(8):
        a = 2 * math.pi * k / 8 + math.pi / 8
        d = Vector((math.cos(a), math.sin(a), 0))
        cyl(2.0, 7.5, 'iron', Vector(centre) + d * 15.5, tuple(math.degrees(v) for v in
                                                              d.to_track_quat('Z', 'Y').to_euler()), sides=8,
            radius2=0.1)

def bridle(design):
    """A bridle lying on its coiled reins: the headstall standing as a leaning loop with its cheek straps, flattened
    leather loops of the reins round it, strap ends, a steel bit (two rings and a bar) and brass buckles."""
    torus(13, 1.4, 'leather', (0, 0, 0.6), segments=40, sides=8, section=(1, 0.35))
    torus(10.5, 1.4, 'leather', (1.2, 0.8, 1.3), (6, -4, 15), segments=40, sides=8, section=(1, 0.35))
    # The headstall: an upright loop leaning back, the strap's flat side facing out.
    torus(8.5, 1.3, 'leather', (0, 2.5, 9.5), (70, 0, 0), segments=32, sides=8, section=(0.35, 1),
          scale=(0.85, 1.25, 1))
    torus(6.0, 1.1, 'leather', (0, -3.5, 4.0), (35, 0, 0), segments=28, sides=8, section=(0.35, 1),
          scale=(1, 0.8, 1))
    # Strap ends running off the coil.
    sweep([(12, -5, 0.6), (17, -9, 0.6), (21, -10, 0.6)], 1.4, 'leather', sides=8, section=(1, 0.35))
    sweep([(-9, 9, 1.2), (-13, 14, 0.6), (-14.5, 18, 0.6)], 1.3, 'leather', sides=8, section=(1, 0.35))
    # The bit: two rings standing at the front and the jointed bar between them.
    for x in (-6, 6):
        torus(3.0, 0.5, 'steel', (x, -12.5, 3.3), (90, 0, 0), segments=20, sides=6)
    sweep([(-6, -12.5, 3.3), (-1, -12.8, 3.6), (0, -12.8, 3.4), (1, -12.8, 3.6), (6, -12.5, 3.3)], 0.6, 'steel',
          sides=6)
    # Brass buckles on the straps.
    for x, y, z, yaw in ((12.5, 1.5, 1.2, 90), (-9.5, -6.5, 1.8, 40), (19.5, -9.8, 1.3, 15)):
        torus(1.8, 0.35, 'gold', (x, y, z), (0, 0, yaw), segments=4, sides=5, scale=(1.3, 1, 1))
    for x in (-7.2, 7.2):
        torus(1.5, 0.3, 'gold', (x, 1.6, 9.0), (70, 90, 0), segments=4, sides=5)

def build_x12346():
    """Bridle."""
    bridle('x12346')


def build_x12347():
    """Enchanted Bridle (the glowing runes are painted)."""
    bridle('x12347')


def generic(design):
    """Every design without a build_<design> of its own, by the builder classify.py gave it."""
    entry = DESIGNS[design]
    builder = entry['builder']
    if builder == 'rock':
        rock(design, **entry.get('rock', {}))
    elif builder == 'outline_slab':
        outline_slab(design, entry.get('slab_depth', 0.12), entry.get('slab_class', 'gold'),
                     entry.get('slab_bevel', 0.3))
    elif builder == 'sphere':
        build_sphere(design)
    elif builder == 'disc':
        build_disc(design)
    elif builder in ('auto_weapon', 'ring_generic', 'amulet_generic', 'book_generic', 'vessel_upright'):
        globals()[builder](design)
    else:
        raise ValueError(f'{design}: no builder {builder}')


# --- Build -----------------------------------------------------------------------------------------------------
def build(design):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    parts.clear()
    builder = globals().get('build_' + design)
    if builder:
        builder()
    else:
        generic(design)
    for obj in bpy.context.scene.objects:
        obj.select_set(obj in parts)
    with bpy.context.temp_override(active_object=parts[0], selected_editable_objects=parts, object=parts[0]):
        bpy.ops.object.join()
    obj = parts[0]
    obj.name = obj.data.name = design
    points = [v.co for v in obj.data.vertices]
    lo = Vector([min(p[i] for p in points) for i in range(3)])
    hi = Vector([max(p[i] for p in points) for i in range(3)])
    # Longest horizontal side = the binding's length; origin at the centre of the footprint, lowest point at 0.
    scale = DESIGNS[design]['length'] / max(hi.x - lo.x, hi.y - lo.y)
    shift = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for v in obj.data.vertices:
        v.co = (v.co - shift) * scale
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    with bpy.context.temp_override(active_object=obj, selected_objects=[obj], object=obj):
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    obj.data.calc_loop_triangles()
    size = (hi - lo) * scale
    os.makedirs(PROCEDURAL, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(PROCEDURAL, f'{design}.blend'))
    bpy.ops.export_scene.gltf(filepath=os.path.join(PROCEDURAL, f'{design}.glb'), export_format='GLB',
                              use_selection=False, export_apply=True)
    report = {'triangles': len(obj.data.loop_triangles), 'size': [round(v, 1) for v in size]}
    print('BUILT', design, json.dumps(report))
    return report


def main():
    designs = sys.argv[sys.argv.index('--') + 1:]
    path = os.path.join(PROCEDURAL, 'built.json')
    reports = json.load(open(path)) if os.path.exists(path) else {}
    for design in designs:
        reports[design] = build(design)
    os.makedirs(PROCEDURAL, exist_ok=True)
    with open(path, 'w') as handle:
        json.dump(reports, handle, indent=1, sort_keys=True)


main()
