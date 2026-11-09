"""Refine the capped LOD3 silhouette with the actual Workbench rasterizer at its switch size."""
import bpy,json,sys,math,numpy as np,time
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];D=P/'review/round2/reduction';W=P/'work/round2';sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from round2_reduce import render
import common
bpy.ops.wm.open_mainfile(filepath=str(W/'body_l3_fitted.blend'));ob=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];original=np.array([v.co[:]for v in ob.data.vertices]);render(ob,rig,'body',3,'body_l3_exact_start',P/'work/round2/metric_tiers/baked/arc1_a')
sc=bpy.context.scene;camdata=json.loads((D/'camera.json').read_text())['body'];center=Vector(camdata['center']);scale=camdata['body_diameter_m']*192/88;cameras=[];targets=[]
for i in range(8):
 d=Vector((math.sin(i*math.pi/4),-math.cos(i*math.pi/4),.05)).normalized();cam=common.ortho_camera('FitCamera',center+d*6,(0,0,0),scale);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');cameras.append(cam)
 image=bpy.data.images.load(str(D/f'body_l3_arc1_a_high_{i}.png'),check_existing=False);a=np.zeros(192*192*4,np.float32);image.pixels.foreach_get(a);targets.append(a.reshape(-1,4)[:,3]>=.5);bpy.data.images.remove(image)
def score():
 union=intersection=0
 for cam,target in zip(cameras,targets):
  sc.camera=cam;sc.render.filepath=str(W/'distance_fit_frame.png');bpy.ops.render.render(write_still=True)
  image=bpy.data.images.load(sc.render.filepath,check_existing=False);a=np.zeros(192*192*4,np.float32);image.pixels.foreach_get(a);mask=a.reshape(-1,4)[:,3]>=.5;bpy.data.images.remove(image)
  union+=int((mask|target).sum());intersection+=int((mask&target).sum())
 return intersection/union
best=score();history=[];used=set(i for f in ob.data.polygons for i in f.vertices);print('EXACT_INITIAL',best,flush=True)
for radius in [.004,.002,.001]:
 changed=0
 for vi,v in enumerate(ob.data.vertices):
  if vi not in used:continue
  before=v.co.copy();pick=None;local=best
  for axis in range(3):
   if axis==2 and original[vi,2]<.03:continue
   for sign in [-1,1]:
    v.co=before;v.co[axis]+=sign*radius;ob.data.update();value=score()
    if value>local+1e-8:local=value;pick=v.co.copy()
  v.co=before if pick is None else pick;ob.data.update()
  if pick is not None:best=local;changed+=1
  if vi%40==0:print('EXACT_PROGRESS',radius,vi,best,flush=True)
  if best>=.978:break
 history.append({'radius_m':radius,'pooled_iou':best,'vertices_changed':changed});print('EXACT_FIT',history[-1],flush=True);bpy.ops.wm.save_as_mainfile(filepath=str(W/'body_l3_exact.blend'));(D/'distance_exact_fit.json').write_text(json.dumps({'history':history,'triangles':603,'max_extra_vertex_displacement_m':max((v.co-Vector(original[v.index])).length for v in ob.data.vertices)},indent=2))
 if best>=.978:break
render(ob,rig,'body',3,'body_l3_exact',P/'work/round2/metric_tiers/baked/arc1_a')
