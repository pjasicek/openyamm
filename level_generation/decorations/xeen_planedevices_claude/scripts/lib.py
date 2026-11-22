"""Shared helpers of the plane devices (xeen_planedevices_claude): periodic noise textures, height-to-normal maps,
a small mesh builder (grids with smooth or flat shading, lathes, tubes, ellipsoids) and a GLB writer for opaque and
blended PBR materials. Model space: metres (1 m = 100 units at the decoration's scale), +Y up, front toward +Z."""
import io
import json
import struct

import numpy as np
from PIL import Image


# ---------------------------------------------------------------- textures
def noise(rng, h, w, sy, sx=None):
    """Periodic Gaussian-filtered noise (h, w), zero mean, unit deviation; sigma in pixels."""
    sx = sy if sx is None else sx
    white = rng.standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    k = np.exp(-2.0 * np.pi ** 2 * ((sy * fy) ** 2 + (sx * fx) ** 2))
    f = np.real(np.fft.ifft2(np.fft.fft2(white) * k))
    f -= f.mean()
    return f / max(f.std(), 1e-9)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def ramp(t, stops):
    """t (h, w) in 0..1 -> RGB (h, w, 3) through [(pos, (r, g, b)), ...] (0..255)."""
    pos = np.array([s[0] for s in stops])
    col = np.array([s[1] for s in stops], float)
    return np.stack([np.interp(t, pos, col[:, c]) for c in range(3)], axis=-1)


