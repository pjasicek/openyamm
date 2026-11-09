"""Retain our rig; match unchanged faces exactly and project Meshy's retriangulated tail sheets."""
from pathlib import Path
import bpy,json,numpy as np
from mathutils import Vector,kdtree,geometry
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/equipped_v1.blend'))
b=bpy.data.objects['Body'];me=b.data;before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(P/'meshy/body_texture_v1/model_urls_glb.glb'))
s=max((o for o in bpy.data.objects if o not in before and o.type=='MESH'),key=lambda o:len(o.data.polygons))
S=np.array([s.matrix_world@v.co for v in s.data.vertices]);T=np.array([b.matrix_world@v.co for v in me.vertices])
scale=np.ptp(T,axis=0).max()/np.ptp(S,axis=0).max();S=S*scale+(T.max(0)+T.min(0))/2-(S.max(0)+S.min(0))*scale/2
sv=[Vector(p)for p in S];faces=[tuple(p.vertices)for p in s.data.polygons];tree=kdtree.KDTree(len(faces))
for i,vs in enumerate(faces):tree.insert(Vector(S[list(vs)].mean(0)),i)
tree.balance();bvh=BVHTree.FromPolygons(sv,faces,all_triangles=True)
suv=s.data.uv_layers.active.data;tuv=me.uv_layers['UVMap'].data;report={'exact_faces':0,'retriangulated_tail_faces':[],'maximum_projection_error':0.}
for p in me.polygons:
    if me.attributes['head'].data[p.index].value:continue
    _,i,d=tree.find(Vector(T[list(p.vertices)].mean(0)))
    if d<.001:
        q=s.data.polygons[i]
        for li,vi in zip(p.loop_indices,p.vertices):
            k=int(np.argmin(np.linalg.norm(S[list(q.vertices)]-T[vi],axis=1)));tuv[li].uv=suv[q.loop_indices[k]].uv
        report['exact_faces']+=1
    else:
        assert min(T[list(p.vertices),1])>.85,'Unexpected topology change outside tail sheets'
        report['retriangulated_tail_faces'].append(p.index)
        # One source chart for the whole retriangulated face; nearest vertices can select opposite UV seams.
        _,_,fi,_=bvh.find_nearest(Vector(T[list(p.vertices)].mean(0)));q=s.data.polygons[fi]
        for li,vi in zip(p.loop_indices,p.vertices):
            pos,n,_,dist=bvh.find_nearest(Vector(T[vi]))
            report['maximum_projection_error']=max(report['maximum_projection_error'],dist)
            uv=[Vector((*suv[l].uv,0))for l in q.loop_indices]
            tuv[li].uv=geometry.barycentric_transform(Vector(T[vi]),*[sv[v]for v in q.vertices],*uv).xy
assert report['maximum_projection_error']<.002,report
for o in list(bpy.data.objects):
    if o not in before:bpy.data.objects.remove(o,do_unlink=True)
me.uv_layers.active=me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_uv_v1.blend'))
(P/'work/uv_transfer_report.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
