"""Per-frame posture and actual exported blade-tip/edge motion (48 Hz)."""
import bpy,json,math,numpy as np
from mathutils import Vector
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(P/'work/round3/runtime_combined.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');body=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.parent==rig);scene=bpy.context.scene
W=json.loads((P/'work/weapon_fit.json').read_text());c=Vector(W['centre_rest']);ax=Vector(W['axis_rest']);edge=Vector(W['cut_direction_rest']);tip=c+ax*.85-edge*.18;inv=rig.data.bones['Sword'].matrix_local.inverted();post={};blade={}
g=body.vertex_groups['Sword'].index;bodyids=[v.index for v in body.data.vertices if not any(e.group==g and e.weight>.5 for e in v.groups)]
for ac in bpy.data.actions:
 rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0];rows=[];prev=None;motion=[];height=[]
 for f in np.arange(0,float(ac.frame_range[1])+.001,30/48):
  scene.frame_set(int(f),subframe=float(f-int(f)));a=rig.matrix_world@rig.pose.bones['B_Pelvis'].head;b=rig.matrix_world@rig.pose.bones['B_Neck'].head;rows.append({'seconds':float(f/30),'pelvis_height_m':a.z,'trunk_lean_deg':math.degrees((b-a).angle(Vector((0,0,1))))})
  M=rig.matrix_world@rig.pose.bones['Sword'].matrix@inv;p=M@tip;e=(M.to_3x3()@edge).normalized();flat=(M.to_3x3()@ax.cross(edge)).normalized();forward=(M.to_3x3()@ax).normalized().dot(Vector((0,-1,0)))
  if prev is not None:
   v=(p-prev)*48;speed=v.length;motion.append({'seconds':float((f-30/96)/30),'speed_m_s':speed,'target_dot':forward,'signed_edge_lead':v.dot(e)/max(speed,1e-8),'edge_share':abs(v.dot(e))/max(math.hypot(v.dot(e),v.dot(flat)),1e-8)})
  prev=p
  if ac.name=='Standing':
   ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();zz=[(body.matrix_world@me.vertices[i].co).z for i in bodyids];height.append(max(zz)-min(zz));ev.to_mesh_clear()
 post[ac.name]={'pelvis_height_m':[min(r['pelvis_height_m'] for r in rows),max(r['pelvis_height_m'] for r in rows)],'trunk_lean_deg':[min(r['trunk_lean_deg'] for r in rows),max(r['trunk_lean_deg'] for r in rows)],'samples':rows}
 if height:post[ac.name]['body_height_m']=float(np.median(height))
 if motion:
  speeds=np.array([r['speed_m_s'] for r in motion]);fast=[r for r in motion if r['speed_m_s']>=np.percentile(speeds,80) and r['speed_m_s']>1e-6];blade[ac.name]={'peak_speed_m_s':max(speeds),'fastest20_edge_share':float(np.mean([r['edge_share'] for r in fast])) if fast else 0}
  if ac.name=='Attack':
   candidates=[r for r in motion if r['target_dot']>.5];peak=max(candidates,key=lambda r:r['speed_m_s']);blade['impact']=peak;assert peak['signed_edge_lead']>.5;assert .6<peak['seconds']<.9
(P/'review/round3/posture.json').write_text(json.dumps(post,indent=2));(P/'review/round3/blade_gate.json').write_text(json.dumps(blade,indent=2));print('BLADE GATE',blade['impact']);print('POSTURE',{k:{a:b for a,b in v.items() if a!='samples'} for k,v in post.items()})