def normal_map(height, strength, wrap_v=True, wrap_u=True):
    """Height (h, w) in texels -> OpenGL (+Y up) normal map RGB uint8. strength scales the slopes."""
    def d(a, axis, wrap):
        if wrap:
            return (np.roll(a, -1, axis) - np.roll(a, 1, axis)) * 0.5
        return np.gradient(a, axis=axis)
    dx = d(height, 1, wrap_u) * strength
    dy = d(height, 0, wrap_v) * strength
    # Image rows grow downward while texture v grows upward in glTF only after the flip; glTF puts v = 0 at the image
    # top, so +v is down the image: the +Y (green) slope is minus the row gradient's opposite.
    n = np.stack([-dx, dy, np.ones_like(height)], axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return ((n * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8)


def u8(a):
    return (np.clip(a, 0, 255) + 0.5).astype(np.uint8)


def mr_map(roughness, metallic=0.0):
    """glTF metallic-roughness: G roughness, B metallic (0..1 arrays or scalars)."""
    r = np.asarray(roughness, float)
    out = np.zeros(r.shape + (3,))
    out[..., 0] = 255
    out[..., 1] = r * 255
    out[..., 2] = np.broadcast_to(np.asarray(metallic, float), r.shape) * 255
    return u8(out)


# ---------------------------------------------------------------- mesh
class Mesh:
    """Triangles per material: positions, normals, uvs."""

    def __init__(self):
        self.parts = {}

    def _get(self, material):
        return self.parts.setdefault(material, {'p': [], 'n': [], 'uv': [], 'i': [], 'count': 0})

    def add(self, material, p, n, uv, tris):
        part = self._get(material)
        base = part['count']
        part['p'].append(np.asarray(p, float))
        part['n'].append(np.asarray(n, float))
        part['uv'].append(np.asarray(uv, float))
        part['i'].append(np.asarray(tris, int) + base)
        part['count'] += len(p)

    def transform(self, func, material=None, start=None):
        """Apply func(points) -> points (and its effect on normals by finite differences) to every vertex."""
        for name, part in self.parts.items():
            if material is not None and name != material:
                continue
            for k in range(len(part['p'])):
                if start is not None and k < start.get(name, 0):
                    continue
                p, n = part['p'][k], part['n'][k]
                q = func(p)
                q2 = func(p + n * 1e-4)
                nn = q2 - q
                part['p'][k] = q
                part['n'][k] = nn / np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-12)

    def marks(self):
        return {name: len(part['p']) for name, part in self.parts.items()}

    def arrays(self, material):
        part = self.parts[material]
        return (np.concatenate(part['p']), np.concatenate(part['n']), np.concatenate(part['uv']),
                np.concatenate(part['i']))

    def triangles(self):
        return sum(sum(len(i) for i in part['i']) for part in self.parts.values())

    def bounds(self):
        p = np.concatenate([np.concatenate(part['p']) for part in self.parts.values()])
        return p.min(axis=0), p.max(axis=0)


def grid_tris(rows, cols, flip=False):
    """Quads of a (rows, cols) vertex grid, split on the shorter diagonal later (here: fixed split, see grid())."""
    tris = []
    for i in range(rows - 1):
        for j in range(cols - 1):
            a, b, c, d = i * cols + j, i * cols + j + 1, (i + 1) * cols + j + 1, (i + 1) * cols + j
            tris.append((a, b, c, a, c, d))
    t = np.array(tris).reshape(-1, 3)
    return t[:, ::-1] if flip else t


def _split_short(P, tris_quads):
    """Re-split each quad (pairs of rows a,b,c / a,c,d) on its shorter diagonal."""
    out = []
    for k in range(0, len(tris_quads), 2):
        a, b, c = tris_quads[k]
        _, _, d = tris_quads[k + 1]
        if np.linalg.norm(P[a] - P[c]) <= np.linalg.norm(P[b] - P[d]):
            out += [(a, b, c), (a, c, d)]
        else:
            out += [(a, b, d), (b, c, d)]
    return np.array(out)


def face_normals(P, T):
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    return n


def grid(mesh, material, P, UV, flip=False, smooth=True, wrap_u=False):
    """P (rows, cols, 3), UV (rows, cols, 2). Winding: the normal of row i -> i+1 cross column j -> j+1 is
    cross(dcol, drow) unless flip. smooth: shared vertices with area-weighted normals (wrap_u averages the first and
    last column, which coincide); else every quad flat with its own four vertices."""
    rows, cols = P.shape[:2]
    flatp = P.reshape(-1, 3)
    flatuv = UV.reshape(-1, 2)
    T = _split_short(flatp, grid_tris(rows, cols))
    if flip:
        T = T[:, ::-1].copy()
    if smooth:
        fn = face_normals(flatp, T)
        N = np.zeros_like(flatp)
        for c in range(3):
            np.add.at(N, T[:, c], fn)
        N = N.reshape(rows, cols, 3)
        if wrap_u:
            s = N[:, 0] + N[:, -1]
            N[:, 0] = s
            N[:, -1] = s
        N = N.reshape(-1, 3)
        N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
        mesh.add(material, flatp, N, flatuv, T)
    else:
        ps, ns, uvs, ts = [], [], [], []
        for k in range(0, len(T), 2):
            q = np.unique(np.concatenate([T[k], T[k + 1]]))
            fn = face_normals(flatp, T[k:k + 2]).sum(axis=0)
            fn /= max(np.linalg.norm(fn), 1e-12)
            remap = {int(v): len(ps) + m for m, v in enumerate(q)}
            for v in q:
                ps.append(flatp[v])
                ns.append(fn)
                uvs.append(flatuv[v])
            ts += [[remap[int(v)] for v in T[k]], [remap[int(v)] for v in T[k + 1]]]
        mesh.add(material, np.array(ps), np.array(ns), np.array(uvs), np.array(ts))


def lathe(mesh, material, profile, segments, u_tiles=1.0, v_of=None, smooth_profile=False, flat=True,
          radial=None, phase=0.0, flip=False):
    """profile [(r, y), ...] bottom to top on the outside (normals outward when the profile runs up the outside or
    down an inside). segments around; u = angle / 2pi * u_tiles; v from v_of(index) or the profile's arc length
    (metres). radial(angle, r, y) -> scale of r (dents). flat: faceted (every quad its own normal)."""
    prof = np.asarray(profile, float)
    ang = phase + np.linspace(0.0, 2.0 * np.pi, segments + 1)
    arc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(prof, axis=0), axis=1))])
    v = arc if v_of is None else np.asarray(v_of, float)
    P = np.zeros((len(prof), segments + 1, 3))
    for i, (r, y) in enumerate(prof):
        rr = r * (radial(ang, r, y) if radial is not None else 1.0)
        P[i, :, 0] = rr * np.cos(ang)
        P[i, :, 1] = y
        P[i, :, 2] = -rr * np.sin(ang)
    P[:, -1] = P[:, 0]
    UV = np.zeros((len(prof), segments + 1, 2))
    UV[:, :, 0] = (ang - phase)[None, :] / (2.0 * np.pi) * u_tiles
    UV[:, :, 1] = v[:, None]
    # Rows run up the profile, columns counter-clockwise seen from above (x -> -z): cross(dcol, drow) points out.
    grid(mesh, material, P, UV, flip=flip, smooth=not flat, wrap_u=True)
    return P


