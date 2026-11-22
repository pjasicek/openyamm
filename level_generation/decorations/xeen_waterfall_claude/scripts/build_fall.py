#!/usr/bin/env python3
"""Build one fall decoration (presets.py) straight to GLB: procedural textures, a blended core sheet (a tongue over
the lip, lanes fraying into strands) and additive haze sheets that fade to nothing, every material scrolling down
with openyamm_uv_scroll. Texture V follows the flow's travel time (v0, then gravity along the path), so a constant
scroll moves the grains with the flow: slow on the tongue, accelerating down the drop, streaks stretching as they fall.

A copy of level_generation/decorations/xeen_sandfall_claude/scripts/build_fall.py (2026-11-21) for the water fall,
extended (the sand-fall's own copy is untouched): a core `bottom` (lanes whose end lies below it stay open there, under
the pool), per-layer textures and normals, the core drawn first when `core_first` (the additive layers then add their
white over it), and two foot layers: `foam` (a flat ring on the pool, polar texture scrolling outward) and `mist` (a
cone shell rising from the foot, texture drifting up), both additive and faded through COLOR_0.

Writes work/<preset>/<output>, work/<preset>/textures/*.png and work/<preset>/report.json.
Usage: build_fall.py <preset>"""
import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.interpolate import CubicSpline

sys.path.insert(0, str(Path(__file__).resolve().parent))
from presets import PRESETS  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
UNITS_PER_METRE = 81.7


# ---------------------------------------------------------------- textures
def periodic_noise(rng, size, sigma_u, sigma_v):
    """Gaussian-filtered white noise, periodic in both directions, zero mean, unit deviation. size (width, height);
    sigma_u across (texture x), sigma_v along (texture y), in pixels."""
    width, height = size
    white = rng.standard_normal((height, width))
    fy = np.fft.fftfreq(height)[:, None]
    fx = np.fft.fftfreq(width)[None, :]
    kernel = np.exp(-2.0 * np.pi ** 2 * ((sigma_u * fx) ** 2 + (sigma_v * fy) ** 2))
    field = np.real(np.fft.ifft2(np.fft.fft2(white) * kernel))
    field -= field.mean()
    return field / max(field.std(), 1e-9)


def lane_borders(rng, lanes):
    widths = rng.uniform(0.7, 1.3, lanes)
    return np.concatenate([[0.0], np.cumsum(widths) / widths.sum()])


