"""The Test Emplacement's pitch gate: the head (every vertex not on B_Root) pitched about B_Barrel's x axis from -30
to +30 degrees in 5-degree steps against the base and yoke (B_Root), counting triangle overlaps (BVH); a step passes
when it adds none over the rest pose. Reads export/hes_test_emplacement.blend; writes review/look_gate_emplacement.json."""
import json
import math
import os

import bmesh
import bpy
from mathutils import Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'export', 'hes_test_emplacement.blend'))
obj = bpy.data.objects['TestEmplacement']; rig = bpy.data.objects['Rig']
pivot = rig.data.bones['B_Barrel'].head_local.copy()
root = obj.vertex_groups['B_Root'].index


def tree(on_root, matrix=Matrix()):
    bm = bmesh.new(); bm.from_mesh(obj.data)
    dl = bm.verts.layers.deform.active
    keep = lambda v: (root in v[dl]) == on_root
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if not all(keep(v) for v in f.verts)], context='FACES')
    bm.transform(matrix)
    t = BVHTree.FromBMesh(bm); bm.free()
    return t


base = tree(True)
steps = {}
for angle in range(-30, 31, 5):
    m = Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(-angle), 4, 'X') @ Matrix.Translation(-pivot)
    steps[angle] = len(tree(False, m).overlap(base))
ok = [a for a, c in steps.items() if c <= steps[0]]
up = 0
while up + 5 in ok:
    up += 5
down = 0
while down - 5 in ok:
    down -= 5
result = {'pivot': list(pivot), 'steps': steps, 'clear_up_degrees': up, 'clear_down_degrees': down}
json.dump(result, open(os.path.join(HERE, 'review', 'look_gate_emplacement.json'), 'w'), indent=1)
print('LOOK_GATE', json.dumps(result))