def disc(mesh, material, centre, radius, segments, inner_fracs=(0.66, 0.33), uv_scale=1.0, up=True, phase=0.0):
    """A flat disc (normal +y or -y) of rings; the centre is a small polygon split as a strip (no high-valence fan)."""
    cx, cy, cz = centre
    ang = phase + np.linspace(0.0, 2.0 * np.pi, segments + 1)[:-1]
    rings = [radius] + [radius * f for f in inner_fracs]
    pts, uvs = [], []
    for r in rings:
        for a in ang:
            x, z = cx + r * np.cos(a), cz - r * np.sin(a)
            pts.append((x, cy, z))
            uvs.append((x * uv_scale, z * uv_scale))
    tris = []
    n = segments
    for k in range(len(rings) - 1):
        for j in range(n):
            a, b = k * n + j, k * n + (j + 1) % n
            c, d = (k + 1) * n + (j + 1) % n, (k + 1) * n + j
            tris += [(a, b, c), (a, c, d)]
    last = (len(rings) - 1) * n
    # Strip-triangulate the innermost polygon: zig-zag between its two halves.
    left, right = 0, n - 1
    order = []
    while left <= right:
        order.append(left)
        if left != right:
            order.append(right)
        left += 1
        right -= 1
    for k in range(len(order) - 2):
        t = (last + order[k], last + order[k + 1], last + order[k + 2])
        tris.append(t if k % 2 == 0 else (t[0], t[2], t[1]))
    P = np.array(pts)
    T = np.array(tris)
    fn = face_normals(P, T)
    want = 1.0 if up else -1.0
    flipmask = fn[:, 1] * want < 0
    T[flipmask] = T[flipmask][:, ::-1]
    N = np.tile([0.0, want, 0.0], (len(P), 1))
    mesh.add(material, P, N, np.array(uvs), T)


def tube(mesh, material, path, radius, sides, u_tiles=1.0, v_scale=1.0, caps=True, twist=0.0):
    """A tube along path (n, 3) with radius (scalar or n); u around, v along (metres x v_scale). Smooth."""
    path = np.asarray(path, float)
    rad = np.broadcast_to(np.asarray(radius, float), (len(path),))
    t = np.gradient(path, axis=0)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    ref = np.array([0.0, 1.0, 0.0]) if abs(t[0][1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    frames = []
    nrm = np.cross(t[0], ref)
    nrm /= np.linalg.norm(nrm)
    for k in range(len(path)):
        nrm = nrm - t[k] * np.dot(nrm, t[k])
        nrm /= np.linalg.norm(nrm)
        frames.append((nrm.copy(), np.cross(t[k], nrm)))
    ang = np.linspace(0.0, 2.0 * np.pi, sides + 1)
    arc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))])
    P = np.zeros((len(path), sides + 1, 3))
    UV = np.zeros((len(path), sides + 1, 2))
    for k in range(len(path)):
        a = ang + twist * arc[k]
        n1, b1 = frames[k]
        P[k] = path[k] + rad[k] * (np.cos(a)[:, None] * n1 + np.sin(a)[:, None] * b1)
        UV[k, :, 0] = ang / (2.0 * np.pi) * u_tiles
        UV[k, :, 1] = arc[k] * v_scale
    P[:, -1] = P[:, 0]
    grid(mesh, material, P, UV, flip=False, smooth=True, wrap_u=True)
    if caps:
        for k, sign in ((0, -1.0), (len(path) - 1, 1.0)):
            ring = P[k, :-1]
            centre = path[k]
            pts = np.vstack([ring, centre[None]])
            m = len(ring)
            T = np.array([(j, (j + 1) % m, m) for j in range(m)])
            fn = face_normals(pts, T)
            want = t[k] * sign
            bad = fn @ want < 0
            T[bad] = T[bad][:, ::-1]
            uv = np.vstack([UV[k, :-1] * 0 + [0.5, arc[k] * v_scale], [[0.5, arc[k] * v_scale]]])
            mesh.add(material, pts, np.tile(want, (len(pts), 1)), uv, T)
    return P


