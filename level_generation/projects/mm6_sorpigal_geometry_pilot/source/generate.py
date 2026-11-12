"""Generate the visible detail geometry of the pilot buildings (see ../README.md).

For every relief wall face of a building, the texture's surface material class map (plus per-texture rectangles from
buildings.yml) gives a depth level per texel: wood stands proud, glass and door leaves are recessed, the rest stays on
the wall plane. The levels become integer polygons in the face's texture space, faces at their depth, and side walls
where the depth steps, so the painted timbers, frames and openings get real depth with the same texels. Window sills,
the gable roof (thicker, deeper eaves, rafter ends, ridge cap) and the hidden original faces follow buildings.yml.

  python3 source/generate.py [--map <stem>]     (config: source/maps/<stem>.yml + source/textures.yml)

Output: build/<stem>/models.txt (odmtool append format) and build/<stem>/plan.json (hidden faces, events, counts).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import mapbox_earcut
import numpy as np
import shapely
import yaml
from PIL import Image
from shapely.geometry import Point, Polygon, box
from shapely.geometry.polygon import orient

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT / 'util'))
import map_export  # noqa: E402

MASTERS = ROOT / 'assets_source/worlds/mm6/textures_x4'
CLASSES = ROOT / 'assets_source/worlds/mm6/surface_materials'
S = 4  # master texels per native texel (= per world unit on these faces)
CLASS_KEYS = {
    'wood': (255, 128, 0), 'glass': (0, 255, 255), 'iron': (0, 60, 255), 'stone': (190, 150, 90),
    'plaster': (255, 255, 255), 'mortar': (110, 110, 110), 'polished_stone': (255, 255, 170),
    'bright_metal': (160, 0, 255), 'earth': (100, 50, 20), 'painted': (255, 110, 200), 'patina': (0, 200, 110),
    'foliage': (120, 220, 0),
}
# Plain beams, boards and logs: no painted openings or frames to lift, only grain and snow lumps.
PLAIN_TIMBER = ('bem', 'ced', 'wood', 'sgstr', 'gstr', 'bdks', 'cbeam')
MAX_RELIEF_CORNERS = 300  # per texture tile; New Sorpigal's half-timbering and stained glass stay well under
UNTOUCHABLE = 0x20000000
INVISIBLE = 0x2000
CLICKABLE = 0x02000000
PLANE_BITS = 0x100 | 0x200 | 0x400
OUTSIDE = 'outside'  # a point beyond the face with no relief face there


# ---------------------------------------------------------------- texture levels

class TextureLevels:
    """Per-texture depth level image at master resolution (world units along the face normal)."""

    def __init__(self, config):
        self.config = config
        self.cache = {}

    def size(self, name):
        path = MASTERS / f'{name.lower()}.png'
        if not path.exists():  # the project's own textures (source/make_textures.py)
            path = PROJECT / 'textures/root/worlds/mm6/textures_x4' / f'{name.lower()}.png'
        with Image.open(path) as image:
            return image.size[0] // S, image.size[1] // S

    def classes(self, name):
        rgb = np.array(Image.open(CLASSES / f'{name.lower()}_m.png').convert('RGB'))
        return rgb

    def levels(self, name):
        key = name.lower()
        if key in self.cache:
            return self.cache[key]
        spec = self.config['textures'][key]
        rgb = self.classes(key)
        level = np.zeros(rgb.shape[:2], np.int16)
        masks = {}
        for cls, value in spec.get('classes', {}).items():
            hit = np.all(rgb == CLASS_KEYS[cls], axis=2)
            masks[value] = masks.get(value, np.zeros(hit.shape, bool)) | hit
        # Close gaps (lead cames, carving) of up to `close` texels; recesses are solid panels (holes filled).
        close = spec.get('close', 1)
        kernel = np.ones((close * S, close * S), np.uint8)
        opening = np.ones((S, S), np.uint8)
        for value in sorted(masks, key=lambda v: (v < 0, abs(v))):
            mask = masks[value].astype(np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, opening)
            if value < 0:
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                mask = np.zeros_like(mask)
                cv2.drawContours(mask, contours, -1, 1, thickness=cv2.FILLED)
            level[mask == 1] = value
        raised = spec.get('height')
        if raised:  # the texture's height map: its raised parts (frames, beams) stand proud
            mask = raised_mask(key, raised['above'])
            if mask is not None:
                level[(mask == 1) & (level == 0)] = raised['level']
        for x0, y0, x1, y1, value in spec.get('rects', []):
            level[y0 * S:y1 * S, x0 * S:x1 * S] = value
        self.cache[key] = level
        return level


def raised_mask(stem, above):
    """Texels of a texture's height map above `above` (0-1 of its range, blurred), cleaned of specks; None without
    a height map."""
    path = CLASSES / f'{stem}_h.png'
    if not path.exists():
        return None
    height = np.asarray(Image.open(path), np.float32)
    if height.ndim == 3:
        height = height[..., 0]
    height = cv2.GaussianBlur(height, (0, 0), 3)
    height = (height - height.min()) / max(float(np.ptp(height)), 1e-6)
    mask = (height > above).astype(np.uint8)
    kernel = np.ones((3 * S, 3 * S), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)


# ---------------------------------------------------------------- face mapping

class FaceMap:
    """Affine map between a BModel face's plane and its texture space (native texels)."""

    def __init__(self, model, face, width, height, strict=True):
        V = model['vertices']
        self.points = np.array([[V[i]['x'], V[i]['y'], V[i]['z']] for i in face['vertex_indices']], float)
        self.uvs = np.array([[u + face['texture_delta_u'], v + face['texture_delta_v']]
                             for u, v in zip(face['texture_us'], face['texture_vs'])], float)
        n = np.zeros(3)
        P = self.points
        for i in range(len(P)):
            a, b = P[i], P[(i + 1) % len(P)]
            n += [(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])]
        self.normal = n / np.linalg.norm(n)
        self.width, self.height = width, height
        # uv = M (p - p0) + uv0 with M n = 0
        i1 = 1
        i2 = next(i for i in range(2, len(P)) if np.linalg.norm(np.cross(P[i1] - P[0], P[i] - P[0])) > 1e-6)
        A = np.array([P[i1] - P[0], P[i2] - P[0], self.normal])
        B = np.array([self.uvs[i1] - self.uvs[0], self.uvs[i2] - self.uvs[0], [0, 0]])
        self.M = np.linalg.solve(A, B).T  # 2x3
        # inverse on the plane: p = p0 + E (uv - uv0)
        t1 = (P[i1] - P[0]) / np.linalg.norm(P[i1] - P[0])
        t2 = np.cross(self.normal, t1)
        T = np.array([t1, t2]).T  # 3x2
        self.E = T @ np.linalg.inv(self.M @ T)  # 3x2
        scale = np.linalg.norm(self.E, axis=0)
        if strict and not np.allclose(scale, 1.0, atol=0.05):  # the ship's hull is scaled by 3 %
            raise ValueError(f"face {face['index']} texture scale {scale} is not one texel per unit")
        for p, uv in zip(P, self.uvs):
            if not np.allclose(self.uv(p), uv, atol=0.51):  # a mapping the plane cannot reproduce: left as it is
                raise ValueError(f"face {face['index']} texture mapping is not affine on its plane")
        self.plane_d = float(self.normal @ P[0])

    def uv(self, p):
        return self.M @ (np.asarray(p, float) - self.points[0]) + self.uvs[0]

    def world(self, uv, depth=0.0):
        return self.points[0] + self.E @ (np.asarray(uv, float) - self.uvs[0]) + depth * self.normal

    def polygon_uv(self):
        return Polygon([tuple(np.round(uv)) for uv in self.uvs])


# ---------------------------------------------------------------- mesh output

class Mesh:
    def __init__(self, name):
        self.name = name
        self.vertices = []
        self.index = {}
        self.faces = []  # (attributes, polygonType, event, texture, [(vertex, u, v)])

    def vertex(self, p):
        key = tuple(int(round(c)) for c in p)
        if key not in self.index:
            self.index[key] = len(self.vertices)
            self.vertices.append(key)
        return self.index[key]

    def add(self, points, uvs, texture, normal, attributes=0, event=0, width=None):
        """points: world (float, rounded here); uvs: texels (rounded); normal: desired outward normal."""
        pts = [tuple(int(round(c)) for c in p) for p in points]
        uvl = [tuple(int(round(c)) for c in uv) for uv in uvs]
        # drop consecutive duplicates
        cleaned = []
        for p, uv in zip(pts, uvl):
            if not cleaned or cleaned[-1][0] != p:
                cleaned.append((p, uv))
        while len(cleaned) > 1 and cleaned[0][0] == cleaned[-1][0]:
            cleaned.pop()
        if len(cleaned) < 3:
            return
        P = np.array([c[0] for c in cleaned], float)
        n = np.zeros(3)
        for i in range(len(P)):
            a, b = P[i], P[(i + 1) % len(P)]
            n += [(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])]
        if np.linalg.norm(n) < 1e-6:
            return
        if n @ np.asarray(normal) < 0:
            cleaned.reverse()
            n = -n
        n /= np.linalg.norm(n)
        # Keep texture coordinates small: shift by whole tiles.
        if width:
            w, h = width
            du = int(math.floor(min(c[1][0] for c in cleaned) / w)) * w
            dv = int(math.floor(min(c[1][1] for c in cleaned) / h)) * h
            cleaned = [(p, (uv[0] - du, uv[1] - dv)) for p, uv in cleaned]
        ax = int(np.argmax(np.abs(n)))
        plane = {0: 0x400, 1: 0x200, 2: 0x100}[ax]
        if abs(n[2]) < 0.01:
            ptype = 1
        elif n[2] > 0.99:
            ptype = 3
        elif n[2] < -0.99:
            ptype = 5
        else:
            ptype = 4 if n[2] > 0 else 6
        for chunk in split_fan(cleaned):
            self.faces.append((attributes | plane | UNTOUCHABLE, ptype, event, texture,
                               [(self.vertex(p), uv[0], uv[1]) for p, uv in chunk]))

    def triangles(self):
        return sum(len(f[4]) - 2 for f in self.faces)

    def write(self, stream):
        stream.write(f'model {self.name}\n')
        for v in self.vertices:
            stream.write(f'v {v[0]} {v[1]} {v[2]}\n')
        for attributes, ptype, event, texture, verts in self.faces:
            stream.write(f'f {attributes} {ptype} {event} {texture} {len(verts)} '
                         + ' '.join(f'{i} {u} {v}' for i, u, v in verts) + '\n')


def split_fan(points, limit=20):
    """Split a convex polygon with more than `limit` vertices into fans that share vertex 0."""
    if len(points) <= limit:
        return [points]
    parts = []
    start = 1
    while start < len(points) - 1:
        end = min(start + limit - 2, len(points) - 1)
        parts.append([points[0]] + points[start:end + 1])
        start = end
    return parts


# ---------------------------------------------------------------- polygon helpers

def convex_pieces(polygon):
    """Triangulate a polygon with holes (earcut) and greedily merge triangles into convex pieces."""
    polygon = orient(polygon, 1.0)
    rings = [list(polygon.exterior.coords)[:-1]] + [list(r.coords)[:-1] for r in polygon.interiors]
    flat = np.array([p for ring in rings for p in ring], float)
    ends = np.cumsum([len(r) for r in rings]).astype(np.uint32)
    tris = mapbox_earcut.triangulate_float64(flat, ends).reshape(-1, 3)
    pieces = [list(t) for t in tris if abs(area(flat[list(t)])) > 1e-9]
    pieces = [p if area(flat[p]) > 0 else p[::-1] for p in pieces]
    changed = True
    while changed:
        changed = False
        edges = {}
        for k, piece in enumerate(pieces):
            for i in range(len(piece)):
                edges[(piece[i], piece[(i + 1) % len(piece)])] = k
        for (a, b), k in list(edges.items()):
            j = edges.get((b, a))
            if j is None or j == k or pieces[k] is None or pieces[j] is None:
                continue
            merged = merge(pieces[k], pieces[j], a, b)
            if merged and len(merged) <= 20 and is_convex(flat[merged]):
                pieces[k], pieces[j] = merged, None
                changed = True
                break
        pieces = [p for p in pieces if p is not None]
    return [simplify_collinear(flat[p]) for p in pieces]


def merge(p, q, a, b):
    """p has edge a->b, q has b->a; return the merged ring."""
    i = p.index(a)
    p = p[i:] + p[:i]          # p starts at a, p[1] == b
    j = q.index(b)
    q = q[j:] + q[:j]          # q starts at b, q[1] == a
    if p[1] != b or q[1] != a:
        return None
    return [a] + q[2:] + [b] + p[2:]


