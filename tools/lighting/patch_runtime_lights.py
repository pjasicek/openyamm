"""Add live point lights to a v5 sun/sky bake while preserving existing illumination.

The mounted map and profile are inputs. Existing compressed pages and probes are retained
byte for byte. Initially hidden faces in revealed_cogs receive a black paired page, so they
take the authored local lights instead of the unbaked full-bright surface path.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

from stale_bakes import fnv1a64 as fnv


def patch(source, profile, output, assets):
    data = source.read_bytes()
    if (len(data) < 96 or data[:8] != b'OYMLIT1\0'
            or struct.unpack_from('<I', data, 8)[0] != 5 or struct.unpack_from('<I', data, 76)[0] != 1):
        raise ValueError('Expected version-5 lighting')
    world, name = profile['world'], profile['map']
    map_path = assets / 'worlds' / world / 'maps' / name
    if fnv(map_path.read_bytes()) != struct.unpack_from('<Q', data, 16)[0]:
        raise ValueError('Geometry does not match the retained bake')
    pc, fc, vc, lc = struct.unpack_from('<4I', data, 32)
    po, fo, vo, lo, pixels = struct.unpack_from('<5I', data, 48)
    if lc:
        raise ValueError('Retained bake already has authored lights')
    pages = []
    for i in range(pc):
        w, h, start, length = struct.unpack_from('<4I', data, po + i * 16)
        pages.append((w, h, data[start:start + length]))
    end = start + length
    probes, dependencies = struct.unpack_from('<II', data, end + 24)
    cursor = end + 32 + probes * 52
    probe_bytes = data[end:cursor]
    deps = []
    for _ in range(dependencies):
        length, digest = struct.unpack_from('<IQ', data, cursor)
        cursor += 12
        dep = data[cursor:cursor + length].decode('utf-8')
        cursor += length
        deps.append((dep, digest))
    direct_count, = struct.unpack_from('<I', data, cursor)
    if direct_count != pc // 2:
        raise ValueError('Direct receiver page count does not match')
    direct = data[cursor + 4:]
    faces = bytearray(data[fo:vo])
    vertices = bytearray(data[vo:lo])
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'util'))
    from map_export import parse_odm_file
    native = parse_odm_file(map_path)['payload']
    revealed = set(profile.get('revealed_cogs', []))
    black = bytes((0, 0, 0, 0, 1))
    repaired = []
    for i in range(fc):
        _, bi, fi, page, flags, first = struct.unpack_from('<QIIHHI', faces, i * 24)
        face = native['bmodels'][bi]['faces'][fi]
        if face['cog_number'] not in revealed or page != 65535:
            continue
        struct.pack_into('<HH', faces, i * 24 + 16, pc, 1)
        for j in range(len(face['vertex_indices'])):
            struct.pack_into('<ff', vertices, (first + j) * 12, .5, .5)
        repaired.append([bi, fi])
    if repaired:
        pages.extend([(1, 1, black), (1, 1, black)])
        direct += struct.pack('<III', 1, 1, len(black)) + black
        direct_count += 1
    lights = bytearray()
    for i, light in enumerate(profile['point_lights']):
        position, radius, colour = light['position'], light['radius'], light['color_abgr']
        if (len(position) != 3 or not all(math.isfinite(value) for value in position)
                or not math.isfinite(radius) or radius <= 0 or not 0 <= colour <= 0xffffffff):
            raise ValueError('Invalid local light')
        lights += struct.pack('<II4fII6f6I', i, 0, *position, radius, colour, 3,
                              0, 0, 0, 1, 90, 1, 0x3f800000, colour, 0, 0, 0, 0)
    recipe = json.loads(source.with_suffix('.bake.json').read_text())
    recipe['runtime_lighting'] = {
        'profile': profile, 'retained_sha256': hashlib.sha256(data).hexdigest(),
        'revealed_receivers': repaired,
        'producer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    output.mkdir(parents=True, exist_ok=True)
    recipe_path = output / source.with_suffix('.bake.json').name
    recipe_path.write_text(json.dumps(recipe, indent=2) + '\n')
    recipe_name = map_path.with_suffix('.bake.json').relative_to(assets).as_posix()
    deps = [(dep, fnv(recipe_path.read_bytes()) if dep == recipe_name else digest) for dep, digest in deps]
    if recipe_name not in dict(deps):
        raise ValueError('Retained bake does not declare its recipe')
    new_fo = 96 + len(pages) * 16
    new_vo = new_fo + len(faces)
    new_lo = new_vo + len(vertices)
    new_pixels = new_lo + len(lights)
    directory, payload = bytearray(), bytearray()
    for w, h, content in pages:
        directory += struct.pack('<4I', w, h, new_pixels + len(payload), len(content))
        payload += content
    extension = bytearray(probe_bytes)
    for dep, digest in deps:
        encoded = dep.encode('utf-8')
        extension += struct.pack('<IQ', len(encoded), digest) + encoded
    extension += struct.pack('<I', direct_count) + direct
    header = bytearray(data[:96])
    struct.pack_into('<4I', header, 32, len(pages), fc, vc, len(lights) // 80)
    result = header + directory + faces + vertices + lights + payload + extension
    struct.pack_into('<6I', result, 48, 96, new_fo, new_vo, new_lo, new_pixels, len(result))
    (output / source.name).write_bytes(result)
    print(json.dumps({'retained_pages': pc, 'retained_probe_bytes': len(probe_bytes),
                      'new_receivers': repaired, 'local_lights': len(lights) // 80}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--profile', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--assets', type=Path, default=Path(__file__).resolve().parents[2] / 'assets_dev')
    args = parser.parse_args()
    patch(args.source, json.loads(args.profile.read_text()), args.output, args.assets)
