"""Native raised-knee spear wind-up and planted low thrust, referenced to cached 2HandSpearAttack10."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C,common
D=json.loads((P/'work/round3_pose_reference.json').read_text());base={n:Matrix(v)for n,v in D['standing_basis'].items()};world={n:Matrix(v)for n,v in D['standing'].items()}
def ease(t):
 t=max(0,min(1,t));return t*t*t*(10+t*(-15+6*t))
def curve(f,values,keys=(0,21,34,43,76)):
 for i in range(len(keys)-1):
  if f<=keys[i+1]:return np.array(values[i])*(1-ease((f-keys[i])/(keys[i+1]-keys[i])))+np.array(values[i+1])*ease((f-keys[i])/(keys[i+1]-keys[i]))
 return np.array(values[-1])
def source_residual(frame,n):
 keys=[0,21,34,43,76]
 for j in range(4):
  if frame<=keys[j+1]:break
 t=(frame-keys[j])/(keys[j+1]-keys[j]);a=Matrix(D['source'][str(keys[j])][n]);b=Matrix(D['source'][str(keys[j+1])][n]);actual=Matrix(D['source'][str(frame)][n]);baseline=a.to_quaternion().slerp(b.to_quaternion(),t)
 q=actual.to_quaternion()@baseline.inverted();q=Quaternion().slerp(q,.20)
 delta=(actual.translation-a.translation.lerp(b.translation,t))*.12
 if delta.length>.025:delta.normalize();delta*=.025
 return q,delta

def bags(a):
 for layer in a.layers:
  for strip in layer.strips:
   for slot in a.slots:
    bag=strip.channelbag(slot)
    if bag:yield bag
def put(n,R):
 b=r.pose.bones[n];m=R.to_4x4();m.translation=b.head;b.matrix=m;bpy.context.view_layer.update()
def leg(sd,target):
 ns=[f'B_{sd}_{n}'for n in ['Thigh','Calf','Foot']];H,K,A=[r.pose.bones[n].head.copy()for n in ns];a=(K-H).length;b=(A-K).length;u=(target-H).normalized();dist=min((target-H).length,(a+b)*.997)
 v=Vector((0,-1,0));v=(v-u*v.dot(u)).normalized();x=(a*a+dist*dist-b*b)/(2*dist);knee=H+u*x+v*math.sqrt(max(0,a*a-x*x))
 for n,c,T in [(ns[0],ns[1],knee),(ns[1],ns[2],H+u*dist)]:
  pb=r.pose.bones[n];q=(r.pose.bones[c].head-pb.head).rotation_difference(T-pb.head);put(n,q.to_matrix()@pb.matrix.to_3x3())
 put(ns[2],world[ns[2]].to_3x3());r.pose.bones[f'B_{sd}_Toe0'].matrix_basis=base[f'B_{sd}_Toe0']

poses=[];report={'source':'Cached 2HandSpearAttack10 reviewed for raised knee and lunge; native target poses refitted with anatomical IK, planted feet and target-facing head.','frames':76,'windup_end_frame':21,'drive_end_frame':34,'poses':{}}
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/review_round3_before/work/runtime_lod{level}.blend'));C.reset();r=bpy.data.objects['Rig'];sc=bpy.context.scene
 if level==0:
  import arm_ik as IK
  sides={s:IK.Side(s)for s in 'LR'};G=IK.GDATA;rest={b.name:b.matrix_local.copy()for b in r.data.bones};mirror=Matrix.Diagonal(Vector((-1,1,1)))
  # Mirror the fitted right grip through the real left/right bind frames.
  transform=rest['B_L_Hand'].to_3x3().inverted()@mirror@rest['B_R_Hand'].to_3x3()
  sides['L'].grip_hand=transform@Vector(G['handle_centre_hand_local']);Laxis=(transform@Vector(G['handle_axis_hand_local'])).normalized()
  lg=json.loads((P/'work/round3_left_grip.json').read_text());sides['L'].grip_hand=Vector(lg['handle_centre_hand_local']);Laxis=Vector(lg['handle_axis_hand_local']);closed={n:Quaternion(q)for n,q in lg['finger_local'].items()}
  buckler=bpy.data.objects['BucklerMesh'];localB=[rest['Buckler'].inverted()@v.co for v in buckler.data.vertices][::12]
  buckleChain=rest['B_L_Forearm'].inverted()@rest['B_L_ForearmTwist']@base['B_L_ForearmTwist']@rest['B_L_ForearmTwist'].inverted()@rest['Buckler']@base['Buckler']
  axisR=world['Spear'].to_3x3()@Vector((0,0,1));HR=world['B_R_Hand'].to_3x3();HL=world['B_L_Hand'].to_3x3();previous={};prevRh={}
  r.animation_data.action=None;options={s:[]for s in 'LR'}
  for frame in range(77):
   for b in r.pose.bones:b.matrix_basis=base[b.name]
   bpy.context.view_layer.update()
   pelvis=Vector(curve(frame,[[0,-.065,.969],[0,.10,.99],[0,-.36,.73],[0,-.36,.73],[0,-.065,.969]]));lean=float(curve(frame,[0,-18,40,40,0]));yaw=float(curve(frame,[0,-18,8,8,0]));pelvis+=source_residual(frame,'B_Pelvis')[1];m=world['B_Pelvis'].copy();m.translation=pelvis;r.pose.bones['B_Pelvis'].matrix=m;bpy.context.view_layer.update()
   for n,share in [('B_Pelvis',.3),('B_Spine',.75),('B_Spine1',1),('B_Spine2',1)]:
    put(n,source_residual(frame,n)[0].to_matrix()@Matrix.Rotation(math.radians(yaw)*share,3,'Z')@Matrix.Rotation(math.radians(lean)*share,3,'X')@world[n].to_3x3())
   footL=Vector(curve(frame,[[.135,-.045,.152],[.17,-.24,.52],[.17,-.55,.152],[.17,-.55,.152],[.135,-.045,.152]]));leg('L',footL);leg('R',Vector((-.135,-.045,.152)))
   # Recovery lifts the forward foot before placing it back at home.
   if frame>43:
    footL.z+=.12*math.sin(math.pi*(frame-43)/33)**2;leg('L',footL)
   spine=r.pose.bones['B_Spine2'];delta=(spine.matrix.to_3x3()@spine.bone.matrix_local.to_3x3().inverted()).to_quaternion()
   for n,share in [('B_Neck',.55),('B_Head',.035)]:put(n,Quaternion().slerp(delta,share).to_matrix()@rest[n].to_3x3());r.pose.bones[n].location=(0,0,0);r.pose.bones[n].scale=(1,1,1)
   bpy.context.view_layer.update()
   startG=world['B_R_Hand']@Vector(G['handle_centre_hand_local']);grip=Vector(curve(frame,[startG,[-.50,.26,1.50],[-.245,-.75,1.03],[-.245,-.75,1.03],startG]));axis=Vector(curve(frame,[axisR,[0,-.707,.707],[0,-1,0],[0,-1,0],axisR])).normalized()
   grip+=source_residual(frame,'B_R_Hand')[1]
   if 43<frame<76:grip.x-=.13*math.sin(math.pi*(frame-43)/33)**2
   if 43<frame<66:axis=Vector((0,-1,0)).lerp(axis,ease((frame-60)/6)).normalized()
   Rh0=axisR.rotation_difference(axis).to_matrix()@HR
   # Shaft roll has no visual effect: choose a continuous, anatomical arm solution.
   for sd in 'RL':
    side=sides[sd]
    if sd=='R':target=grip;desired=Rh0;pole=Vector((-.8,.25,-.3))
    else:
     held=ease((frame-18)/13)*(1-ease((frame-46)/15));startW=world['B_L_Hand'].translation
     free=Vector(curve(frame,[startW,[.25,-.38,1.42],[-.245,-.85,1.03],[-.245,-.85,1.03],startW]));target=free.lerp(grip+axis*.10,held)
     if frame>46:free=Vector(curve(frame,[[-.245,-.85,1.03],[.38,-.48,1.16],[.301,-.056,.863]],keys=(46,58,76)))
     desired=(HL@Laxis).rotation_difference(axis).to_matrix()@HL;pole=Vector((.9,-.2,-.3))
    candidates=[];parent=r.pose.bones[f'B_{sd}_Clavicle'].matrix.to_3x3()@side.rel['Arm']
    fingeraxis=(sum((rest[f'B_{sd}_Finger{i}'].translation for i in range(5)),Vector())/5-rest[f'B_{sd}_Hand'].translation).normalized();fingeraxis=rest[f'B_{sd}_Hand'].to_3x3().inverted()@fingeraxis
    for roll in range(-180,180,15):
     rh=Quaternion(axis,math.radians(roll)).to_matrix()@desired
     T=target if sd=='R' else free+rh@side.grip_hand if held==0 else (free+rh@side.grip_hand).lerp(grip+axis*.10,held)
     direction=(T-r.pose.bones[f'B_{sd}_UpperArm'].head).normalized()
     for pd in range(-180,180,15):
      pole2=Quaternion(direction,math.radians(pd))@pole;sol=side.pose_anatomical(T,rh,pole2)
      sw,tw=IK.swing_twist_deg(((sol['Rf']@side.rel['Hand']).inverted()@rh).to_quaternion(),fingeraxis)
      upper=IK.swing_twist_deg((parent.inverted()@sol['Ra']).to_quaternion(),side.uA)[1]
      flex=math.degrees((sol['E']-sol['S']).angle(sol['W']-sol['E']))
      cost=sw*.3+abs(tw)*.12+abs(upper)*.08+abs(pd)*.01
      cost+=max(0,sw-65)**2*100000+max(0,abs(tw)-80)**2*100000+max(0,abs(upper)-80)**2*100000+max(0,flex-145)**2*100000+sol['miss']**2*1e8
      if .8<sol['E'].z<1.5:cost+=max(0,.24-abs(sol['E'].x))**2*20000
      # Temporal branch choice is solved globally below.
      
      if sd=='L':
       fm=sol['Rf'].to_4x4();fm.translation=sol['E'];bm=fm@buckleChain;center=r.pose.bones['B_Spine1'].head;head=r.pose.bones['B_Head'].head+Vector((0,0,.07))
       for bv in localB:
        pt=bm@bv;torso=((pt.x-center.x)/.21)**2+((pt.y-center.y)/.155)**2+((pt.z-center.z)/.30)**2;skull=((pt.x-head.x)/.10)**2+((pt.y-head.y)/.10)**2+((pt.z-head.z)/.15)**2
        cost+=(max(0,1-torso)**2+max(0,1-skull)**2)*200000
      # Keep arms outside a conservative torso envelope while approaching/recovering.
      spine=r.pose.bones['B_Spine1'].head
      for pt in [sol['E'],sol['W'],(sol['E']+sol['W'])*.5]:
       if spine.z-.22<pt.z<spine.z+.19:
        rad=((pt.x-spine.x)/.235)**2+((pt.y-spine.y)/.155)**2
        cost+=max(0,1-rad)**2*100000
      edge=ease(frame/12)*(1-ease((frame-63)/13));cost+=(1-edge)*math.degrees(2*math.acos(min(1,abs(world[f'B_{sd}_Hand'].to_quaternion().dot(rh.to_quaternion())))))**2*20
      candidates.append((cost,sol))
    candidates=sorted(candidates,key=lambda x:x[0])[:96];options[sd].append({'cost':np.array([v[0]for v in candidates]),'q':np.array([list(v[1]['Ra'].to_quaternion())for v in candidates]),'h':np.array([list(v[1]['Rh'].to_quaternion())for v in candidates]),'solutions':[v[1]for v in candidates]});sol=candidates[0][1];side.apply(sol);prevRh[sd]=sol['Rh'].to_quaternion();previous[sd]=sol['Ra'].to_quaternion()
    for bn,ch,helper,factor in [('Forearm','Hand','ForearmTwist',.6),('UpperArm','Forearm','UpperArmTwist',-.5)]:
     pb=r.pose.bones[f'B_{sd}_{bn}'];cb=r.pose.bones[f'B_{sd}_{ch}'];ax=(pb.bone.matrix_local.inverted()@cb.bone.head_local).normalized();dq=(pb.matrix.inverted()@cb.matrix).to_quaternion()@(pb.bone.matrix_local.inverted()@cb.bone.matrix_local).to_quaternion().inverted()if bn=='Forearm'else pb.matrix_basis.to_quaternion();tw=(2*math.atan2(Vector((dq.x,dq.y,dq.z)).dot(ax),dq.w)+math.pi)%(2*math.pi)-math.pi;r.pose.bones[f'B_{sd}_{helper}'].rotation_quaternion=Quaternion(ax,max(-math.radians(80),min(math.radians(80),tw*factor)))
   for n,q in G['finger_local'].items():r.pose.bones[n].rotation_quaternion=Quaternion(q)
   close=ease((frame-18)/13)*(1-ease((frame-46)/15))
   for n,q in closed.items():r.pose.bones[n].rotation_quaternion=base[n].to_quaternion().slerp(q,close)
   # Panels follow the pelvis while retaining their accepted shape; swing them clear of the raised thigh.
   for n in ['ClothFront','ClothBack']:
    if n in r.pose.bones:r.pose.bones[n].rotation_quaternion=Quaternion((1,0,0),math.radians(float(curve(frame,[0,-40,-18,-18,0]if n=='ClothFront'else[0,25,18,18,0]))))@base[n].to_quaternion()
   bpy.context.view_layer.update();poses.append({b.name:b.matrix_basis.copy()for b in r.pose.bones})
   r.pose.bones['B_L_ForearmTwist'].matrix_basis=base['B_L_ForearmTwist']
   if frame in [0,21,34,43,76]:report['poses'][str(frame)]={'pelvis':list(r.pose.bones['B_Pelvis'].head),'head':list(r.pose.bones['B_Head'].head),'right_grip':list(r.pose.bones['Spear'].head)}
  # Choose continuous branches across the whole clip, rather than greedily jumping between IK solutions.
  selected={}
  for sd in 'RL':
   rows=options[sd];cost=rows[0]['cost'].copy();back=[]
   for f in range(1,77):
    prev=rows[f-1];cur=rows[f]
    dots=np.clip(abs(prev['q']@cur['q'].T),0,1);angles=np.degrees(2*np.arccos(dots))
    hdots=np.clip(abs(prev['h']@cur['h'].T),0,1);hangles=np.degrees(2*np.arccos(hdots))
    transition=angles**2*.9+hangles**2*.8+np.maximum(0,angles-16)**2*50+np.maximum(0,hangles-16)**2*50
    values=cost[:,None]+transition;parent=np.argmin(values,axis=0);back.append(parent);cost=cur['cost']+values[parent,np.arange(len(parent))]
   ids=[int(np.argmin(cost))]
   for parent in reversed(back):ids.append(int(parent[ids[-1]]))
   selected[sd]=list(reversed(ids))
  final=[]
  for frame,row in enumerate(poses):
   for n,m in row.items():r.pose.bones[n].matrix_basis=m
   bpy.context.view_layer.update()
   for sd in 'RL':
    sol=options[sd][frame]['solutions'][selected[sd][frame]];sides[sd].apply(sol)
    if frame in [21,34,43,55]:print('DP_SELECTED',frame,sd,options[sd][frame]['cost'][selected[sd][frame]],sol['sw'],sol['tw'],flush=True)
    fb=r.data.bones[f'B_{sd}_Forearm'];hb=r.data.bones[f'B_{sd}_Hand'];ub=r.data.bones[f'B_{sd}_UpperArm'];ax=(fb.matrix_local.inverted()@hb.head_local).normalized();rel=(r.pose.bones[fb.name].matrix.inverted()@r.pose.bones[hb.name].matrix).to_quaternion();rr=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion();tw=IK.swing_twist_deg(rel@rr.inverted(),ax)[1];r.pose.bones[f'B_{sd}_ForearmTwist'].rotation_quaternion=Quaternion(ax,math.radians(max(-80,min(80,(.3 if sd=='L'else .6)*tw))))
    ax=(ub.matrix_local.inverted()@fb.head_local).normalized();tw=IK.swing_twist_deg(r.pose.bones[ub.name].rotation_quaternion,ax)[1];r.pose.bones[f'B_{sd}_UpperArmTwist'].rotation_quaternion=Quaternion(ax,math.radians(-.5*tw))
   r.pose.bones['B_L_ForearmTwist'].matrix_basis=base['B_L_ForearmTwist'];bpy.context.view_layer.update();final.append({b.name:b.matrix_basis.copy()for b in r.pose.bones})
  poses=final
 a=bpy.data.actions['Attack'];bpy.data.actions.remove(a);a=bpy.data.actions.new('Attack');a.use_fake_user=True;r.animation_data.action=a
 prev={}
 for frame,row in enumerate(poses):
  for n,m in row.items():
   b=r.pose.bones[n];b.matrix_basis=m;b.rotation_mode='QUATERNION';q=b.rotation_quaternion
   if n in prev and prev[n].dot(q)<0:q.negate()
   prev[n]=q.copy();b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=frame,group=n)
   if n=='B_Pelvis':b.keyframe_insert('location',frame=frame,group=n)
 for bag in bags(a):
  for fc in bag.fcurves:
   for k in fc.keyframe_points:k.interpolation='LINEAR'
 a.use_frame_range=True;a.frame_start=0;a.frame_end=76
 death=bpy.data.actions['Death']
 for bag in bags(death):
  for fc in bag.fcurves:
   for k in fc.keyframe_points:k.co.x*=.5;k.handle_left.x*=.5;k.handle_right.x*=.5
 death.use_frame_range=True;death.frame_start=0;death.frame_end=80
 C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'))
 if level==0:
  bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_natm.blend'));C.activate('Attack',0);common.workbench_clay(sc,True)
  out=P/'review/round3_motion';out.mkdir(exist_ok=True)
  for f in [0,15,21,28,34,43,60,76]:
   C.activate('Attack',f/48);common.render_views(str(out/f'attack_{f:02}'),.95,2.7,views=('front','left','three_quarter'),resolution=(550,650),target=(0,-.15))
(P/'review/round3_motion_authoring.json').write_text(json.dumps(report,indent=2))