def ellipsoid(mesh, material, centre, radii, rings, segments, rng=None, jitter=0.0, flat=False, uv_tiles=(1.0, 1.0),
              squash_bottom=None):
    """An ellipsoid (rings latitude bands, segments around); jitter perturbs radii (rocks); squash_bottom flattens
    the part below that local y fraction (resting face). Poles: small rings, not single points (no high valence)."""
    lat = np.linspace(-np.pi / 2 * 0.92, np.pi / 2 * 0.92, rings + 1)
    ang = np.linspace(0.0, 2.0 * np.pi, segments + 1)
    P = np.zeros((rings + 1, segments + 1, 3))
    noise_r = np.ones((rings + 1, segments + 1))
    if rng is not None and jitter > 0:
        noise_r = 1.0 + jitter * rng.uniform(-1, 1, (rings + 1, segments))
        noise_r = np.concatenate([noise_r, noise_r[:, :1]], axis=1)
    for i, la in enumerate(lat):
        y = np.sin(la)
        r = np.cos(la)
        P[i, :, 0] = r * np.cos(ang) * radii[0] * noise_r[i]
        P[i, :, 1] = y * radii[1] * noise_r[i]
        P[i, :, 2] = -r * np.sin(ang) * radii[2] * noise_r[i]
    if squash_bottom is not None:
        floor = -radii[1] * squash_bottom
        P[:, :, 1] = np.maximum(P[:, :, 1], floor)
    P += np.asarray(centre)
    UV = np.zeros((rings + 1, segments + 1, 2))
    UV[:, :, 0] = ang[None, :] / (2 * np.pi) * uv_tiles[0]
    UV[:, :, 1] = ((lat + np.pi / 2) / np.pi)[:, None] * uv_tiles[1]
    grid(mesh, material, P, UV, flip=False, smooth=not flat, wrap_u=True)
    # close the poles with small strip caps
    for i, want in ((0, -1.0), (rings, 1.0)):
        ring = P[i, :-1]
        m = len(ring)
        left, right, order = 0, m - 1, []
        while left <= right:
            order.append(left)
            if left != right:
                order.append(right)
            left += 1
            right -= 1
        T = np.array([(order[k], order[k + 1], order[k + 2]) for k in range(len(order) - 2)])
        fn = face_normals(ring, T)
        bad = fn[:, 1] * want < 0
        T[bad] = T[bad][:, ::-1]
        mesh.add(material, ring, np.tile([0.0, want, 0.0], (m, 1)), UV[i, :-1], T)


