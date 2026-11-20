#!/usr/bin/env python3
"""The floating bottle of Beethoven (BottleFollow.scr) as one scripted model: work/mm9_bottlefloat.glb, the wine bottle
(work/mm9_deco_winebottle.glb, MM9's WineBottle01 at its Scale 1.3 and its 47-degree tilt) on a node with one looping
clip per start: sw, nw, ne, se. Each clip: six seconds' bobbing and turning at the start (FloatLoop), then the drift
along the start's markers at MM9's 40 LT/s, a jump to MarkerLower0, the drift along MarkerLower0-8 to Ludwig's
manuscript, and a jump back to the start. The map spawns it with evt.SpawnWorldModel at the origin, at scale 1: the
model is in native units, the path in world coordinates. Node translation in glTF is (-x, z, y) of the native point
(ModelAsset gltfModelPlacement).

Usage: bottle.py [--install]"""
import json
import math
import struct
import subprocess
import sys

import numpy as np

import props_table

sys.path.insert(0, str(props_table.ISLE / 'scripts'))
from glbio import array, read_glb  # noqa: E402

SPEED_LT = 40.0                     # ListTraverseNONAI: TRAVERSE_SPEED = 40
BOB_SECONDS, BOB_LT = 6.0, 3.0      # FloatLoop: six moves of 10 LT at 10/s; here a gentle bob round the waterline
RIDE_LT = 8.0                       # the bottle rides this far above its markers, which lie on the water (MM9's is translucent)
TURN_DEGREES_PER_SECOND = 90.0      # FloatLoop: 180 degrees at 90/s
TILT = 0.817                        # the bottles' Rotation pitch in the DAT
SCALE_MM9 = 1.3
STEP = 0.25                         # seconds between keys
STARTS = {'sw': 'BottleSW', 'nw': 'BottleNW', 'ne': 'BottleNE', 'se': 'BottleSE'}
MARKERS = {'sw': ('MarkerSW', 8), 'nw': ('MarkerNW', 8), 'ne': ('MarkerNE', 9), 'se': ('MarkerSE', 1)}
LOWER = ('MarkerLower', 8)


def named_objects():
    return {o['props'].get('Name'): o['props'] for o in props_table.objects() if o['props'].get('Name')}


def path_points(objects, base, last):
    return [np.array(objects[f'{base}{k}']['Pos'], float) for k in range(last + 1)]


def keyframes(objects, clip):
    """Times, LT positions and yaw (degrees) of one loop of a clip."""
    start = np.array(objects[STARTS[clip]]['Pos'], float)
    upper = [start] + path_points(objects, *MARKERS[clip])
    lower = path_points(objects, *LOWER)
    times, points, yaws = [], [], []

    def add(t, p, bob=True):
        times.append(t)
        lift = RIDE_LT if p[1] > -500 or p[1] < -1150 else 0.0     # the waterline: the surface stands 12 over the bed
        points.append(p + np.array([0.0, lift + (BOB_LT * math.sin(2 * math.pi * t / 2.0) if bob else 0.0), 0.0]))
        yaws.append(TURN_DEGREES_PER_SECOND * min(t, BOB_SECONDS))

    t = 0.0
    while t < BOB_SECONDS:
        add(t, start)
        t += STEP

    def drift(chain, t):
        for a, b in zip(chain, chain[1:]):
            length = float(np.linalg.norm(b - a))
            seconds = length / SPEED_LT
            for s in np.arange(0.0, seconds, STEP):
                add(t + s, a + (b - a) * (s / seconds))
            t += seconds
        return t

    t = drift(upper, t)
    add(t, upper[-1])
    add(t + 0.01, lower[0])
    t = drift(lower, t + 0.01)
    add(t, lower[-1])
    add(t + 0.01, start)
    keep, last = [], -1.0
    for index, time in enumerate(times):              # strictly increasing keys (the loader's rule)
        if time > last + 0.002:
            keep.append(index)
            last = time
    return np.array(times, np.float32)[keep], np.array(points)[keep], np.array(yaws)[keep]


