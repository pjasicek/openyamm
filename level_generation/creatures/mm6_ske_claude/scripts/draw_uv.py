"""Draw the UVMap layout per material slot to PNGs (mesh lines). Args: -- <blend> <out prefix>"""
import bpy, sys, os
import numpy as np
blend, prefix = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
me = bpy.data.objects['Skeleton'].data
uv = me.uv_layers['UVMap'].data
for mi, mat in enumerate(me.materials):
    lines = []
    for p in me.polygons:
        if p.material_index != mi:
            continue
        li = list(p.loop_indices)
        for a, b in zip(li, li[1:] + li[:1]):
            lines.append((tuple(uv[a].uv), tuple(uv[b].uv)))
    np.save(f'{prefix}_{mat.name}.npy', np.array(lines))
