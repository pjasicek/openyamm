"""Fit belt-pinned cloth controls to actual triangle contacts, preserving ordinary four-weight skinning."""
import bpy,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/corpse_settled.blend'))
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene;me=b.data;pv=np.array([v.value for v in me.attributes['piece'].data]);rest=np.array([v.co[:] for v in me.vertices]);faces=[tuple(p.vertices) for p in me.polygons];cf=[f for f in faces if all(pv[i]==1 and rest[i,2]<.99 for i in f)];sf=[f for f in faces if all(pv[i]==0 and rest[i,2]<1.1 for i in f)];cn=[n for n in r.pose.bones.keys() if n.startswith('Skirt_')];ng=[g.name for g in b.vertex_groups];A=np.zeros((len(rest),len(cn)))
for v in me.vertices:
 for g in v.groups:
  if ng[g.group] in cn:A[v.index,cn.index(ng[g.group])]=g.weight
reports={};solutions={}
for nm in ['Death']:
 act=bpy.data.actions[nm];rows=[];prev=np.zeros((len(cn),3));maxit=0;maxmove=0;maxcontacts=0
 for f in range(int(act.frame_range[1])+1):
  r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];sc.frame_set(f);r.animation_data.action=None
  for n in cn:r.pose.bones[n].location=(0,0,0);r.pose.bones[n].rotation_quaternion=(1,0,0,0)
  bpy.context.view_layer.update();ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();base=np.array([v.co[:] for v in mesh.vertices]);ev.to_mesh_clear();tree=BVHTree.FromPolygons(base.tolist(),sf);D=prev*.88
  for it in range(35):
   pts=base+A@D;pairs=BVHTree.FromPolygons(pts.tolist(),cf).overlap(tree);maxcontacts=max(maxcontacts,len(pairs));ci=sorted({i for i,j in pairs});ids=sorted({v for i in ci for v in cf[i]});aa=[];dd=[]
   samples=[(pts[i],A[i]) for i in ids]+[(pts[list(cf[i])].mean(0),A[list(cf[i])].mean(0)) for i in ci]
   for pt,coef in samples:
    loc,nrm,fi,dist=tree.find_nearest(Vector(pt),.15)
    if loc is not None and np.linalg.norm(coef)>.02 and (Vector(pt)-loc).dot(nrm)<.002:
     aa.append(coef);dd.append(np.array(loc+nrm*.010)-pt)
   if not aa:break
   a=np.array(aa);d=np.array(dd);delta=np.linalg.solve(a.T@a+np.eye(len(cn))*.025,a.T@d);D+=delta*.75
   lengths=np.linalg.norm(D,axis=1);D*=np.minimum(1,.24/np.maximum(lengths,1e-8))[:,None]
  maxit=max(maxit,it);maxmove=max(maxmove,float(np.linalg.norm(D,axis=1).max()));prev=D;local={n:r.pose.bones[n].matrix.to_3x3().inverted()@Vector(D[i]) for i,n in enumerate(cn)};rows.append(local)
  if f in [0,10] and nm=='Walking':
   for n,loc in local.items():r.pose.bones[n].location=loc
   bpy.context.view_layer.update();ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();actual=np.array([v.co[:] for v in mesh.vertices]);ev.to_mesh_clear();error=float(np.max(np.linalg.norm(actual-(base+A@D),axis=1)));print('CLOTH linear playback error',f,error,flush=True);assert error<.00001,error
 reports[nm]={'max_iterations':maxit+1,'max_control_offset_m':maxmove,'max_initial_intersections':maxcontacts};solutions[nm]=rows;print('CLOTH',nm,reports[nm],flush=True)
for nm,rows in solutions.items():
 act=bpy.data.actions[nm];r.animation_data.action=act;r.animation_data.action_slot=act.slots[0]
 for f,row in enumerate(rows):
  for n,loc in row.items():r.pose.bones[n].location=loc;r.pose.bones[n].keyframe_insert('location',frame=f)
# Copy all control endpoints to the held corpse.
a=bpy.data.actions['Dead'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
for f in range(121):
 for n,loc in solutions['Death'][-1].items():r.pose.bones[n].location=loc;r.pose.bones[n].keyframe_insert('location',frame=f)
for a in bpy.data.actions:
 for lay in a.layers:
  for st in lay.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
(P/'review/cloth_fit_corpse.json').write_text(json.dumps(reports,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/production_master.blend'))