def area(points):
    x, y = points[:, 0], points[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def is_convex(points):
    n = len(points)
    for i in range(n):
        a, b, c = points[i], points[(i + 1) % n], points[(i + 2) % n]
        if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) < -1e-9:
            return False
    return True


def simplify_collinear(points):
    out = []
    n = len(points)
    for i in range(n):
        a, b, c = points[i - 1], points[i], points[(i + 1) % n]
        if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) > 1e-9:
            out.append(b)
    return np.array(out)


def polygonal(geometry):
    """Only the polygon parts of a geometry (overlays on the integer grid can leave stray lines and points)."""
    parts = polygons_of(geometry)
    return shapely.union_all(parts) if parts else Polygon()


def polygons_of(geometry):
    if geometry.is_empty:
        return []
    if geometry.geom_type == 'Polygon':
        return [geometry]
    if hasattr(geometry, 'geoms'):
        return [p for part in geometry.geoms for p in polygons_of(part)]
    return []


# ---------------------------------------------------------------- relief faces

class ReliefFace:
    def __init__(self, model, face, levels, spec):
        spec = spec or {}
        self.face = face
        self.texture = face['texture_name']
        w, h = levels.size(self.texture)
        self.map = FaceMap(model, face, w, h)
        self.size = (w, h)
        self.outline = self.map.polygon_uv()
        texlev = levels.levels(self.texture)
        umin, vmin, umax, vmax = (int(c) for c in self.outline.bounds)
        us = umin + (np.arange((umax - umin) * S) + 0.5) / S
        vs = vmin + (np.arange((vmax - vmin) * S) + 0.5) / S
        xi = np.floor(np.mod(us, w) * S).astype(int)
        yi = np.floor(np.mod(vs, h) * S).astype(int)
        raster = texlev[np.ix_(yi, xi)]
        self.regions = []  # (level, polygon in uv)
        taken = Polygon()
        for value in sorted((v for v in np.unique(raster) if v != 0), key=lambda v: -abs(v)):
            mask = (raster == value).astype(np.uint8)
            contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
            if hierarchy is None:
                continue
            shapes = []
            for k, contour in enumerate(contours):
                if hierarchy[0][k][3] != -1 or len(contour) < 3:
                    continue
                shell = self.to_uv(contour, umin, vmin)
                holes = [self.to_uv(contours[c], umin, vmin) for c in range(len(contours))
                         if hierarchy[0][c][3] == k and len(contours[c]) >= 3]
                poly = Polygon(shell, [h for h in holes if len(h) >= 3]).buffer(0)
                shapes.append(poly.simplify(spec.get('simplify', 0.8)))
            if not shapes:
                continue
            shape = polygonal(shapely.union_all(shapes, grid_size=1))
            shape = polygonal(shapely.intersection(shape, self.outline, grid_size=1))
            shape = polygonal(shapely.difference(shape, taken, grid_size=1))
            for poly in polygons_of(shape):
                if poly.area >= spec.get('min_area', 8):
                    self.regions.append((int(value), poly))
            taken = shapely.union(taken, shape, grid_size=1)
        # Budget: relief that breaks a face into a mesh of small pieces (rubble, snow, noisy class maps) is not the
        # modular detail we want and costs thousands of triangles; such a face stays flat.
        corners = sum(len(poly.exterior.coords) + sum(len(r.coords) for r in poly.interiors)
                      for _, poly in self.regions)
        tiles = max(self.outline.area / (w * h), 0.25)
        if corners / tiles > MAX_RELIEF_CORNERS:
            raise ValueError(f"face {face['index']} relief too complex ({corners / tiles:.0f} corners per tile)")
        base = shapely.difference(self.outline, taken, grid_size=1)
        self.regions += [(0, p) for p in polygons_of(base) if p.area > 0]
        self.event = face['cog_triggered_number'] if face['attributes'] & CLICKABLE else 0
        self.clickable = face['attributes'] & CLICKABLE

    @staticmethod
    def to_uv(contour, umin, vmin):
        pts = contour[:, 0, :].astype(float)
        # Contours trace pixel centres; pad half a pixel outward is not needed at 1/4-unit raster.
        return [(umin + (x + 0.5) / S, vmin + (y + 0.5) / S) for x, y in pts]

    def level_at_uv(self, uv):
        point = Point(uv)
        for value, poly in self.regions:
            if poly.covers(point):
                return value
        return None


def build_relief(mesh, relief_faces, by_plane, wall_texture_sizes):
    """Faces at their depth plus side walls where the depth steps."""
    for rf in relief_faces:
        attrs = CLICKABLE if rf.clickable else 0
        for value, poly in rf.regions:
            for piece in convex_pieces(poly):
                world = [rf.map.world(uv, value) for uv in piece]
                mesh.add(world, piece, rf.texture, rf.map.normal, attrs, rf.event, rf.size)
        for value, poly in rf.regions:
            poly = orient(poly, 1.0)
            for ring in [poly.exterior] + list(poly.interiors):
                coords = list(ring.coords)
                for a, b in zip(coords[:-1], coords[1:]):
                    side_walls(mesh, rf, value, np.array(a), np.array(b), by_plane, attrs)


def side_walls(mesh, rf, value, a, b, by_plane, attrs):
    edge = b - a
    length = float(np.linalg.norm(edge))
    if length < 1e-6:
        return
    # A horizontal step along the face's bottom edge would lie on the ground (sole beams, door thresholds):
    # never seen, and coinciding with the terrain it would bake a black patch there.
    wa, wb = rf.map.world(a), rf.map.world(b)
    bottom = rf.map.points[:, 2].min()
    if abs(wa[2] - bottom) < 0.5 and abs(wb[2] - bottom) < 0.5:
        return
    direction = edge / length
    # The region is to the left of a->b in uv space when uv is right-handed with the polygon's orientation.
    outward = np.array([direction[1], -direction[0]])
    steps = max(1, int(math.ceil(length / 2.0)))
    samples = []
    for k in range(steps):
        t0, t1 = k / steps, (k + 1) / steps
        mid = a + edge * (t0 + t1) / 2 + outward * 0.5
        samples.append((t0, t1, neighbour_level(rf, mid, by_plane)))
    # merge runs
    runs = []
    for t0, t1, level in samples:
        if runs and runs[-1][2] == level:
            runs[-1][1] = t1
        else:
            runs.append([t0, t1, level])
    for t0, t1, level in runs:
        if level == OUTSIDE:
            if value < 0:
                # A recess reaching the face's edge with no relief face beyond it: close it up to the plane.
                pa, pb = a + edge * t0, b - edge * (1 - t1)
                k = min(-value, 4)
                inward = -outward
                world = [rf.map.world(pa, value), rf.map.world(pb, value), rf.map.world(pb, 0),
                         rf.map.world(pa, 0)]
                uvs = [pa, pb, pb + inward * k, pa + inward * k]
                mesh.add(world, uvs, rf.texture, rf.map.E @ inward, attrs, rf.event, rf.size)
                continue
            level = 0
        if level is None or level >= value:
            continue
        pa, pb = a + edge * t0, b - edge * (1 - t1)
        depth = value - level
        k = min(depth, 4)
        inward = -outward
        world = [rf.map.world(pa, level), rf.map.world(pb, level), rf.map.world(pb, value), rf.map.world(pa, value)]
        uvs = [pa + inward * k, pb + inward * k, pb, pa]
        normal_world = rf.map.E @ outward
        mesh.add(world, uvs, rf.texture, normal_world, attrs, rf.event, rf.size)


def neighbour_level(rf, uv, by_plane):
    level = rf.level_at_uv(uv)
    if level is not None:
        return level
    world = rf.map.world(uv)
    key = plane_key(rf.map)
    for other in by_plane.get(key, []):
        if other is rf:
            continue
        level = other.level_at_uv(other.map.uv(world))
        if level is not None:
            return level
    return OUTSIDE


def plane_key(face_map):
    n = face_map.normal
    return (round(n[0], 3), round(n[1], 3), round(n[2], 3), round(face_map.plane_d))


# ---------------------------------------------------------------- sills

def build_sills(mesh, rf, levels, spec, trim):
    """A wooden sill under every window: below the frame, a little wider, standing out past it."""
    tex = levels.levels(rf.texture)
    w, h = rf.size
    glass_level = spec['glass_level']
    down = rf.map.M @ np.array([0, 0, -1.0])  # uv direction of world down
    down = np.round(down)
    if not np.allclose(np.abs(down).sum(), 1):
        return
    # One sill and one head per window: panes split by mullions and transoms (within 16 texels of each other) are
    # one window (a sill under every pane and a head over the lower row put bars across the barn windows).
    windows = []
    for pane in (poly for value, poly in rf.regions if value == glass_level):
        grown = pane.buffer(16, join_style=2)
        for k, window in enumerate(windows):
            if grown.intersects(window):
                windows[k] = shapely.union(window, pane)
                break
        else:
            windows.append(pane)
    for poly in windows:
        u0, v0, u1, v1 = poly.bounds
        if (u1 - u0) < 8 or (v1 - v0) < 8:
            continue
        cu, cv = (u0 + u1) / 2, (v0 + v1) / 2
        # frame below the glass in uv: march along `down` from the glass edge while the level is wood (> 0)
        edge_v = v1 if down[1] > 0 else v0
        if down[0] != 0:
            continue
        step = 1 if down[1] > 0 else -1
        v = edge_v
        while 0 <= abs(v - edge_v) < 24:
            lev = tex[int((v % h) * S + S / 2) % (h * S), int((cu % w) * S) % (w * S)]
            if lev == 0 and abs(v - edge_v) > 1:
                break
            v += step
        frame_bottom = v
        # frame sides along u
        left, right = u0, u1
        for direction in (-1, 1):
            u = u0 if direction < 0 else u1
            start = u
            while abs(u - start) < 24:
                lev = tex[int((cv % h) * S) % (h * S), int((u % w) * S + S / 2) % (w * S)]
                if lev == 0 and abs(u - start) > 1:
                    break
                u += direction
            if direction < 0:
                left = u
            else:
                right = u
        left -= spec['sill_overhang']
        right += spec['sill_overhang']
        thickness = spec['sill_thickness']
        depth = spec['sill_depth']
        v_top, v_bottom = frame_bottom, frame_bottom + step * thickness
        corners = [(left, v_top), (right, v_top), (right, v_bottom), (left, v_bottom)]
        add_box(mesh, rf.map, corners, 0, depth, trim)
        # A head over rectangular windows (pointed and round ones keep their painted arch).
        # The head goes over flat-topped windows only: the top tenth of the window's box is glass all across.
        top_band = box(u0, v0, u1, v0 + (v1 - v0) * 0.1) if step > 0 else box(u0, v1 - (v1 - v0) * 0.1, u1, v1)
        flat = shapely.intersection(poly.buffer(16, join_style=2).buffer(-16, join_style=2), top_band).area
        if spec.get('heads') and flat > 0.9 * top_band.area:
            edge = v0 if step > 0 else v1
            v = edge
            while abs(v - edge) < 24:
                lev = tex[int((v % h) * S - step * S / 2) % (h * S), int((cu % w) * S) % (w * S)]
                if lev == 0 and abs(v - edge) > 1:
                    break
                v -= step
            head = [(left, v), (right, v), (right, v - step * thickness), (left, v - step * thickness)]
            add_box(mesh, rf.map, head, 0, depth - 2, trim)
            if spec.get('jambs'):  # the kit: a full frame, jambs from the sill to the head
                jw = spec['jambs']
                for ja, jb in ((left + spec['sill_overhang'] - jw, left + spec['sill_overhang']),
                               (right - spec['sill_overhang'], right - spec['sill_overhang'] + jw)):
                    jamb = [(ja, frame_bottom), (jb, frame_bottom), (jb, v), (ja, v)]
                    add_box(mesh, rf.map, jamb, 0, depth - 3, trim)


def add_box(mesh, face_map, corners_uv, depth0, depth1, trim):
    """A box on a face: corners_uv (4, in the face's uv plane) extruded from depth0 to depth1, in the trim."""
    lo = [face_map.world(c, depth0) for c in corners_uv]
    hi = [face_map.world(c, depth1) for c in corners_uv]
    centre = np.mean(lo + hi, axis=0)
    n = face_map.normal
    trim.add(mesh, hi, n)
    for i in range(4):
        a, b = i, (i + 1) % 4
        quad = [lo[a], lo[b], hi[b], hi[a]]
        mid = np.mean(quad, axis=0)
        normal = mid - centre
        normal -= n * (normal @ n)
        trim.add(mesh, quad, normal)