# ---------------------------------------------------------------- GLB
class Glb:
    def __init__(self, generator):
        self.doc = {'asset': {'version': '2.0', 'generator': generator}, 'buffers': [{'byteLength': 0}],
                    'bufferViews': [], 'accessors': [], 'images': [], 'textures': [], 'samplers': [],
                    'materials': [], 'meshes': [], 'nodes': [], 'scenes': [{'nodes': [0]}], 'scene': 0}
        self.bin = bytearray()
        self.mat_index = {}

    def view(self, data, target=None):
        self.bin += b'\0' * (-len(self.bin) % 4)
        v = {'buffer': 0, 'byteOffset': len(self.bin), 'byteLength': len(data)}
        if target:
            v['target'] = target
        self.bin += data
        self.doc['bufferViews'].append(v)
        return len(self.doc['bufferViews']) - 1

    def accessor(self, a, kind, comp, target, bounds=False):
        a = np.ascontiguousarray(a)
        acc = {'bufferView': self.view(a.tobytes(), target), 'componentType': comp, 'count': int(a.shape[0]),
               'type': kind}
        if bounds:
            acc['min'] = a.min(axis=0).tolist()
            acc['max'] = a.max(axis=0).tolist()
        self.doc['accessors'].append(acc)
        return len(self.doc['accessors']) - 1

    def texture(self, img, wrap=10497):
        buf = io.BytesIO()
        mode = 'RGBA' if img.ndim == 3 and img.shape[2] == 4 else 'RGB'
        Image.fromarray(img, mode).save(buf, 'PNG', optimize=True)
        self.doc['images'].append({'bufferView': self.view(buf.getvalue()), 'mimeType': 'image/png'})
        self.doc['samplers'].append({'magFilter': 9729, 'minFilter': 9987, 'wrapS': wrap, 'wrapT': wrap})
        self.doc['textures'].append({'source': len(self.doc['images']) - 1, 'sampler': len(self.doc['samplers']) - 1})
        return len(self.doc['textures']) - 1

    def material(self, name, base, mr=None, normal=None, emissive=None, emissive_factor=(1.0, 1.0, 1.0),
                 strength=1.0, blend=False, double=False, extras=None, wrap=10497, normal_scale=1.0):
        m = {'name': name, 'pbrMetallicRoughness': {'baseColorTexture': {'index': self.texture(base, wrap)}}}
        if mr is not None:
            m['pbrMetallicRoughness']['metallicRoughnessTexture'] = {'index': self.texture(mr, wrap)}
        else:
            m['pbrMetallicRoughness']['metallicFactor'] = 0.0
            m['pbrMetallicRoughness']['roughnessFactor'] = 0.9
        if normal is not None:
            m['normalTexture'] = {'index': self.texture(normal, wrap)}
            if normal_scale != 1.0:
                m['normalTexture']['scale'] = normal_scale
        if emissive is not None:
            m['emissiveTexture'] = {'index': self.texture(emissive, wrap)}
            m['emissiveFactor'] = list(emissive_factor)
            if strength != 1.0:
                m['extensions'] = {'KHR_materials_emissive_strength': {'emissiveStrength': strength}}
                used = self.doc.setdefault('extensionsUsed', [])
                if 'KHR_materials_emissive_strength' not in used:
                    used.append('KHR_materials_emissive_strength')
        if blend:
            m['alphaMode'] = 'BLEND'
        if double:
            m['doubleSided'] = True
        if extras:
            m['extras'] = extras
        self.doc['materials'].append(m)
        self.mat_index[name] = len(self.doc['materials']) - 1

    def write(self, path, name, mesh, order):
        prims = []
        for mat in order:
            if mat not in mesh.parts:
                continue
            p, n, uv, i = mesh.arrays(mat)
            idx_type, comp = (np.uint16, 5123) if len(p) < 65536 else (np.uint32, 5125)
            prims.append({'attributes': {
                'POSITION': self.accessor(p.astype(np.float32), 'VEC3', 5126, 34962, bounds=True),
                'NORMAL': self.accessor(n.astype(np.float32), 'VEC3', 5126, 34962),
                'TEXCOORD_0': self.accessor(uv.astype(np.float32), 'VEC2', 5126, 34962)},
                'indices': self.accessor(i.astype(idx_type).ravel(), 'SCALAR', comp, 34963),
                'material': self.mat_index[mat]})
        self.doc['meshes'].append({'name': name, 'primitives': prims})
        self.doc['nodes'].append({'name': name, 'mesh': 0})
        self.bin += b'\0' * (-len(self.bin) % 4)
        self.doc['buffers'][0]['byteLength'] = len(self.bin)
        enc = json.dumps(self.doc, separators=(',', ':')).encode()
        enc += b' ' * (-len(enc) % 4)
        path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(enc) + len(self.bin))
                         + struct.pack('<II', len(enc), 0x4e4f534a) + enc
                         + struct.pack('<II', len(self.bin), 0x004e4942) + bytes(self.bin))