def make_texture(spec, rng, borders=None):
    """RGBA uint8 (height, width). With lane borders, alpha falls to 0 at every border (U fixed: no scroll across)."""
    width, height = spec['size']
    streak = periodic_noise(rng, spec['size'], spec['streak_u'], spec['streak_v'])
    clump = periodic_noise(rng, spec['size'], spec['streak_u'] * 6.0, spec['clump_v'])
    grain = periodic_noise(rng, spec['size'], 0.6, 1.4)
    weights = spec.get('weights', (0.34, 0.26, 0.10))
    density = np.clip(spec['base'] + weights[0] * streak + weights[1] * clump + weights[2] * grain, 0.0, 1.0)
    if borders is not None:
        u = (np.arange(width) + 0.5) / width
        profile = np.zeros(width)
        for left, right in zip(borders[:-1], borders[1:]):
            inside = (u > left) & (u < right)
            t = (u[inside] - left) / (right - left)
            profile[inside] = np.sin(np.pi * t) ** 0.55
        edge = spec.get('edge_fade', 0.0)
        if edge > 0.0:
            profile *= smoothstep(0.0, edge, u) * smoothstep(0.0, edge, 1.0 - u)
        density = density * profile[None, :]
    alpha = spec['alpha'] * density
    shade = 1.0 + spec['rgb_spread'] * (0.55 * streak + 0.35 * clump + 0.25 * grain)
    rgb = np.clip(np.array(spec['rgb'])[None, None, :] * shade[:, :, None], 0.0, 1.0)
    image = np.dstack([rgb, alpha[:, :, None]])
    return (np.clip(image, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)


# ---------------------------------------------------------------- path
def table(points, keys):
    points = np.array(points, dtype=np.float64)
    return np.interp(keys, points[:, 0], points[:, 1])


def smoothstep(edge0, edge1, x):
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


class Path2:
    """The centre-line in (out, up), sampled densely by arc length, with its key (inland distance, negative, on the
    tongue; drop below the lip past the edge), tangent and outward normal."""

    def __init__(self, preset):
        control = np.array(preset['path'], dtype=np.float64)
        chord = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(control, axis=0), axis=1))])
        spline = CubicSpline(chord, control, bc_type='natural')
        dense = np.linspace(0.0, chord[-1], 6000)
        points = spline(dense)
        steps = np.linalg.norm(np.diff(points, axis=0), axis=1)
        self.s = np.concatenate([[0.0], np.cumsum(steps)])
        self.points = points
        tangent = spline(dense, 1)
        self.tangent = tangent / np.linalg.norm(tangent, axis=1)[:, None]
        self.normal = np.stack([-self.tangent[:, 1], self.tangent[:, 0]], axis=1)
        out, up = points[:, 0], points[:, 1]
        self.key = np.where(out < 0.0, out, -up)
        self.preset = preset

    def at(self, s):
        index = np.clip(np.searchsorted(self.s, s), 1, len(self.s) - 1)
        w = (s - self.s[index - 1]) / np.maximum(self.s[index] - self.s[index - 1], 1e-9)
        lerp = lambda a: a[index - 1] + (a[index] - a[index - 1]) * (w[:, None] if a.ndim == 2 else w)
        normal = lerp(self.normal)
        normal /= np.linalg.norm(normal, axis=1)[:, None]
        return lerp(self.points), normal, lerp(self.key)

    def s_of_key(self, key):
        return float(np.interp(float(np.asarray(key).ravel()[0]), self.key, self.s))

    def travel_time(self, gravity):
        """Seconds from the tongue's inland end to each dense sample."""
        p = self.preset
        ds = np.diff(self.s)
        falling = np.maximum(-np.diff(self.points[:, 1]) / np.maximum(ds, 1e-9), 0.0)
        accel = np.where(self.key[1:] < 0.0, p['tongue_accel'], gravity * falling)
        speed = np.empty(len(self.s))
        speed[0] = p['v0']
        for i in range(len(ds)):
            speed[i + 1] = np.sqrt(speed[i] ** 2 + 2.0 * accel[i] * ds[i])
        time = np.concatenate([[0.0], np.cumsum(ds / (0.5 * (speed[1:] + speed[:-1])))])
        return time, speed

    def time_at(self, time, s):
        return np.interp(s, self.s, time)


# ---------------------------------------------------------------- sheets
def sheet_point(path, preset, s, a, offset=0.0, width_scale=1.0):
    """Positions (n, 3) as (across, up, out) for arc lengths s (n) and lateral fractions a (n, -0.5..0.5)."""
    centre, normal, key = path.at(s)
    width = table(preset['width'], key) * width_scale
    bulge = table(preset['bulge'], key)
    sink = table(preset['sink'], key)
    cross = (2.0 * a) ** 2
    lift = bulge * (1.0 - cross) - sink * cross + offset
    planar = centre + normal * lift[:, None]
    shift = table(preset['shift'], key) if preset.get('shift') else 0.0    # the channel's centre across (XD-17's gully)
    return np.stack([a * width + shift, planar[:, 1], planar[:, 0]], axis=1), key


def core_rows(path, preset, key_end):
    s_end = path.s_of_key(key_end)
    k = np.arange(preset['rows'] + 1) / preset['rows']
    return s_end * k ** 1.35


