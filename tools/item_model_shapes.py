#!/usr/bin/env python3
"""Write the collision box of every ground-item model into assets_dev/engine/world_items/items.yml.

Each binding gets `bounds: [minX, minY, minZ, maxX, maxY, maxZ]`: the model's static bounds in world units at its
game scale (the binding's `length` over the longest horizontal side), in the item's own frame before its yaw
(OpenYAMM axes: glTF -X is x, glTF Z is y, glTF Y is up). The world runtimes collide and pick with it, also headless,
where models are never loaded (GROUND_ITEMS_3D_BEHAVIOUR.md section 3).

Reads the runtime copies under assets_dev (or --assets, a stage), the models the game loads. Re-run after installing or
replacing a model; --check only reports bindings whose bounds are missing or stale.
"""

import argparse
import json
import re
import struct
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
BINDINGS = REPO / 'assets_dev' / 'engine' / 'world_items' / 'items.yml'
ENTRY = re.compile(r'^(\s*- \{)(.*?)(\}.*)$')
FIELD = re.compile(r'\s*([A-Za-z_]+):\s*(\[[^\]]*\]|[^,]+)')
TOLERANCE = 0.15


def read_gltf(path):
    data = path.read_bytes()
    magic, _, _ = struct.unpack_from('<III', data, 0)
    if magic != 0x46546C67:
        raise ValueError(f'{path}: not a GLB')
    length, chunk_type = struct.unpack_from('<II', data, 12)
    if chunk_type != 0x4E4F534A:
        raise ValueError(f'{path}: first chunk is not JSON')
    return json.loads(data[20:20 + length])


def node_matrix(node):
    if 'matrix' in node:
        return np.array(node['matrix'], dtype=np.float64).reshape(4, 4).T
    translation = np.array(node.get('translation', [0.0, 0.0, 0.0]))
    x, y, z, w = node.get('rotation', [0.0, 0.0, 0.0, 1.0])
    rotation = np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    matrix = np.identity(4)
    matrix[:3, :3] = rotation * np.array(node.get('scale', [1.0, 1.0, 1.0]))
    matrix[:3, 3] = translation
    return matrix


def gltf_bounds(path):
    """Static bounds in glTF axes: every POSITION accessor's box, transformed by its node's world matrix."""
    gltf = read_gltf(path)
    nodes = gltf.get('nodes', [])
    scene = gltf.get('scenes', [{}])[gltf.get('scene', 0)]
    low = np.full(3, np.inf)
    high = np.full(3, -np.inf)
    stack = [(index, np.identity(4)) for index in scene.get('nodes', [])]
    while stack:
        index, parent = stack.pop()
        node = nodes[index]
        world = parent @ node_matrix(node)
        if 'mesh' in node:
            for primitive in gltf['meshes'][node['mesh']]['primitives']:
                accessor = gltf['accessors'][primitive['attributes']['POSITION']]
                if accessor.get('componentType') != 5126 or 'min' not in accessor or 'max' not in accessor:
                    raise ValueError(f'{path}: POSITION needs float components with min and max')
                a, b = accessor['min'], accessor['max']
                corners = np.array([[x, y, z, 1.0] for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])])
                points = (world @ corners.T).T[:, :3]
                low = np.minimum(low, points.min(axis=0))
                high = np.maximum(high, points.max(axis=0))
        stack.extend((child, world) for child in node.get('children', []))
    if not np.all(np.isfinite(low)):
        raise ValueError(f'{path}: no mesh')
    return low, high


def item_bounds(path, length):
    low, high = gltf_bounds(path)
    extent = max(high[0] - low[0], high[2] - low[2])
    if extent <= 1.0e-4:
        raise ValueError(f'{path}: no horizontal extent')
    scale = length / extent
    # OpenYAMM x = -glTF x, y = glTF z, z = glTF y.
    values = [-high[0], low[2], low[1], -low[0], high[2], high[1]]
    return [round(float(value) * scale, 1) for value in values]


def parse_fields(body):
    fields = {}
    for match in FIELD.finditer(body):
        fields[match.group(1)] = match.group(2).strip()
    return fields


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--check', action='store_true', help='report missing or stale bounds; change nothing')
    parser.add_argument('--bindings', type=Path, default=BINDINGS)
    parser.add_argument('--assets', type=Path, default=REPO / 'assets_dev',
                        help='the asset root the bindings\' model paths are relative to (a stage, say)')
    args = parser.parse_args()

    lines = args.bindings.read_text().splitlines(keepends=True)
    stale = []
    written = 0
    for number, line in enumerate(lines):
        match = ENTRY.match(line)
        if match is None:
            continue
        fields = parse_fields(match.group(2))
        if 'model' not in fields or 'length' not in fields:
            continue
        model = args.assets / fields['model']
        bounds = item_bounds(model, float(fields['length']))
        current = None
        if 'bounds' in fields:
            current = [float(value) for value in fields['bounds'].strip('[]').split(',')]
        if current is not None and len(current) == 6 \
                and all(abs(a - b) <= TOLERANCE for a, b in zip(current, bounds)):
            continue
        stale.append(fields.get('icon', fields['model']))
        if args.check:
            continue
        text = ', '.join(f'{value:g}' for value in bounds)
        body = re.sub(r',\s*bounds:\s*\[[^\]]*\]', '', match.group(2)).rstrip()
        newline = '\n' if line.endswith('\n') else ''
        lines[number] = f'{match.group(1)}{body}, bounds: [{text}]{match.group(3)}{newline}'
        written += 1

    if args.check:
        if stale:
            print(f'{len(stale)} bindings need bounds: {", ".join(stale[:20])}{" ..." if len(stale) > 20 else ""}')
            return 1
        print('all bounds current')
        return 0
    if written:
        args.bindings.write_text(''.join(lines))
    print(f'{written} bindings updated')
    return 0


if __name__ == '__main__':
    sys.exit(main())
