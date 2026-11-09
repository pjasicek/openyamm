from pathlib import Path
import runpy,sys,json,bpy,bmesh,numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_twisted.blend'))
body=bpy.data.objects['Body'];before=(len(body.data.vertices),len(body.data.polygons))
bm=bmesh.new();bm.from_mesh(body.data)
bmesh.ops.dissolve_degenerate(bm,dist=1e-6,edges=list(bm.edges))
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
bmesh.ops.triangulate(bm,faces=list(bm.faces))
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
co=np.array([tuple(v.co) for v in body.data.vertices]);rig=bpy.data.objects['Rig']
piece=np.array([x.value for x in body.data.attributes['piece'].data]);groups=list(body.vertex_groups)
w=np.zeros((len(co),len(groups)))
for v in body.data.vertices:
 for g in v.groups:w[v.index,g.group]=g.weight
hand=w[:,[g.index for g in groups if 'Hand' in g.name or 'Finger' in g.name]].sum(1)
band=np.zeros(len(co),bool)
for side in 'LR':
 for name,radius in (('UpperArm',.24),('Forearm',.10)):
  joint=np.array(rig.data.bones[f'B_{side}_{name}'].head_local)
  band|=np.linalg.norm(co-joint,axis=1)<radius
band&=(piece==0)&(hand<.05)
adj=[[] for _ in co]
for e in body.data.edges:
 i,j=e.vertices
 if piece[i]==piece[j]==0:adj[i].append(j);adj[j].append(i)
for _ in range(12):
 nw=w.copy()
 for i in np.where(band)[0]:
  if adj[i]:nw[i]=w[i]*.5+w[adj[i]].mean(0)*.5
 w=nw
for i in np.where(band)[0]:
 for g in groups:g.remove([int(i)])
 for gi in np.where(w[i]>1e-6)[0]:groups[gi].add([int(i)],float(w[i,gi]),'REPLACE')
max_drop=0;maximum=0
for v in body.data.vertices:
 weights=sorted([(g.group,g.weight) for g in v.groups if g.weight>1e-6],key=lambda x:-x[1])
 maximum=max(maximum,len(weights));max_drop=max(max_drop,sum(w for _,w in weights[8:]))
 keep=weights[:8];total=sum(w for _,w in keep);assert total>.9,(v.index,total)
 for g in body.vertex_groups:g.remove([v.index])
 for gi,w in keep:body.vertex_groups[gi].add([v.index],w/total,'REPLACE')
assert max_drop<.01,max_drop
edges=np.array([tuple(e.vertices) for e in body.data.edges]);co=np.array([tuple(v.co) for v in body.data.vertices])
assert np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1).min()>1e-7
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_final.blend'))
(P/'work/weighted_cleanup.json').write_text(json.dumps({'before':before,'after':[len(body.data.vertices),len(body.data.polygons)],'input_max_influences':maximum,'max_removed_weight':max_drop},indent=2)+'\n')
runpy.run_path(str(P/'scripts/inspect_animation.py'),run_name='__main__')
