#!/usr/bin/env python3
"""Fit the XD-17 cascade (build_fall.py waterfall_xd17) to the valley's real rock and move its origin to the foot.

The built model has its origin at the lip (the notch's crest point) and follows the measured centre-line profile.
This script places it as the game will (origin at the cliff-foot point FOOT, facing FACING with the binding's
yaw_offset -90 deg, so glTF +Z pours along FACING and glTF +X lies to the left of it), triangulates the valley
floor's points from A5's L4 (devdocs/xeen/briefs/xd17/L4/rooms.yml, room:valley) and lifts every vertex of the core
and the spray veils that lies less than its layer's clearance above the rock. Foam and mist are left alone (they
stand on the pool). Then it shifts every vertex so the origin is the foot point (z 0, the floor there).

Usage: fit_xd17.py <in.glb> <out.glb>"""
import json
import math
import struct
import sys
from pathlib import Path

import numpy as np
import yaml
from scipy.spatial import Delaunay

REPO = Path(__file__).resolve().parents[4]
UNITS = 81.7
FOOT = np.array([6272.0, 2304.0])       # the cliff-foot point under the notch (floor z 0)
FACING = 200.0                          # degrees, the direction the water pours (west-south-west)
LIP_OUT, LIP_Z = 1483.0, 1941.0         # the lip's distance behind the foot along FACING, and its height
POOL = (5120.0, 2304.0, 1024.0, 704.0)  # places_l2.POOL: centre and radii (its surface -40)
CLEARANCE = {'Stream': 10.0, 'Core': 16.0, 'Haze1': 34.0, 'Haze2': 56.0}
BURY_BEYOND = 690.0                     # inland of this the stream may lie under the ground: it wells up there

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
raw = src.read_bytes()
json_len = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + json_len])
bin_off = 20 + json_len
bin_len = struct.unpack_from('<I', raw, bin_off)[0]
binary = bytearray(raw[bin_off + 8:bin_off + 8 + bin_len])

rooms = yaml.safe_load(open(REPO / 'devdocs/xeen/briefs/xd17/L4/rooms.yml'))['rooms']
valley = next(r for r in rooms if r['id'] == 'room:valley')
pts = np.array(valley['floor_points'], dtype=float)
tri = Delaunay(pts[:, :2])


def rock(xy):
    s = tri.find_simplex(xy)
    z = np.full(len(xy), np.nan)
    ok = s >= 0
    T = tri.transform[s[ok]]
    b = np.einsum('nij,nj->ni', T[:, :2], xy[ok] - T[:, 2])
    b = np.concatenate([b, 1.0 - b.sum(axis=1, keepdims=True)], axis=1)
    z[ok] = (b * pts[tri.simplices[s[ok]], 2]).sum(axis=1)
    return z


a = math.radians(FACING)
u = np.array([math.cos(a), math.sin(a)])
left = np.array([-u[1], u[0]])
lip = FOOT - u * LIP_OUT
report = {}
for mesh in doc['meshes']:
    for prim in mesh['primitives']:
        name = doc['materials'][prim['material']]['name']
        acc = doc['accessors'][prim['attributes']['POSITION']]
        view = doc['bufferViews'][acc['bufferView']]
        start = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
        stride = view.get('byteStride', 12)
        assert stride == 12 and acc['componentType'] == 5126
        p = np.frombuffer(bytes(binary[start:start + 12 * acc['count']]), dtype='<f4').reshape(-1, 3).astype(float)
        p *= UNITS                                           # (across-left, up, out) in units, origin at the lip
        if name in CLEARANCE:
            xy = lip + np.outer(p[:, 2], u) + np.outer(p[:, 0], left)
            z = LIP_Z + p[:, 1]
            floor = rock(xy) + CLEARANCE[name]
            pool = ((xy[:, 0] - POOL[0]) / POOL[2]) ** 2 + ((xy[:, 1] - POOL[1]) / POOL[3]) ** 2 < 1.0
            floor[pool] = np.nan                             # the pool is a sunken level: the water goes under it
            if name == 'Stream':
                # It wells up: inland the floor sinks to 40 under the rock, rising to the clearance by 520 inland, so
                # the water breaks out of the ground along the gully's own shape, not along one straight row.
                ramp = np.clip((p[:, 2] + 740.0) / 220.0, 0.0, 1.0)
                ramp = ramp * ramp * (3.0 - 2.0 * ramp)
                floor = floor - (CLEARANCE[name] + 40.0) * (1.0 - ramp)
                low = np.isfinite(floor) & (z < floor)
            else:
                low = np.isfinite(floor) & (z < floor) & (p[:, 2] > -BURY_BEYOND)
            report[name] = {'vertices': int(len(p)), 'lifted': int(low.sum()),
                            'max_lift': float(np.max(floor[low] - z[low])) if low.any() else 0.0}
            z = np.where(low, floor, z)
            p[:, 1] = z - LIP_Z
        p[:, 2] -= LIP_OUT
        p[:, 1] += LIP_Z
        p /= UNITS
        binary[start:start + 12 * acc['count']] = p.astype('<f4').tobytes()
        acc['min'] = p.min(axis=0).tolist()
        acc['max'] = p.max(axis=0).tolist()
encoded = json.dumps(doc, separators=(',', ':')).encode()
encoded += b' ' * (-len(encoded) % 4)
binary += b'\0' * (-len(binary) % 4)
dst.write_bytes(struct.pack('<III', 0x46546c67, 2, 28 + len(encoded) + len(binary))
                + struct.pack('<II', len(encoded), 0x4e4f534a) + encoded
                + struct.pack('<II', len(binary), 0x004e4942) + bytes(binary))
lo = np.min([doc['accessors'][pr['attributes']['POSITION']]['min'] for m in doc['meshes'] for pr in m['primitives']], 0)
hi = np.max([doc['accessors'][pr['attributes']['POSITION']]['max'] for m in doc['meshes'] for pr in m['primitives']], 0)
report['bounds_units'] = {'lo': (lo * UNITS).round(1).tolist(), 'hi': (hi * UNITS).round(1).tolist(),
                          'height': round(float((hi[1] - lo[1]) * UNITS), 2)}
print(json.dumps(report, indent=1))
