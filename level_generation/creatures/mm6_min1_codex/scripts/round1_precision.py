"""48 Hz anatomical wrist, fixed palm frame, sole-plane and gait checks."""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/globals().get('INPUT','work/round1_clothed.blend')))
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene;fps=sc.render.fps/sc.render.fps_base
rest={n:x.matrix_local.copy() for n,x in r.data.bones.items()}
gr={s:json.loads((P/f'work/grip_pose_{s}.json').read_text()) for s in 'RL'}
meta=json.loads((P/'work/round1_grip_frames.json').read_text());HF={s:Matrix(meta['frames'][s]) for s in 'RL'}
xyz=np.array([v.co[:] for v in b.data.vertices]);W=np.zeros((len(xyz),len(b.vertex_groups)))
for v in b.data.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
names=[g.name for g in b.vertex_groups];sole={};hand={}
for s,sign in [('R',-1),('L',1)]:
 ids=np.where((xyz[:,2]<.025)&(xyz[:,0]*sign>0))[0];assert len(ids)>10
 sole[s]={'all':ids,'heel':ids[xyz[ids,1]>=np.median(xyz[ids,1])],'toe':ids[xyz[ids,1]<np.median(xyz[ids,1])]}
 hand[s]=np.where(W[:,[i for i,n in enumerate(names) if n.startswith(f'B_{s}_') and ('Hand' in n or 'Finger' in n)]].sum(1)>.5)[0]
def twist(q,axis):return (2*math.atan2(Vector(q[1:]).dot(axis),q.w)+math.pi)%(2*math.pi)-math.pi
def angle(q):return math.degrees(min(q.angle,2*math.pi-q.angle))
def xyz_pose():
 e=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();a=np.array([v.co[:] for v in m.vertices]);e.to_mesh_clear();return a
def normal(p):
 n=np.linalg.svd(p-p.mean(0))[2][-1];return n if n[2]>0 else -n