def build_core(path, preset, rng, borders):
    core = preset['core']
    time, _ = path.travel_time(preset['gravity'])
    lanes = len(borders) - 1
    split = rng.uniform(*core['split'], lanes)
    ends = rng.uniform(*core['end'], lanes)
    middle = np.abs((borders[:-1] + borders[1:]) * 0.5 - 0.5)
    ends = ends + (0.5 - 2.0 * middle) * 250.0          # middle lanes fall furthest
    core_bottom = core.get('bottom')
    rows = core_rows(path, preset, float(min(ends.max(), core_bottom)) if core_bottom else float(ends.max()))
    # `start` (key range): each lane's white water begins at its own key at `start_width` of its width and widens over
    # `grow`, the middle lanes first, so the brink is a ragged curve, not one straight edge across the sheet
    # (session 11).
    starts = None
    if core.get('start'):
        starts = rng.uniform(*core['start'], lanes) + 2.0 * middle * core.get('start_bias', 0.0)
        s_first = path.s_of_key(float(starts.min()))
        rows = np.concatenate([[s_first], s_first + (rows[rows > 0] / rows[-1]) * (rows[-1] - s_first)])
    positions, uvs = [], []
    indices = []
    columns = core['columns_per_lane']
    for lane in range(lanes):
        left, right = borders[lane], borders[lane + 1]
        u = np.linspace(left, right, columns + 1)
        centre_u = 0.5 * (left + right)
        open_end = core_bottom is not None and ends[lane] >= core_bottom
        s_end = path.s_of_key(min(ends[lane], core_bottom) if open_end else ends[lane])
        s_start = path.s_of_key(float(starts[lane])) if starts is not None else 0.0
        lane_rows = ([s_start] if starts is not None else []) + list(
            rows[(rows < s_end - 15.0) & (rows > s_start + 8.0 if starts is not None else rows >= 0.0)]) + [s_end]
        grid = []
        for r, s in enumerate(lane_rows):
            tip = r == len(lane_rows) - 1 and not open_end
            us = np.array([centre_u]) if tip else u
            _, _, key = path.at(np.array([s]))
            f = np.clip((key[0] - split[lane]) / (ends[lane] - split[lane]), 0.0, 1.0)
            squeeze = (1.0 - f) ** 0.85
            if starts is not None:
                begin = core.get('start_width', 0.0)
                squeeze *= begin + (1.0 - begin) * smoothstep(starts[lane], starts[lane] + core['grow'], key[0]) ** 0.5
            a = (centre_u + (us - centre_u) * squeeze) - 0.5
            point, _ = sheet_point(path, preset, np.full(len(us), s), a)
            v = core['scroll'] * path.time_at(time, s)
            first = sum(len(p) for p in positions)
            grid.append(list(range(first, first + len(us))))
            positions.append(point)
            uvs.append(np.stack([us, np.full(len(us), v)], axis=1))
        for r in range(len(grid) - 1):
            top, bottom = grid[r], grid[r + 1]
            if len(top) == 1:
                for c in range(len(bottom) - 1):
                    indices.append((top[0], bottom[c + 1], bottom[c]))
                continue
            if len(bottom) == 1:
                for c in range(len(top) - 1):
                    indices.append((top[c], top[c + 1], bottom[0]))
                continue
            for c in range(len(top) - 1):
                indices.append((top[c], top[c + 1], bottom[c + 1]))
                indices.append((top[c], bottom[c + 1], bottom[c]))
    positions = np.concatenate(positions)
    uvs = np.concatenate(uvs)
    colours = np.ones((len(positions), 4))
    return positions, uvs, colours, np.array(indices), {'split': split.tolist(), 'ends': ends.tolist()}


def build_haze(path, preset, haze):
    time, _ = path.travel_time(haze['gravity'])
    s0, s1 = path.s_of_key(haze['start']), path.s_of_key(haze['end'])
    k = np.arange(haze['rows'] + 1) / haze['rows']
    rows = s0 + (s1 - s0) * k ** 1.25
    a = np.linspace(-0.5, 0.5, haze['columns'] + 1)
    positions, uvs, colours = [], [], []
    for s in rows:
        point, key = sheet_point(path, preset, np.full(len(a), s), a, haze['offset'], haze['width'])
        fade = (smoothstep(haze['start'], haze['start'] + haze['fade_in'], key[0])
                * (1.0 - smoothstep(haze['full_until'], haze['end'], key[0])) ** 1.4)
        side = np.clip(1.0 - (2.0 * a) ** 2, 0.0, 1.0) ** 1.3
        v = haze['scroll'] * path.time_at(time, s)
        positions.append(point)
        uvs.append(np.stack([(a + 0.5) * haze['u_tiles'], np.full(len(a), v)], axis=1))
        rgb = (fade * side)[:, None] * np.ones((1, 3))
        colours.append(np.concatenate([rgb, np.ones((len(a), 1))], axis=1))
    width = len(a)
    indices = []
    for r in range(len(rows) - 1):
        for c in range(width - 1):
            i = r * width + c
            indices.append((i, i + 1, i + width + 1))
            indices.append((i, i + width + 1, i + width))
    return np.concatenate(positions), np.concatenate(uvs), np.concatenate(colours), np.array(indices)


