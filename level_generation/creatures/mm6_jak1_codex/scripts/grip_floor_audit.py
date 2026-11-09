import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from timing import phase
import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(P/'export/mm6_jak1_runtime_lod0.glb'));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');body=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.parent is rig and 'Staff' in o.vertex_groups);names={g.index:g.name for g in body.vertex_groups};st=body.vertex_groups['Staff'].index;staff=np.array([any(g.group==st and g.weight>.5 for g in v.groups)for v in body.data.vertices]);hand=np.array([sum(g.weight for g in v.groups if names[g.group].startswith(('B_R_Hand','B_R_Finger')))> .5 for v in body.data.vertices]);left_hand=np.array([sum(g.weight for g in v.groups if names[g.group].startswith(('B_L_Hand','B_L_Finger')))> .5 for v in body.data.vertices]);sc=bpy.context.scene;report={}
for a in bpy.data.actions:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];r={'body_min_z_m':1e9,'staff_min_z_m':1e9,'grip_min_skin_radius_m':1e9}
 for f in np.arange(0,a.frame_range[1]+.001,30/48):
  sc.frame_set(int(f),subframe=float(f-int(f)));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.empty((len(me.vertices),3),np.float32);me.vertices.foreach_get('co',co.ravel());ev.to_mesh_clear();co=(np.c_[co,np.ones(len(co))]@np.array(body.matrix_world).T)[:,:3]
  for k,z in [('body_min_z_m',co[~staff,2].min()),('staff_min_z_m',co[staff,2].min())]:
   if z<r[k]:r[k]=float(z);r[k+'_seconds']=float(f/30)
  if a.name=='Dead':r['corpse_max_z_m']=float(co[~staff,2].max())
  inv=np.array((rig.matrix_world@rig.pose.bones['Staff'].matrix).inverted());q=(np.c_[co[hand],np.ones(hand.sum())]@inv.T)[:,:3];q=q[np.abs(q[:,2])<.075];rad=float(np.linalg.norm(q[:,:2],axis=1).min()) if len(q) else 1e9
  if (a.name not in ['Death','Dead'] or (a.name=='Death' and f/30<=phase('Death',.20))) and rad<r['grip_min_skin_radius_m']:r['grip_min_skin_radius_m']=rad;r['grip_seconds']=float(f/30)
  if a.name=='Attack' and phase('Attack',.4)<=f/30<=phase('Attack',1.2):
   q=(np.c_[co[left_hand],np.ones(left_hand.sum())]@inv.T)[:,:3];q=q[np.abs(q[:,2]-.29)<.075];rad=float(np.linalg.norm(q[:,:2],axis=1).min());r['offhand_min_skin_radius_m']=min(r.get('offhand_min_skin_radius_m',1e9),rad)
 if a.name=='Dead':r['grip_min_skin_radius_m']=None;r['staff_released']=True
 if a.name=='Death':r['grip_checked_until_seconds']=phase('Death',.20);r['staff_release_seconds']=phase('Death',.25)
 report[a.name]=r
(P/'review/grip_floor.json').write_text(json.dumps(report,indent=2));print('GRIP FLOOR',report,flush=True)