def quaternion(yaw_degrees):
    """glTF rotation: the tilt about x, then the turn about up (+y)."""
    half = math.radians(yaw_degrees) / 2
    q_yaw = np.array([0.0, math.sin(half), 0.0, math.cos(half)])
    q_tilt = np.array([math.sin(TILT / 2), 0.0, 0.0, math.cos(TILT / 2)])
    x1, y1, z1, w1 = q_yaw
    x2, y2, z2, w2 = q_tilt
    return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                     w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2], np.float32)


def main():
    work = props_table.HERE / 'work'
    document, binary = read_glb(work / 'mm9_deco_winebottle.glb')
    binary = bytearray(binary)
    meta = json.loads((work / 'winebottle_meta.json').read_text())
    node_index = next(i for i, n in enumerate(document['nodes']) if 'mesh' in n and n.get('name', '').lower() == 'winebottle')
    node = document['nodes'][node_index]
    positions = np.concatenate([array(document, bytes(binary), p['attributes']['POSITION'])
                                for p in document['meshes'][node['mesh']]['primitives']])
    height = float(np.ptp(positions[:, 1]))
    size = meta['height_units'] * SCALE_MM9 / height
    print('bottle height', meta['height_units'] * SCALE_MM9, 'scale', size)
    for key in ('extensions', 'extras'):
        document.pop(key, None)
        node.pop(key, None)
    document['nodes'] = [{'name': 'Bottle', 'mesh': node['mesh'], 'scale': [size] * 3}]
    document['scenes'] = [{'nodes': [0]}]
    document['scene'] = 0
    document.pop('extensionsUsed', None) if 'MSFT_lod' in str(document.get('extensionsUsed')) else None
    objects = named_objects()
    document.setdefault('animations', [])
    views, accessors = document['bufferViews'], document['accessors']

    def add_accessor(data, kind, component=5126):
        while len(binary) % 4:
            binary.append(0)
        offset = len(binary)
        raw = np.asarray(data, np.float32).tobytes()
        binary.extend(raw)
        views.append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(raw)})
        accessor = {'bufferView': len(views) - 1, 'componentType': component, 'count': len(data), 'type': kind}
        if kind == 'SCALAR':
            accessor.update(min=[float(np.min(data))], max=[float(np.max(data))])
        if kind == 'VEC3':
            accessor.update(min=[float(v) for v in np.min(data, 0)], max=[float(v) for v in np.max(data, 0)])
        accessors.append(accessor)
        return len(accessors) - 1

    for clip in STARTS:
        times, points, yaws = keyframes(objects, clip)
        native = points[:, [0, 2, 1]] * 2.56
        translation = np.stack([-native[:, 0], native[:, 2], native[:, 1]], 1).astype(np.float32)
        rotation = np.array([quaternion(y) for y in yaws], np.float32)
        input_ = add_accessor(times, 'SCALAR')
        document['animations'].append({
            'name': clip,
            'samplers': [{'input': input_, 'output': add_accessor(translation, 'VEC3'), 'interpolation': 'LINEAR'},
                         {'input': input_, 'output': add_accessor(rotation, 'VEC4'), 'interpolation': 'LINEAR'}],
            'channels': [{'sampler': 0, 'target': {'node': 0, 'path': 'translation'}},
                         {'sampler': 1, 'target': {'node': 0, 'path': 'rotation'}}]})
        print(clip, 'seconds', round(float(times[-1]), 1), 'keys', len(times))
    while len(binary) % 4:
        binary.append(0)
    document['buffers'] = [{'byteLength': len(binary)}]
    text = json.dumps(document, separators=(',', ':')).encode()
    text += b' ' * (-len(text) % 4)
    out = work / 'mm9_bottlefloat.glb'
    with open(out, 'wb') as stream:
        stream.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(text) + 8 + len(binary)))
        stream.write(struct.pack('<II', len(text), 0x4E4F534A))
        stream.write(text)
        stream.write(struct.pack('<II', len(binary), 0x004E4942))
        stream.write(bytes(binary))
    print('WROTE', out)
    if '--install' in sys.argv:
        subprocess.run([sys.executable, str(props_table.REPO / 'tools/install_model.py'), str(out), '--world', 'mm9',
                        '--name', 'mm9_bottlefloat.glb'], check=True, cwd=props_table.REPO)


if __name__ == '__main__':
    main()
