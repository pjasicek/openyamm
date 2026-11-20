#!/usr/bin/env python3
"""Bake burn maps (engine burn death, actors.yml `death_effect: burn`) straight from a creature GLB.

Burn order = surface distance from ignition points over the welded LOD 0 mesh (UV seams joined), with broad 3D noise,
equalised by surface area to 0..1; each texel adds fine noise so the front is ragged. Ignition: the rims of the listed
materials (wing membranes: open edges, or fold-back edges of a closed thin membrane) and every vertex mainly weighted to the listed bones (head, tail tip).
Listed fast materials burn at a fraction of the distance cost (membranes go first). Output per material, in its UV
space: red = burn order, green = ridged crack noise. Embed with burn_maps.py before region_variants.apply_variants.

  bake_burn_maps.py in.glb OUT_PREFIX --node Body --material DragonBody_A=body --material DragonHead_A=head
      --material DragonWings_A=wings --open DragonWings_A --fast DragonWings_A=0.5 --ignite Head Tail8 Tail9
writes OUT_PREFIX_body_burn.png etc. and OUT_PREFIX_burn.json (statistics).
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

from region_variants import read_glb

COMPONENTS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
TYPES = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}


def accessor(doc, binary, index):
    meta = doc['accessors'][index]
    view = doc['bufferViews'][meta['bufferView']]
    dtype = np.dtype(TYPES[meta['componentType']])
    width = COMPONENTS[meta['type']]
    stride = view.get('byteStride', dtype.itemsize * width)
    start = view.get('byteOffset', 0) + meta.get('byteOffset', 0)
    rows = np.ndarray((meta['count'], width), dtype, binary, start, (stride, dtype.itemsize))
    values = rows.astype(np.float64)
    if meta.get('normalized'):
        values /= np.iinfo(dtype).max
    return values if width > 1 else values[:, 0]


def hash3(cells):
    h = (cells[..., 0] * 73856093) ^ (cells[..., 1] * 19349663) ^ (cells[..., 2] * 83492791)
    h = (h ^ (h >> 13)) * 1274126177
    return ((h ^ (h >> 16)) & 0xffff).astype(np.float64) / 65535.0


def value_noise(points):
    cell = np.floor(points).astype(np.int64)
    f = points - cell
    f = f * f * (3 - 2 * f)
    result = 0.0
    for corner in range(8):
        offset = np.array([(corner >> axis) & 1 for axis in range(3)])
        weight = np.prod(np.where(offset == 1, f, 1 - f), axis=-1)
        result = result + weight * hash3(cell + offset)
    return result


def fbm(points, octaves=3):
    total, amplitude, scale = 0.0, 0.5, 1.0
    for _ in range(octaves):
        total = total + amplitude * value_noise(points * scale)
        amplitude *= 0.5
        scale *= 2.03
    return total / (1 - 0.5 ** octaves)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('glb')
    parser.add_argument('prefix')
    parser.add_argument('--node', default='Body')
    parser.add_argument('--material', action='append', required=True, help='MATERIAL=label')
    parser.add_argument('--open', action='append', default=[], help='material whose open edges ignite')
    parser.add_argument('--fast', action='append', default=[], help='MATERIAL=cost factor')
    parser.add_argument('--ignite', nargs='*', default=[], help='bones whose vertices ignite')
    parser.add_argument('--size', type=int, default=1024)
    args = parser.parse_args()
    labels = dict(item.split('=', 1) for item in args.material)
    fast = {name: float(value) for name, value in (item.split('=', 1) for item in args.fast)}
    doc, binary = read_glb(args.glb)
    node = next(n for n in doc['nodes'] if n.get('name') == args.node)
    joint_names = [doc['nodes'][j].get('name', '') for j in doc['skins'][node['skin']]['joints']]
    material_names = [m.get('name', '') for m in doc['materials']]

    positions, uvs, dominant, triangles, owners = [], [], [], [], []
    offset = 0
    for primitive in doc['meshes'][node['mesh']]['primitives']:
        name = material_names[primitive['material']]
        label = next((v for k, v in labels.items() if name == k or name.startswith(k + '.')), None)
        if label is None:
            raise SystemExit(f'material {name} has no --material label')
        attributes = primitive['attributes']
        position = accessor(doc, binary, attributes['POSITION'])
        joints = accessor(doc, binary, attributes['JOINTS_0']).astype(int)
        weights = accessor(doc, binary, attributes['WEIGHTS_0'])
        positions.append(position)
        uvs.append(accessor(doc, binary, attributes['TEXCOORD_0']))
        dominant.extend(joint_names[joints[i, np.argmax(weights[i])]] for i in range(len(position)))
        triangles.append(accessor(doc, binary, primitive['indices']).astype(int).reshape(-1, 3) + offset)
        owners.extend([name] * (len(triangles[-1])))
        offset += len(position)
    position = np.concatenate(positions)
    uv = np.concatenate(uvs)
    triangle = np.concatenate(triangles)
    owner = np.array(owners)
    # Weld UV-seam copies so distance flows across seams and material borders.
    keys = np.round(position / 1e-5).astype(np.int64)
    _, weld = np.unique(keys, axis=0, return_inverse=True)
    weld = weld.reshape(-1)
    count = weld.max() + 1
    welded = np.zeros((count, 3))
    welded[weld] = position
    tri = weld[triangle]
    edges = np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
    edge_owner = np.concatenate([owner, owner, owner])
    keyed = np.sort(edges, axis=1)
    unique, inverse, uses = np.unique(keyed, axis=0, return_inverse=True, return_counts=True)
    inverse = inverse.reshape(-1)
    factor = np.ones(len(edges))
    for name, value in fast.items():
        factor[np.char.startswith(edge_owner.astype(str), name)] = value
    edge_factor = np.ones(len(unique))
    np.minimum.at(edge_factor, inverse, factor)
    length = np.linalg.norm(welded[unique[:, 0]] - welded[unique[:, 1]], axis=1) * edge_factor + 1e-9
    graph = coo_matrix((np.concatenate([length, length]),
                        (np.concatenate([unique[:, 0], unique[:, 1]]), np.concatenate([unique[:, 1], unique[:, 0]]))),
                       shape=(count, count)).tocsr()
    sources = set()
    # A membrane's rim: an open edge, or on a closed thin membrane an edge whose two faces point opposite ways.
    corners = welded[tri]
    normals = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
    edge_normals = np.concatenate([normals, normals, normals])
    first_normal = np.zeros((len(unique), 3))
    folded = np.zeros(len(unique), bool)
    seen = np.zeros(len(unique), bool)
    for edge, normal in zip(inverse, edge_normals):
        if seen[edge]:
            folded[edge] |= float(np.dot(first_normal[edge], normal)) < -0.3
        else:
            first_normal[edge], seen[edge] = normal, True
    rim = (uses == 1) | folded
    for name in args.open:
        mine = np.zeros(len(unique), bool)
        mine[inverse[np.char.startswith(edge_owner.astype(str), name)]] = True
        sources.update(unique[rim & mine].reshape(-1).tolist())
    sources.update(weld[i] for i, name in enumerate(dominant) if name in args.ignite)
    distance = dijkstra(graph, indices=sorted(sources), min_only=True)
    # Separate pieces (teeth, claws, horns) the front cannot walk to burn with the nearest surface it reaches.
    unreached = ~np.isfinite(distance)
    if unreached.any():
        gap, nearest = cKDTree(welded[~unreached]).query(welded[unreached])
        distance[unreached] = distance[~unreached][nearest] + gap
    order = distance / distance.max() + 0.22 * (fbm(welded * 3.2 + 11.0) - 0.5)
    # Equalise by surface area, so the front sweeps area evenly whatever the mesh density.
    area = np.linalg.norm(np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0]), axis=1) / 2
    vertex_area = np.zeros(count)
    for corner in range(3):
        np.add.at(vertex_area, tri[:, corner], area / 3)
    sorted_vertices = np.argsort(order, kind='stable')
    cumulative = np.cumsum(vertex_area[sorted_vertices])
    vertex_order = np.empty(count)
    vertex_order[sorted_vertices] = 0.02 + 0.94 * (cumulative - 0.5 * vertex_area[sorted_vertices]) / cumulative[-1]

    size = args.size
    report = {'ignition_vertices': len(sources), 'rim_edges': int(rim.sum()), 'separate_piece_vertices': int(unreached.sum()),
              'maps': {}}
    for name, label in labels.items():
        values = np.full((size, size), np.nan)
        texel_position = np.zeros((size, size, 3))
        for index in np.nonzero(np.char.startswith(owner.astype(str), name))[0]:
            vertices = triangle[index]
            pixels = uv[vertices] * size   # glTF v runs down the image, as its rows
            x0, y0 = np.maximum(np.floor(pixels.min(0)).astype(int), 0)
            x1, y1 = np.minimum(np.ceil(pixels.max(0)).astype(int), size - 1)
            if x1 < x0 or y1 < y0:
                continue
            xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            a, b, c = pixels
            den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(den) < 1e-12:
                continue
            w0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
            w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
            w2 = 1 - w0 - w1
            inside = (w0 >= -0.01) & (w1 >= -0.01) & (w2 >= -0.01)
            if not inside.any():
                continue
            rows = (ys[inside] - 0.5).astype(int)
            columns = (xs[inside] - 0.5).astype(int)
            weights = np.stack([w0[inside], w1[inside], w2[inside]], -1)
            values[rows, columns] = weights @ vertex_order[weld[vertices]]
            texel_position[rows, columns] = weights @ position[vertices]
        covered = np.isfinite(values)
        red = np.where(covered, np.clip(values + 0.12 * (fbm(texel_position * 14.0 + 3.0) - 0.5), 0, 1), np.nan)
        green = np.where(covered, (1.0 - np.abs(2.0 * fbm(texel_position * 9.0 + 29.0, 2) - 1.0)) ** 4, np.nan)
        for _ in range(16):   # pad islands for filtering and mips
            missing = ~np.isfinite(red)
            if not missing.any():
                break
            shifted_r = np.stack([np.roll(np.roll(red, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1)])
            shifted_g = np.stack([np.roll(np.roll(green, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1)])
            known = np.isfinite(shifted_r).sum(0)
            fill = missing & (known > 0)
            red[fill] = np.nansum(shifted_r, 0)[fill] / known[fill]
            green[fill] = np.nansum(shifted_g, 0)[fill] / known[fill]
        image = np.zeros((size, size, 3), np.uint8)
        image[..., 0] = np.round(np.nan_to_num(red, nan=1.0) * 255)
        image[..., 1] = np.round(np.nan_to_num(green, nan=0.0) * 255)
        Image.fromarray(image, 'RGB').save(f'{args.prefix}_{label}_burn.png', optimize=True)
        report['maps'][label] = {'covered_texels': int(covered.sum()),
                                 'order_range': [float(np.nanmin(values)), float(np.nanmax(values))]}
    Path(f'{args.prefix}_burn.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
