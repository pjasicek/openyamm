"""Rubble error only where the rubble shows: Death frames 12-18 and Dead 0, both directions, per candidate.
blender -b -P rubble_err.py -- <ladder.blend>"""
import sys, bpy, bmesh, numpy as np
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
def ev(o):
    b = bmesh.new(); b.from_object(o, bpy.context.evaluated_depsgraph_get()); b.transform(o.matrix_world); return b
for c in sorted([o for o in bpy.data.objects if o.name.startswith('Cand_')], key=lambda o: -int(o.name[5:])):
    e = []; worst = (0, '')
    for clip, frames in (('Death', range(12, 19)), ('Dead', [0])):
        rig.animation_data.action = bpy.data.actions[clip]
        for f in frames:
            sc.frame_set(f); bs, bc = ev(src), ev(c); ts, tc = BVHTree.FromBMesh(bs), BVHTree.FromBMesh(bc)
            d = [tc.find_nearest(v.co)[3] for v in bs.verts] + [ts.find_nearest(v.co)[3] for v in bc.verts]
            if max(d) > worst[0]: worst = (max(d), f'{clip}:{f}')
            e += d; bs.free(); bc.free()
    e = np.array(e) * 1000
    print('RUBBLE', c.name, len(c.data.polygons), 'p99 %.2f max %.2f at %s' % (np.percentile(e, 99), worst[0] * 1000, worst[1]))
