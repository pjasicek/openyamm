import bpy,bmesh,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_props.blend'))
body=bpy.data.objects['Body'];me=body.data
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table(); layer=bm.verts.layers.int['piece']
from mathutils.bvhtree import BVHTree
points=[v.co.copy() for v in bm.verts]; faces=[[v.index for v in f.verts] for f in bm.faces if f.verts[0][layer]==0]
tree=BVHTree.FromPolygons(points,faces)
result={}
for piece in (7,8):
    vs=[v for v in bm.verts if v[layer]==piece and v.is_boundary]
    remaining=set(vs); comps=[]
    while remaining:
        todo=[remaining.pop()];ids=[]
        while todo:
            v=todo.pop();ids.append(v)
            for e in v.link_edges:
                u=e.other_vert(v)
                if u in remaining:remaining.remove(u);todo.append(u)
        p=np.array([tuple(v.co) for v in ids]); ds=[tree.find_nearest(v.co)[3] for v in ids]
        comps.append({'verts':[v.index for v in ids],'centre':p.mean(0).tolist(),'lo':p.min(0).tolist(),'hi':p.max(0).tolist(),'distance_torso_cm':[min(ds)*100,max(ds)*100]})
    result[piece]=comps
(P/'work/sleeve_boundaries.json').write_text(json.dumps(result,indent=2)+'\n');print('SLEEVE',result)
