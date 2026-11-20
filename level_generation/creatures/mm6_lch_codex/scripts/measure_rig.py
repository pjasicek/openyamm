"""G4/G5 and posture: every clip at 48 Hz. Rigid bones must remain rigid."""
import bpy,sys,json,math,os
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/os.environ.get('LCH_GATE_BLEND','work/rig_reduced.blend')))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene
rest=np.array([tuple(v.co) for v in me.vertices]);edges=np.array([tuple(e.vertices) for e in me.edges])
d0=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1);valid=d0>1e-6
bone_names={b.name for b in rig.data.bones}
dom=[]
for v in me.vertices:
 weights=[(body.vertex_groups[e.group].name,e.weight) for e in v.groups if body.vertex_groups[e.group].name in bone_names]
 assert len(weights)==1 and abs(weights[0][1]-1)<1e-5,weights
 dom.append(weights[0][0])
arm=np.array([any(x in n for x in ['UpperArm','Forearm','Clavicle']) for n in dom]);hand=np.array([any(x in n for x in ['Hand','Finger']) for n in dom])
assert all(dom[a]==dom[b] for a,b in edges), 'A rigid piece crosses joint weights'
report={}
for act in bpy.data.actions:
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 n=int(round((act.frame_range[1]-act.frame_range[0])/scene.render.fps*48));stmax=1.;armmax=1.;handmax=1.;pelvis=[];lean=[];lowest=[];hands=[];heights=[];feet={'L':[],'R':[]}
 for i in range(n+1):
  f=act.frame_range[0]+i*scene.render.fps/48;scene.frame_set(int(f),subframe=f-int(f))
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();coords=np.array([tuple(body.matrix_world@v.co) for v in m.vertices]);ev.to_mesh_clear()
  ratio=np.linalg.norm(coords[edges[:,0]]-coords[edges[:,1]],axis=1)/np.maximum(d0,1e-6)
  stmax=max(stmax,float(ratio[valid].max()));armmax=max(armmax,float(ratio[valid & arm[edges[:,0]]].max()));handmax=max(handmax,float(ratio[valid & hand[edges[:,0]]].max()))
  J=lambda b:rig.matrix_world@rig.pose.bones[b].head
  pelvis.append(J('B_Pelvis').z);d=J('B_Neck')-J('B_Spine');lean.append(math.degrees(math.atan2(-d.y,d.z)));lowest.append(coords[:,2].min())
  hands.append([list(J('B_L_Hand')),list(J('B_R_Hand'))]);heights.append(float(coords[:,2].max()-coords[:,2].min()))
  for sd in 'LR':feet[sd].append(list(J(f'B_{sd}_Foot')))
 rec={'samples':n+1,'g4_arm_edge_max':armmax,'g5_hand_edge_max':handmax,'whole_mesh_edge_max':stmax,'pelvis_height_m':[min(pelvis),max(pelvis)],'sagittal_trunk_lean_deg':[min(lean),max(lean)],'lowest_vertex_m':min(lowest)}
 rec['posed_height_m']=[min(heights),max(heights)]
 rec['foot_fore_aft_range_m']={sd:float(np.ptp(np.array(v)[:,1])) for sd,v in feet.items()}
 if act.name in ['Attack','Cast']:
  h=np.array(hands);v=np.linalg.norm(np.diff(h,axis=0),axis=2)*48
  # Fastest forward hand delivery, excluding return to the standing stance.
  forward=(np.diff(h,axis=0)[:,:,1]<0)&(h[1:,:,1]<-.15);v[~forward]=0
  f,side=np.unravel_index(np.argmax(v),v.shape);rec['release_seconds']=(f+1)/48;rec['release_hand']='LR'[side];rec['release_hand_speed_m_s']=float(v[f,side])
 report[act.name]=rec;print('GATES',act.name,json.dumps(rec))
 assert stmax<1.01 and armmax<1.01 and handmax<1.01,(act.name,stmax)
 if act.name in ['Standing','Walking','Attack','Cast','Fidget']:
  assert max(abs(x) for x in lean)<30,(act.name,lean)
json.dump(report,open(P/os.environ.get('LCH_GATE_REPORT','work/rig_gates.json'),'w'),indent=2)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
for ob in bpy.data.objects:ob.select_set(ob in (rig,body))
bpy.context.view_layer.objects.active=rig
if not os.environ.get('LCH_SKIP_GATE_EXPORT'):
 bpy.ops.export_scene.gltf(filepath=str(P/'work/rig_gate.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
