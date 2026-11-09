import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/export_reimport.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];axe=bpy.data.objects['Axe'];scene=bpy.context.scene
me=body.data;pv=np.array([a.value for a in me.attributes['piece'].data]);rest=np.array([tuple(v.co)for v in me.vertices]);faces=[tuple(f.vertices)for f in me.polygons];names={g.index:g.name for g in body.vertex_groups}
def points(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();ps=[ob.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear();return ps
def polys(parts):return [f for f in faces if int(pv[f[0]])in parts]
def depth(ps,fl,samples):
 tree=BVHTree.FromPolygons(ps,fl);worst=(0.,None,None);trees={}
 def inside(point,piece):
  if piece not in trees:trees[piece]=BVHTree.FromPolygons(ps,[f for f in fl if pv[f[0]]==piece])
  t=trees[piece];votes=0
  for direction in [Vector((1,.117,.071)).normalized(),Vector((.093,1,.061)).normalized(),Vector((.081,.151,1)).normalized()]:
   origin=point.copy();hits=0
   for _ in range(20):
    loc,n,fi,d=t.ray_cast(origin,direction,3)
    if loc is None:break
    hits+=1;origin=loc+direction*.00001
   votes+=hits%2
  return votes>=2
 for i,p in samples:
  loc,n,fi,d=tree.find_nearest(p,.08)
  if loc is not None and d>1e-7 and (p-loc).dot(n)<-.7071*d and d>worst[0] and inside(p,int(pv[fl[fi][0]])):worst=(float(d),int(i),int(pv[fl[fi][0]]))
 return worst
armsets={s:[i for i in range(len(rest))if pv[i]in pieces]for s,pieces in [('R',[3]),('L',[4])]}
bodyfaces={s:polys([0,1,2,5,6,7,8,11,4 if s=='R'else 3])for s in 'RL'}
axefaces=polys([0,1,2,4,5,6,7,8,9,10,11]);collar_top=max(rest[i,2]for i in range(len(rest))if pv[i]in [1,8]);headids=[i for i in range(len(rest))if pv[i]==0 and rest[i,2]>collar_top+.002 and rest[i,1]>-.13];headfaces=[f for f in polys([1,8,9,10])if all(abs(rest[i,0])>.14 for i in f)];skirtfaces=polys([2]);pantsids=[i for i in range(len(rest))if pv[i]==5 and rest[i,2]>.45]
with bpy.data.libraries.load(str(P/'work/textured_master.blend'),link=False)as(src,dst):dst.objects=['Rig']
ref=dst.objects[0];canonical=(ref.data.bones['B_R_Hand'].matrix_local@Matrix(json.loads((P/'work/axe_attachment.json').read_text())['hand_local_matrix'])).inverted();bladeids={v.index for v in axe.data.vertices if (canonical@(axe.matrix_world@v.co)).x>.22};assert len(bladeids)>100;print('ACTUAL BLADE VERTICES',len(bladeids));bpy.data.objects.remove(ref,do_unlink=True)
roles=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'];report={}
for name in roles:
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];worst={k:[0,None,None,None]for k in ['R_arm','L_arm','axe','blade_full_body','head']};post=[];stretch=[]
 for f in np.arange(0,float(a.frame_range[1])+1e-6,scene.render.fps/48):
  scene.frame_set(int(f),subframe=float(f-int(f)));ps=points(body)
  for key,fl,ss in [(s+'_arm',bodyfaces[s],[(i,ps[i])for i in armsets[s]])for s in'RL']+[('blade_full_body',faces,[(i,p)for i,p in enumerate(points(axe))if i in bladeids]),('axe',axefaces,list(enumerate(points(axe)))),('head',headfaces,[(i,ps[i])for i in headids])]:
   d,i,p=depth(ps,fl,ss)
   if d>worst[key][0]:worst[key]=[d,float(f),i,p]
  H=rig.pose.bones['B_Pelvis'].head;v=rig.pose.bones['B_Neck'].head-rig.pose.bones['B_Spine'].head;post.append([float(H.z),math.degrees(math.atan2(-v.y,v.z))])
 report[name]={'head_exposed_rest_plane_m':float(collar_top+.002),'head_test_vertices':len(headids),'contacts':worst,'posture':{'pelvis_z_min':min(p[0]for p in post),'pelvis_z_max':max(p[0]for p in post),'lean_deg_min':min(p[1]for p in post),'lean_deg_max':max(p[1]for p in post)}};print('CONTACT',name,report[name],flush=True)
(P/'review/g6_exported.json').write_text(json.dumps(report,indent=2))