def build_stream(path, preset, stream):
    """Clear water under the white core (blended, lit): from where it wells up out of the ground down past the brink,
    where the core's lanes cover it, its end narrowing to a quarter. The texture's sides fade (u_fade), so the stream
    has no hard edges; it scrolls with the flow (session 11, the lip seen from the cliff top)."""
    time, _ = path.travel_time(preset['gravity'])
    s0, s1 = path.s_of_key(stream['start']), path.s_of_key(stream['end'])
    rows = np.linspace(s0, s1, stream['rows'] + 1)
    a = np.linspace(-0.5, 0.5, stream['columns'] + 1)
    positions, uvs = [], []
    for s in rows:
        _, _, key = path.at(np.array([s]))
        taper = 1.0 - 0.75 * smoothstep(stream['taper_from'], stream['end'], key[0])
        point, _ = sheet_point(path, preset, np.full(len(a), s), a * taper, stream['offset'], stream['width'])
        positions.append(point)
        uvs.append(np.stack([a + 0.5, np.full(len(a), stream['scroll'] * path.time_at(time, s))], axis=1))
    return (np.concatenate(positions), np.concatenate(uvs), np.ones((len(rows) * len(a), 4)),
            grid_indices(len(rows), len(a)))


def build_plume(preset):
    """Dust lifting off the lip (additive): its own curve up and out from just behind the edge, faded at its foot,
    its sides and its top through COLOR_0; the texture drifts up it at a constant speed."""
    plume = preset['plume']
    control = np.array(plume['path'], dtype=np.float64)
    chord = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(control, axis=0), axis=1))])
    spline = CubicSpline(chord, control, bc_type='natural')
    t = np.arange(plume['rows'] + 1) / plume['rows']
    points = spline(chord[-1] * t)
    a = np.linspace(-0.5, 0.5, plume['columns'] + 1)
    width = table(plume['width'], t)
    fade = smoothstep(0.0, plume['foot'], t) * (1.0 - smoothstep(plume['full_until'], 1.0, t)) ** 1.5
    side = np.clip(1.0 - (2.0 * a) ** 2, 0.0, 1.0) ** 1.3
    positions = np.stack([(a[None, :] * width[:, None]).ravel(),
                          np.repeat(points[:, 1], len(a)), np.repeat(points[:, 0], len(a))], axis=1)
    length = np.repeat(chord[-1] * t, len(a))
    uvs = np.stack([np.tile(a + 0.5, len(t)) * plume['u_tiles'], -length / plume['period']], axis=1)
    rgb = (fade[:, None] * side[None, :]).ravel()
    colours = np.stack([rgb, rgb, rgb, np.ones_like(rgb)], axis=1)
    width_count = len(a)
    indices = []
    for r in range(len(t) - 1):
        for c in range(width_count - 1):
            i = r * width_count + c
            indices.append((i, i + 1, i + width_count + 1))
            indices.append((i, i + width_count + 1, i + width_count))
    return positions, uvs, colours, np.array(indices)


def grid_indices(rows, columns):
    indices = []
    for r in range(rows - 1):
        for c in range(columns - 1):
            i = r * columns + c
            indices.append((i, i + 1, i + columns + 1))
            indices.append((i, i + columns + 1, i + columns))
    return np.array(indices)


def foot_point(path, preset):
    """(out, up) of the core's centre-line where it meets the pool (key = preset['foot'])."""
    centre, _, _ = path.at(np.array([path.s_of_key(preset['foot'])]))
    return centre[0]


def bake_fades(image, spec):
    """The game's static model shader does not apply COLOR_0 (it carries placement lighting there), so a layer's
    fades must live in its texture: `u_fade` (edge width) fades RGB and alpha to 0 at both u ends (a sheet's sides;
    such a layer keeps u_tiles 1 and no u drift); `v_fade` [fade_in, full_until, power] fades along v as the vertex
    fade did along t (a `baked` mist or foam layer maps v = t once, with no v scroll)."""
    if not spec.get('u_fade') and not spec.get('v_fade'):
        return image
    height, width = image.shape[:2]
    fade = np.ones((height, width))
    if spec.get('u_fade'):
        u = (np.arange(width) + 0.5) / width
        fade *= (smoothstep(0.0, spec['u_fade'], u) * smoothstep(0.0, spec['u_fade'], 1.0 - u))[None, :]
    if spec.get('v_fade'):
        fade_in, full_until, power = spec['v_fade']
        t = (np.arange(height) + 0.5) / height
        fade *= (smoothstep(0.0, fade_in, t) * (1.0 - smoothstep(full_until, 1.0, t)) ** power)[:, None]
    return (image.astype(np.float64) * fade[:, :, None] + 0.5).astype(np.uint8)


