"""Fit run root height to the source heel/toe contact anchors, keeping authored leg rotations."""
import bpy,numpy as np,json,math
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];repo=P.parents[2]
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.render.fps=30;bpy.ops.import_scene.fbx(filepath=str(repo/'anim_library/mixamo/Standard Run.fbx'));src=next(o for o in bpy.data.objects if o.type=='ARMATURE');act=src.animation_data.action;start,end=act.frame_range
# The library FBX is skeleton-only: project heel/toe anchors onto its bind-pose floor.
prefix=next(b.name for b in src.data.bones if b.name.endswith('Hips'))[:-4]
sourceleg=sum((src.matrix_world@(src.data.bones[prefix+b].head_local-src.data.bones[prefix+a].head_local)).length for a,b in [('LeftUpLeg','LeftLeg'),('LeftLeg','LeftFoot')])
anchors={}
for side in ['Left','Right']:
 for part in ['Foot','ToeBase']:
  n=prefix+side+part;rest=src.matrix_world@src.data.bones[n].matrix_local;point=rest.translation.copy();point.z=0;anchors[n]=rest.inverted()@point
low=[];ts=np.arange(0,22.001,.25)
for f in ts:
 sf=start+f;sc.frame_set(int(sf),subframe=float(sf%1));low.append(min((src.matrix_world@src.pose.bones[n].matrix@anchor).z for n,anchor in anchors.items()))
low=np.array(low);low-=np.percentile(low,5);low=np.maximum(low,0)
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_delivery.blend'));sc=bpy.context.scene;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];a=bpy.data.actions['Running'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
ourleg=sum((rig.data.bones[b].head_local-rig.data.bones[c].head_local).length for c,b in [('B_L_Thigh','B_L_Calf'),('B_L_Calf','B_L_Foot')]);ratio=ourleg/sourceleg
pc=np.array([v.value for v in body.data.attributes['piece'].data]);feet=np.isin(pc,[5,6]);rows=[]
# Fit the skeleton-only source contact band to the boots; retain its flight phases with a softer height profile.
clearance=np.maximum(low*ratio-.03,0);target=.004+.45*clearance*clearance/(clearance+.01)
for f,desired in zip(ts,target):
 sc.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();z=np.array([v.co.z for v in m.vertices]);ev.to_mesh_clear();rows.append((rig.pose.bones['B_Pelvis'].location.copy(),float(desired-z[feet].min())))
inv=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted()
for f,(loc,dz) in zip(ts,rows):
 rig.pose.bones['B_Pelvis'].location=loc+inv@Vector((0,0,dz));rig.pose.bones['B_Pelvis'].keyframe_insert('location',frame=float(f))
for layer in a.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    if fc.data_path.endswith('.location'):
     for k in fc.keyframe_points:k.interpolation='LINEAR'
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master_grounded_delivery.blend'))
r={'source_contact_method':'Skeleton-only FBX: bind-floor heel/toe anchors transformed by authored foot bones','source_leg_m':sourceleg,'model_leg_m':ourleg,'source_sole_height_m':low.tolist(),'model_sole_height_m':target.tolist(),'max_flight_mm':float(target.max()*1000),'contact_pct':float((target<=.01).mean()*100)}
(P/'review/run_source_floor.json').write_text(json.dumps(r,indent=2));print('SOURCE_RUN_FLOOR',r['max_flight_mm'],r['contact_pct'],ratio)
