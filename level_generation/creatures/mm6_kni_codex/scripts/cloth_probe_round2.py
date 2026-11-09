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


DETAILS={}
def inside(co, fixed=None):
    trees={k:BVHTree.FromPolygons([tuple(c) for c in co],[tuple(p.vertices) for p in sp if pv[p.vertices[0]]==k]) for k in STRIPS}
    side = {}
    for i in skin:
        part=fixed[i][2] if fixed is not None and i in fixed else 201 if rest[i,0]>0 else 202
        loc, nrm, fi, d = trees[part].find_nearest(Vector(co[i]), 0.05)
        if loc is not None:
            v = Vector(co[i]) - loc
            edges={}
            for poly in sp:
                if pv[poly.vertices[0]]==part:
                    for a,b in zip(poly.vertices,list(poly.vertices[1:])+[poly.vertices[0]]):
                        key=tuple(sorted((a,b)));edges[key]=edges.get(key,0)+1
            ds=[]
            for (a,b),count in edges.items():
                if count==1:
                    A=Vector(co[a]);B=Vector(co[b]);ab=B-A;t=max(0,min(1,(loc-A).dot(ab)/max(ab.length_squared,1e-16)));ds.append((loc-A-ab*t).length)
            DETAILS[i]={'vertex':int(i),'point':co[i].tolist(),'rest':rest[i].tolist(),'nearest':list(loc),'normal':list(nrm),'nearest_open_edge_m':min(ds,default=1.)}
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
                worst = (d, f, piece, dict(DETAILS[i]))
    print(f'SKIRTPOKE {an:9s} deepest thigh skin through a strip {worst[0] * 100:.1f} cm at frame {worst[1]} (strip {worst[2]})')

    REPORT[an]={'depth_m':worst[0],'frame':worst[1],'panel':worst[2],'detail':worst[3]if len(worst)>3 else None}
Path(__file__).resolve().parents[1].joinpath('work/g6_fauld.json').write_text(json.dumps(REPORT,indent=2))
