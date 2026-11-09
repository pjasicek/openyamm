"""Print dominant bone per region of the Body in a rig blend. Args: blend bone_substring"""
import bpy, sys
from collections import Counter
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
b = bpy.data.objects['Body']; arm = bpy.data.objects['MM9_Rig']
names = {g.index: g.name for g in b.vertex_groups}
for bn in arm.data.bones:
    if argv[1] in bn.name:
        print('BONE', bn.name, tuple(round(x, 3) for x in bn.head_local))
rows = []
for v in b.data.vertices:
    if not v.groups:
        continue
    g = max(v.groups, key=lambda g: g.weight)
    if argv[1] in names[g.group]:
        rows.append((names[g.group], round(v.co.y, 1), round(v.co.z, 1)))
print('DOM', Counter(rows).most_common(40))
