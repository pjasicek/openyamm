"""One-off repair of an already built master (bow_rig.py now writes it): string vertices (piece 102) wholly on Bow get
0.5 % StringNock, so tools/split_attachment.py sees no triangle mixing bow and body vertices. Args: -- <blend> [...]"""
import bpy, sys, os
import numpy as np
for path in sys.argv[sys.argv.index('--') + 1:]:
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(path))
    body = bpy.data.objects['Body']; me = body.data
    if 'piece' not in me.attributes:
        body = next(o for o in bpy.data.objects if o.type == 'MESH' and 'piece' in o.data.attributes); me = body.data
    pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
    gb, gn = body.vertex_groups['Bow'], body.vertex_groups['StringNock']
    fixed = 0
    for v in me.vertices:
        if pv[v.index] != 102:
            continue
        w = {body.vertex_groups[e.group].name: e.weight for e in v.groups}
        if w.get('StringNock', 0) < 0.005:
            gn.add([v.index], 0.005, 'REPLACE'); gb.add([v.index], 0.995, 'REPLACE'); fixed += 1
    print('PATCH', path, 'string vertices fixed', fixed)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(path))