assert np.linalg.norm(normal(np.array([[0,0,0],[1,0,0],[0,1,0],[1,1,0]]))-[0,0,1])<1e-6
report={}
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];rows={s:[] for s in 'RL'};prev={};sole_rows={s:[] for s in 'RL'}
 for f in sorted(set(np.arange(0,float(a.frame_range[1]),fps/48).tolist()+[float(a.frame_range[1])])):
  sc.frame_set(int(f),subframe=f%1);t=f/fps;pts=xyz_pose();A=r.pose.bones['Axe'].matrix@rest['Axe'].inverted();ar=A.to_3x3();axis=(ar@Vector((0,0,1))).normalized();held=a.name!='Dead' and not(a.name=='Death' and t>=1/6)
  for s in 'RL':
   un,fn,hn=[f'B_{s}_{n}' for n in ['UpperArm','Forearm','Hand']];U,F,H=[r.pose.bones[n].matrix for n in [un,fn,hn]];up=(F.translation-U.translation).normalized();fo=(H.translation-F.translation).normalized()
   ru=(rest[fn].translation-rest[un].translation).normalized();rb=Vector((0,-1,0));rb=(rb-ru*rb.dot(ru)).normalized();plane=(U.to_3x3()@rest[un].to_3x3().inverted()@ru.cross(rb)).normalized();forward=plane.cross(up).normalized()
   flex=math.degrees(math.atan2(fo.dot(forward),fo.dot(up)));off=math.degrees(math.asin(max(-1,min(1,fo.dot(plane)))))
   localaxis=(rest[fn].inverted()@rest[hn].translation).normalized();q=(F.to_3x3().inverted()@H.to_3x3()@(rest[fn].to_3x3().inverted()@rest[hn].to_3x3()).inverted()).to_quaternion();roll=twist(q,localaxis);bend=(q@Quaternion(localaxis,-roll)).angle
   tr=twist(r.pose.bones[f'B_{s}_ForearmTwist'].matrix_basis.to_quaternion(),localaxis)
   x={'time':t,'elbow_flex':flex,'elbow_off_plane':abs(off),'forearm_roll':abs(math.degrees(roll)),'twist_helper_roll':abs(math.degrees(tr)),'wrist_residual_roll':abs(math.degrees(roll-tr)),'wrist_bend':math.degrees(bend),'roll_step':0 if s not in prev else abs(math.degrees((roll-prev[s]+math.pi)%(2*math.pi)-math.pi)),'segment_error_mm':1000*abs((H.translation-F.translation).length-(rest[hn].translation-rest[fn].translation).length)}
   prev[s]=roll
   if held:
    c=H@Vector(gr[s]['handle_centre_hand_local']);target=A@Vector((0,0,meta['grip_z'][s]));x['fixed_grip_error_mm']=1000*(c-target).length;x['palm_frame_error_deg']=angle((ar@HF[s]).to_quaternion().rotation_difference(H.to_quaternion()));ha=(H.to_3x3()@Vector(gr[s]['handle_axis_hand_local'])).normalized();x['haft_axis_error_deg']=math.degrees(math.acos(max(-1,min(1,abs(ha.dot(axis))))))
    # Palm faces the shaft: anatomical palm normal is -Z in the fitted hand frame.
    palm=H@Vector((0,.115,0));inward=target-palm;inward-=axis*inward.dot(axis);pn=H.to_3x3()@Vector((0,0,1 if s=='R' else -1));x['palm_to_haft_cos']=pn.normalized().dot(inward.normalized())
    v=pts[hand[s]]-np.array(c);along=v@np.array(axis);rad=np.linalg.norm(v-np.outer(along,np.array(axis)),axis=1);near=abs(along)<.05;minimum=float(rad[near].min());x['skin_gap_mm']=1000*(minimum-.0165)
   rows[s].append(x)
   sp=pts[sole[s]['all']];n=normal(sp);tilt=math.degrees(math.acos(min(1,float(n[2]))));z=float(sp[:,2].min());heel=float(pts[sole[s]['heel'],2].min());toe=float(pts[sole[s]['toe'],2].min())
   foot=r.pose.bones[f'B_{s}_Foot'].matrix;v=foot.to_3x3()@rest[f'B_{s}_Foot'].to_3x3().inverted()@Vector((0,-1,0));heading=abs(math.degrees(math.atan2(v.x,-v.y)))
   thigh,calf,ankle=[r.pose.bones[f'B_{s}_{n}'].head for n in ['Thigh','Calf','Foot']];knee=math.degrees((calf-thigh).angle(ankle-calf))
   sole_rows[s].append({'time':t,'tilt_deg':tilt,'lowest_m':z,'heel_m':heel,'toe_m':toe,'heading_deg':heading,'knee_deg':knee})
 rr={}
 for s in 'RL':
  x=rows[s];ss=sole_rows[s];summary={k:max(v[k] for v in x if k in v) for k in x[0] if k!='time'};summary['elbow_flex_min']=min(v['elbow_flex'] for v in x);summary['palm_to_haft_cos_min']=min((v['palm_to_haft_cos'] for v in x if 'palm_to_haft_cos' in v),default=1);summary['lowest_sole_min_m']=min(v['lowest_m'] for v in ss);summary['swing_peak_m']=max(v['lowest_m'] for v in ss);summary['sole_tilt_max_deg']=max(v['tilt_deg'] for v in ss);summary['heel_range_m']=[min(v['heel_m'] for v in ss),max(v['heel_m'] for v in ss)];summary['toe_range_m']=[min(v['toe_m'] for v in ss),max(v['toe_m'] for v in ss)];summary['heading_max_deg']=max(v['heading_deg'] for v in ss);summary['knee_at_swing_peak_deg']=max(ss,key=lambda v:v['lowest_m'])['knee_deg']
  summary['pass']={'elbow':summary['elbow_flex_min']>=-5 and summary['elbow_off_plane']<1,'roll':summary['forearm_roll']<=90 and summary['wrist_residual_roll']<=45 and summary['roll_step']<45,'wrist_bend':summary['wrist_bend']<=60,'segment':summary['segment_error_mm']<1}
  if any('fixed_grip_error_mm' in v for v in x):
   summary['pass']['palm']=summary['fixed_grip_error_mm']<=3 and summary['palm_frame_error_deg']<=3 and summary['haft_axis_error_deg']<=3 and summary['palm_to_haft_cos_min']>.5 and summary['skin_gap_mm']<=3
  if a.name in ['Standing','Fidget']:summary['pass']['sole']=summary['sole_tilt_max_deg']<=1 and max(abs(v) for k in ['heel_range_m','toe_range_m'] for v in summary[k])<=.01
  if a.name in ['Walking','Running']:summary['pass']['heading']=summary['heading_max_deg']<=10
  rr[s]=summary
 rr['contact_fraction']=float(np.mean([min(x['lowest_m'],y['lowest_m'])<.01 for x,y in zip(sole_rows['R'],sole_rows['L'])]));rr['pass']=all(all(v['pass'].values()) for s,v in rr.items() if s in 'RL');report[a.name]=rr;print('PRECISION',a.name,json.dumps(rr),flush=True)
(P/globals().get('REPORT','review/round1/precision_gate.json')).write_text(json.dumps(report,indent=2))
