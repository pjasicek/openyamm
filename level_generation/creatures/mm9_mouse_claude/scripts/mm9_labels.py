"""MM9 mesh: per dominant bone, vertex count and x/y/z ranges (bind). Args: <rig blend>"""
import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
o = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'Body')
d = {}
for v in o.data.vertices:
    g = max(v.groups, key=lambda g: g.weight)
    d.setdefault(o.vertex_groups[g.group].name, []).append(o.matrix_world @ v.co)
for k, ps in d.items():
    print('LABEL', k, len(ps), ['%.4f..%.4f' % (min(p[i] for p in ps), max(p[i] for p in ps)) for i in range(3)])
arm = bpy.data.objects['MM9_Rig']
for b in arm.data.bones:
    print('BONE', b.name, tuple(round(x, 4) for x in b.head_local), tuple(round(x, 4) for x in b.tail_local), b.parent.name if b.parent else None)