def add_planar(mesh, points, texture, normal, size, scale=1):
    """Texture a planar polygon with a world-aligned projection (one texel per `scale` units)."""
    normal = np.asarray(normal, float)
    normal /= np.linalg.norm(normal)
    if abs(normal[2]) > 0.7:
        axes = (np.array([1.0, 0, 0]), np.array([0, 1.0, 0]))
    else:
        horizontal = np.cross([0, 0, 1.0], normal)
        horizontal /= np.linalg.norm(horizontal)
        axes = (horizontal, np.array([0, 0, -1.0]))
    uvs = [(float(p @ axes[0]) / scale, float(p @ axes[1]) / scale) for p in points]
    mesh.add(points, uvs, texture, normal, 0, 0, size)


class Trim:
    """A painted beam inside a wall texture: faces get u along their longest edge (one texel per unit, wrapping
    along the beam) and v squeezed into the beam's rows [v0, v1]."""

    def __init__(self, spec, levels):
        self.texture = spec['texture']
        self.v0, self.v1 = spec.get('v0'), spec.get('v1')
        self.size = levels.size(self.texture)
        self.scale = spec.get('scale', TRIM_SCALE.get(self.texture.lower(), 1))

    def add(self, mesh, points, normal, attributes=0, event=0):
        if self.v0 is None:  # no painted beam: a world-aligned projection of the whole texture
            add_planar(mesh, points, self.texture, normal, self.size, self.scale)
            return
        points = [np.asarray(p, float) for p in points]
        normal = np.asarray(normal, float)
        normal /= np.linalg.norm(normal)
        edges = [(points[(i + 1) % len(points)] - points[i]) for i in range(len(points))]
        a = max(edges, key=np.linalg.norm)
        a = a / np.linalg.norm(a)
        b = np.cross(normal, a)
        us = [p @ a for p in points]
        ws = [p @ b for p in points]
        wmin, span = min(ws), max(ws) - min(ws)
        band = self.v1 - self.v0
        scale = min(1.0, band / span) if span > 0 else 1.0
        uvs = [(u, self.v0 + (w - wmin) * scale) for u, w in zip(us, ws)]
        mesh.add(points, uvs, self.texture, normal, attributes, event, self.size)


# ---------------------------------------------------------------- gable roof

