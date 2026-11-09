"""G6 for the skirt: thigh/hip skin (pieces 0-2, weighted to a thigh) that ends up in FRONT of a strip it sits behind
at rest, i.e. pokes through the strip. Per action and strip piece: the deepest skin point beyond the strip surface
(behind-the-face rule inverted: skin vertex on the outer side of the closest strip face within a 45 deg cone, while at
rest it was on the inner side). Args: -- <blend> action [...]"""
import bpy, sys, os, math, json
from pathlib import Path
REPORT={}
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
STRIPS = [44,200,201,202]
gi = {g.name: g.index for g in body.vertex_groups}
thw = np.array([sum(e.weight for e in v.groups if e.group in (gi['B_L_Thigh'], gi['B_R_Thigh'])) for v in me.vertices])
rest = np.array([tuple(v.co) for v in me.vertices])
skin = np.where((pv==6) & (thw > 0.3) & (rest[:, 2] > 0.78) & (rest[:, 2] < 0.95))[0]
sp = [p for p in me.polygons if pv[p.vertices[0]] in STRIPS]
# UV/normal splits are not physical boundaries. Only exposed panel edges are openings.
from collections import Counter
boundary = {}
keys = [tuple(np.round(v,6)) for v in rest]
for part in STRIPS:
    counts=Counter(); ends={}
    for poly in sp:
        if pv[poly.vertices[0]] != part: continue
        vs=list(poly.vertices)
        for i,j in zip(vs,vs[1:]+vs[:1]):
            key=tuple(sorted((keys[i],keys[j]))); counts[key]+=1; ends[key]=(i,j)
    boundary[part]=[ends[k] for k,n in counts.items() if n==1]
def on_boundary(point, co, part):
    pairs=np.asarray(boundary[part]); a=co[pairs[:,0]]; ab=co[pairs[:,1]]-a
    t=np.clip(np.einsum('ij,ij->i',point-a,ab)/np.maximum(np.einsum('ij,ij->i',ab,ab),1e-20),0,1)
    return np.min(np.linalg.norm(point-a-t[:,None]*ab,axis=1))<1e-5

assert all(boundary[k] for k in [201,202])


def inside(co, fixed=None):
    trees={k:BVHTree.FromPolygons([tuple(c) for c in co],[tuple(p.vertices) for p in sp if pv[p.vertices[0]]==k]) for k in STRIPS}
    side = {}
    for i in skin:
        part=fixed[i][2] if fixed is not None and i in fixed else 201 if rest[i,0]>0 else 202
        loc, nrm, fi, d = trees[part].find_nearest(Vector(co[i]), 0.05)
        if loc is not None and not on_boundary(np.array(loc), co, part):
            v = Vector(co[i]) - loc
            side[i] = (v.dot(nrm) > 0 and v.length > 1e-6 and v.normalized().angle(nrm) < math.radians(45), d,
                       part)
    return side


r0 = inside(rest)
for an in a[1:]:
    act = bpy.data.actions[an]; rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    worst = (0.0, None, None)
    for f in np.arange(float(act.frame_range[0]), float(act.frame_range[1])+.001, bpy.context.scene.render.fps/48):
        bpy.context.scene.frame_set(int(f),subframe=float(f%1))
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        P = np.array([tuple(v.co) for v in m.vertices]); ev.to_mesh_clear()
        for i, (out, d, piece) in inside(P,r0).items():
            if out and i in r0 and not r0[i][0] and d > worst[0]:
                worst = (d, f, piece)
    print(f'SKIRTPOKE {an:9s} deepest thigh skin through a strip {worst[0] * 100:.1f} cm at frame {worst[1]} (strip {worst[2]})')

    REPORT[an]={'depth_m':worst[0],'frame':worst[1],'panel':worst[2]}
Path(__file__).resolve().parents[1].joinpath('work/g6_fauld.json').write_text(json.dumps(REPORT,indent=2))
