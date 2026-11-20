"""Fit panel-bone rotations against the actual animated skin; preserve uploaded geometry and UVs."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));from collision import penetration
bpy.ops.wm.open_mainfile(filepath=str(P/'work/equipped.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;co=np.array([tuple(v.co)for v in body.data.vertices]);pv=np.array([d.value for d in body.data.attributes['piece'].data]);body.data.calc_loop_triangles();tri=np.array([list(t.vertices)for t in body.data.loop_triangles]);skintri=tri[np.all(pv[tri]==0,axis=1)];bary=np.array([[1,0,0],[0,1,0],[0,0,1],[.5,.5,0],[.5,0,.5],[0,.5,.5],[1/3]*3]);report={}
for act in bpy.data.actions:
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];changes=[];last={}
 for f in range(int(act.frame_range[1])+1):
  sc.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=np.array([tuple(v.co)for v in me.vertices]);ev.to_mesh_clear();tree=BVHTree.FromPolygons([Vector(p)for p in v],skintri.tolist(),all_triangles=True)
  for part,name in [(1,'ClothFront'),(10,'ClothBack')]:
   ids=np.where(pv==part)[0];tt=tri[np.all(pv[tri]==part,axis=1)&(np.max(co[tri,2],axis=1)<.93)];rest=rig.data.bones[name].matrix_local;pb=rig.pose.bones[name];pel=rig.pose.bones['B_Pelvis'].matrix;pr=rig.data.bones['B_Pelvis'].matrix_local;parent=pel@pr.inverted();base=parent@rest;w=np.clip((.98-co[:,2])/.075,0,1)[:,None];baseline=pb.rotation_quaternion.to_euler('XYZ').x
   a=np.c_[co,np.ones(len(co))]@np.array(parent).T
   def evaluate(angle):
    M=base@Matrix.Rotation(angle,4,'X')@rest.inverted();b=np.c_[co,np.ones(len(co))]@np.array(M).T;posed=a[:,:3]*(1-w)+b[:,:3]*w;pts=np.einsum('kj,tjd->tkd',bary,posed[tt]).reshape(-1,3);d,_=penetration(tree,pts);floor=float(posed[ids,2].min());score=1e9*max(0,d-.0002)**2+1e9*max(0,-floor-.0005)**2+.0001*math.degrees(angle-baseline)**2+.0002*math.degrees(angle-last.get(name,baseline))**2;return score,d,floor
   r=evaluate(baseline);best=(r[0],baseline,r[1],r[2])
   if r[1]>.0004 or r[2]<-.0005:
    for deg in np.arange(-105,106,3):
     angle=baseline+math.radians(float(deg));q=evaluate(angle)
     if q[0]<best[0]:best=(q[0],angle,q[1],q[2])
    for deg in np.arange(-2.5,2.51,.5):
     angle=best[1]+math.radians(float(deg));q=evaluate(angle)
     if q[0]<best[0]:best=(q[0],angle,q[1],q[2])
   last[name]=best[1];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion((1,0,0),best[1]);pb.keyframe_insert('rotation_quaternion',frame=f)
   changes.append({'frame':f,'panel':name,'angle_deg':math.degrees(best[1]),'change_deg':math.degrees(best[1]-baseline),'penetration_m':best[2],'floor_m':best[3]})
 report[act.name]={'max_penetration_m':max(r['penetration_m']for r in changes),'min_floor_m':min(r['floor_m']for r in changes),'max_correction_deg':max(abs(r['change_deg'])for r in changes),'samples':changes};print('CLOTH FIT',act.name,{k:v for k,v in report[act.name].items()if k!='samples'},flush=True)
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     if 'Cloth' in fc.data_path:
      for key in fc.keyframe_points:key.interpolation='LINEAR'
rig.animation_data.action=None;(P/'review/cloth_fit.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/equipped.blend'))
