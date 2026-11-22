#!/usr/bin/env python3
"""Stage 3: the cage bird's two GLBs from the MM9 crow (assets_source/worlds/mm9/models/mm9_crow.glb, copied into
Xeen per D-44) and the stage 1-2 textures.

  export/xeen_deco_cagebird_anim.glb  the skinned copy (the binding's `animated`): the crow's skeleton, its four LODs
      and its shadow LODs untouched, its materials replaced by the baked colour (no tiers, no region extras, no
      variants), a tray skinned to a new still joint `Tray`, and one seamless idle clip `perch` (Perch three times,
      then PerchFidget once, the joins blended over a few frames). MM9's perched clips move the feet up and down
      (PerchFidget drops them 0.10 m), so every frame's root is lifted by the feet's drop: the feet stay on the perch bar.
      Its rest is the clip's first frame.
  export/xeen_deco_cagebird.glb       the rigid static copy (the binding's `model`, picking only): the same four LODs
      skinned at that first frame, plus the tray, LODs linked by tools/link_static_model_lods.py.

Asset space: metres (x 100 = world units at the binding's height 50), glTF +Y up, +Z out from the wall, origin at the
tray's back edge middle on its underside (the wall line, at the panel bottom).
Usage: build_glbs.py"""
import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from cagelib import PROJECT, REPO, Model, array, lod_meshes, trs, write_glb  # noqa: E402

CFG = json.loads((HERE / 'cagebird.json').read_text())
BIRD, TRAY = CFG['bird'], CFG['tray']
TEX = PROJECT / 'work' / 'tex'
OUT = PROJECT / 'export'
FEET = ('Xfoot', 'Xfoot01')
FOOT_JOINTS = ('Xtoe', 'Xtoe01', 'Xfoot', 'Xfoot01')
U = 0.01                       # world unit -> asset metre
STATIC_TEXTURE = 512          # the static copy's largest image (picking only, never drawn)
DENSITY = 2.13                 # tray texels per world unit (the cage picture: 256 px over 120)


# --- the idle clip ------------------------------------------------------------------------------------------------
def sample(model, clip, node, path, time):
    return np.array(model.local_trs(node, clip, time)[path], float)