def build_foam(path, preset):
    """A flat ring on the pool around the foot (additive): polar texture (u around, v outward), faded at the inner
    and outer rims through COLOR_0; a negative v scroll moves the foam outward."""
    foam = preset['foam']
    out, up = foot_point(path, preset)
    up += foam['lift']
    radii = foam['r0'] + (foam['r1'] - foam['r0']) * (np.arange(foam['rings'] + 1) / foam['rings']) ** 1.3
    angles = np.linspace(0.0, 2.0 * np.pi, foam['segments'] + 1)
    positions, uvs, colours = [], [], []
    for r in radii:
        stretch = 1.0 + foam['stretch'] * np.cos(angles)          # longer toward +out (the way the fall comes)
        across = np.sin(angles) * r
        along = out + np.cos(angles) * r * stretch
        positions.append(np.stack([across, np.full(len(angles), up), along], axis=1))
        t = (r - foam['r0']) / (foam['r1'] - foam['r0'])
        v = t if foam.get('baked') else r / foam['period']
        uvs.append(np.stack([angles / (2.0 * np.pi) * foam['u_tiles'], np.full(len(angles), v)], axis=1))
        fade = smoothstep(0.0, foam['fade_in'], t) * (1.0 - smoothstep(foam['full_until'], 1.0, t)) ** 1.4
        colours.append(np.tile([fade, fade, fade, 1.0], (len(angles), 1)))
    return (np.concatenate(positions), np.concatenate(uvs), np.concatenate(colours),
            grid_indices(len(radii), len(angles)))


def build_mist(path, preset, mist):
    """A cone shell rising from the foot (additive), its texture drifting up (v = height / period), faded at the
    water and toward its top through COLOR_0."""
    out, up = foot_point(path, preset)
    heights = mist['height'] * (np.arange(mist['rows'] + 1) / mist['rows']) ** 1.2
    angles = np.linspace(0.0, 2.0 * np.pi, mist['segments'] + 1)
    positions, uvs, colours = [], [], []
    for h in heights:
        t = h / mist['height']
        r = mist['r0'] + (mist['r1'] - mist['r0']) * t ** 0.7
        positions.append(np.stack([np.sin(angles) * r, np.full(len(angles), up + mist['lift'] + h),
                                   out + mist['shift'] + np.cos(angles) * r], axis=1))
        v = t if mist.get('baked') else h / mist['period']
        uvs.append(np.stack([angles / (2.0 * np.pi) * mist['u_tiles'], np.full(len(angles), v)], axis=1))
        fade = smoothstep(0.0, mist['fade_in'], t) * (1.0 - smoothstep(mist['full_until'], 1.0, t)) ** 1.6
        colours.append(np.tile([fade, fade, fade, 1.0], (len(angles), 1)))
    return (np.concatenate(positions), np.concatenate(uvs), np.concatenate(colours),
            grid_indices(len(heights), len(angles)))


