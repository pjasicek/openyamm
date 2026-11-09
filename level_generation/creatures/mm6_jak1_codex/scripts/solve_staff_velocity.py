"""Solve the released staff's inherited horizontal velocity against dense body contact samples."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));from timing import phase
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_master.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Jackalman'];sc=bpy.context.scene;a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];group=body.vertex_groups['Staff'].index;staff=np.array([any(g.group==group and g.weight>.5 for g in v.groups)for v in body.data.vertices]);faces=[tuple(f.vertices)for f in body.data.polygons if not staff[f.vertices[0]]];body.data.calc_loop_triangles();sf=np.array([tuple(f.vertices)for f in body.data.loop_triangles if staff[f.vertices[0]]]);edges=np.unique(np.sort(np.concatenate([sf[:,[0,1]],sf[:,[1,2]],sf[:,[2,0]]]),axis=1),axis=0);times=np.arange(.25,.85001,1/48);cache=[]
for t in times:
 f=phase('Death',float(t))*sc.render.fps;sc.frame_set(int(f),subframe=f-int(f));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([body.matrix_world@v.co for v in me.vertices]);ev.to_mesh_clear();samples=np.concatenate([co[staff],co[sf].mean(1),co[edges].mean(1)]);tree=BVHTree.FromPolygons(co.tolist(),faces);u=min(1,(t-.25)/.6);cache.append((float(t),.6*(u*u*u-2*u*u+u),samples,tree,co[~staff].min(0)-.01,co[~staff].max(0)+.01))
rays=[Vector(q).normalized()for q in [(1,.13,.27),(-1,.31,.17),(.19,1,.41),(.23,-1,.37),(.31,.21,1),(.11,.27,-1),(1,1,1)]]
def check(v):
 worst=0;at=None
 for t,weight,points,tree,lo,hi in cache:
  shifted=points+np.array([v[0],v[1],0])*weight;selected=shifted[((shifted>=lo)&(shifted<=hi)).all(1)]
  for point in selected:
   p=Vector(point);loc,n,fi,d=tree.find_nearest(p,.04)
   if loc is not None and d>worst and (p-loc).dot(n)<-.7*d:
    exits=0
    for ray in rays:
     hit,normal,_,_=tree.ray_cast(p+ray*1e-6,ray,10);exits+=hit is not None and normal.dot(ray)>0
    if exits>=5:worst=d;at=t
    if worst>.002:return worst,at
 return worst,at
candidates=sorted([(x,y)for x in [-3,-2,-1,-.5,0,.5,1,2,3]for y in [-3,-2,-1,-.5,0,.5,1,2,3]],key=lambda v:v[0]*v[0]+v[1]*v[1]);rows=[];best=None
for v in candidates:
 depth,at=check(v);rows.append({'velocity_xy_mps':v,'depth_m':depth,'source_seconds':at})
 if depth<=.002:best=rows[-1];break
(P/'work/staff_velocity_sweep.json').write_text(json.dumps(rows,indent=2));assert best,sorted(rows,key=lambda r:r['depth_m'])[:5];(P/'work/staff_release_velocity.json').write_text(json.dumps(best,indent=2));print('SAFE DROP VELOCITY',best,flush=True)
# Preserve all body poses and the staff orientation; only the free prop's translation changes.
curve=next(fc for layer in a.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves if fc.data_path=='pose.bones["Staff"].location' and fc.array_index==0);frames=[float(k.co.x)for k in curve.keyframe_points];author=np.arange(0,1.95834,.0005);mapped=np.array([phase('Death',float(t))for t in author]);poses=[];pb=rig.pose.bones['Staff'];v=np.array([*best['velocity_xy_mps'],0.])
for f in frames:
 sc.frame_set(int(f),subframe=f-int(f));t=float(np.interp(f/sc.render.fps,mapped,author));u=max(0,min(1,(t-.25)/.6));m=(rig.matrix_world@pb.matrix).copy();m.translation+=Vector(v*.6*(u*u*u-2*u*u+u));pb.matrix=rig.matrix_world.inverted()@m;poses.append(pb.location.copy())
for f,p in zip(frames,poses):pb.location=p;pb.keyframe_insert('location',frame=f)
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];sc.frame_set(0)
for o in bpy.data.objects:o.select_set(o in [body,rig])
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/mm6_jak1_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/runtime_master.blend'))
