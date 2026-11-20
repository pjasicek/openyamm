"""Carry the texture layout (UVMap, HeadUV, face attribute 'head') from the textured master to a rebuilt rig with
(almost) the same rest geometry: a rig change that alters topology locally (e.g. which sword-hand finger faces are
subdivided) must not cost a new Meshy retexture. Per new face the head class comes from the nearest old face centroid;
per corner the UV is interpolated barycentrically on the nearest old face of the same class (BVH, rest pose).
Reports the largest corner distance to the old surface outside the hands. Args: -- <new blend> <old master> <out>"""
import bpy, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
new_b, old_b, out = sys.argv[sys.argv.index('--') + 1:]
with bpy.data.libraries.load(os.path.abspath(old_b)) as (df, dt):
    dt.meshes = ['Body']
old = dt.meshes[0]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(new_b))
body = bpy.data.objects['Body']; me = body.data
with bpy.data.libraries.load(os.path.abspath(old_b)) as (df, dt):
    dt.meshes = ['Body']
old = dt.meshes[0]
ohd = np.zeros(len(old.polygons), np.int32); old.attributes['head'].data.foreach_get('value', ohd)
oco = [v.co.copy() for v in old.vertices]
trees, tri_of = {}, {}
for cls in (0, 1, 'all'):
    tris, owner = [], []
    for p in old.polygons:
        if cls != 'all' and ohd[p.index] != cls:
            continue
        vs = list(p.vertices); ls = list(p.loop_indices)
        for k in range(1, len(vs) - 1):
            tris.append((vs[0], vs[k], vs[k + 1])); owner.append((ls[0], ls[k], ls[k + 1]))
    trees[cls] = BVHTree.FromPolygons(oco, tris); tri_of[cls] = (tris, owner)
cen_tree = BVHTree.FromPolygons(oco, [tuple(p.vertices) for p in old.polygons])
hd = np.zeros(len(me.polygons), np.int32)
for p in me.polygons:
    _, _, fi, _ = cen_tree.find_nearest(p.center)
    hd[p.index] = ohd[fi]
a = me.attributes.get('head') or me.attributes.new('head', 'INT', 'FACE')
a.data.foreach_set('value', hd.tolist())
for name in ('UVMap', 'HeadUV'):
    if name not in me.uv_layers:
        me.uv_layers.new(name=name)
worst = 0.0
for name in ('UVMap', 'HeadUV'):
    ouv = old.uv_layers[name].data; nuv = me.uv_layers[name].data
    for p in me.polygons:
        cls = int(hd[p.index])
        if name == 'HeadUV' and cls != 1:
            continue
        if name == 'UVMap':
            cls = 'all'                         # the master keeps Meshy's body-atlas UVs on the head faces too
        tris, owner = tri_of[cls]
        # one old triangle per new face (at its centroid): corners mapped independently landed on different UV islands
        # across seams and made giant UV triangles
        loc0, _, ti, d = trees[cls].find_nearest(p.center)
        t = tris[ti]; o = owner[ti]
        uvs = [Vector((ouv[l].uv[0], ouv[l].uv[1], 0)) for l in o]
        for li, vi in zip(p.loop_indices, p.vertices):
            q = me.vertices[vi].co
            if abs(q.x) < 0.45:
                worst = max(worst, trees[cls].find_nearest(q)[3])
            uv = barycentric_transform(q, oco[t[0]], oco[t[1]], oco[t[2]], *uvs)
            nuv[li].uv = (min(max(uv.x, 0.0), 1.0), min(max(uv.y, 0.0), 1.0))
me.uv_layers.active = me.uv_layers['UVMap']
print('CARRYUV faces', len(me.polygons), 'old', len(old.polygons), 'head faces', int(hd.sum()),
      'max corner distance outside the hands mm', round(worst * 1000, 3))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
