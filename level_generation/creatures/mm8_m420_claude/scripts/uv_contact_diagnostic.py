import bpy,numpy as np,json
from pathlib import Path
from mathutils import Vector,kdtree
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_motion.blend'));body=bpy.data.objects['Body'];T=np.array([(body.matrix_world@v.co)[:] for v in body.data.vertices]);before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(P/'meshy/body_retexture_v1/model_urls_glb.glb'));src=max((o for o in set(bpy.data.objects)-before if o.type=='MESH'),key=lambda o:len(o.data.polygons));S=np.array([(src.matrix_world@v.co)[:] for v in src.data.vertices]);scale=np.ptp(T,axis=0).max()/np.ptp(S,axis=0).max();S=S*scale+(T.max(0)+T.min(0)-(S.max(0)+S.min(0))*scale)*.5
tr=kdtree.KDTree(len(S))
for i,x in enumerate(S):tr.insert(Vector(x),i)
tr.balance();dist=[tr.find(Vector(x))[2] for x in T]
print('UV_DIAG',json.dumps({'source_faces':len(src.data.polygons),'target_faces':len(body.data.polygons),'source_vertices':len(S),'target_vertices':len(T),'scale':float(scale),'bounds_source':np.ptp(S,axis=0).tolist(),'bounds_target':np.ptp(T,axis=0).tolist(),'nearest_vertex_mm':(np.percentile(dist,[0,50,95,99,100])*1000).tolist()}))
tree=kdtree.KDTree(len(src.data.polygons))
for f in src.data.polygons:tree.insert(Vector(S[list(f.vertices)].mean(0)),f.index)
tree.balance();errors=[]
for f in body.data.polygons:
 vs=T[list(f.vertices)];_,i,d=tree.find(Vector(vs.mean(0)));sf=S[list(src.data.polygons[i].vertices)];error=np.min(np.linalg.norm(vs[:,None]-sf[None,:],axis=2),axis=1).max();errors.append((error,f.index,i,d))
print('UV_WORST',sorted(errors,reverse=True)[:12])
bpy.ops.wm.open_mainfile(filepath=str(P/'work/grounded.blend'));body=bpy.data.objects['Body'];staff=bpy.data.objects['StaffMesh'];rig=bpy.data.objects['Rig'];parts=[a.value for a in body.data.attributes['piece'].data]
faces=[list(f.vertices) for f in body.data.polygons if parts[f.vertices[0]] not in [5,11,14]];sfaces=[list(f.vertices) for f in staff.data.polygons]
for name,frame in [('Walking',19),('Death',27)]:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(frame);cs=[]
 for o in [body,staff]:
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();cs.append(np.array([(o.matrix_world@v.co)[:] for v in m.vertices]));ev.to_mesh_clear()
 hits=BVHTree.FromPolygons(cs[0].tolist(),faces).overlap(BVHTree.FromPolygons(cs[1].tolist(),sfaces));ids=sorted(set(v for i,j in hits for v in faces[i]));r=np.array([body.data.vertices[i].co[:] for i in ids]);z=cs[0][ids]
 print('CONTACT_DIAG',name,frame,'vertices',len(ids),'rest',r.min(0).tolist(),r.max(0).tolist(),'posed',z.min(0).tolist(),z.max(0).tolist())