def build_gable_roof(mesh, model, spec, levels, trim):
    """Rebuild a two-slope gable roof: deeper eaves and gable overhang, a slab edge (fascia/barge), a soffit,
    rafter ends under the eaves and a ridge cap. The slopes keep their texture mapping."""
    V = model['vertices']
    faces = {f['index']: f for f in model['faces']}
    roof_tex = spec['texture']
    soffit = spec['soffit_texture']
    soffit_size = levels.size(soffit)
    roof_size = levels.size(roof_tex)
    slopes = [faces[i] for i in spec['slopes']]
    thickness = spec['thickness']
    eave_extra = spec['eave_extra']
    gable_extra = spec['gable_extra']
    ridge_points = []
    for face in slopes:
        fm = FaceMap(model, face, *roof_size, strict=False)
        P = fm.points
        top = P[:, 2].max()
        ridge = [p for p in P if abs(p[2] - top) < 0.5]
        eave = [p for p in P if abs(p[2] - top) >= 0.5]
        ridge_dir = ridge[1] - ridge[0]
        ridge_dir /= np.linalg.norm(ridge_dir)
        down_slope = np.mean(eave, axis=0) - np.mean(ridge, axis=0)
        down_slope -= ridge_dir * (down_slope @ ridge_dir)
        run = np.linalg.norm(down_slope)
        down_slope /= run
        r0, r1 = sorted(ridge, key=lambda p: p @ ridge_dir)
        r0 = r0 - ridge_dir * gable_extra
        r1 = r1 + ridge_dir * gable_extra
        e0 = r0 + down_slope * (run + eave_extra)
        e1 = r1 + down_slope * (run + eave_extra)
        top_quad = [r0, r1, e1, e0]
        n = fm.normal
        mesh.add(top_quad, [fm.uv(p) for p in top_quad], face['texture_name'], n, 0, 0, roof_size)
        bot = [p - n * thickness for p in top_quad]
        add_planar(mesh, bot[::-1], soffit, -n, soffit_size)
        # slab edges: eave fascia, two barge edges (the ridge edge is covered by the cap)
        for a, b in ((2, 3), (1, 2), (3, 0)):
            quad = [top_quad[a], top_quad[b], bot[b], bot[a]]
            outward = np.mean(quad, axis=0) - np.mean(top_quad, axis=0)
            outward -= n * (outward @ n)
            trim.add(mesh, quad, outward)
        # rafter ends: small beams under the soffit, from the wall line out to the fascia
        wall_line = r0 + down_slope * run  # the original eave line is the wall plane in these models
        count = max(2, int((np.linalg.norm(r1 - r0) - 2 * gable_extra) // spec['rafter_spacing']) + 1)
        span = np.linalg.norm(r1 - r0) - 2 * gable_extra
        for k in range(count):
            t = gable_extra + (span * k / (count - 1) if count > 1 else span / 2)
            centre = r0 + ridge_dir * t
            start = centre + down_slope * (run - spec['rafter_inset']) - n * thickness
            end = centre + down_slope * (run + eave_extra - 2) - n * thickness
            add_beam(mesh, start, end, ridge_dir, -n, spec['rafter_width'], spec['rafter_height'], trim)
        ridge_points.append((r0, r1, n))
    # ridge cap: a small beam along the ridge
    (a0, a1, n0), (b0, b1, n1) = ridge_points
    up = (n0 + n1)
    up /= np.linalg.norm(up)
    start, end = a0 - (a1 - a0) / np.linalg.norm(a1 - a0) * 2, a1 + (a1 - a0) / np.linalg.norm(a1 - a0) * 2
    add_beam(mesh, start - up * spec['ridge_height'] * 0.4, end - up * spec['ridge_height'] * 0.4,
             np.cross(up, (a1 - a0) / np.linalg.norm(a1 - a0)), up, spec['ridge_width'], spec['ridge_height'],
             trim)


def add_beam(mesh, start, end, side, up, width, height, trim):
    """A rectangular beam from start to end: `side` and `up` span its cross-section (start is the bottom centre
    when up points up from it)."""
    axis = (end - start) / np.linalg.norm(end - start)
    side = np.asarray(side, float) - axis * (np.asarray(side) @ axis)
    side /= np.linalg.norm(side)
    wanted = np.asarray(up, float)
    up = np.cross(axis, side)
    if up @ wanted < 0:
        side, up = -side, -up
    hw = width / 2
    corners = [(-hw, 0), (hw, 0), (hw, height), (-hw, height)]

    def ring(origin):
        return [origin + side * x + up * y for x, y in corners]
    s, e = ring(start), ring(end)
    centre = (start + end) / 2 + up * height / 2
    for i in range(4):
        j = (i + 1) % 4
        quad = [s[i], s[j], e[j], e[i]]
        normal = np.mean(quad, axis=0) - centre
        normal -= axis * (normal @ axis)
        trim.add(mesh, quad, normal)
    trim.add(mesh, e, axis)
    trim.add(mesh, s[::-1], -axis)


# ---------------------------------------------------------------- posts

def build_post(mesh, model, faces, spec, levels):
    """Replace a square box post (its four side faces) with a chamfered shaft on a base block, a capital and
    diagonal brackets up to the beam it carries."""
    V = model['vertices']
    pts = np.array([[V[i]['x'], V[i]['y'], V[i]['z']] for f in model['faces'] if f['index'] in faces
                    for i in f['vertex_indices']], float)
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    cx, cy = (lo[:2] + hi[:2]) / 2
    half = (hi[0] - lo[0]) / 2
    z0, z1 = lo[2], hi[2]
    wood = Trim({'texture': spec['texture']}, levels)
    base_h, cap_h = spec['base_height'], spec['cap_height']
    grow = spec['block_grow']
    # The base stands on the floor the post stands on: clipped to it, so a post at a platform's edge has a base
    # flush with the edge instead of one hanging over it (tavern porch, user 2026-11-11).
    shaft = box(cx - half, cy - half, cx + half, cy + half)
    floor = support_under(model, shaft, z0)
    base = box(cx - half - grow, cy - half - grow, cx + half + grow, cy + half + grow)
    if floor is not None:
        base = shapely.intersection(base, shapely.union(floor, shaft, grid_size=1), grid_size=1)
    add_prism(mesh, wood, base, z0, z0 + base_h, bottom=False)
    add_block(mesh, wood, cx, cy, half + grow - 2, z1 - cap_h, z1)
    # chamfered shaft: an octagon
    c = spec['chamfer']
    ring = [(half - c, -half), (half, -half + c), (half, half - c), (half - c, half),
            (-half + c, half), (-half, half - c), (-half, -half + c), (-half + c, -half)]
    bottom = [np.array([cx + x, cy + y, z0 + base_h]) for x, y in ring]
    top = [np.array([cx + x, cy + y, z1 - cap_h]) for x, y in ring]
    for i in range(8):
        j = (i + 1) % 8
        quad = [bottom[i], bottom[j], top[j], top[i]]
        mid = np.mean(quad, axis=0)
        wood.add(mesh, quad, [mid[0] - cx, mid[1] - cy, 0])
    # brackets: from the shaft up to the beam soffit, along each given horizontal direction
    for direction in spec['brackets'].get(str(faces[0]), spec['brackets'].get('default', [])):
        d = np.array(direction + [0], float)
        d /= np.linalg.norm(d)
        reach, drop, size = spec['bracket_reach'], spec['bracket_drop'], spec['bracket_size']
        start = np.array([cx, cy, z1 - cap_h - drop]) + d * (half - 2)
        end = np.array([cx, cy, z1]) + d * (half + reach)
        side = np.cross(d, [0, 0, 1.0])
        add_beam(mesh, start, end, side, np.cross(end - start, side), size, size, wood)


def support_under(model, footprint, z):
    """The union of the model's upward floor faces at height z around a footprint (floors usually leave a hole
    where a post stands), or None when the footprint touches none of them (it stands on the terrain)."""
    pieces = []
    for face, P, n in model_faces(model):
        if n[2] > 0.98 and all(abs(p[2] - z) < 2 for p in P):
            pieces.append(Polygon([(p[0], p[1]) for p in P]).buffer(0))
    if not pieces:
        return None
    floor = shapely.union_all(pieces, grid_size=1)
    return floor if floor.buffer(1).intersects(footprint) else None


def add_prism(mesh, trim, plan, z0, z1, bottom=True):
    """A vertical prism on a plan polygon (or several) from z0 to z1; no bottom for one standing on a floor."""
    for poly in polygons_of(plan):
        for piece in convex_pieces(poly):
            trim.add(mesh, [np.array([px, py, z1]) for px, py in piece], [0, 0, 1])
            if bottom:
                trim.add(mesh, [np.array([px, py, z0]) for px, py in piece[::-1]], [0, 0, -1])
        ring = list(orient(poly, 1.0).exterior.coords)
        for (ax, ay), (bx, by) in zip(ring[:-1], ring[1:]):
            quad = [np.array([ax, ay, z0]), np.array([bx, by, z0]), np.array([bx, by, z1]), np.array([ax, ay, z1])]
            trim.add(mesh, quad, [by - ay, ax - bx, 0])


def add_block(mesh, trim, cx, cy, half, z0, z1):
    corners = [(-half, -half), (half, -half), (half, half), (-half, half)]
    lo = [np.array([cx + x, cy + y, z0]) for x, y in corners]
    hi = [np.array([cx + x, cy + y, z1]) for x, y in corners]
    trim.add(mesh, hi, [0, 0, 1])
    trim.add(mesh, lo[::-1], [0, 0, -1])
    for i in range(4):
        j = (i + 1) % 4
        quad = [lo[i], lo[j], hi[j], hi[i]]
        mid = np.mean(quad, axis=0)
        trim.add(mesh, quad, [mid[0] - cx, mid[1] - cy, 0])


# ---------------------------------------------------------------- coping, arch rings, roof trim

def face_points(model, face):
    V = model['vertices']
    return [np.array([V[i]['x'], V[i]['y'], V[i]['z']], float) for i in face['vertex_indices']]


def newell(points):
    n = np.zeros(3)
    for i in range(len(points)):
        a, b = points[i], points[(i + 1) % len(points)]
        n += [(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])]
    return n / np.linalg.norm(n)


def add_solid(mesh, trim, rings, closed_ends=True):
    """A loft through parallel rings of equal length (bottom first): sides, top and optionally bottom. A last ring
    that collapses to a point (all corners equal) makes a pyramid."""
    rings = [list(r) for r in rings]
    centre = np.mean([p for r in rings for p in r], axis=0)
    count = len(rings[0])
    for lo, hi in zip(rings[:-1], rings[1:]):
        for i in range(count):
            j = (i + 1) % count
            quad = [lo[i], lo[j], hi[j], hi[i]]
            mid = np.mean(quad, axis=0)
            axis = np.mean(hi, axis=0) - np.mean(lo, axis=0)
            axis /= max(np.linalg.norm(axis), 1e-9)
            core = np.mean(lo + hi, axis=0)
            outward = (mid - core) - axis * ((mid - core) @ axis)
            normal = newell([np.asarray(p, float) for p in quad]) if len({tuple(np.round(p)) for p in quad}) >= 3 \
                else outward
            trim.add(mesh, quad, normal if normal @ outward > 0 else -normal)
    up = np.mean(rings[-1], axis=0) - np.mean(rings[0], axis=0)
    trim.add(mesh, rings[-1], up)
    if closed_ends:
        trim.add(mesh, rings[0][::-1], -up)


def chamfered_rings(corners, base, n, thickness, chamfer, across=None):
    """Rings of a slab on a rectangle `corners` (4 points at `base`, along normal n): straight sides up to
    thickness - chamfer, then a weathered top inset by `chamfer` (only across the `across` axis when given)."""
    bottom = [base + p for p in corners]
    if not chamfer:
        return [bottom, [p + n * thickness for p in bottom]]
    middle = [p + n * (thickness - chamfer) for p in bottom]
    centre = np.mean(corners, axis=0)
    top = []
    for p in corners:
        d = p - centre
        if across is not None:
            d = across * (d @ across)
        length = np.linalg.norm(d)
        top.append(base + p - (d / length * chamfer if length > 1e-9 else 0) + n * thickness)
    return [bottom, middle, top]


def build_coping(mesh, model, spec, levels):
    """Coping stones along thin top faces (parapets, wall tops): blocks a little wider than the face, with joints."""
    faces = {f['index']: f for f in model['faces']}
    trim = Trim({'texture': spec['texture']}, levels)
    for index in spec['faces']:
        P = face_points(model, faces[index])
        n = newell(P)
        edges = [P[(i + 1) % len(P)] - P[i] for i in range(len(P))]
        a = max(edges, key=np.linalg.norm)
        a /= np.linalg.norm(a)
        w = np.cross(n, a)
        c = np.mean(P, axis=0)
        ss = [(p - c) @ a for p in P]
        ts = [(p - c) @ w for p in P]
        s0, s1 = min(ss), max(ss)
        t0, t1 = min(ts) - spec['overhang'], max(ts) + spec['overhang']
        count = max(1, int(round((s1 - s0) / spec['block'])))
        gap = spec['gap'] / 2
        chamfer = spec.get('chamfer', 0)
        pyramid = spec.get('pyramid', 0)
        for k in range(count):
            sa = s0 + (s1 - s0) * k / count + (gap if k else 0)
            sb = s0 + (s1 - s0) * (k + 1) / count - (gap if k < count - 1 else 0)
            corners = [a * x + w * y for x, y in ((sa, t0), (sb, t0), (sb, t1), (sa, t1))]
            # Wall copings weather across the wall only; a single cap stone all round.
            rings = chamfered_rings(corners, c, n, spec['thickness'], chamfer, None if count == 1 else w)
            if pyramid:
                apex = c + np.mean(corners, axis=0) + n * (spec['thickness'] + pyramid)
                rings.append([apex] * 4)
            add_solid(mesh, trim, rings)
        merlons = spec.get('merlons')
        if merlons:
            period = merlons['length'] + merlons['gap']
            count = max(1, int((s1 - s0 + merlons['gap']) // period))
            start = s0 + ((s1 - s0) - (count * period - merlons['gap'])) / 2
            half = spec['overhang'] - merlons.get('inset', 2)
            for k in range(count):
                sa = start + k * period
                sb = sa + merlons['length']
                corners = [(sa, min(ts) - half), (sb, min(ts) - half), (sb, max(ts) + half), (sa, max(ts) + half)]
                bottom = [c + a * x + w * y + n * spec['thickness'] for x, y in corners]
                top = [p + n * merlons['height'] for p in bottom]
                add_solid(mesh, trim, (bottom, top), closed_ends=False)


def build_arch_ring(mesh, model, spec, levels):
    """Voussoirs: a ring of stone blocks around an arch opening on each side wall, standing out of the wall."""
    faces = {f['index']: f for f in model['faces']}
    trim = Trim({'texture': spec['texture']}, levels)
    axis = spec['axis']
    others = [k for k in range(3) if k != axis]
    for plane in spec['planes']:
        value, sign = plane
        points = {}
        for index in spec['faces']:
            for p in face_points(model, faces[index]):
                if abs(p[axis] - value) < 0.5:
                    points[tuple(p)] = p
        pts = list(points.values())
        cu = np.mean([p[others[0]] for p in pts])
        cz = min(p[2] for p in pts)
        pts.sort(key=lambda p: math.atan2(p[2] - cz, p[others[0]] - cu))
        poly = [np.array([p[others[0]], p[2]]) for p in pts]
        centre = np.array([cu, cz])

        def normal_of(a, b):
            d = b - a
            nrm = np.array([d[1], -d[0]]) / np.linalg.norm(d)
            return nrm if nrm @ ((a + b) / 2 - centre) > 0 else -nrm
        seg_normals = [normal_of(poly[i], poly[i + 1]) for i in range(len(poly) - 1)]
        vert_normals = [seg_normals[0]] + [(seg_normals[i - 1] + seg_normals[i]) / np.linalg.norm(
            seg_normals[i - 1] + seg_normals[i]) for i in range(1, len(poly) - 1)] + [seg_normals[-1]]
        lengths = [np.linalg.norm(poly[i + 1] - poly[i]) for i in range(len(poly) - 1)]
        total = sum(lengths)
        cum = np.concatenate([[0], np.cumsum(lengths)])

        def at(s):
            i = min(int(np.searchsorted(cum, s, side='right')) - 1, len(lengths) - 1)
            t = (s - cum[i]) / lengths[i]
            point = poly[i] + (poly[i + 1] - poly[i]) * t
            nrm = seg_normals[i]
            return point, nrm

        def to3d(uv, h):
            p = np.zeros(3)
            p[others[0]] = uv[0]
            p[2] = uv[1]
            p[axis] = value + sign * h
            return p
        count = max(2, int(round(total / spec['block'])))
        gap = spec['gap'] / 2
        for k in range(count):
            sa = total * k / count + gap
            sb = total * (k + 1) / count - gap
            inner = [at(sa)]
            inner += [(poly[i], vert_normals[i]) for i in range(1, len(poly) - 1) if sa < cum[i] < sb]
            inner.append(at(sb))
            inner_pts = [p for p, _ in inner]
            outer_pts = [p + nrm * spec['width'] for p, nrm in inner]
            ring2d = inner_pts + outer_pts[::-1]
            front = Polygon([tuple(q) for q in ring2d])
            if not front.is_valid or front.area < 1:
                continue
            for piece in convex_pieces(orient(front, 1.0)):
                trim.add(mesh, [to3d(q, spec['depth']) for q in piece], np.eye(3)[axis] * sign)
            for chain, facing in ((inner_pts, -1), (outer_pts, 1)):
                for i in range(len(chain) - 1):
                    q0, q1 = chain[i], chain[i + 1]
                    quad = [to3d(q0, 0), to3d(q1, 0), to3d(q1, spec['depth']), to3d(q0, spec['depth'])]
                    nrm2 = normal_of(q0, q1) * facing
                    trim.add(mesh, quad, to3d(nrm2 + centre, 0) - to3d(centre, 0))
            for (p_in, p_out), direction in (((inner_pts[0], outer_pts[0]), -1), ((inner_pts[-1], outer_pts[-1]), 1)):
                quad = [to3d(p_in, 0), to3d(p_out, 0), to3d(p_out, spec['depth']), to3d(p_in, spec['depth'])]
                tangent = (inner_pts[-1] - inner_pts[0]) * direction
                trim.add(mesh, quad, to3d(tangent + centre, 0) - to3d(centre, 0))


def build_roof_trim(mesh, model, spec, levels):
    """Fascia boards under the eaves, rafter ends under the overhang and caps along hips and ridges."""
    faces = {f['index']: f for f in model['faces']}
    polys = {i: face_points(model, faces[i]) for i in spec['faces']}
    normals = {i: newell(P) for i, P in polys.items()}
    edge_faces = {}
    for i, P in polys.items():
        for k in range(len(P)):
            a, b = tuple(P[k]), tuple(P[(k + 1) % len(P)])
            edge_faces.setdefault(tuple(sorted((a, b))), []).append(i)
    caps = spec.get('caps')
    if caps:
        trim = Trim({'texture': caps['texture']}, levels)
        for (a, b), owners in edge_faces.items():
            if len(owners) != 2 or normals[owners[0]] @ normals[owners[1]] > 0.995:
                continue
            a, b = np.array(a), np.array(b)
            # A hip or ridge is the top of both faces along it; a slope break (a steeper face below a flatter one)
            # gets no cap.
            if abs(a[2] - b[2]) < 1 and any(max(p[2] for p in polys[o]) > a[2] + 1 for o in owners):
                continue
            up = normals[owners[0]] + normals[owners[1]]
            up /= np.linalg.norm(up)
            d = (b - a) / np.linalg.norm(b - a)
            side = np.cross(up, d)
            drop = up * caps['height'] * 0.4
            start, end = a - d * 2, b + d * 2
            low = caps.get('extend_low', 0)
            if low and abs(a[2] - b[2]) > 1:  # a hip: run its low end out to the corner of the eave lips
                horizontal = np.linalg.norm(d[:2])
                if horizontal > 0.2:
                    reach = low * math.sqrt(2) / horizontal
                    if a[2] < b[2]:
                        start = a - d * reach
                    else:
                        end = b + d * reach
            add_beam(mesh, start - drop, end - drop, side, up, caps['width'], caps['height'], trim)
    fascia, rafters = spec.get('fascia'), spec.get('rafters')
    for i, P in polys.items():
        zmin = min(p[2] for p in P)
        centre = np.mean(P, axis=0)
        for k in range(len(P)):
            a, b = P[k], P[(k + 1) % len(P)]
            if abs(a[2] - zmin) > 0.5 or abs(b[2] - zmin) > 0.5:
                continue
            if len(edge_faces[tuple(sorted((tuple(a), tuple(b))))]) != 1:
                continue
            d = b - a
            length = np.linalg.norm(d)
            if length < 1:  # a repeated vertex
                continue
            d /= length
            o = np.array([d[1], -d[0], 0.0])
            if o @ (a - centre) < 0:
                o = -o
            if fascia:
                trim = Trim({'texture': fascia['texture']}, levels)
                shift = o * (fascia['out'] - fascia['depth'] / 2) - np.array([0, 0, fascia['height']])
                add_beam(mesh, a + shift - d * fascia['out'], b + shift + d * fascia['out'], o, [0, 0, 1],
                         fascia['depth'], fascia['height'], trim)
            if rafters:
                # 'inset': 'wall' spans the real overhang, from the wall face under the eave to the fascia; eaves
                # without a wall under them, or with less than 10 units of overhang, get none (auto rafters sat
                # hidden inside the walls).
                inset = rafters['inset']
                if inset == 'wall':
                    overhang = eave_overhang(model, a, b, o)
                    if overhang is None or overhang < 10:
                        continue
                    inset = overhang + 4
                trim = Trim({'texture': rafters['texture']}, levels)
                count = max(2, int(length // rafters['spacing']) + 1)
                margin = rafters.get('margin', rafters['spacing'] / 2)
                for r in range(count):
                    t = margin + (length - 2 * margin) * r / (count - 1)
                    point = a + d * t
                    start = point - o * inset
                    end = point - o * ((fascia['depth'] - fascia['out']) if fascia else 0)
                    add_beam(mesh, start, end, d, [0, 0, -1], rafters['width'], rafters['height'], trim)


def eave_overhang(model, a, b, o):
    """How far the eave edge a-b stands out (along o) from the wall face under it, or None without a wall."""
    d = (b - a) / np.linalg.norm(b - a)
    best = None
    for face, P, n in model_faces(model):
        if abs(n[2]) > 0.01 or n[:2] @ o[:2] < 0.95:
            continue
        P = np.asarray(P, float)
        top = P[:, 2].max()
        if not a[2] - 160 <= top <= a[2] + 2:
            continue
        along = [(q - a) @ d for q in P]
        if min(along) > np.linalg.norm(b - a) - 8 or max(along) < 8:
            continue
        distance = (a - P[0]) @ o
        if 0 <= distance <= 96 and (best is None or distance < best):
            best = distance
    return best


def wall_slices(data, models, z):
    """The vertical faces of a group of BModels cut at height z: (a, b, outward normal) in the plane."""
    slices = []
    for index in models:
        model = data['bmodels'][index]
        for face in model['faces']:
            P = face_points(model, face)
            n = newell(P)
            if abs(n[2]) > 0.01:
                continue
            hits = []
            for i in range(len(P)):
                a, b = P[i], P[(i + 1) % len(P)]
                if (a[2] - z) * (b[2] - z) < 0:
                    t = (z - a[2]) / (b[2] - a[2])
                    hits.append((a + (b - a) * t)[:2])
            if len(hits) == 2 and np.linalg.norm(hits[1] - hits[0]) > 1:
                slices.append((hits[0], hits[1], n[:2] / np.linalg.norm(n[:2])))
    return slices


def band_shape(slices, out, exclude):
    """The plan of a band standing `out` in front of every wall slice; strips run past their ends by `out`, so
    outer corners fill in, and the strips merge."""
    from shapely.geometry import box as rect
    strips = []
    for a, b, n in slices:
        d = (b - a) / np.linalg.norm(b - a)
        a2, b2 = a - d * out, b + d * out
        strips.append(Polygon([tuple(a2), tuple(b2), tuple(b2 + n * out), tuple(a2 + n * out)]))
    shape = shapely.union_all(strips, grid_size=1)
    # Nothing inside the walls: drop what a strip's corner extension pushed behind another wall.
    walls = shapely.union_all([Polygon([tuple(a), tuple(b), tuple(b - n * 64), tuple(a - n * 64)])
                               for a, b, n in slices], grid_size=1)
    shape = shapely.difference(shape, walls, grid_size=1)
    for x0, y0, x1, y1 in exclude:
        shape = shapely.difference(shape, rect(x0, y0, x1, y1), grid_size=1)
    return shape


def extrude_band(mesh, trim, shape, slices, z0, z1, bottom=True):
    """Top, bottom and the outer sides of a band plan; sides lying on a wall are left out, and the bottom when the
    band stands on the ground (a face on the terrain bakes a black patch into it)."""
    from shapely.geometry import LineString
    wall_lines = [LineString([tuple(a), tuple(b)]) for a, b, _ in slices]
    for poly in polygons_of(shape):
        for piece in convex_pieces(poly):
            if bottom:
                trim.add(mesh, [np.array([x, y, z0]) for x, y in piece[::-1]], [0, 0, -1])
            trim.add(mesh, [np.array([x, y, z1]) for x, y in piece], [0, 0, 1])
        oriented = orient(poly, 1.0)
        for ring in [oriented.exterior] + list(oriented.interiors):
            coords = list(ring.coords)
            for (ax, ay), (bx, by) in zip(coords[:-1], coords[1:]):
                mid = Point((ax + bx) / 2, (ay + by) / 2)
                if any(line.distance(mid) < 1.5 for line in wall_lines):
                    continue
                quad = [np.array([ax, ay, z0]), np.array([bx, by, z0]), np.array([bx, by, z1]),
                        np.array([ax, ay, z1])]
                trim.add(mesh, quad, [by - ay, ax - bx, 0])


def build_band(mesh, data, spec, levels):
    """A plinth course, string course or cornice in front of a group of BModels' walls, optionally on corbels."""
    trim = Trim({'texture': spec['texture']}, levels)
    slices = wall_slices(data, spec['models'], spec['slice_z'])
    shape = band_shape(slices, spec['out'], spec.get('exclude', []))
    # A plinth starting at the foot of its models stands on the ground: no bottom face.
    foot = min(v['z'] for index in spec['models'] for v in data['bmodels'][index]['vertices'])
    extrude_band(mesh, trim, shape, slices, spec['z0'], spec['z1'], bottom=spec['z0'] > foot + 2)
    corbels = spec.get('corbels')
    if corbels:
        for a, b, n in slices:
            length = np.linalg.norm(b - a)
            if length < corbels['spacing']:
                continue
            d = (b - a) / length
            count = int(length // corbels['spacing'])
            hw = corbels['width'] / 2
            for k in range(count):
                c = a + d * (length * (k + 0.5) / count)
                foot = [c - d * hw, c + d * hw, c + d * hw + n * corbels['out'], c - d * hw + n * corbels['out']]
                bottom = [np.array([x, y, spec['z0'] - corbels['height']]) for x, y in foot]
                top = [np.array([x, y, spec['z0']]) for x, y in foot]
                add_solid(mesh, trim, (bottom, top))


def build_quoins(mesh, data, spec, levels):
    """Quoin stones up every convex vertical corner of a group of BModels: courses of `height`, alternating a long and
    a short return along the two walls, standing `out` proud. `post: true` makes one block the corner's full height
    (timber corner posts)."""
    trim = Trim(spec.get('trim', {'texture': spec.get('texture')}), levels)
    corners = {}
    for index in spec['models']:
        model = data['bmodels'][index]
        for face in model['faces']:
            P = face_points(model, face)
            n = newell(P)
            if abs(n[2]) > 0.01:
                continue
            width = max(np.linalg.norm((p - q)[:2]) for p in P for q in P)
            if width < spec.get('min_wall', 96):
                continue
            centre = np.mean(P, axis=0)[:2]
            for p in P:
                key = (round(p[0]), round(p[1]))
                entry = corners.setdefault(key, {'normals': [], 'z': [], 'runs': []})
                entry['z'].append(p[2])
                if not any(np.allclose(n[:2], m) for m in entry['normals']):
                    entry['normals'].append(n[:2] / np.linalg.norm(n[:2]))
                    run = centre - p[:2]
                    entry['runs'].append(run / max(np.linalg.norm(run), 1e-9))
    for (x, y), entry in corners.items():
        if len(entry['normals']) != 2:
            continue
        na, nb = entry['normals']
        if abs(na @ nb) > 0.1:
            continue
        # Convex (outer) corner: each wall runs away from the corner against the other wall's normal.
        run_a, run_b = entry['runs']
        if run_a @ nb > -0.5 or run_b @ na > -0.5:
            continue
        if min(entry['z']) > spec.get('ground_z', 1e9):
            continue
        c = np.array([x, y], float)
        # Convex corner: each wall runs away from the corner against the other wall's normal.
        ta, tb = -nb, -na
        z0, z1 = max(min(entry['z']), spec.get('z_min', -1e9)), min(max(entry['z']), spec.get('z_max', 1e9))
        if z1 - z0 < spec.get('min_height', 256):
            continue
        courses = 1 if spec.get('post') else int((z1 - z0) // spec['height'])
        out, gap = spec['out'], 0 if spec.get('post') else spec.get('gap', 2)
        if spec.get('post'):
            spec = {**spec, 'height': z1 - z0}
        for k in range(courses):
            la, lb = (spec['long'], spec['short']) if k % 2 == 0 else (spec['short'], spec['long'])
            zb = z0 + k * spec['height'] + gap / 2
            zt = z0 + (k + 1) * spec['height'] - gap / 2
            plan = [c + na * out + nb * out, c + na * out + ta * la, c + ta * la, c, c + tb * lb, c + nb * out + tb * lb]
            poly = orient(Polygon([tuple(q) for q in plan]), 1.0)
            for piece in convex_pieces(poly):
                trim.add(mesh, [np.array([qx, qy, zt]) for qx, qy in piece], [0, 0, 1])
            ring = list(poly.exterior.coords)
            for (ax, ay), (bx, by) in zip(ring[:-1], ring[1:]):
                mid = np.array([(ax + bx) / 2, (ay + by) / 2])
                # sides lying on a wall face are hidden
                if abs((mid - c) @ na) < 0.5 or abs((mid - c) @ nb) < 0.5:
                    continue
                quad = [np.array([ax, ay, zb]), np.array([bx, by, zb]), np.array([bx, by, zt]), np.array([ax, ay, zt])]
                trim.add(mesh, quad, [by - ay, ax - bx, 0])


def build_frame(mesh, spec, levels):
    """A stone surround (two jambs and a lintel) around a rectangular opening in a wall plane: the opening spans
    [u0, u1] along the wall and [z0, z1]; the wall plane is `plane` on `axis` (0 x, 1 y) with outward `sign`."""
    trim = Trim({'texture': spec['texture']}, levels)
    axis, sign, w, out = spec['axis'], spec['sign'], spec['width'], spec['out']
    other = 1 - axis

    def point(u, z, h):
        p = np.zeros(3)
        p[other] = u
        p[axis] = spec['plane'] + sign * h
        p[2] = z
        return p
    u0, u1, z0, z1 = spec['u0'], spec['u1'], spec['z0'], spec['z1']
    for a, b, c, d in ((u0 - w, u0, z0, z1 + w), (u1, u1 + w, z0, z1 + w), (u0, u1, z1, z1 + w)):
        bottom = [point(a, c, 0), point(b, c, 0), point(b, c, out), point(a, c, out)]
        top = [point(a, d, 0), point(b, d, 0), point(b, d, out), point(a, d, out)]
        add_solid(mesh, trim, (bottom, top), closed_ends=False)


def build_beams(mesh, spec, levels):
    """Straight timbers (kerbs, rails) between two points: `width` across, `height` up from the line."""
    trim = Trim({'texture': spec['texture']}, levels)
    for start, end in spec['lines']:
        a, b = np.array(start, float), np.array(end, float)
        d = (b - a) / np.linalg.norm(b - a)
        side = np.cross([0, 0, 1.0], d)
        add_beam(mesh, a, b, side, [0, 0, 1], spec['width'], spec['height'], trim)


def build_piles(mesh, spec, levels):
    """Square posts every `spacing` along lines, from z0 to z1 (piles under a pier, bollards on it)."""
    trim = Trim({'texture': spec['texture']}, levels)
    half = spec['size'] / 2
    for start, end in spec['lines']:
        a, b = np.array(start[:2], float), np.array(end[:2], float)
        length = np.linalg.norm(b - a)
        count = max(1, int(length // spec['spacing']) + 1)
        for k in range(count):
            c = a + (b - a) * (k / (count - 1) if count > 1 else 0.5)
            ring = [(-half, -half), (half, -half), (half, half), (-half, half)]
            bottom = [np.array([c[0] + x, c[1] + y, spec['z0']]) for x, y in ring]
            top = [np.array([c[0] + x, c[1] + y, spec['z1']]) for x, y in ring]
            add_solid(mesh, trim, (bottom, top), closed_ends=False)


def build_wales(mesh, data, spec, levels):
    """Wales: heavy planks along a hull, cut from every hull face of the models at heights `z` and laid on it,
    standing `out` proud along the face normal."""
    trim = Trim({'texture': spec['texture']}, levels)
    textures = {t.lower() for t in spec['textures']}
    half = spec['height'] / 2
    for index in spec['models']:
        model = data['bmodels'][index]
        for face, P, n in model_faces(model):
            if face['texture_name'].lower() not in textures or abs(n[2]) > 0.6:
                continue
            if 'side' in spec and np.sign(n[spec['side'][0]]) != spec['side'][1]:
                continue
            for z in spec['z']:
                hits = []
                for i in range(len(P)):
                    a, b = P[i], P[(i + 1) % len(P)]
                    if (a[2] - z) * (b[2] - z) < 0:
                        hits.append(a + (b - a) * (z - a[2]) / (b[2] - a[2]))
                if len(hits) != 2 or np.linalg.norm(hits[1] - hits[0]) < 8:
                    continue
                a, b = hits
                d = (b - a) / np.linalg.norm(b - a)
                # the plank lies on the face: its height runs up the face, its thickness along the normal
                up = np.cross(n, d)
                if up[2] < 0:
                    up = -up
                ring = [-up * half, up * half, up * half + n * spec['out'], -up * half + n * spec['out']]
                start, end = [a + q for q in ring], [b + q for q in ring]
                for i in range(1, 4):  # side 0 lies on the hull
                    j = (i + 1) % 4
                    quad = [start[i], start[j], end[j], end[i]]
                    trim.add(mesh, quad, np.mean(quad, axis=0) - (a + b) / 2 - n * spec['out'] / 2)


def as_list(value):
    return value if isinstance(value, list) else [value]


# ---------------------------------------------------------------- automatic configuration

DOOR_NAMES = ('dr', 'dor', 'door')
STONE_TOPS = ('rbl', 'tew', 'tav', 't1', 't3', 'granite', 'crdflr', 'cbrd', 'cbmx', 'bemob', '6wtr', 'cs', 'hc', 'gb',
              'str', 'sgstrsb')
NOT_STONE_TOPS = ('tavrf', 'strroof', 'cstr', 't1f')  # roofs and floor tiles
# Wooden walls: no stone plinth under them (it hid the painted sole beam of half-timbering, user 2026-11-11).
TIMBER = ('pxstr', 'rh', 'pbr', 'dkw', 'sdkw', 'sgstrst', 'sgstrl', 'sgstrr', 'sgstrw', 'sgstrd')
PAINTED_TIMBER = ('pxstr', 'rh', 'pbr')  # painted sole beams: no plinth
PLANK = ('dkw', 'sdkw', 'sgstrst', 'sgstrl', 'sgstrr', 'sgstrw', 'sgstrd')
WALLISH = ('stone', 'plaster', 'brick', 'polished_stone', 'mortar')


CLASS_CACHE = {}


def class_fractions(stem):
    if stem in CLASS_CACHE:
        return CLASS_CACHE[stem]
    path = CLASSES / f'{stem}_m.png'
    if not path.exists():
        CLASS_CACHE[stem] = None
        return None
    rgb = np.asarray(Image.open(path).convert('RGB')).reshape(-1, 3).astype(np.uint32)
    packed = (rgb[:, 0] << 16) | (rgb[:, 1] << 8) | rgb[:, 2]
    names = {v: k for k, v in CLASS_KEYS.items() if v}
    names[(220, 30, 30)] = 'brick'
    values, counts = np.unique(packed, return_counts=True)
    result = {}
    for value, count in zip(values, counts):
        key = names.get((int(value) >> 16, (int(value) >> 8) & 255, int(value) & 255), 'other')
        result[key] = result.get(key, 0) + count / len(packed)
    CLASS_CACHE[stem] = result
    return result


def auto_texture_spec(stem, clickable, levels):
    """Depth levels for a wall texture from its class map: windows set in, timbers proud, doors recessed."""
    fractions = class_fractions(stem)
    if fractions is None:
        return None
    plain = stem.startswith(PLAIN_TIMBER)
    if plain and fractions.get('glass', 0) < 0.02:
        return None
    if clickable and any(part in stem for part in DOOR_NAMES):
        w, h = levels.size(stem)
        return {'sills': False, 'rects': [[0, 0, w, h, -12]]}
    wall = sum(fractions.get(k, 0) for k in WALLISH)
    wood, glass = fractions.get('wood', 0), fractions.get('glass', 0)
    classes = {}
    if glass >= 0.02:
        classes.update({'glass': -12, 'iron': -12})
    if 0.10 <= wood <= 0.60 and wall >= 0.25 and not plain:
        classes['wood'] = 6 if glass < 0.02 else 5
    if not classes:
        # Wood on wood (plank walls with beams): the classes are one; the height map's raised parts are the frames.
        # Only a few large raised shapes are frames; rubble, logs and snow give hundreds of lumps.
        mask = raised_mask(stem, 0.78) if wood >= 0.6 and not plain else None
        if mask is not None and 0.05 <= mask.mean() <= 0.45:
            count, _, stats, _ = cv2.connectedComponentsWithStats(mask)
            big = [a for a in stats[1:, 4] if a >= 0.01 * mask.size]
            if len(big) <= 12 and sum(big) >= 0.8 * mask.sum():
                return {'height': {'above': 0.78, 'level': 5}, 'close': 2, 'simplify': 1.5, 'min_area': 40}
        return None
    spec = {'classes': classes}
    if glass >= 0.02:
        spec.update({'close': 3, 'simplify': 1.2, 'min_area': 30})
    return spec


def model_faces(model):
    for face in model['faces']:
        if face['attributes'] & INVISIBLE or len(face['vertex_indices']) < 3:
            continue
        P = face_points(model, face)
        yield face, P, newell(P)


def auto_posts(model):
    """Square box posts: four narrow vertical faces closing a column at most 56 units wide."""
    narrow = []
    for face, P, n in model_faces(model):
        if abs(n[2]) > 0.01:
            continue
        width = max(np.linalg.norm((p - q)[:2]) for p in P for q in P)
        height = P[:, 2].max() - P[:, 2].min() if isinstance(P, np.ndarray) else max(p[2] for p in P) - min(p[2] for p in P)
        if width <= 56 and height >= 96:
            narrow.append((face['index'], np.array(P), n))
    groups, used = [], set()
    for i, (fi, P, n) in enumerate(narrow):
        if fi in used:
            continue
        lo, hi = P.min(axis=0), P.max(axis=0)
        members = [(fi, n)]
        for fj, Q, m in narrow[i + 1:]:
            if fj in used:
                continue
            qlo, qhi = Q.min(axis=0), Q.max(axis=0)
            if (np.all(np.abs(qlo[:2] - lo[:2]) <= 56) and np.all(np.abs(qhi[:2] - hi[:2]) <= 56)
                    and abs(qlo[2] - lo[2]) < 1 and abs(qhi[2] - hi[2]) < 1):
                members.append((fj, m))
        normals = {(round(m[0]), round(m[1])) for _, m in members}
        if len(members) == 4 and len(normals) == 4:
            groups.append([f for f, _ in members])
            used.update(f for f, _ in members)
    return groups


# Trim that belongs to the material it sits on (source/trim_textures.py): host texture prefix -> trim texture.
# Light granite everywhere looked pasted on dark rubble, wood and brick (user, 2026-11-11).
STONE_TRIMS = (('rbl', 'rblcut'), ('tew', 'tewcut'), ('tav', 'tavcut'), ('t1', 't1cut'), ('t3', 't1cut'),
               ('th', 'thcut'), ('rh', 'rhwood'), ('ced', 'BemHwal1'), ('bem', 'BemHwal1'), ('cs', 'cscut'),
               ('str', 'strcut'), ('hc', 'hccut'), ('gb', 'gbcut'), ('sgstrsb', 'rblcut'), ('sgstr', 'dkwood'),
               ('dkw', 'dkwood'), ('sdkw', 'dkwood'))
# Roof caps and fascia from the roof's own family.
ROOF_TRIMS = (('pxshings', 'pxshcap'), ('plruf', 'plrcap'), ('tavrf', 'TAVRF'), ('mystrya', 'tewcut'),
              ('wood012', 'WOOD012'), ('pbtrm', 'slatecap'), ('t1c', 't1cut'), ('sdknkrf', 'snowcap'),
              ('sgstrrf', 'snowcap'), ('dkwrf', 'dkwood'), ('dknkrf', 'dkwood'), ('gstrrf', 'dkwood'),
              ('pbroof', 'pbrcap'), ('bcsrf', 'pbrcap'), ('strroof', 'thatchcap'), ('roof', 'roofcap'),
              ('rblrf', 'roofcap'), ('wood013', 'WOOD013'), ('cstr', 'cscut'), ('t1f', 't1cut'))
# Dressed stone trims are projected at half their texel density: blocks twice as big, so a coping stone or a sill
# shows one or two joints instead of a grid of small ones (Astra, r2).
# Coping by material (thickness, overhang, chamfer): chunky weathered stones on rubble, a slim dressed rim on ashlar
# walls (Castle Ironfist's concepts; chunky slabs there read as rounded blocks).
COPING = {'hccut': (10, 4, 3), 'cscut': (10, 4, 3), 'tavcut': (12, 5, 4), 't1cut': (10, 4, 3), 'thcut': (10, 4, 3)}
TRIM_SCALE = {'rblcut': 2, 'tewcut': 2, 'tavcut': 2, 't1cut': 2, 'thcut': 2, 'dockdeck': 1.5, 'cscut': 2,
              'strcut': 2, 'hccut': 2, 'gbcut': 2}


def host_trim(textures, table, default):
    """The trim of the most used host texture that has one (textures: name -> area)."""
    for name, _ in sorted(textures.items(), key=lambda kv: -kv[1]):
        for prefix, trim in table:
            if name.startswith(prefix):
                return trim
    return default


def face_area(P):
    P = np.asarray(P, float)
    return 0.5 * float(np.linalg.norm(sum(np.cross(P[i], P[(i + 1) % len(P)]) for i in range(len(P)))))


def kit_texture(spec):
    """The kit's wall relief: openings set in 4-6 units, nothing raised (raised painted timber cost most of the
    triangles and could not be seen; 12-unit window recesses baked black)."""
    spec = dict(spec)
    spec['classes'] = {k: max(v, -4) for k, v in spec.get('classes', {}).items() if v < 0}
    spec['rects'] = [r[:4] + [max(r[4], -6)] for r in spec.get('rects', []) if r[4] < 0]
    spec.pop('height', None)
    return spec


def kit_building(model, textures, levels):
    """The silhouette kit (user, 2026-11-12): what the concepts add and the game can see. Eave lips with fascia
    and rafter ends, corner posts or corner stones, full window frames, door frames with a step, a footing."""
    spec = auto_building(model, textures, levels)
    walls = [f['texture_name'].lower() for f, P, n in model_faces(model) if abs(n[2]) < 0.01]
    half_timber = any(t.startswith(('pxstr', 'pbr')) for t in walls)
    timber = any(t.startswith(TIMBER) for t in walls)
    zs = [v['z'] for v in model['vertices']]
    z0 = min(zs)
    wood = {'texture': 'PXSTRST', 'v0': 166, 'v1': 181} if half_timber else spec.get('trim', {'texture': 'BemHwal1'})
    stone = spec.get('trim', {'texture': 'rblcut'}) if not timber else {'texture': 'rblcut'}
    roof = spec.get('roof_trim')
    eave_z = None
    if roof:
        trim = roof['caps']['texture']
        eave_z = min(min(p[2] for p in face_points(model, model['faces'][i])) for i in roof['faces'])
        spec['roof_trim'] = {'faces': roof['faces'], 'caps': {**roof['caps'], 'extend_low': 26}}
        # On timber houses the soffit and fascia are the house's own timber (grey slate boards read as a porch).
        spec['eave_lips'] = {'faces': roof['faces'], 'length': 26, 'thickness': 8,
                             'trim': wood if timber else {'texture': trim},
                             'fascia': {'height': 20, 'depth': 10},
                             'rafters': {'spacing': 40, 'width': 9, 'height': 10}}
    if 'sills' in spec:
        spec['sills'] = {**spec['sills'], 'glass_level': -4, 'sill_thickness': 8, 'sill_depth': 10, 'jambs': 8,
                         'heads': True}
    if 'door_frames' in spec:
        spec['door_frames'] = {**spec['door_frames'], 'width': 14, 'out': 8,
                               'step': {'trim': wood if timber else stone, 'depth': 24, 'height': 8}}
        if eave_z is not None:
            spec['door_frames']['top_limit'] = eave_z - 24
    corner = {'models': [model['index']], 'min_wall': 96, 'ground_z': z0 + 16, 'z_min': z0, 'min_height': 128}
    if timber:
        spec['quoins'] = {**corner, 'post': True, 'trim': wood, 'long': 20, 'short': 20, 'out': 6}
    else:
        spec['quoins'] = {**corner, 'trim': spec.get('trim', {'texture': 'rblcut'}), 'height': 28, 'long': 36,
                          'short': 22, 'out': 4}
    return spec


def auto_building(model, textures, levels):
    """A building spec from the model's faces: sills, roof caps and fascia, coping, posts, plinth."""
    V = model['vertices']
    zs = [v['z'] for v in V]
    z0, z1 = min(zs), max(zs)
    height = max(z1 - z0, 1)
    walls = {}
    for f, P, n in model_faces(model):
        if abs(n[2]) < 0.01:
            name = f['texture_name'].lower()
            walls[name] = walls.get(name, 0) + face_area(P)
    wall_textures = [f['texture_name'].lower() for f, P, n in model_faces(model) if abs(n[2]) < 0.01]
    stone_trim = host_trim(walls, STONE_TRIMS, 'rblcut')
    timber = any(t.startswith(TIMBER) for t in wall_textures)
    spec = {'bmodel': model['index']}
    has_glass = any(textures.get(t) and 'glass' in textures[t].get('classes', {}) for t in wall_textures)
    if has_glass:
        half_timber = any(t.startswith(('pxstr', 'pbr')) for t in wall_textures)
        spec['trim'] = {'texture': 'PXSTRST', 'v0': 166, 'v1': 181} if half_timber else {'texture': stone_trim}
        spec['sills'] = {'glass_level': -12, 'sill_overhang': 3, 'sill_thickness': 5, 'sill_depth': 10,
                         'heads': not half_timber}
    roofs, copings, caps = [], [], []
    roof_textures = {}
    for face, P, n in model_faces(model):
        P = np.array(P)
        lo = P[:, 2].min()
        extent = P.max(axis=0) - P.min(axis=0)
        if 0.2 < n[2] < 0.97 and lo >= z0 + 0.35 * height and np.linalg.norm(extent) > 160:
            roofs.append(face['index'])
            name = face['texture_name'].lower()
            roof_textures[name] = roof_textures.get(name, 0) + face_area(P)
        elif n[2] > 0.98 and lo >= z0 + 0.3 * height:
            short, long = sorted(extent[:2])
            texture = face['texture_name'].lower()
            stone_top = texture.startswith(STONE_TOPS) and not texture.startswith(NOT_STONE_TOPS)
            # A wall top: walls go down from both long edges (stair treads have a riser going up on one side).
            # true width: area over the longest edge (a diagonal strip's bounding box is wide)
            longest = max(np.linalg.norm(P[(i + 1) % len(P)] - P[i]) for i in range(len(P)))
            width = face_area(P) / max(longest, 1)
            if stone_top and 8 <= width <= 64 and wall_top(model, face, P):
                copings.append(face['index'])
            elif long <= 112 and lo - z0 >= 1.5 * long and stone_top and shaft_top(model, face, P):
                caps.append(face['index'])
    if roofs:
        trim = host_trim(roof_textures, ROOF_TRIMS, 'BemHwal1')
        spec['roof_trim'] = {'faces': roofs, 'caps': {'texture': trim, 'width': 10, 'height': 7},
                             'fascia': {'texture': trim, 'height': 14, 'depth': 10, 'out': 3},
                             'rafters': {'texture': trim, 'inset': 'wall', 'spacing': 40, 'width': 8, 'height': 10}}
    spec['coping'] = []
    if copings:  # weathered coping stones, a little proud of both wall faces
        thickness, overhang, chamfer = COPING.get(stone_trim, (18, 8, 6))
        spec['coping'].append({'faces': copings, 'texture': stone_trim, 'overhang': overhang, 'thickness': thickness,
                               'chamfer': chamfer, 'block': 56, 'gap': 2})
    if caps:  # pillar tops: one overhanging cap stone each, weathered to a low pyramid
        spec['coping'].append({'faces': caps, 'texture': stone_trim, 'overhang': 7, 'thickness': 10,
                               'chamfer': 0, 'pyramid': 14, 'block': 10000, 'gap': 0})
    posts = auto_posts(model)
    if posts:
        texture = model['faces'][posts[0][0]]['texture_name']
        spec['posts'] = {'faces': posts, 'texture': texture, 'base_height': 18, 'cap_height': 10, 'block_grow': 7,
                         'chamfer': 5, 'bracket_reach': 32, 'bracket_drop': 40, 'bracket_size': 8,
                         'brackets': post_brackets(model, posts)}
    stone_walls = [t for t in wall_textures if (class_fractions(t) or {}).get('wood', 0) < 0.1]
    # A plinth only under real buildings: stone walls a full storey high (not well rings, planters or low walls).
    wall_height = max((np.ptp([p[2] for p in P]) for f, P, n in model_faces(model)
                       if abs(n[2]) < 0.01 and f['texture_name'].lower() in stone_walls), default=0)
    # Door frames: jambs and a lintel round every clickable door face at the foot of the building.
    door_faces = [face['index'] for face, P, n in model_faces(model)
                  if face['attributes'] & CLICKABLE and abs(n[2]) < 0.01 and min(p[2] for p in P) <= z0 + 16
                  and 48 <= max(np.linalg.norm((p - q)[:2]) for p in P for q in P) <= 320
                  and 96 <= np.ptp([p[2] for p in P]) <= 320
                  and max(p[2] for p in P) < z0 + 0.7 * height]  # the door, not a wall piece up to the eaves
    if door_faces:
        half_timber = any(t.startswith(('pxstr', 'pbr')) for t in wall_textures)
        spec['door_frames'] = {'faces': door_faces, 'width': 10, 'out': 6,
                               'trim': {'texture': 'PXSTRST', 'v0': 166, 'v1': 181} if half_timber
                               else {'texture': stone_trim}}
    plank = any(t.startswith(PLANK) for t in wall_textures) and not any(t.startswith(PAINTED_TIMBER)
                                                                         for t in wall_textures)
    if plank:  # log and plank houses stand on a stone footing (the concepts); half-timbering never does
        spec['bands'] = {'models': [model['index']], 'slice_z': z0 + 40, 'z0': z0, 'z1': z0 + 16, 'out': 6,
                         'texture': 'rblcut', 'exclude': door_boxes(model, z0)}
    if not timber and len(stone_walls) >= max(4, len(wall_textures) * 0.6) and wall_height >= 192:
        doors = []
        for face, P, n in model_faces(model):
            if face['attributes'] & CLICKABLE and abs(n[2]) < 0.01:
                P = np.array(P)
                if P[:, 2].min() <= z0 + 16:
                    lo, hi = P.min(axis=0) - 16, P.max(axis=0) + 16
                    doors.append([float(lo[0]), float(lo[1]), float(hi[0]), float(hi[1])])
        spec['bands'] = {'models': [model['index']], 'slice_z': z0 + 40, 'z0': z0, 'z1': z0 + 16, 'out': 6,
                         'texture': stone_trim, 'exclude': doors}
    return spec


def post_brackets(model, groups):
    """Brace directions per post: towards its nearest neighbours in the same row (posts sharing x or y)."""
    centres = []
    for group in groups:
        P = np.array([p for f in model['faces'] if f['index'] in group for p in face_points(model, f)])
        centres.append((P.min(axis=0)[:2] + P.max(axis=0)[:2]) / 2)
    result = {}
    for k, group in enumerate(groups):
        directions = []
        for axis in (0, 1):
            other = 1 - axis
            row = [c for j, c in enumerate(centres) if j != k and abs(c[other] - centres[k][other]) < 8
                   and abs(c[axis] - centres[k][axis]) < 768]
            for sign in (-1, 1):
                if any(np.sign(c[axis] - centres[k][axis]) == sign for c in row):
                    d = [0, 0]
                    d[axis] = sign
                    directions.append(d)
        result[str(group[0])] = directions
    return result


def wall_top(model, face, P):
    """A thin top face capping a wall: each of its two longest edges is the top edge of a vertical face below it."""
    P = np.asarray(P, float)
    edges = sorted(((np.linalg.norm(P[(i + 1) % len(P)] - P[i]), i) for i in range(len(P))), reverse=True)[:2]
    keys = [tuple(sorted((tuple(np.round(P[i])), tuple(np.round(P[(i + 1) % len(P)]))))) for _, i in edges]
    found = set()
    top = P[:, 2].max()
    for other, Q, n in model_faces(model):
        if other['index'] == face['index'] or abs(n[2]) > 0.01:
            continue
        Q = np.asarray(Q, float)
        if Q[:, 2].max() > top + 1:
            continue
        for i in range(len(Q)):
            a, b = Q[i], Q[(i + 1) % len(Q)]
            for k, (ka, kb) in enumerate(keys):
                # the wall's top edge lies along the face edge (it may be split into several pieces)
                A, B = np.array(ka), np.array(kb)
                d = B - A
                length = np.linalg.norm(d)
                if length < 1:
                    continue
                d /= length
                if all(np.linalg.norm(np.cross(q - A, d)) < 1.5 and -1 <= (q - A) @ d <= length + 1 for q in (a, b)) \
                        and np.linalg.norm(b - a) > 4:
                    found.add(k)
    return len(found) == 2


def door_boxes(model, z0):
    boxes = []
    for face, P, n in model_faces(model):
        if face['attributes'] & CLICKABLE and abs(n[2]) < 0.01:
            P = np.array(P)
            if P[:, 2].min() <= z0 + 16:
                lo, hi = P.min(axis=0) - 16, P.max(axis=0) + 16
                boxes.append([float(lo[0]), float(lo[1]), float(hi[0]), float(hi[1])])
    return boxes


def build_door_frames(mesh, model, spec, levels):
    """Jambs and a lintel standing `out` proud round each door face, `width` wide."""
    trim = Trim(spec['trim'], levels)
    w, out = spec['width'], spec['out']
    for index in spec['faces']:
        P = np.array(face_points(model, model['faces'][index]))
        n = newell(P)
        d = np.cross([0, 0, 1.0], n)
        d /= np.linalg.norm(d)
        base = P[0].copy()
        base[2] = 0
        us = [(q - base) @ d for q in P]
        u0, u1, z0, z1 = min(us), max(us), P[:, 2].min(), P[:, 2].max()

        def point(u, z, h):
            return base + d * u + n * h + np.array([0, 0, z])
        # Below the eave: a door face that runs up to the roof gets its lintel lowered into it, or none (lintels
        # stuck up through the eave lip on the kit prototype, user 2026-11-12).
        top = min(z1 + w, spec.get('top_limit', 1e9))
        pieces = [(u0 - w, u0, z0, top), (u1, u1 + w, z0, top)]
        if top - w >= z0 + 96:
            pieces.append((u0, u1, top - w, top))
        for a, b, c, e in pieces:
            bottom = [point(a, c, 0), point(b, c, 0), point(b, c, out), point(a, c, out)]
            top = [point(a, e, 0), point(b, e, 0), point(b, e, out), point(a, e, out)]
            add_solid(mesh, trim, (bottom, top), closed_ends=False)
        step = spec.get('step')
        if step:  # a threshold slab in front of the door, standing on the ground (no bottom face)
            stone = Trim(step['trim'], levels)
            lo = [point(u0 - w, z0, 0), point(u1 + w, z0, 0), point(u1 + w, z0, step['depth']),
                  point(u0 - w, z0, step['depth'])]
            add_solid(mesh, stone, (lo, [q + np.array([0, 0, step['height']]) for q in lo]), closed_ends=False)


def build_eave_lips(mesh, model, spec, levels):
    """The eave lips, fitted round the building's original small parts: a blade sign under an eave stays where it is
    (moving it opened a hole in the wall, user 2026-11-12), so the whole roof's lip is made shorter and its fascia
    slimmer, without rafter ends, until no new face cuts into a sign's box; failing that the roof gets no lip."""
    boxes = []
    for face in model['faces']:
        if face['attributes'] & CLICKABLE:
            S = np.array(face_points(model, face))
            if np.ptp(S[:, 2]) < 120 and max(np.linalg.norm((p - q)[:2]) for p in S for q in S) < 160:
                lo, hi = S.min(axis=0) - 2, S.max(axis=0) + 2
                lo[:2] -= 16  # the sign's other side and edge board
                hi[:2] += 16
                boxes.append((lo, hi))
    for scale, board in ((1.0, None), (0.85, 14), (0.7, 12), (0.55, 10), (0.45, 8), (0.35, 6)):
        trial = Mesh('lip')
        fitted = {**spec, 'length': spec['length'] * scale,
                  'fascia': {**spec['fascia'], 'height': board or spec['fascia']['height']},
                  'no_rafters': board is not None}
        lip_geometry(trial, model, fitted, levels)
        if not any(polygon_in_box([np.array(trial.vertices[i], float) for i, _, _ in f[4]], lo, hi)
                   for f in trial.faces for lo, hi in boxes):
            for attributes, ptype, event, texture, verts in trial.faces:
                points = [trial.vertices[i] for i, _, _ in verts]
                mesh.add(points, [(u, v) for _, u, v in verts], texture, newell(np.array(points, float)))
            return fitted['length']
    return 0


def polygon_in_box(points, lo, hi):
    """Whether a convex polygon reaches into an axis-aligned box (clipped against its six planes)."""
    poly = list(points)
    for axis in range(3):
        for bound, keep in ((lo[axis], 1), (hi[axis], -1)):
            out = []
            for k in range(len(poly)):
                a, b = poly[k], poly[(k + 1) % len(poly)]
                da, db = (a[axis] - bound) * keep, (b[axis] - bound) * keep
                if da >= 0:
                    out.append(a)
                if da * db < 0:
                    out.append(a + (b - a) * (da / (da - db)))
            poly = out
            if not poly:
                return False
    return len(poly) >= 3


def lip_geometry(mesh, model, spec, levels):
    """The kit's eave: every eave edge of the roof faces continued outward in the roof's plane by `length`
    (mitred where two eaves meet at a hip), a soffit under it, a fascia board along its outer edge and rafter ends
    under it. The roof faces stay; the lip is new geometry in the roof's own texture and mapping."""
    faces = {f['index']: f for f in model['faces']}
    polys = {i: face_points(model, faces[i]) for i in spec['faces']}
    normals = {i: newell(P) for i, P in polys.items()}
    owners = {}
    for i, P in polys.items():
        for k in range(len(P)):
            owners.setdefault(tuple(sorted((tuple(P[k]), tuple(P[(k + 1) % len(P)])))), []).append(i)
    eaves = []
    for i, P in polys.items():
        zmin = min(p[2] for p in P)
        centre = np.mean(P, axis=0)
        for k in range(len(P)):
            a, b = np.array(P[k], float), np.array(P[(k + 1) % len(P)], float)
            if abs(a[2] - zmin) > 0.5 or abs(b[2] - zmin) > 0.5 or np.linalg.norm(b - a) < 8:
                continue
            if len(owners[tuple(sorted((tuple(P[k]), tuple(P[(k + 1) % len(P)]))))]) != 1:
                continue
            d = (b - a) / np.linalg.norm(b - a)
            o = np.array([d[1], -d[0], 0.0])
            if o @ (a - centre) < 0:
                o = -o
            n = normals[i]
            s_dir = o - n * (o @ n)
            s_dir /= np.linalg.norm(s_dir)
            eaves.append((i, a, b, d, o, n, s_dir * spec['length'] / (s_dir @ o)))
    at = {}
    for e in eaves:
        for p in (e[1], e[2]):
            at.setdefault(tuple(np.round(p)), []).append(e)
    trim = Trim(spec['trim'], levels)
    L, T = spec['length'], spec['thickness']
    fascia, rafters = spec['fascia'], spec['rafters']
    rafter_ends = True
    for i, a, b, d, o, n, v in eaves:
        span = np.linalg.norm(b - a)
        cuts = []
        pieces, t = [], 0.0
        for c0, c1 in sorted(cuts):
            if c0 > t + 8:
                pieces.append((t, min(c0, span)))
            t = max(t, c1)
        if t < span - 8:
            pieces.append((t, span))
        corner = []
        for p in (a, b):
            others = [e for e in at[tuple(np.round(p))] if e[0] != i or not np.allclose(e[1], a)]
            others = [e for e in others if abs(e[4] @ o) < 0.9]
            corner.append(v + others[0][6] if others else v)
        face = faces[i]
        texture = face['texture_name']
        size = levels.size(texture)
        fm = FaceMap(model, face, *size, strict=False)
        down = np.array([0, 0, -1.0])
        for t0, t1 in pieces:
            p0, p1 = a + d * t0, a + d * t1
            # mitred at the eave's own corners, square at a notch
            off0 = corner[0] if t0 <= 0 else v
            off1 = corner[1] if t1 >= span else v
            P0, P1 = p0 + off0, p1 + off1
            top = [p0, p1, P1, P0]
            mesh.add(top, [fm.uv(q) for q in top], texture, n, 0, 0, size)
            under = [q - n * T for q in top]
            trim.add(mesh, under[::-1], -n)
            for p, q, side, open_end in ((p0, P0, -d, t0 > 0 or len(at[tuple(np.round(a))]) == 1),
                                         (p1, P1, d, t1 < span or len(at[tuple(np.round(b))]) == 1)):
                if open_end:  # the lip's ends (at gables and notches)
                    trim.add(mesh, [p, q, q - n * T, p - n * T], side)
            # fascia: a board along the outer edge, its top at the lip's top edge
            f0 = P0 - o * (fascia['depth'] / 2) + down * fascia['height']
            f1 = P1 - o * (fascia['depth'] / 2) + down * fascia['height']
            add_beam(mesh, f0, f1, o, [0, 0, 1], fascia['depth'], fascia['height'] + 2, trim)
            # rafter ends under the lip, from the wall line out to the fascia
            length = t1 - t0
            if length < rafters['spacing'] or spec.get('no_rafters'):
                continue
            count = max(2, int(length // rafters['spacing']) + 1)
            margin = rafters['spacing'] / 2
            for r in range(count):
                t = t0 + margin + (length - 2 * margin) * r / (count - 1)
                p = a + d * t - n * T
                add_beam(mesh, p - v * 0.15, p + v - o * fascia['depth'], d, -n, rafters['width'],
                         rafters['height'], trim)


def shaft_top(model, face, P):
    """A flat top that closes a vertical shaft (a pier or pillar): no edge meets a sloped face (the tip of a pyramid
    roof is not a pillar top) and at least half of them meet vertical faces."""
    edges = {tuple(sorted((tuple(np.round(P[i])), tuple(np.round(P[(i + 1) % len(P)]))))) for i in range(len(P))}
    vertical, sloped = set(), set()
    for other, Q, n in model_faces(model):
        if other['index'] == face['index'] or abs(n[2]) > 0.98:
            continue
        for i in range(len(Q)):
            e = tuple(sorted((tuple(np.round(Q[i])), tuple(np.round(Q[(i + 1) % len(Q)])))))
            if e in edges:
                (vertical if abs(n[2]) < 0.01 else sloped).add(e)
    return not sloped and 2 * len(vertical) >= len(edges)


# ---------------------------------------------------------------- main

def main():
    import maps
    stem = sys.argv[sys.argv.index('--map') + 1] if '--map' in sys.argv else 'oute3'
    config = maps.config(stem)
    if '--kit' in sys.argv:  # the silhouette kit: `all`, or a prototype on the listed BModels only
        config['kit'] = True
        which = sys.argv[sys.argv.index('--kit') + 1]
        config['kit_only'] = None if which == 'all' else [int(i) for i in which.split(',')]
    odm_path = ROOT / config['map']
    data = map_export.parse_odm_file(odm_path)['payload']
    levels = TextureLevels(config)
    out = []
    plan = {'map': config['map'], 'base_bmodels': len(data['bmodels']), 'buildings': []}
    manual = {b['bmodel'] for b in config['buildings'].values() if not b.get('extend')}
    extensions = {b['bmodel']: b for b in config['buildings'].values() if b.get('extend')}
    skip = tuple(config.get('auto_skip', []))
    clickable = {f['texture_name'].lower() for m in data['bmodels'] for f in m['faces']
                 if f['attributes'] & CLICKABLE}
    used = {f['texture_name'].lower() for m in data['bmodels'] for f in m['faces'] if f['texture_name']}
    for texture in sorted(used - set(config['textures'])):
        spec = (auto_texture_spec(texture, texture in clickable, levels) if (MASTERS / f'{texture}.png').exists()
                else None)
        if spec:
            config['textures'][texture] = spec
    kit = config.get('kit', False)
    # The kit's wall relief (openings set in a little) for the automatic buildings; hand-tuned buildings keep theirs.
    # A texture the kit leaves nothing to do on is not redrawn at all.
    kit_textures = {k: spec for k, spec in ((k, kit_texture(v)) for k, v in config['textures'].items())
                    if spec['classes'] or spec['rects']}
    kit_levels = TextureLevels({**config, 'textures': kit_textures})
    buildings = {name: b for name, b in config['buildings'].items() if not b.get('extend')}
    if kit and config.get('kit_only'):  # a prototype on chosen buildings only
        buildings = {}
        manual = set()
    if config.get('auto', False):
        for model in data['bmodels']:
            if model['index'] in manual or model['name'].startswith(skip):
                continue
            if kit and config.get('kit_only') and model['index'] not in config['kit_only']:
                continue
            spec = (kit_building(model, kit_textures, kit_levels) if kit
                    else auto_building(model, config['textures'], levels))
            # A hand-written `extend: true` entry adds its features to the automatic ones.
            for key, value in extensions.get(model['index'], {}).items():
                if key in ('extend', 'bmodel'):
                    continue
                spec[key] = as_list(spec.get(key, [])) + as_list(value) if key in (
                    'bands', 'coping', 'roof_trim', 'frames', 'beams', 'piles', 'retexture') else value
            buildings[f"auto_{model['index']:02d}_{model['name']}"] = spec
    import time
    for name, building in buildings.items():
        started = time.time()
        model = data['bmodels'][building['bmodel']]
        mesh = Mesh(f"{model['name']}_geo")
        relief = []
        hidden = set()
        textures, wall_levels = ((kit_textures, kit_levels) if kit and name.startswith('auto_')
                                 else (config['textures'], levels))
        for face in model['faces']:
            texture = face['texture_name'].lower()
            if face['attributes'] & INVISIBLE or face['index'] in building.get('skip_faces', []):
                continue
            if texture in textures and texture not in building.get('skip_textures', []):
                try:
                    relief.append(ReliefFace(model, face, wall_levels, textures[texture]))
                except ValueError as error:  # stretched texture mapping: leave the face as it is
                    print(f"  {model['name']}: skipped face {face['index']} ({error})")
                    continue
                hidden.add(face['index'])
        by_plane = {}
        for rf in relief:
            by_plane.setdefault(plane_key(rf.map), []).append(rf)
        build_relief(mesh, relief, by_plane, None)
        trim = Trim(building['trim'], levels) if 'trim' in building else None
        sill = building.get('sills')
        if sill:
            for rf in relief:
                if textures[rf.texture.lower()].get('sills', True):
                    build_sills(mesh, rf, wall_levels, sill, trim)
        posts = building.get('posts')
        if posts:
            for group in posts['faces']:
                build_post(mesh, model, group, posts, levels)
                hidden.update(group)
        for spec in as_list(building.get('coping', [])):
            build_coping(mesh, model, spec, levels)
        for spec in as_list(building.get('arch_ring', [])):
            build_arch_ring(mesh, model, spec, levels)
        # The eave lips first: a lip shrunk round a sign (or left out) sets how far the hip caps run out.
        lip_length = None
        for spec in as_list(building.get('eave_lips', [])):
            lip_length = build_eave_lips(mesh, model, spec, levels)
        for spec in as_list(building.get('roof_trim', [])):
            if lip_length is not None and spec.get('caps', {}).get('extend_low'):
                spec = {**spec, 'caps': {**spec['caps'], 'extend_low': lip_length}}
            build_roof_trim(mesh, model, spec, levels)
        for spec in as_list(building.get('bands', [])):
            build_band(mesh, data, spec, levels)
        for spec in as_list(building.get('quoins', [])):
            build_quoins(mesh, data, spec, levels)
        for spec in as_list(building.get('frames', [])):
            build_frame(mesh, spec, levels)
        for spec in as_list(building.get('beams', [])):
            build_beams(mesh, spec, levels)
        for spec in as_list(building.get('piles', [])):
            build_piles(mesh, spec, levels)
        for spec in as_list(building.get('door_frames', [])):
            build_door_frames(mesh, model, spec, levels)
        for spec in as_list(building.get('wales', [])):
            build_wales(mesh, data, spec, levels)
        for spec in as_list(building.get('retexture', [])):  # faces redrawn in another texture
            tex = Trim({'texture': spec['texture']}, levels)
            for index in spec['faces']:
                P = face_points(model, model['faces'][index])
                tex.add(mesh, P, newell(P))
                hidden.add(index)
        hidden.update(building.get('hide', []))
        roof = building.get('gable_roof')
        if roof:
            build_gable_roof(mesh, model, roof, levels, trim)
            hidden.update(roof['slopes'])
            hidden.update(roof.get('hide', []))
        if not mesh.faces:
            continue
        out.append(mesh)
        events = sorted({(f[2], f[0] & CLICKABLE != 0) for f in mesh.faces if f[2]})
        plan['buildings'].append({
            'name': name, 'bmodel': building['bmodel'], 'model_name': model['name'],
            'units_per_texel': building.get('units_per_texel', config.get('auto_units_per_texel', 8)
                                            if name.startswith('auto_') else config['detail_units_per_texel']),
            'original_faces': len(model['faces']),
            'original_triangles': sum(len(f['vertex_indices']) - 2 for f in model['faces']),
            'hidden_faces': sorted(hidden), 'new_faces': len(mesh.faces), 'new_triangles': mesh.triangles(),
            'new_vertices': len(mesh.vertices), 'events': events, 'seconds': round(time.time() - started, 1)})
    build = maps.build(stem)
    build.mkdir(parents=True, exist_ok=True)
    with open(build / 'models.txt', 'w') as stream:
        for mesh in out:
            mesh.write(stream)
    (build / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    for b in plan['buildings']:
        print(f"{b['name']}: {b['original_triangles']} -> +{b['new_triangles']} triangles "
              f"({b['new_faces']} faces), hides {len(b['hidden_faces'])} faces, events {b['events']}, {b['seconds']} s")


if __name__ == '__main__':
    main()