def build_clip(model):
    """{(node, path): (frames, k) values} for the loop, its frame times, and the per-frame feet lift."""
    fps = BIRD['fps']
    channels = sorted(set(model.tracks['Perch']) | set(model.tracks['PerchFidget']))
    names = {n.get('name'): i for i, n in enumerate(model.doc['nodes'])}
    scene_root = names['Scene Root']
    if (scene_root, 'translation') not in channels:
        channels.append((scene_root, 'translation'))
    perch_n = int(round(model.duration('Perch') * fps))
    fidget_n = int(round(model.duration('PerchFidget') * fps))
    segments = [('Perch', perch_n)] * BIRD['perch_repeats'] + [('PerchFidget', fidget_n)]
    plan = [(clip, k / fps) for clip, n in segments for k in range(n)] + [('Perch', 0.0)]
    values = {}
    for channel in channels:
        node, path = channel
        v = np.array([sample(model, clip, node, path, t) for clip, t in plan])
        if path == 'rotation':     # one hemisphere, so the blends and the linear keys turn the short way
            for i in range(1, len(v)):
                if np.dot(v[i], v[i - 1]) < 0:
                    v[i] = -v[i]
        values[channel] = v
    # Blend each segment's end into the next segment's first frame (Perch ends where it starts, PerchFidget a few
    # millimetres off it): the last B frames before a join take a growing share of the jump.
    blend = BIRD['blend_frames']
    start = 0
    for (clip, n) in segments:
        join = start + n                              # the next segment's first frame (or the closing frame)
        end_clip, end_time = clip, model.duration(clip)
        for channel, v in values.items():
            node, path = channel
            target = v[join]
            reached = sample(model, end_clip, node, path, end_time)
            if path == 'rotation' and np.dot(reached, target) < 0:
                reached = -reached
            jump = target - reached
            for b in range(blend):
                frame = join - blend + b
                v[frame] = v[frame] + jump * (b + 1) / (blend + 1)
            if path == 'rotation':
                v[start:join] /= np.linalg.norm(v[start:join], axis=1, keepdims=True)
        start = join
    times = np.arange(len(plan)) / fps
    # Feet lock: forward kinematics per frame; lift the Scene Root by the feet's drop below frame 0.
    feet = [names[f] for f in FEET]

    def world(node, frame):
        m = np.identity(4)
        while True:
            n = model.doc['nodes'][node]
            got = {path: values[(node, path)][frame] if (node, path) in values else n.get(path, default)
                   for path, default in (('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]), ('scale', [1, 1, 1]))}
            m = trs(got['translation'], got['rotation'], got['scale']) @ m
            if node not in model.parent:
                return m
            node = model.parent[node]

    heights = np.array([np.mean([world(f, i)[1, 3] for f in feet]) for i in range(len(plan))])
    lift = heights[0] - heights
    values[(scene_root, 'translation')][:, 1] += lift
    print(f'clip {BIRD["clip"]}: {len(plan) - 1} frames, {times[-1]:.2f} s; feet lift {lift.min():+.4f}..'
          f'{lift.max():+.4f} m (crow space); seam {np.abs(np.concatenate([v[0] - v[-1] for v in values.values()])).max():.2e}')
    return values, times


# --- the tray -----------------------------------------------------------------------------------------------------
# atlas regions (pixels): slats rows 0-160 (20 px each), cross bands rows 160-256 (24 px each)
SLATS = (0, 160)
BANDS = [(160, 184), (184, 208), (208, 232), (232, 256)]


def box(lo, hi, rows, rows_top=None):
    """A closed box, flat shaded, outward faces (counter-clockwise from outside). rows: atlas rows of the side faces,
    rows_top of the top face (default rows). Returns (positions, normals, uvs, indices)."""
    lo, hi = np.array(lo, float), np.array(hi, float)
    P, N, T, I = [], [], [], []
    faces = []
    for axis in range(3):
        for sign in (-1, 1):
            n = np.zeros(3)
            n[axis] = sign
            o1, o2 = [a for a in range(3) if a != axis]
            if sign < 0:
                o1, o2 = o2, o1
            faces.append((n, axis, o1, o2))
    for n, axis, o1, o2 in faces:
        c = (hi if n[axis] > 0 else lo)[axis]
        quad = []
        for s1, s2 in ((0, 0), (1, 0), (1, 1), (0, 1)):
            p = np.zeros(3)
            p[axis] = c
            p[o1] = (lo, hi)[s1][o1]
            p[o2] = (lo, hi)[s2][o2]
            quad.append(p)
        e1, e2 = quad[1] - quad[0], quad[3] - quad[0]
        if np.dot(np.cross(e1, e2), n) < 0:
            quad = [quad[0], quad[3], quad[2], quad[1]]
        # u along the longer of the two in-plane axes, v across the other
        ext = {o1: hi[o1] - lo[o1], o2: hi[o2] - lo[o2]}
        ua, va = (o1, o2) if ext[o1] >= ext[o2] else (o2, o1)
        r = rows_top if (rows_top is not None and axis == 1 and n[1] > 0) else rows
        span_u = min(256.0, ext[ua] / U * DENSITY)
        uvs = [((p[ua] - lo[ua]) / ext[ua] * span_u / 256,
                (r[0] + (p[va] - lo[va]) / ext[va] * (r[1] - r[0])) / 256) for p in quad]
        base = len(P)
        P += quad
        N += [n] * 4
        T += uvs
        I += [base, base + 1, base + 2, base, base + 2, base + 3]
    return P, N, T, I


def bar(half, cy, cz, radius, sides, rows):
    """A closed prism along x (the perch): smooth sides, flat end caps; u along x, v around."""
    P, N, T, I = [], [], [], []
    span_u = min(256.0, 2 * half / U * DENSITY) / 256
    for k in range(sides + 1):
        a = 2 * np.pi * k / sides
        n = np.array([0.0, np.sin(a), np.cos(a)])
        for x, u in ((-half, 0.0), (half, span_u)):
            P.append(np.array([x, cy, cz]) + radius * n)
            N.append(n)
            T.append((u, (rows[0] + (rows[1] - rows[0]) * k / sides) / 256))
    for k in range(sides):
        a, b, c, e = 2 * k, 2 * k + 1, 2 * k + 3, 2 * k + 2      # (-x, a) (+x, a) (+x, a') (-x, a')
        tri = [a, b, c, a, c, e]
        normal = np.cross(P[b] - P[a], P[c] - P[a])
        if np.dot(normal, N[a] + N[e]) < 0:
            tri = [a, c, b, a, e, c]
        I += tri
    for x, sign in ((-half, -1.0), (half, 1.0)):
        base = len(P)
        n = np.array([sign, 0.0, 0.0])
        for k in range(sides):
            a = 2 * np.pi * k / sides
            P.append(np.array([x, cy + radius * np.sin(a), cz + radius * np.cos(a)]))
            N.append(n)
            T.append((0.5 + 0.03 * np.cos(a), (rows[0] + 10 + 8 * np.sin(a)) / 256))
        for k in range(1, sides - 1):
            tri = [base, base + k, base + k + 1]
            if np.dot(np.cross(P[tri[1]] - P[tri[0]], P[tri[2]] - P[tri[0]]), n) < 0:
                tri = [tri[0], tri[2], tri[1]]
            I += tri
    return P, N, T, I


def tray_geometry():
    w, d = TRAY['width'] * U / 2, TRAY['depth'] * U
    floor, rim, t = TRAY['floor'] * U, TRAY['rim'] * U, TRAY['rim_thickness'] * U
    top, radius, sides = TRAY['perch_top'] * U, TRAY['perch_radius'] * U, TRAY['perch_sides']
    half, post = TRAY['perch_half_length'] * U, TRAY['post_size'] * U
    perch_z = BIRD['origin_z'] * U + perch_offset
    # floor rows: as many 20 px slats as the inner depth takes at DENSITY
    floor_rows = (SLATS[0], SLATS[0] + min(SLATS[1], (d - t) / U * DENSITY))
    parts = [
        box((-w + t, 0, 0), (w - t, floor, d - t), floor_rows),                    # the slatted floor
        box((-w, 0, d - t), (w, rim, d), BANDS[0], BANDS[1]),                      # front rim
        box((-w, 0, 0), (-w + t, rim, d - t), BANDS[2], BANDS[1]),                 # left rim
        box((w - t, 0, 0), (w, rim, d - t), BANDS[2], BANDS[1]),                   # right rim
        bar(half, top - radius, perch_z, radius, sides, (20, 40)),                 # the perch bar, ends in the posts
        box((-half - post / 2, floor, perch_z - post / 2), (-half + post / 2, top + post / 4, perch_z + post / 2),
            (60, 80)),
        box((half - post / 2, floor, perch_z - post / 2), (half + post / 2, top + post / 4, perch_z + post / 2),
            (60, 80)),
    ]
    P, N, T, I = [], [], [], []
    for p, n, uv, idx in parts:
        base = len(P)
        P += p
        N += n
        T += uv
        I += [base + i for i in idx]
    return (np.array(P, np.float32), np.array(N, np.float32), np.array(T, np.float32), np.array(I, np.uint32))


perch_offset = 0.0            # set in main(): the soles' centre in z, so the bar is under the toes


# --- GLB writing --------------------------------------------------------------------------------------------------
class Blob:
    def __init__(self):
        self.data = bytearray()
        self.views, self.accessors = [], []

    def view(self, raw, target=None):
        self.data.extend(b'\0' * (-len(self.data) % 4))
        entry = {'buffer': 0, 'byteOffset': len(self.data), 'byteLength': len(raw)}
        if target:
            entry['target'] = target
        self.views.append(entry)
        self.data.extend(raw)
        return len(self.views) - 1

    def accessor(self, values, kind, target=None, bounds=False):
        values = np.ascontiguousarray(values)
        component = {np.dtype(np.float32): 5126, np.dtype(np.uint32): 5125, np.dtype(np.uint16): 5123,
                     np.dtype(np.uint8): 5121}[values.dtype]
        entry = {'bufferView': self.view(values.tobytes(), target), 'componentType': component,
                 'count': int(len(values)), 'type': kind}
        if bounds:
            flat = values.reshape(len(values), -1)
            entry['min'] = [float(x) for x in flat.min(0)]
            entry['max'] = [float(x) for x in flat.max(0)]
        self.accessors.append(entry)
        return len(self.accessors) - 1

    def copy(self, doc, binary, index):
        """An accessor of the source document, copied with its data."""
        source = dict(doc['accessors'][index])
        view = doc['bufferViews'][source['bufferView']]
        start = view.get('byteOffset', 0)
        new_view = self.view(bytes(binary[start:start + view['byteLength']]), view.get('target'))
        if 'byteStride' in view:
            self.views[new_view]['byteStride'] = view['byteStride']
        source['bufferView'] = new_view
        self.accessors.append(source)
        return len(self.accessors) - 1


def materials_and_images(blob, max_size=None):
    """Six crow materials (body/head x LOD0-1, LOD2, LOD3) and the tray's, with their embedded PNGs (max_size: each
    image at most this wide, for the static copy, which is never drawn)."""
    images, textures = [], []

    def texture(path):
        data = path.read_bytes()
        if max_size:
            image = Image.open(path)
            if image.width > max_size:
                out = io.BytesIO()
                image.resize((max_size, max_size * image.height // image.width), Image.LANCZOS).save(out, 'PNG',
                                                                                                    optimize=True)
                data = out.getvalue()
        images.append({'bufferView': blob.view(data), 'mimeType': 'image/png', 'name': path.stem})
        textures.append({'source': len(images) - 1, 'sampler': 0})
        return len(textures) - 1

    materials = []
    for key in ('body0', 'head0', 'body2', 'head2', 'body3', 'head3'):
        materials.append({'name': f'CageBird_{key}',
                          'pbrMetallicRoughness': {'baseColorTexture': {'index': texture(TEX / f'{key}_basecolor.png')},
                                                   'metallicRoughnessTexture': {'index': texture(TEX / f'{key}_mr.png')},
                                                   'metallicFactor': 0.0},
                          'normalTexture': {'index': texture(TEX / f'{key}_normal.png')},
                          'extras': {'openyamm_specular': 0}})
    materials.append({'name': 'CageBird_tray',
                      'pbrMetallicRoughness': {'baseColorTexture': {'index': texture(TEX / 'tray_basecolor.png')},
                                               'metallicFactor': 0.0, 'roughnessFactor': 0.75}})
    return materials, images, textures


# crow material index (skin A's numbering; B shares the textures) -> new material
MATERIAL = {0: 0, 1: 0, 2: 1, 3: 1, 4: 2, 5: 2, 6: 3, 7: 3, 8: 4, 9: 4, 10: 5, 11: 5}
TRAY_MATERIAL = 6
SAMPLERS = [{'magFilter': 9729, 'minFilter': 9987, 'wrapS': 33071, 'wrapT': 33071},
            {'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 10497}]


def tray_primitive(blob, tray, joint=None):
    p, n, uv, idx = tray
    prim = {'attributes': {'POSITION': blob.accessor(p, 'VEC3', 34962, True), 'NORMAL': blob.accessor(n, 'VEC3', 34962),
                           'TEXCOORD_0': blob.accessor(uv, 'VEC2', 34962)},
            'indices': blob.accessor(idx, 'SCALAR', 34963), 'material': TRAY_MATERIAL}
    if joint is not None:
        joints = np.zeros((len(p), 4), np.uint8)
        joints[:, 0] = joint
        weights = np.zeros((len(p), 4), np.float32)
        weights[:, 0] = 1.0
        prim['attributes']['JOINTS_0'] = blob.accessor(joints, 'VEC4', 34962)
        prim['attributes']['WEIGHTS_0'] = blob.accessor(weights, 'VEC4', 34962)
    return prim


def main():
    global perch_offset
    model = Model()
    doc, binary = model.doc, model.bin
    names = {n.get('name'): i for i, n in enumerate(doc['nodes'])}
    values, times = build_clip(model)
    # Rest = the clip's first frame.
    for (node, path), v in values.items():
        doc['nodes'][node][path] = [float(x) for x in v[0]]
        doc['nodes'][node].pop('matrix', None)

    # Measure the perched bird at rest (LOD0, crow space): its top and the soles of its feet.
    skin = doc['skins'][0]
    joint_names = [doc['nodes'][j]['name'] for j in skin['joints']]
    joints = model.joint_matrices(0)
    points, soles = [], []
    for prim in doc['meshes'][0]['primitives']:
        pos, _ = model.skin_primitive(prim, joints)
        j = array(doc, binary, prim['attributes']['JOINTS_0']).astype(int)
        w = array(doc, binary, prim['attributes']['WEIGHTS_0']).astype(float)
        dominant = np.array([joint_names[jj[np.argmax(ww)]] for jj, ww in zip(j, w)])
        points.append(pos)
        soles.append(pos[np.isin(dominant, FOOT_JOINTS)])
    points, soles = np.concatenate(points), np.concatenate(soles)
    top, sole = points[:, 1].max(), soles[:, 1].min()
    scale = BIRD['height_above_feet'] * U / (top - sole)
    yaw = np.radians(BIRD['yaw_degrees'])
    # the bar runs under the soles' centre (turned with the bird)
    feet_centre = soles.mean(0)
    perch_offset = scale * (np.cos(yaw) * feet_centre[2] - np.sin(yaw) * feet_centre[0])
    place_t = [0.0, TRAY['perch_top'] * U - scale * sole, BIRD['origin_z'] * U]
    place_r = [0.0, float(np.sin(yaw / 2)), 0.0, float(np.cos(yaw / 2))]
    print(f'bird: crow perched {top:.4f} m over its soles at {sole:.4f}; scale {scale:.4f} ({scale * 100:.1f} units '
          f'per crow metre), crow at MM9 scale 100 = {(top - points[:, 1].min()) * 100:.1f} units tall')

    # Node tree: CageBird -> [Tray (a still joint), BirdPlace -> Crow_Rig ...]
    old_roots = doc['scenes'][doc.get('scene', 0)]['nodes']
    doc['nodes'].append({'name': 'BirdPlace', 'children': list(old_roots), 'translation': place_t,
                         'rotation': place_r, 'scale': [float(scale)] * 3})
    place_index = len(doc['nodes']) - 1
    doc['nodes'].append({'name': 'Tray'})
    tray_joint_node = len(doc['nodes']) - 1
    doc['nodes'].append({'name': 'CageBird', 'children': [tray_joint_node, place_index]})
    doc['scenes'][doc.get('scene', 0)]['nodes'] = [len(doc['nodes']) - 1]
    model.parent = {c: i for i, n in enumerate(doc['nodes']) for c in n.get('children', [])}

    tray = tray_geometry()
    print(f'tray: {len(tray[3]) // 3} triangles, perch bar centre z {(BIRD["origin_z"] * U + perch_offset) / U:.1f}')

    # ---- the animated copy ----
    blob = Blob()
    materials, images, textures = materials_and_images(blob)
    meshes = []
    for mesh in doc['meshes']:
        prims = []
        for prim in mesh['primitives']:
            new = {'attributes': {k: blob.copy(doc, binary, v) for k, v in prim['attributes'].items()},
                   'indices': blob.copy(doc, binary, prim['indices']), 'material': MATERIAL[prim['material']]}
            prims.append(new)
        out = {'name': mesh['name'], 'primitives': prims}
        if mesh.get('extras'):
            out['extras'] = mesh['extras']
        meshes.append(out)
    tray_joint = len(skin['joints'])
    for mesh in meshes:                     # every draw and shadow LOD carries the tray
        mesh['primitives'].append(tray_primitive(blob, tray, tray_joint))
    ibm = array(doc, binary, skin['inverseBindMatrices']).reshape(-1, 16)
    ibm = np.vstack([ibm, np.identity(4).T.reshape(1, 16)]).astype(np.float32)   # Tray: at the origin, unscaled
    skins = [{'name': 'CageBird_Rig', 'joints': skin['joints'] + [tray_joint_node],
              'inverseBindMatrices': blob.accessor(ibm, 'MAT4')}]
    channels, samplers = [], []
    time_accessor = blob.accessor(times.astype(np.float32), 'SCALAR', None, True)
    for (node, path), v in sorted(values.items()):
        samplers.append({'input': time_accessor, 'output': blob.accessor(v.astype(np.float32),
                                                                         {3: 'VEC3', 4: 'VEC4'}[v.shape[1]]),
                         'interpolation': 'LINEAR'})
        channels.append({'sampler': len(samplers) - 1, 'target': {'node': node, 'path': path}})
    animated = {'asset': {'version': '2.0', 'generator': 'xeen_cagebird_claude build_glbs.py'}, 'scene': 0,
                'scenes': [{'nodes': doc['scenes'][doc.get('scene', 0)]['nodes']}], 'nodes': doc['nodes'],
                'meshes': meshes, 'materials': materials, 'textures': textures, 'images': images,
                'samplers': SAMPLERS[1:], 'skins': skins,
                'animations': [{'name': BIRD['clip'], 'channels': channels, 'samplers': samplers}],
                'accessors': blob.accessors, 'bufferViews': blob.views, 'buffers': [{'byteLength': 0}]}
    OUT.mkdir(parents=True, exist_ok=True)
    anim_path = OUT / 'xeen_deco_cagebird_anim.glb'
    write_glb(anim_path, animated, blob.data)

    # ---- the static copy: each LOD skinned at rest (with BirdPlace), plus the tray ----
    joints = model.joint_matrices(0)
    sblob = Blob()
    smaterials, simages, stextures = materials_and_images(sblob, STATIC_TEXTURE)
    snodes, smeshes = [], []
    chain = lod_meshes(doc)
    for level, mesh_index in enumerate(chain):
        prims = []
        for prim in doc['meshes'][mesh_index]['primitives']:
            pos, nrm = model.skin_primitive(prim, joints)
            prims.append({'attributes': {'POSITION': sblob.accessor(pos.astype(np.float32), 'VEC3', 34962, True),
                                         'NORMAL': sblob.accessor(nrm.astype(np.float32), 'VEC3', 34962),
                                         'TEXCOORD_0': sblob.copy(doc, binary, prim['attributes']['TEXCOORD_0'])},
                          'indices': sblob.copy(doc, binary, prim['indices']), 'material': MATERIAL[prim['material']]})
        prims.append(tray_primitive(sblob, tray))
        name = 'CageBird' if level == 0 else f'CageBird_LOD{level}'
        smeshes.append({'name': name, 'primitives': prims})
        snodes.append({'name': name, 'mesh': len(smeshes) - 1})
    static = {'asset': {'version': '2.0', 'generator': 'xeen_cagebird_claude build_glbs.py'}, 'scene': 0,
              'scenes': [{'nodes': list(range(len(snodes)))}], 'nodes': snodes, 'meshes': smeshes,
              'materials': smaterials, 'textures': stextures, 'images': simages, 'samplers': SAMPLERS[1:],
              'accessors': sblob.accessors, 'bufferViews': sblob.views, 'buffers': [{'byteLength': 0}]}
    raw_static = PROJECT / 'work' / 'static_unlinked.glb'
    write_glb(raw_static, static, sblob.data)
    static_path = OUT / 'xeen_deco_cagebird.glb'
    subprocess.run([sys.executable, str(REPO / 'tools/link_static_model_lods.py'), str(raw_static), str(static_path)],
                   check=True)
    for path in (anim_path, static_path):
        print(f'{path.relative_to(REPO)}: {path.stat().st_size / 1e6:.2f} MB')


if __name__ == '__main__':
    main()
