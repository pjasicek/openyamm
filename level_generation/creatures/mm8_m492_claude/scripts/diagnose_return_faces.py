import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_uv.blend'));o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data_clear()
for pb in rig.pose.bones:pb.matrix_basis.identity()
# Place the release inside the open jaws so adult attacks stay in the native launch envelope.
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
socket=rig.data.edit_bones['Socket_Mouth'];socket.head.y=-.372;socket.tail.y=-.392
bpy.ops.object.mode_set(mode='OBJECT')
me=o.data;T=np.array([v.co[:] for v in me.vertices]);report={}
for slot,label in [(0,'body'),(1,'head'),(2,'wings')]:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'meshy'/f'{label}_retexture_v1/model_urls_glb.glb'));src=max((x for x in bpy.data.objects if x not in before and x.type=='MESH'),key=lambda x:len(x.data.polygons));sm=src.data;S=np.array([tuple(src.matrix_world@v.co) for v in sm.vertices]);ids=sorted({i for f in me.polygons if f.material_index==slot for i in f.vertices});sub=T[ids];scale=np.ptp(sub,axis=0).max()/np.ptp(S,axis=0).max();S=S*scale+(sub.max(0)+sub.min(0))/2-(S.max(0)+S.min(0))/2*scale
 tree=kdtree.KDTree(len(sm.polygons))
 for f in sm.polygons:tree.insert(Vector(S[list(f.vertices)].mean(0)),f.index)
 tree.balance();worst=0;uvmax=0;count=0;oral_count=0;repairs=[]
 orders=np.array([[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]])
 for f in me.polygons:
  if f.material_index!=slot:continue
  if me.attributes['oral'].data[f.index].value:
   oral_count+=1;continue # Oral caps receive a separate dark material, never the service paint.
  hits=tree.find_n(Vector(T[list(f.vertices)].mean(0)),12)
  faces=[sm.polygons[j] for _,j,_ in hits]
  verts=np.array([sf.vertices[:] for sf in faces]);old=np.array([me.uv_layers.active.data[i].uv[:] for i in f.loop_indices])
  coordinates=S[verts[:,orders]];errors=np.linalg.norm(coordinates-T[list(f.vertices)],axis=-1).max(-1)
  minimum=errors.min();candidates=np.argwhere(errors<minimum+1e-6);best=None
  for j,k in candidates:
   sf=faces[j];new=np.array([sm.uv_layers.active.data[sf.loop_indices[n]].uv[:] for n in orders[k]])
   change=float(np.linalg.norm(new-old,axis=1).max());candidate=(change,float(errors[j,k]),new)
   if best is None or candidate[0]<best[0]:best=candidate
  change,error,new=best;worst=max(worst,error);uvmax=max(uvmax,change);count+=1
  if error>1e-5:print('SURFACE',label,f.index,'error',error,'area',f.area,'part',[me.attributes['part'].data[v].value for v in f.vertices],'uv_delta',change,'coordinates',T[list(f.vertices)].tolist(),flush=True)
  if change>1e-5:repairs.append({'face':f.index,'target_uv':old.tolist(),'source_uv':new.tolist()})
 # Keep the frozen non-overlapping rig UVs. Transfer paint for omitted coincident faces only.
 report[label]={'faces_verified':count,'oral_caps_painted_separately':oral_count,'corner_error':worst,'uv_change':uvmax,'repairs':repairs}
 print('UV_PARITY',label,{k:v for k,v in report[label].items() if k!='repairs'},'paint_transfers',len(repairs),flush=True)
 for x in list(bpy.data.objects):
  if x not in before:bpy.data.objects.remove(x,do_unlink=True)
