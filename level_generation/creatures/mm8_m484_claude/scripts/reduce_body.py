import bpy,bmesh,json
import numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilots.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
old=np.array([v.co[:] for v in b.data.vertices]);ng=[g.name for g in b.vertex_groups];protect=[]
for v in b.data.vertices:
 protect.append(sum(g.weight for g in v.groups if ng[g.group] in ['B_Head','B_Neck'] or 'Hand' in ng[g.group] or 'Finger' in ng[g.group])>.3)
g=b.vertex_groups.new(name='_protect_detail')
for i,p in enumerate(protect):
 if p:g.add([i],1,'REPLACE')
prior=sum(len(f.vertices)-2 for f in b.data.polygons)
for o in bpy.data.objects:o.select_set(o is b)
bpy.context.view_layer.objects.active=b
m=b.modifiers.new('Silhouette reduction','DECIMATE');m.ratio=.60;m.vertex_group=g.name;m.invert_vertex_group=True;m.vertex_group_factor=10;bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name)
bm=bmesh.new();bm.from_mesh(b.data);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.0006);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(b.data);bm.free();b.data.validate(verbose=True);b.vertex_groups.remove(b.vertex_groups['_protect_detail'])
for v in b.data.vertices:
 groups=sorted([(x.group,x.weight) for x in v.groups if x.weight>1e-6],key=lambda x:-x[1]);keep=groups[:4];total=sum(w for _,w in keep)
 for i,w in groups:b.vertex_groups[i].remove([v.index])
 for i,w in keep:b.vertex_groups[i].add([v.index],w/total,'REPLACE')
kd=KDTree(len(b.data.vertices))
for i,v in enumerate(b.data.vertices):kd.insert(v.co,i)
kd.balance();dist=[kd.find(v)[2] for v,p in zip(old,protect) if p];report={'before':prior,'after':len(b.data.polygons),'protected_vertex_max_nearest_distance_m':max(dist),'protected_p99_nearest_distance_m':float(np.percentile(dist,99))};print('REDUCE',report);(P/'review/reduction.json').write_text(json.dumps(report,indent=2));assert np.percentile(dist,99)<.003,report
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/pilots_reduced.blend'))
