import bpy,json,sys,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];D=P/'review/round3/reduction';sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/lod3.blend'));ob=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc=bpy.context.scene;sc.frame_set(0);original=[v.co.copy()for v in ob.data.vertices];gn={g.index:g.name for g in ob.vertex_groups};piece=ob.data.attributes['piece'];eligible=[v.index for v in ob.data.vertices if v.co.z>.04 and piece.data[v.index].value in [0,1]and sum(g.weight for g in v.groups if any(t in gn[g.group]for t in ['Hand','Finger','Foot','Toe','Head','Neck']))<.15]
common.workbench_clay(sc,False);sc.display.shading.show_cavity=False;sc.display.shading.show_shadows=False;sc.display.render_aa='32';sc.render.film_transparent=True;sc.render.image_settings.color_mode='RGBA';sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.render.resolution_x=sc.render.resolution_y=192;sc.render.resolution_percentage=100;camera=json.loads((D/'camera.json').read_text())['body'];center=Vector(camera['center']);scale=camera['body_diameter_m']*192/88;cameras=[];targets=[]
for o in bpy.data.objects:
 if o.type=='MESH':o.hide_render=o.name not in ['Body','BowAsset','BowString']
for i in range(8):
 d=Vector((math.sin(i*math.pi/4),-math.cos(i*math.pi/4),.05)).normalized();cam=common.ortho_camera('FitCamera',center+d*6,(0,0,0),scale);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');cameras.append(cam);im=bpy.data.images.load(str(D/f'assembled_l3_Standing_high_{i}.png'),check_existing=False);v=np.zeros(192*192*4,np.float32);im.pixels.foreach_get(v);targets.append(v.reshape(-1,4)[:,3]>=.5);bpy.data.images.remove(im)
def score():
 total=inter=0
 for cam,target in zip(cameras,targets):
  sc.camera=cam;sc.render.filepath=str(P/'work/round3/fit_frame.png');bpy.ops.render.render(write_still=True);im=bpy.data.images.load(sc.render.filepath,check_existing=False);v=np.zeros(192*192*4,np.float32);im.pixels.foreach_get(v);mask=v.reshape(-1,4)[:,3]>=.5;bpy.data.images.remove(im);total+=int((mask|target).sum());inter+=int((mask&target).sum())
 return inter/total
best=score();history=[];print('EXACT_START',best,flush=True)
for radius in [.004,.002,.001]:
 for vi in eligible:
  v=ob.data.vertices[vi];start=v.co.copy();pick=None;local=best
  for axis in range(3):
   for sign in [-1,1]:
    v.co=start;v.co[axis]+=sign*radius
    if (v.co-original[vi]).length>.009:continue
    ob.data.update();value=score()
    if value>local+1e-8:local=value;pick=v.co.copy()
  v.co=start if pick is None else pick;ob.data.update()
  if pick is not None:best=local;history.append({'vertex':vi,'radius_m':radius,'iou':best});print('EXACT_ACCEPT',history[-1],flush=True)
  if best>=.971:break
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round3/lod3_exact.blend'));(D/'exact_fit.json').write_text(json.dumps({'initial_iou':.9644511202903993,'final_iou':best,'history':history,'max_displacement_m':max((v.co-original[v.index]).length for v in ob.data.vertices),'triangles':sum(len(f.vertices)-2 for f in ob.data.polygons)},indent=2))
 if best>=.971:break
