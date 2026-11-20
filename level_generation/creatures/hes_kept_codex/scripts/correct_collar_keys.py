"""Clear tiny collar/neck contacts by local clearance corrections to its own rigid attachment keys."""
import bpy,sys,os,json,math
from pathlib import Path
import numpy as np
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];path=P/'work/male/runtime_ragged.blend';bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Kept'];o=bpy.data.objects['hes_kept_collar'];scene=bpy.context.scene;D=np.load(P/'texturing/kept_m_uv.npz');faces=D['faces'][D['piece']==1].tolist();bone=rig.pose.bones['Kept_Collar'];restinv=rig.data.bones['Kept_Collar'].matrix_local.inverted()
local=[restinv@v.co for v in o.data.vertices];local += [(restinv@o.data.vertices[e.vertices[0]].co+restinv@o.data.vertices[e.vertices[1]].co)*.5 for e in o.data.edges];local += [sum((restinv@o.data.vertices[i].co for i in f.vertices),Vector())/len(f.vertices) for f in o.data.polygons]
def inside(tree,p):
 direction=Vector((.719,.371,.588)).normalized();origin=p.copy();hits=0
 for _ in range(64):
  hit,n,ix,d=tree.ray_cast(origin,direction,10.)
  if hit is None:return hits%2==1
  hits+=1;origin=hit+direction*1e-5
 raise AssertionError('ray')
report={}
for a in sorted(bpy.data.actions,key=lambda a:a.name):
 if not a.name.startswith('Kept_'):continue
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 curves=[fc for l in a.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves if 'Kept_Collar' in fc.data_path]
 loc=sorted([fc for fc in curves if fc.data_path.endswith('location')],key=lambda fc:fc.array_index);assert len(loc)==3
 original={float(k.co.x):Vector(tuple(fc.evaluate(k.co.x) for fc in loc)) for k in loc[0].keyframe_points};cache=[]
 for f in np.arange(a.frame_range[0],a.frame_range[1]+.001,.5):
  scene.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();points=[body.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();cache.append((f,BVHTree.FromPolygons(points,faces,all_triangles=True)))
 its=[]
 for attempt in range(30):
  worst=0.;count=0
  for f,tree in cache:
   scene.frame_set(int(f),subframe=float(f%1));world=rig.matrix_world@bone.matrix;depth=0.;normal=None
   for p in local:
    point=world@p;hit,n,ix,dist=tree.find_nearest(point,.025)
    if hit is not None and dist>max(depth,.00008) and (point-hit).dot(n)<-.5*dist and inside(tree,point):depth=float(dist);normal=n
   if normal is None:continue
   worst=max(worst,depth);count+=1
   basis=rig.matrix_world@bone.parent.matrix@bone.parent.bone.matrix_local.inverted()@bone.bone.matrix_local;delta=basis.to_3x3().inverted()@(normal*(depth+.00015))
   # Half-frame corrections are retained by the final 60 Hz export.
   for axis,fc in enumerate(loc):
    for k in fc.keyframe_points:
     weight=1.0 if abs(k.co.x-f)<.01 else 0
     if weight:k.co.y+=delta[axis]*weight
    fc.update()
  its.append({'iteration':attempt,'penetrating_poses':count,'max_inside_m':worst});print('COLLAR_KEY',a.name,its[-1],flush=True)
  if count==0:break
 else:raise AssertionError(('collar key correction did not converge',a.name))
 maxmove=max((Vector(tuple(fc.evaluate(f) for fc in loc))-v).length for f,v in original.items());assert maxmove<.025,(a.name,maxmove);report[a.name]={'max_local_translation_correction_m':maxmove,'iterations':its}
bpy.ops.wm.save_as_mainfile(filepath=str(path))
for a in bpy.data.actions:
 for l in a.layers:
  for strip in l.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.co.x*=2;k.handle_left.x*=2;k.handle_right.x*=2
     fc.update()
 a.frame_start*=2;a.frame_end*=2
scene.render.fps=60
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
for obj in bpy.data.objects:obj.select_set(obj in (rig,body))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(P/'export/hes_kept_m_ragged_lod0.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=True,export_attributes=False,export_morph=False,export_extras=True,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
(P/'review/collar_key_clearance.json').write_text(json.dumps({'pass':True,'tolerance_m':.00008,'clips':report},indent=2)+'\n');sys.stdout.flush();sys.stderr.flush();os._exit(0)