# ---------------------------------------------------------------- GLB
class GlbWriter:
    def __init__(self):
        self.doc = {'asset': {'version': '2.0', 'generator': 'xeen_sandfall_claude build_fall.py'},
                    'buffers': [{'byteLength': 0}], 'bufferViews': [], 'accessors': [], 'images': [],
                    'textures': [], 'samplers': [], 'materials': [], 'meshes': [], 'nodes': [],
                    'scenes': [{'nodes': [0]}], 'scene': 0}
        self.binary = bytearray()

    def view(self, data, target=None):
        self.binary += b'\0' * (-len(self.binary) % 4)
        view = {'buffer': 0, 'byteOffset': len(self.binary), 'byteLength': len(data)}
        if target:
            view['target'] = target
        self.binary += data
        self.doc['bufferViews'].append(view)
        return len(self.doc['bufferViews']) - 1

    def accessor(self, array, kind, component, target, bounds=False):
        data = np.ascontiguousarray(array).tobytes()
        accessor = {'bufferView': self.view(data, target), 'componentType': component,
                    'count': int(array.shape[0]), 'type': kind}
        if bounds:
            accessor['min'] = array.min(axis=0).tolist()
            accessor['max'] = array.max(axis=0).tolist()
        self.doc['accessors'].append(accessor)
        return len(self.doc['accessors']) - 1

    def texture(self, rgba, wrap_s):
        buffer = io.BytesIO()
        Image.fromarray(rgba, 'RGBA').save(buffer, 'PNG', optimize=True)
        self.doc['images'].append({'bufferView': self.view(buffer.getvalue()), 'mimeType': 'image/png'})
        self.doc['samplers'].append({'magFilter': 9729, 'minFilter': 9987, 'wrapS': wrap_s, 'wrapT': 10497})
        self.doc['textures'].append({'source': len(self.doc['images']) - 1,
                                     'sampler': len(self.doc['samplers']) - 1})
        return len(self.doc['textures']) - 1

    def material(self, name, texture, colour, extras, emissive=None):
        material = {
            'name': name, 'alphaMode': 'BLEND', 'doubleSided': True, 'extras': extras,
            'pbrMetallicRoughness': {'baseColorTexture': {'index': texture}, 'baseColorFactor': colour,
                                     'metallicFactor': 0.0, 'roughnessFactor': 0.95}}
        if emissive:
            # Glowing layers (X7's lava): the layer's own texture as the emission map, times the factor and strength;
            # the engine adds it unlit after lighting (MODEL_RENDERING.md, "Emission and bloom").
            material['emissiveTexture'] = {'index': texture}
            material['emissiveFactor'] = list(emissive['factor'])
            if emissive.get('strength', 1.0) != 1.0:
                material['extensions'] = {'KHR_materials_emissive_strength':
                                          {'emissiveStrength': emissive['strength']}}
                used = self.doc.setdefault('extensionsUsed', [])
                if 'KHR_materials_emissive_strength' not in used:
                    used.append('KHR_materials_emissive_strength')
        self.doc['materials'].append(material)
        return len(self.doc['materials']) - 1

    def primitive(self, positions, normal, uvs, colours, indices, material):
        count = len(positions)
        normals = np.asarray(normal, dtype=np.float32)
        if normals.ndim == 1:
            normals = np.tile(normals, (count, 1))
        return {'attributes': {
            'POSITION': self.accessor(positions.astype(np.float32), 'VEC3', 5126, 34962, bounds=True),
            'NORMAL': self.accessor(normals, 'VEC3', 5126, 34962),
            'TEXCOORD_0': self.accessor(uvs.astype(np.float32), 'VEC2', 5126, 34962),
            'COLOR_0': self.accessor(colours.astype(np.float32), 'VEC4', 5126, 34962)},
            'indices': self.accessor(indices.astype(np.uint16).ravel(), 'SCALAR', 5123, 34963),
            'material': material}

    def write(self, path, name, primitives):
        self.doc['meshes'].append({'name': name, 'primitives': primitives})
        self.doc['nodes'].append({'name': name, 'mesh': 0})
        self.binary += b'\0' * (-len(self.binary) % 4)
        self.doc['buffers'][0]['byteLength'] = len(self.binary)
        encoded = json.dumps(self.doc, separators=(',', ':')).encode()
        encoded += b' ' * (-len(encoded) % 4)
        path.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(encoded) + len(self.binary))
                         + struct.pack('<II', len(encoded), 0x4e4f534a) + encoded
                         + struct.pack('<II', len(self.binary), 0x004e4942) + bytes(self.binary))


def additive_extras(layer):
    return {'openyamm_additive': True, 'openyamm_uv_scroll': [layer.get('drift', 0.0), -layer['scroll']],
            'openyamm_specular': 0.0, 'openyamm_translucency': layer['translucency']}


