"""The turret's pitch gate: the barrel group (housing, lens pods, barrel and front sleeves: parts 3 and 4) pitched
about the hub axis (pivot, the B_Barrel bone's x axis) from -40 to +40 degrees in 5-degree steps, tested for triangle
overlaps (BVH) against the yoke and turntable (parts 1, 2) and the mount (part 0). Overlaps already present at 0 degrees
(parts that touch at rest) are the baseline; a step passes when it adds none. Writes review/look_gate.json.
Args: -- <name>"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
name = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', f'{name}_tex.blend'))
obj = bpy.data.objects[name]
pivot = Vector(obj['pivot'])


def group(keep, matrix=Matrix()):
    bm = bmesh.new(); bm.from_mesh(obj.data)
    layer = bm.faces.layers.int['part']
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[layer] not in keep], context='FACES')
    bm.transform(matrix)
    tree = BVHTree.FromBMesh(bm); bm.free()
    return tree


static = {'yoke+turntable': group({1, 2}), 'mount': group({0})}
result = {'pivot': list(pivot), 'steps': {}}
baseline = None
for angle in range(-40, 41, 5):
    # + raises the muzzle (front at -y): rotation about +x by -angle lifts -y upward
    m = Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(-angle), 4, 'X') @ Matrix.Translation(-pivot)
    moving = group({3, 4}, m)
    counts = {k: len(moving.overlap(t)) for k, t in static.items()}
    if angle == 0:
        baseline = counts
    result['steps'][angle] = counts
result['baseline'] = baseline
ok = [a for a, c in result['steps'].items() if all(c[k] <= baseline[k] for k in c)]
up = 0
while up + 5 in ok:
    up += 5
down = 0
while down - 5 in ok:
    down -= 5
result['clear_up_degrees'], result['clear_down_degrees'] = up, down
json.dump(result, open(os.path.join(HERE, 'review', 'look_gate.json'), 'w'), indent=1)
print('LOOK_GATE', json.dumps(result))
