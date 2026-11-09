"""Make sleeve attachment rings follow the torso surface underneath them."""
import bpy,json,heapq,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_props.blend'))
body=bpy.data.objects['Body']; me=body.data; nv=len(me.vertices)
co=np.array([tuple(v.co) for v in me.vertices]);pv=np.zeros(nv,np.int32);me.attributes['piece'].data.foreach_get('value',pv)
me.calc_loop_triangles();faces=[tuple(t.vertices) for t in me.loop_triangles if pv[t.vertices[0]]==0]
tree=BVHTree.FromPolygons(co.tolist(),faces,all_triangles=True)
W=np.zeros((nv,len(body.vertex_groups)))
for v in me.vertices:
    for g in v.groups:W[v.index,g.group]=g.weight
nb=[[] for _ in range(nv)]
for e in me.edges:
    a,b=e.vertices;length=float(np.linalg.norm(co[a]-co[b]));nb[a].append((b,length));nb[b].append((a,length))
rings=json.loads((P/'work/sleeve_boundaries.json').read_text()); report={}
for p in (7,8):
    root=max(rings[str(p)],key=lambda r:r['centre'][2])['verts'];dist={i:0. for i in root};q=[(0.,i) for i in root];heapq.heapify(q)
    while q:
        d,i=heapq.heappop(q)
        if d>dist[i]+1e-8:continue
        for j,l in nb[i]:
            nd=d+l
            if pv[j]==p and nd<.035 and nd<dist.get(j,1):dist[j]=nd;heapq.heappush(q,(nd,j))
    moves=[]
    for i,d in dist.items():
        loc,nrm,face,_=tree.find_nearest(Vector(co[i]));a,b,c=faces[face]
        bary=barycentric_transform(loc,Vector(co[a]),Vector(co[b]),Vector(co[c]),Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
        bary=np.clip(np.array(bary),0,1);bary/=bary.sum();targetW=bary@W[[a,b,c]]
        f=float(np.clip(1-d/.035,0,1));f=f*f*(3-2*f)
        target=np.array(loc-nrm*.004);moves.append(float(np.linalg.norm(target-co[i])*f))
        me.vertices[i].co=Vector(co[i]*(1-f)+target*f)
        weights=W[i]*(1-f)+targetW*f;ix=np.argsort(weights)[-4:];total=weights[ix].sum();assert total>.90
        for g in list(me.vertices[i].groups):body.vertex_groups[g.group].remove([i])
        for j in ix:
            if weights[j]>1e-5:body.vertex_groups[int(j)].add([i],float(weights[j]/total),'REPLACE')
    report[p]={'vertices':len(dist),'largest_rest_move_cm':max(moves)*100}
me.update();(P/'work/sleeve_seal_report.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_gated_candidate.blend'))
print('SLEEVE attached roots',report)
