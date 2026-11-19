"""Merge the translated Paradise Valley chest and its local Cycles illumination into the retained bake."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bake_geometry import rle_bgra
from stale_bakes import fnv1a64


class Lighting:
    def __init__(self, path):
        self.path = path
        self.data = path.read_bytes()
        b = self.data
        if b[:8] != b'OYMLIT1\0' or struct.unpack_from('<I', b, 8)[0] != 5:
            raise ValueError('Expected version-5 lighting')
        self.pc, self.fc, self.vc, self.lc = struct.unpack_from('<4I', b, 32)
        self.po, self.fo, self.vo, self.lo, self.pixel = struct.unpack_from('<5I', b, 48)
        self.pages = []
        for i in range(self.pc):
            w, h, start, length = struct.unpack_from('<4I', b, self.po + i * 16)
            self.pages.append((w, h, b[start:start + length]))
        end = start + length
        self.probe_count, count = struct.unpack_from('<II', b, end + 24)
        self.probes = b[end + 32:end + 32 + self.probe_count * 52]
        self.probe_prefix = b[end:end + 24]
        cursor = end + 32 + len(self.probes)
        self.deps = {}
        for _ in range(count):
            length, digest = struct.unpack_from('<IQ', b, cursor)
            cursor += 12
            name = b[cursor:cursor + length].decode()
            cursor += length
            self.deps[name] = digest
        direct_count, = struct.unpack_from('<I', b, cursor)
        cursor += 4
        self.direct = []
        if direct_count != self.pc // 2:
            raise ValueError('Direct page count mismatch')
        for _ in range(direct_count):
            w, h, length = struct.unpack_from('<III', b, cursor)
            cursor += 12
            self.direct.append((w, h, b[cursor:cursor + length]))
            cursor += length
        if cursor != len(b):
            raise ValueError('Unexpected lighting extension')
        self.faces = {}
        for i in range(self.fc):
            key, model, face, page, flags, first = struct.unpack_from('<QIIHHI', b, self.fo + i * 24)
            self.faces[model, face] = page, first

    def uv(self, model, face, count):
        page, first = self.faces[model, face]
        return page, np.array([struct.unpack_from('<ff', self.data, self.vo + (first + i) * 12)
                               for i in range(count)])


def decode(page):
    w, h, content = page
    result = bytearray()
    cursor = 0
    while cursor < len(content):
        tag = content[cursor]
        cursor += 1
        count = (tag & 127) + 1
        if tag & 128:
            result += content[cursor:cursor + 4] * count
            cursor += 4
        else:
            result += content[cursor:cursor + 4 * count]
            cursor += count * 4
    if len(result) != w * h * 4:
        raise ValueError('Invalid RGBM page')
    return np.frombuffer(result, dtype=np.uint8).reshape(h, w, 4).copy()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', required=True, type=Path)
    parser.add_argument('--rebake', required=True, type=Path)
    parser.add_argument('--map', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    old, new = Lighting(args.original), Lighting(args.rebake)
    geometry = args.map.read_bytes()
    if struct.unpack_from('<Q', new.data, 16)[0] != fnv1a64(geometry):
        raise ValueError('Rebake does not match the translated chest geometry')
    if (old.fc, old.vc, old.lc) != (new.fc, new.vc, new.lc):
        raise ValueError('Translation changed topology or authored lights')
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'util'))
    from map_export import parse_odm_file
    native = parse_odm_file(args.map)['payload']
    original_map = args.original.with_suffix('.odm')
    if fnv1a64(original_map.read_bytes()) != struct.unpack_from('<Q', old.data, 16)[0]:
        raise ValueError('Original map does not match the retained bake')
    original_native = parse_odm_file(original_map)['payload']
    for before, after in zip(original_native['bmodels'][26]['vertices'], native['bmodels'][26]['vertices']):
        if after != dict(before, x=before['x'] + 2048):
            raise ValueError('Expected a horizontal 2048-unit chest translation')
    original_native['bmodels'][26] = native['bmodels'][26]
    if original_native != native:
        raise ValueError('Geometry outside the chest changed')
    changed = {}
    changed_direct = {}

    def update(page, direct=False):
        entries = old.direct if direct else old.pages
        cache = changed_direct if direct else changed
        if page not in cache:
            cache[page] = decode(entries[page])
        return cache[page]

    rectangles = []
    for fi, face in enumerate(native['bmodels'][26]['faces']):
        page, uv = old.uv(26, fi, len(face['vertex_indices']))
        next_page, next_uv = new.uv(26, fi, len(face['vertex_indices']))
        if page == 65535 or next_page == 65535:
            raise ValueError('Chest face has no baked receiver')
        w, h, _ = old.pages[page]
        nw, nh, _ = new.pages[next_page]
        original_xy = uv * [w, h] - .5
        next_xy = next_uv * [nw, nh] - .5
        transform = np.linalg.lstsq(np.column_stack([original_xy, np.ones(len(uv))]), next_xy, rcond=None)[0]
        if not np.allclose(np.column_stack([original_xy, np.ones(len(uv))]) @ transform, next_xy, atol=.01):
            raise ValueError('Chest chart transform is not planar')
        lo = np.maximum(0, np.floor(original_xy.min(axis=0)).astype(int) - 3)
        hi = np.minimum([w - 1, h - 1], np.ceil(original_xy.max(axis=0)).astype(int) + 3)
        xs, ys = np.meshgrid(np.arange(lo[0], hi[0] + 1), np.arange(lo[1], hi[1] + 1))
        points = np.stack([xs, ys, np.ones_like(xs)], axis=-1) @ transform
        sx = np.clip(np.rint(points[:, :, 0]).astype(int), 0, nw - 1)
        sy = np.clip(np.rint(points[:, :, 1]).astype(int), 0, nh - 1)
        for term in [0, 1]:
            update(page + term)[ys, xs] = decode(new.pages[next_page + term])[sy, sx]
        update(page // 2, True)[ys, xs] = decode(new.direct[next_page // 2])[sy, sx]
        rectangles.append([page, lo.tolist(), hi.tolist()])

    w, h, _ = old.pages[0]
    if (w, h) != new.pages[0][:2]:
        raise ValueError('Terrain atlas dimensions differ')
    x, y = np.meshgrid(np.linspace(-32768, 32256, w), np.linspace(32768, -32256, h))
    local = np.minimum((x + 24328) ** 2 + (y - 21184) ** 2,
                       (x + 22280) ** 2 + (y - 21184) ** 2) <= 512 ** 2
    for term in [0, 1]:
        update(term)[local] = decode(new.pages[term])[local]
    update(0, True)[local] = decode(new.direct[0])[local]

    def near(position):
        x, y = position[:2]
        return min((x + cx) ** 2 + (y - 21184) ** 2 for cx in [24328, 22280]) <= 512 ** 2

    old_probes = [old.probes[i:i + 52] for i in range(0, len(old.probes), 52)]
    new_probes = [new.probes[i:i + 52] for i in range(0, len(new.probes), 52)]
    position = lambda record: struct.unpack_from('<3f', record)
    retained = [record for record in old_probes if not near(position(record))]
    old_outside = {position(record) for record in retained}
    new_outside = {position(record) for record in new_probes if not near(position(record))}
    if old_outside != new_outside:
        raise ValueError('Rebake changed probe coverage outside the repair region')
    probes = b''.join(retained + [record for record in new_probes if near(position(record))])

    pages = list(old.pages)
    direct = list(old.direct)
    for index, pixels in changed.items():
        pages[index] = (*pages[index][:2], rle_bgra(pixels.tobytes()))
    for index, pixels in changed_direct.items():
        direct[index] = (*direct[index][:2], rle_bgra(pixels.tobytes()))
    recipe = json.loads(old.path.with_suffix('.bake.json').read_text())
    recipe['chest_relocation'] = {
        'model': 26, 'event': 76, 'delta': [2048, 0, 0], 'region_radius': 512,
        'retained_sha256': hashlib.sha256(old.data).hexdigest(),
        'rebake_sha256': hashlib.sha256(new.data).hexdigest(),
        'rebake_recipe': json.loads(new.path.with_suffix('.bake.json').read_text()),
        'producer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    recipe_path = args.output / 'outa2.bake.json'
    recipe_path.write_text(json.dumps(recipe, indent=2) + '\n')
    deps = old.deps | new.deps
    deps['worlds/mm6/maps/outa2.odm'] = fnv1a64(geometry)
    deps['worlds/mm6/maps/outa2.bake.json'] = fnv1a64(recipe_path.read_bytes())
    directory, payload = bytearray(), bytearray()
    for width, height, content in pages:
        directory += struct.pack('<4I', width, height, old.pixel + len(payload), len(content))
        payload += content
    extension = bytearray(old.probe_prefix)
    extension += struct.pack('<II', len(probes) // 52, len(deps)) + probes
    for name, digest in sorted(deps.items()):
        name_bytes = name.encode()
        extension += struct.pack('<IQ', len(name_bytes), digest) + name_bytes
    extension += struct.pack('<I', len(direct))
    for width, height, content in direct:
        extension += struct.pack('<III', width, height, len(content)) + content
    result = bytearray(old.data[:old.pixel])
    result[old.po:old.fo] = directory
    result += payload + extension
    struct.pack_into('<Q', result, 16, fnv1a64(geometry))
    struct.pack_into('<I', result, 68, len(result))
    (args.output / 'outa2.lighting').write_bytes(result)
    report = {'chest_faces': len(rectangles), 'terrain_texels': int(local.sum()),
              'retained_probes': len(retained), 'updated_probes': len(probes) // 52 - len(retained),
              'chest_chart_rectangles': rectangles}
    (args.output / 'repair-report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report))


if __name__ == '__main__':
    main()
