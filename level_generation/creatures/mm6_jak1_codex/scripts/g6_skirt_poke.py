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
STRIPS = [1]
gi = {g.name: g.index for g in body.vertex_groups}
thw = np.array([sum(e.weight for e in v.groups if e.group in (gi['B_L_Thigh'], gi['B_R_Thigh'])) for v in me.vertices])
rest = np.array([tuple(v.co) for v in me.vertices])
skin = np.where((pv==0) & (thw > 0.3) & (rest[:, 2] > 0.67) & (rest[:, 2] < 1.04))[0]
sp = [p for p in me.polygons if pv[p.vertices[0]] in STRIPS and p.normal.dot(Vector((p.center.x,p.center.y,0)).normalized()) > .25]
assert len(sp)>100, len(sp)  # This skirt has inward-facing inner walls as well as its visible outer shell.


def covered(tree,point,ray):
    hit,normal,_,_=tree.ray_cast(point+ray*.0001,ray,.6)
    return hit is not None and normal.dot(ray)>0
# Two overlapping outward-facing panels: an inner nearest face is not an exposed poke.
test_tree=BVHTree.FromPolygons([(x,y,z)for x in [0,.02]for y,z in [(-1,-1),(1,-1),(1,1),(-1,1)]],[(0,1,2,3),(4,5,6,7)])
assert covered(test_tree,Vector((.01,0,0)),Vector((1,0,0)))
assert not covered(test_tree,Vector((.03,0,0)),Vector((1,0,0)))

def inside(co, fixed=None):
    trees={k:BVHTree.FromPolygons([tuple(c) for c in co],[tuple(p.vertices) for p in sp if pv[p.vertices[0]]==k]) for k in STRIPS}
    side = {}
    for i in skin:
        part=fixed[i][2] if fixed is not None and i in fixed else 1
        loc, nrm, fi, d = trees[part].find_nearest(Vector(co[i]), 0.05)
        if loc is not None:
            v = Vector(co[i]) - loc
            out=v.dot(nrm)>0 and v.length>1e-6 and v.normalized().angle(nrm)<math.radians(45)
            # An overlapping wrap panel can be the nearest face while another panel still covers the skin.
            if out:
                if covered(trees[part],Vector(co[i]),v.normalized()):out=False
            side[i] = (out, d,
                       part,fi,tuple(loc))
    return side


r0 = inside(rest)
for an in a[1:]:
    act = bpy.data.actions[an]; rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    worst = (0.0, None, None,None,None,None,None)
    for f in np.arange(act.frame_range[0],act.frame_range[1]+.001,bpy.context.scene.render.fps/48):
        bpy.context.scene.frame_set(int(f),subframe=float(f-int(f)))
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        P = np.array([tuple(v.co) for v in m.vertices]); ev.to_mesh_clear()
        for i, (out, d, piece, face, loc) in inside(P,r0).items():
            if out and i in r0 and not r0[i][0] and d > worst[0]:
                worst = (float(d),float(f),piece,int(i),int(face),list(P[i]),list(loc))
    print(f'SKIRTPOKE {an:9s} deepest thigh skin through a strip {worst[0] * 100:.1f} cm at frame {worst[1]} (strip {worst[2]})')

    REPORT[an]={'depth_m':worst[0],'frame':worst[1],'panel':worst[2],'skin_vertex':worst[3],'outer_face':worst[4],'skin_point':worst[5],'cloth_point':worst[6]}
Path(__file__).resolve().parents[1].joinpath('work/g6_fauld.json').write_text(json.dumps(REPORT,indent=2))