def main():
    name = sys.argv[1]
    preset = PRESETS[name]
    rng = np.random.default_rng(preset['seed'])
    out_dir = HERE / 'work' / name
    (out_dir / 'textures').mkdir(parents=True, exist_ok=True)
    borders = lane_borders(rng, preset['core']['lanes'])
    images = {}
    for key, spec in preset['textures'].items():
        images[key] = make_texture(spec, rng, borders if key == preset['core']['texture'] else None)
        images[key] = bake_fades(images[key], spec)
        Image.fromarray(images[key], 'RGBA').save(out_dir / 'textures' / f'{key}.png')
    path = Path2(preset)
    normal_out, normal_up = preset['normal']
    normal = (0.0, normal_up, normal_out)
    writer = GlbWriter()
    textures = {key: writer.texture(images[key], 33071 if key == preset['core']['texture'] else 10497)
                for key in preset['textures']}
    layers, report = [], {'preset': name, 'layers': []}
    core = preset['core']
    positions, uvs, colours, indices, lanes = build_core(path, preset, rng, borders)
    material = writer.material('Core', textures[core['texture']], core['colour'], {
        'openyamm_uv_scroll': [0.0, -core['scroll']], 'openyamm_specular': core['specular'],
        'openyamm_translucency': core['translucency']}, core.get('emissive'))
    layers.append(('Core', (positions, uvs, colours, indices, material), normal, lanes))
    stream = preset.get('stream')
    if stream:
        positions, uvs, colours, indices = build_stream(path, preset, stream)
        material = writer.material('Stream', textures[stream['texture']], stream['colour'], {
            'openyamm_uv_scroll': [0.0, -stream['scroll']], 'openyamm_specular': stream['specular'],
            'openyamm_translucency': stream['translucency']})
        # Drawn before the core (blended draws keep their order), so the white water lies over it.
        layers.insert(0, ('Stream', (positions, uvs, colours, indices, material), normal, {}))
    for index, haze in enumerate(preset['haze']):
        positions, uvs, colours, indices = build_haze(path, preset, haze)
        material = writer.material(f'Haze{index + 1}', textures[haze['texture']], haze['colour'],
                                   additive_extras(haze), haze.get('emissive'))
        layers.append((f'Haze{index + 1}', (positions, uvs, colours, indices, material), normal, {}))
    if preset.get('foam'):
        foam = preset['foam']
        positions, uvs, colours, indices = build_foam(path, preset)
        material = writer.material('Foam', textures[foam['texture']], foam['colour'], additive_extras(foam),
                                   foam.get('emissive'))
        layers.append(('Foam', (positions, uvs, colours, indices, material), (0.0, 1.0, 0.0), {}))
    for index, mist in enumerate(preset.get('mist', [])):
        positions, uvs, colours, indices = build_mist(path, preset, mist)
        material = writer.material(f'Mist{index + 1}', textures[mist['texture']], mist['colour'],
                                   additive_extras(mist), mist.get('emissive'))
        layers.append((f'Mist{index + 1}', (positions, uvs, colours, indices, material), normal, {}))
    # Blended draws keep their order within a model: the core first, so the white additive layers add over it
    # (the sand-fall drew its haze first and the core last; core_first False keeps that order).
    if not preset.get('core_first', False):
        layers = layers[1:][::-1] + layers[:1]
    primitives = [layer[1] for layer in layers]
    for layer in layers:
        report['layers'].append({'name': layer[0], 'triangles': len(layer[1][3]), **layer[3]})
    everything = np.concatenate([p[0] for p in primitives])
    lo, hi = everything.min(axis=0), everything.max(axis=0)
    gltf = [writer.primitive(p[0] / UNITS_PER_METRE, layer[2], p[1], p[2], p[3], p[4])
            for p, layer in zip(primitives, layers)]
    output = out_dir / preset['output']
    writer.write(output, Path(preset['output']).stem, gltf)
    time, speed = path.travel_time(preset['gravity'])
    edge = path.s_of_key(0.0)
    start = float(path.key[0])
    report.update({
        'output': str(output), 'triangles': int(sum(len(p[3]) for p in primitives)),
        'bounds_units': {'across': [float(lo[0]), float(hi[0])], 'up': [float(lo[1]), float(hi[1])],
                         'out': [float(lo[2]), float(hi[2])]},
        'height_units': float(hi[1] - lo[1]),
        'speed_units_per_second': {f'key {k}': float(np.interp(path.s_of_key(k), path.s, speed))
                                   for k in (start, 0, 300, 800, 1200, preset.get('foot', 2000))},
        'tongue_seconds': float(np.interp(edge, path.s, time)),
    })
    if preset.get('foot') is not None:
        out, up = foot_point(path, preset)
        report['foot_units'] = {'out': float(out), 'up': float(up)}
    (out_dir / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
