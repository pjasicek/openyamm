"""Billow the wing membrane (2026-10-30 rework): the Coons panels of build_wings_v2.py are nearly planar between the
bones, so a smooth-shaded membrane still lit like flat boards. Each membrane vertex (piece 3) moves along the sheet
normal by AMP x smoothstep(0, REACH, distance to the nearest rim vertex), so the edges on the bones, the trailing
scallops and the body line stay where they are. Both layers of the solidified shell move together: every vertex is
paired with its twin on the other layer (nearest vertex with an opposite normal) and the pair uses one direction, so
the thickness does not change. Only positions change: UVs and weights stay valid.
Args: <in blend> <out blend>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

AMP, REACH = 0.045, 0.35
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']
me = body.data
pc = np.zeros(len(me.vertices), np.int32)
me.attributes['piece'].data.foreach_get('value', pc)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.normal_update()
mem = [v for v in bm.verts if pc[v.index] == 3]
sharp = me.attributes.get('sharp_edge')
sh = np.zeros(len(me.edges), bool)
if sharp:
    sharp.data.foreach_get('value', sh)
bm.edges.ensure_lookup_table()
rim = [v for v in mem if any(sh[e.index] for e in v.link_edges)]
kr = KDTree(len(rim))
for k, v in enumerate(rim):
    kr.insert(v.co, k)
kr.balance()
km = KDTree(len(mem))
for k, v in enumerate(mem):
    km.insert(v.co, k)
km.balance()
ref = Vector((0.0, 1.0, 0.35)).normalized()
moved, worst_pair = 0, 0.0
disp = {}
for v in mem:
    if v in disp:
        continue
    twin = None
    for co, k, d in km.find_n(v.co, 6):
        w = mem[k]
        if w is not v and w.normal.dot(v.normal) < -0.5 and d < 0.03:
            twin = w
            break
    n = v.normal if (twin is None or v.normal.dot(ref) >= twin.normal.dot(ref)) else twin.normal
    _, _, dr = kr.find(v.co)
    t = min(max(dr / REACH, 0.0), 1.0)
    off = n * (AMP * t * t * (3 - 2 * t))
    disp[v] = off
    if twin is not None and twin not in disp:
        disp[twin] = off
        worst_pair = max(worst_pair, (v.co - twin.co).length)
for v, off in disp.items():
    if off.length > 1e-6:
        v.co += off
        moved += 1
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('BILLOW', moved, 'of', len(mem), 'membrane vertices moved; rim', len(rim), '; widest twin pair', round(worst_pair, 4))
