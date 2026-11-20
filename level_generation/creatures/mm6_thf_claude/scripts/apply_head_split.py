"""Restore the head split of the head retexture (texturing/thf_head_upload.glb) on a master (in place): faces whose
centroid matches an uploaded face get the face attribute `head` and the uploaded UVs. Re-deriving the split from the
head weights (claude_shared/head_texture_split.py) changes it whenever weights near the hood change (2,429 -> 2,435
faces after the cloak attach change), and the head texture was painted on the uploaded layout.
Run: blender --background <master.blend> --python apply_head_split.py"""
import bpy, os, sys
import numpy as np
from mathutils.kdtree import KDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
master = bpy.data.objects['Thief']; rig = bpy.data.objects['Thief_Rig']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(common.PROJECT, 'texturing', 'thf_head_upload.glb'))
up = next(o for o in set(bpy.data.objects) - before if o.type == 'MESH')
um = up.data; uuv = um.uv_layers.active.data
cent = [up.matrix_world @ p.center for p in um.polygons]
kd = KDTree(len(cent))
for i, c in enumerate(cent):
    kd.insert(c, i)
kd.balance()
me = master.data
if 'head' in me.attributes:
    me.attributes.remove(me.attributes['head'])
flag = np.zeros(len(me.polygons), np.int32)
uv = me.uv_layers.active.data
miss = 0
for p in me.polygons:
    c, i, d = kd.find(master.matrix_world @ p.center)
    if d > 1e-4:
        continue
    q = um.polygons[i]
    upos = [(up.matrix_world @ um.vertices[um.loops[li].vertex_index].co, uuv[li].uv.copy()) for li in q.loop_indices]
    for li in p.loop_indices:
        w = master.matrix_world @ me.vertices[me.loops[li].vertex_index].co
        best = min(upos, key=lambda x: (x[0] - w).length)
        if (best[0] - w).length > 1e-4:
            miss += 1
        uv[li].uv = best[1]
    flag[p.index] = 1
me.attributes.new('head', 'INT', 'FACE').data.foreach_set('value', flag)
for o in set(bpy.data.objects) - before:
    bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.wm.save_mainfile()
print('HEAD_RESTORE faces', int(flag.sum()), 'of', len(um.polygons), 'uploaded; loop misses', miss)
