"""Fit the sparse rest contour against the eight LOD0 switch-size silhouettes, keeping topology and UVs."""
import bpy,math,json,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1]
def fit(body,staff,rig):
 import common
 scene=bpy.context.scene;common.workbench_clay(scene,textured=False);scene.render.film_transparent=True;scene.render.resolution_x=scene.render.resolution_y=97;scene.render.resolution_percentage=100
 rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=bpy.data.actions['Standing'].slots[0];scene.frame_set(0)
 with bpy.data.libraries.load(str(p/'work/round3_lod0.blend'),link=False) as (a,b):b.objects=['Body','Staff']
 refs=list(b.objects)
 for ob in refs:
  bpy.context.collection.objects.link(ob)
  for mod in ob.modifiers:
   if mod.type=='ARMATURE':mod.object=rig
 bpy.context.view_layer.update();lo,hi=common.world_bounds(refs);centre=(lo+hi)/2;h=hi.z-lo.z
 cam=common.ortho_camera('ContourCamera',(0,-6,centre.z),(math.pi/2,0,0),h*1.1);scene.camera=cam
 path=p/'work/contour_fit.png'
 def render(objects):
  for ob in bpy.data.objects:
   if ob.type=='MESH':ob.hide_render=ob not in objects
  arrays=[]
  for i in range(8):
   a=i*math.pi/4;cam.location=(centre.x+6*math.sin(a),centre.y-6*math.cos(a),centre.z);cam.rotation_euler=(math.pi/2,0,a);scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
   im=bpy.data.images.load(str(path),check_existing=False);arrays.append(np.array(im.pixels[:],np.float32).reshape(97,97,4)[:,:,3]);bpy.data.images.remove(im)
  return np.array(arrays)
 target=render(refs);mask=target>.5
 rest=np.array([v.co[:] for v in body.data.vertices]);parts=np.array([x.value for x in body.data.attributes['piece'].data]);basis=[]
 for ids in [[1],[2],[100],[101,102],[5,7,8,9,10]]:
  sel=np.isin(parts,ids);origin=rest[sel].mean(0)
  for axis in range(3):
   delta=np.zeros_like(rest);delta[sel,axis]=rest[sel,axis]-origin[axis];basis.append(delta)
 normals=np.array([v.normal[:] for v in body.data.vertices])
 for sel in [(parts==1)&(rest[:,0]<-.16),(parts==1)&(abs(rest[:,0])<=.16),(parts==1)&(rest[:,0]>.16),parts==2,parts==100,np.isin(parts,[101,102]),np.isin(parts,[5,7,8,9,10])]:
  delta=np.zeros_like(rest);delta[sel]=normals[sel]*.1;basis.append(delta)
 delta=np.zeros_like(rest);delta[parts==2,2]=.1;basis.append(delta)
 for ids in [[1],[2],[100],[101,102],[5,7,8,9,10]]:
  for axis in range(3):
   delta=np.zeros_like(rest);delta[np.isin(parts,ids),axis]=.1;basis.append(delta)
 basis=np.array(basis);params=np.zeros(len(basis));evaluations=0
 def evaluate(values):
  nonlocal evaluations
  delta=np.einsum('i,ijk->jk',values,basis);length=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,.010/np.maximum(length,1e-12))[:,None]
  body.data.vertices.foreach_set('co',(rest+delta).astype(np.float32).ravel());body.data.update();bpy.context.view_layer.update();a=render([body,staff]);m=a>.5;iou=float((m&mask).sum()/(m|mask).sum());loss=1-iou+.05*float(np.abs(a-target).sum()/target.sum());evaluations+=1;return loss,iou,delta
 best,iou,_=evaluate(params);initial=iou
 for step in [.03,.02,.01,.005,.01,.005]:
  for j in range(len(params)):
   winner=params.copy()
   for sign in [-1,1]:
    trial=params.copy();trial[j]+=sign*step;loss,value,_=evaluate(trial)
    if loss<best:best=loss;iou=value;winner=trial.copy()
   params=winner
  print('CONTOUR_FIT',step,iou,flush=True)
 _,iou,delta=evaluate(params)
 report={'initial_iou':initial,'final_iou':iou,'evaluations':evaluations,'parameters':params.tolist(),'max_rest_displacement_mm':float(np.linalg.norm(delta,axis=1).max()*1000),'topology_unchanged':True,'fingers_and_grip_unchanged':True}
 (p/'review/round3/reduction/lod3_contour_fit.json').write_text(json.dumps(report,indent=2))
 for ob in refs:bpy.data.objects.remove(ob,do_unlink=True)
 for ob in [body,staff]:ob.hide_render=False
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();print('CONTOUR_FINAL',report,flush=True)
