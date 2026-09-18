#!/usr/bin/env python3
"""Convert installed v1/v2 outdoor lighting sidecars to the sole v3 format."""

import argparse
import hashlib
import json
from pathlib import Path
import struct

import numpy as np

from bake_geometry import rle_bgra


ROOT = Path(__file__).resolve().parents[2]


def fnv(data):
    value = 14695981039346656037
    for byte in data:
        value = ((value ^ byte) * 1099511628211) & 0xffffffffffffffff
    return value


def encode_rgbm(rgb):
    multiplier = np.maximum(np.ceil(rgb.max(axis=2) * 255 / 4), 1)
    rgba = np.empty((*rgb.shape[:2], 4), dtype=np.uint8)
    rgba[:, :, :3] = np.rint(np.clip(rgb / (multiplier[:, :, None] * 4 / 255), 0, 1) * 255)
    rgba[:, :, 3] = multiplier.astype(np.uint8)
    return rgba[:, :, [2, 1, 0, 3]].tobytes()


def downsample_rgbm(payload, width, height):
    if width != 2048 or height != 2048:
        return payload, width, height
    bgra = np.frombuffer(payload, dtype=np.uint8).reshape(height, width, 4)
    rgb = bgra[:, :, [2, 1, 0]].astype(np.float32)
    rgb *= bgra[:, :, 3:4].astype(np.float32) * (4.0 / (255.0 * 255.0))
    rgb = rgb.reshape(1024, 2, 1024, 2, 3).mean(axis=(1, 3))
    return encode_rgbm(rgb), 1024, 1024


def converted_recipe(path):
    recipe = json.loads(path.read_text())
    old_size = recipe['profile']['terrain_size']
    if old_size == 1024:
        payload = path.read_bytes()
        return payload, fnv(payload)
    if old_size != 2048:
        raise ValueError(f'{path}: unsupported terrain size {old_size}')
    recipe['profile']['terrain_size'] = 1024
    recipe['conversion'] = {
        'source_format': 2,
        'terrain_filter': '2x2 linear-light box',
        'converter_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    payload = (json.dumps(recipe, sort_keys=True, indent=2) + '\n').encode()
    return payload, fnv(payload)


def update_recipe_hash(extension, recipe_name, recipe_hash):
    probe_count, dependency_count = struct.unpack_from('<II', extension, 0)
    cursor = 8 + probe_count * 36
    found = False
    for _ in range(dependency_count):
        length = struct.unpack_from('<I', extension, cursor)[0]
        name = extension[cursor + 12:cursor + 12 + length].decode()
        if name.endswith('/maps/' + recipe_name):
            struct.pack_into('<Q', extension, cursor + 4, recipe_hash)
            found = True
        cursor += 12 + length
    if cursor != len(extension) or not found:
        raise ValueError(f'missing dependency for {recipe_name}')


def convert(path):
    data = path.read_bytes()
    if len(data) < 96 or data[:8] != b'OYMLIT1\0':
        raise ValueError(f'{path}: invalid lighting header')
    version, header_size = struct.unpack_from('<II', data, 8)
    if version == 3:
        return False
    if version not in (1, 2) or header_size != 96:
        raise ValueError(f'{path}: unsupported lighting version {version}')

    page_count = struct.unpack_from('<I', data, 32)[0]
    page_offset, face_offset, vertex_offset, light_offset, pixel_offset, file_size = \
        struct.unpack_from('<6I', data, 48)
    if (page_offset != 96 or face_offset != 96 + page_count * 16 or file_size != len(data)
            or not face_offset <= vertex_offset <= light_offset <= pixel_offset <= file_size):
        raise ValueError(f'{path}: inconsistent lighting sections')

    pages = []
    expected_offset = pixel_offset
    for page_index in range(page_count):
        width, height, offset, byte_count = struct.unpack_from('<4I', data, page_offset + page_index * 16)
        if offset != expected_offset or byte_count != width * height * 4 or offset + byte_count > file_size:
            raise ValueError(f'{path}: invalid v{version} page {page_index}')
        payload = data[offset:offset + byte_count]
        if version == 2 and page_index < 2:
            payload, width, height = downsample_rgbm(payload, width, height)
        pages.append((width, height, rle_bgra(payload)))
        expected_offset = offset + byte_count

    extension = bytearray(data[expected_offset:])
    recipe_path = path.with_suffix('.bake.json')
    recipe_payload = None
    if version == 2:
        if page_count < 2 or page_count % 2:
            raise ValueError(f'{path}: invalid paired page count')
        recipe_payload, recipe_hash = converted_recipe(recipe_path)
        update_recipe_hash(extension, recipe_path.name, recipe_hash)
    elif extension:
        raise ValueError(f'{path}: unexpected v1 extension')

    header = bytearray(data[:96])
    struct.pack_into('<I', header, 8, 3)
    struct.pack_into('<I', header, 76, 1 if version == 2 else 0)
    page_records = bytearray()
    payloads = bytearray()
    for width, height, payload in pages:
        page_records += struct.pack('<4I', width, height, pixel_offset + len(payloads), len(payload))
        payloads += payload
    output = header + page_records + data[face_offset:pixel_offset] + payloads + extension
    struct.pack_into('<I', output, 68, len(output))

    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_bytes(output)
    temporary.replace(path)
    if recipe_payload is not None:
        recipe_temporary = recipe_path.with_suffix(recipe_path.suffix + '.tmp')
        recipe_temporary.write_bytes(recipe_payload)
        recipe_temporary.replace(recipe_path)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('paths', nargs='*', type=Path)
    args = parser.parse_args()
    paths = args.paths
    if not paths:
        paths = sorted(
            path
            for world in ('mm6', 'mm7', 'mm8', 'mm9')
            for path in (ROOT / 'assets_dev/worlds' / world / 'maps').glob('*.lighting')
        )
    converted = 0
    for path in paths:
        old_size = path.stat().st_size
        if convert(path):
            converted += 1
            print(f'{path}: {old_size} -> {path.stat().st_size}')
    print(f'Converted {converted} lighting sidecars to version 3.')


if __name__ == '__main__':
    main()
