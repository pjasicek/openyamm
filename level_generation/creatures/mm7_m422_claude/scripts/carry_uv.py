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
SAME = (len(old.polygons) == len(me.polygons) and len(old.loops) == len(me.loops) and len(old.vertices) == len(me.vertices)
        and max((a.co - b.co).length for a, b in zip(old.vertices, me.vertices)) < 1e-6)
if SAME:                                            # the same mesh (the rig was not rebuilt): copy the layout exactly
    for name in ('UVMap', 'HeadUV'):
        ouv = old.uv_layers[name].data; nuv = me.uv_layers[name].data
        for i in range(len(me.loops)):
            nuv[i].uv = ouv[i].uv
    hd = ohd.copy(); me.attributes['head'].data.foreach_set('value', hd.tolist())
    print('CARRYUV identical mesh: layout copied loop by loop')
# m422 user review 1: after a reduction that differs from the textured master's (armpit protection), extrapolating a
# new face's corners from one small old triangle reached into other islands and gutters (specks all over the coat).
# Each new face now picks the UV ISLAND of the old triangle nearest its centroid, and every corner takes the UV of its
# nearest point on that island (barycentric inside the island's triangle, no extrapolation).
for name in (() if SAME else ('UVMap', 'HeadUV')):
    ouv = old.uv_layers[name].data; nuv = me.uv_layers[name].data
    for cls in ((1,) if name == 'HeadUV' else ('all',)):
        tris, owner = tri_of[cls]
        # islands of the old triangles in this layer: triangles sharing an edge whose two UV ends coincide
        key = lambda l: (round(ouv[l].uv[0], 5), round(ouv[l].uv[1], 5))
        par = list(range(len(tris)))
        def find(x):
            while par[x] != x:
                par[x] = par[par[x]]; x = par[x]
            return x
        edge = {}
        for ti, (t, o) in enumerate(zip(tris, owner)):
            for a_, b_ in ((0, 1), (1, 2), (2, 0)):
                k = (min(t[a_], t[b_]), max(t[a_], t[b_]), tuple(sorted((key(o[a_]), key(o[b_])))))
                if k in edge:
                    ra, rb = find(ti), find(edge[k])
                    if ra != rb:
                        par[ra] = rb
                else:
                    edge[k] = ti
        isl = [find(i) for i in range(len(tris))]
        groups = {}
        for ti, g in enumerate(isl):
            groups.setdefault(g, []).append(ti)
        itree = {g: (BVHTree.FromPolygons(oco, [tris[t] for t in ts]), ts) for g, ts in groups.items()}
        for p in me.polygons:
            c_ = int(hd[p.index])
            if name == 'HeadUV' and c_ != 1:
                continue
            # the island: the most common island among the corners' and the centroid's nearest old triangles
            votes = [isl[trees[cls].find_nearest(x)[2]] for x in [p.center] + [me.vertices[v].co for v in p.vertices]]
            tree_i, ts = itree[max(set(votes), key=votes.count)]
            for li, vi in zip(p.loop_indices, p.vertices):
                q = me.vertices[vi].co
                loc, _, k, d = tree_i.find_nearest(q)
                if abs(q.x) < 0.45:
                    worst = max(worst, d)
                t = tris[ts[k]]; o = owner[ts[k]]
                uvs = [Vector((ouv[l].uv[0], ouv[l].uv[1], 0)) for l in o]
                uv = barycentric_transform(loc, oco[t[0]], oco[t[1]], oco[t[2]], *uvs)
                nuv[li].uv = (min(max(uv.x, 0.0), 1.0), min(max(uv.y, 0.0), 1.0))
me.uv_layers.active = me.uv_layers['UVMap']
print('CARRYUV faces', len(me.polygons), 'old', len(old.polygons), 'head faces', int(hd.sum()),
      'max corner distance outside the hands mm', round(worst * 1000, 3))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
