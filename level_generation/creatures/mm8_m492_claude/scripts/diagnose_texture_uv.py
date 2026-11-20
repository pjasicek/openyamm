import bpy,json,itertools
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
 tree.balance();values=[];bad=[]
 for f in me.polygons:
  if f.material_index!=slot:continue
  options=[]
  for _,j,distance in tree.find_n(Vector(T[list(f.vertices)].mean(0)),12):
   sf=sm.polygons[j]
   for order in itertools.permutations(range(3)):
    error=float(np.linalg.norm(S[np.array(sf.vertices)[list(order)]]-T[list(f.vertices)],axis=1).max())
    uv_error=max((me.uv_layers.active.data[li].uv-sm.uv_layers.active.data[sf.loop_indices[k]].uv).length for li,k in zip(f.loop_indices,order))
    options.append((error,uv_error,j,order))
  error,uerr,j,order=min(options)
  values.append((error,uerr,f.area))
  if error>1e-5 or uerr>1e-4:bad.append({'face':f.index,'position_error':error,'uv_error':uerr,'area':f.area})
 v=np.array(values);report[label]={'target_faces':len(values),'returned_faces':len(sm.polygons),'position_quantiles':np.quantile(v[:,0],[0,.5,.9,.99,1]).tolist(),'uv_quantiles':np.quantile(v[:,1],[0,.5,.9,.99,1]).tolist(),'bad_area_fraction':sum(x['area'] for x in bad)/v[:,2].sum(),'bad':bad}
 print('UV_DIAG',label,{k:v for k,v in report[label].items() if k!='bad'},flush=True)
 for x in list(bpy.data.objects):
  if x not in before:bpy.data.objects.remove(x,do_unlink=True)
(P/'work/texture_uv_diagnostic.json').write_text(json.dumps(report,indent=2)+'\n')
