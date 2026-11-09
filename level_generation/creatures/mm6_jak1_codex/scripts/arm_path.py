"""Choose a continuous anatomical elbow plane over each whole library action."""
import math,json
import numpy as np
from mathutils import Vector,Quaternion
import bpy
from staff_ik import swing_twist_deg

def refine_arm_paths(allposes,apply,pose,world,L,R,P):
 report={};theta=np.arange(72)*math.tau/72
 for role in ['Standing','Walking','Hit','Fidget','Attack','Cast','Death']:
  if role not in allposes:continue
  frames=allposes[role];indices=list(range(0,len(frames),5))
  if indices[-1]!=len(frames)-1:indices.append(len(frames)-1)
  for side,obj in [('R',R),('L',L)]:
   samples=[];last_u=None;base=None
   handbone=bpy.data.objects['Rig'].data.bones[f'B_{side}_Hand'];knuckles=sum((bpy.data.objects['Rig'].data.bones[f'B_{side}_Finger{i}'].head_local for i in range(5)),Vector())/5;handaxis=(handbone.matrix_local.inverted()@knuckles).normalized()
   for fi in indices:
    apply(frames[fi]);hm=world(f'B_{side}_Hand');Rh=hm.to_3x3();G=hm@obj.grip_hand;S=world(f'B_{side}_UpperArm').translation;u=(hm.translation-S).normalized()
    if base is None:
     base=world(f'B_{side}_Forearm').translation-S;base-=u*base.dot(u);base.normalize()
    else:base=last_u.rotation_difference(u)@base;base-=u*base.dot(u);base.normalize()
    last_u=u.copy();parent=world(f'B_{side}_Clavicle').to_3x3()@obj.rel['Arm'];axis=(Rh@obj.axis_hand).normalized();qs=[];cost=[];rolls=[];wrists=[]
    for a in theta:
     r=obj.pose_anatomical(G,Rh,Quaternion(u,float(a))@base);q=(parent.inverted()@r['Ra']).to_quaternion();v=Vector((q.x,q.y,q.z));roll=abs((math.degrees(2*math.atan2(v.dot(obj.uA),q.w))+180)%360-180);pen=.001*roll*roll+max(0,roll-60)**2*.08
     if roll>58:pen+=1e8+(roll-58)**2
     sw,tw=swing_twist_deg(((r['Rf']@obj.rel['Hand']).inverted()@Rh).to_quaternion(),handaxis);pen+=.002*(sw*sw+tw*tw)+1e5*(max(0,sw-65)**2+max(0,abs(tw)-40)**2);wrists.append([sw,tw])
     if role=='Death':pen+=1e7*max(0,.055-r['E'].z,.045-r['W'].z)**2
     if (side=='R' and (role!='Death' or fi/240<.25)) or (role=='Attack' and .3<=fi/240<=1.1):
      depth=0
      for t in [.1,.3,.5,.7,.9]:
       d=r['E'].lerp(r['W'],t)-G;depth=max(depth,.063-.018*t-(d-axis*d.dot(axis)).length)
      pen+=1e7*max(0,depth)**2
     if role!='Death':
      center=(world('B_Pelvis').translation+world('B_Neck').translation)*.5;up=(world('B_Neck').translation-world('B_Pelvis').translation).normalized();right=(world('B_L_UpperArm').translation-world('B_R_UpperArm').translation).normalized();forward=up.cross(right).normalized();depth=0
      for t in [.1,.3,.5,.7,.9]:
       point=r['E'].lerp(r['W'],t)-center;ell=(point.dot(right)/.21)**2+(point.dot(forward)/.17)**2+(point.dot(up)/.31)**2;depth=max(depth,.12*(1-math.sqrt(ell)))
      pen+=1e7*max(0,depth)**2
     qs.append([tuple(r['Ra'].to_quaternion()),tuple(r['Rf'].to_quaternion())]);cost.append(pen);rolls.append(roll)
    samples.append({'base':base.copy(),'u':u.copy(),'q':np.array(qs),'cost':np.array(cost),'roll':rolls,'wrist':wrists})
   costs=samples[0]['cost'].copy();backs=[]
   # Equal hand positions can have two elbow solutions; future frames choose the smooth branch before a singularity.
   for prev,cur in zip(samples,samples[1:]):
    da=np.degrees(2*np.arccos(np.clip(np.abs(prev['q'][:,0]@cur['q'][:,0].T),0,1)));df=np.degrees(2*np.arccos(np.clip(np.abs(prev['q'][:,1]@cur['q'][:,1].T),0,1)));cap={'Standing':10,'Walking':12,'Hit':18,'Fidget':18,'Death':35,'Cast':45,'Attack':50}[role];total=costs[:,None]+.025*da*da+.015*df*df+1e8*((da>cap)|(df>cap));back=total.argmin(axis=0);costs=total[back,np.arange(72)]+cur['cost'];backs.append(back)
   path=[int(costs.argmin())]
   for back in reversed(backs):path.append(int(back[path[-1]]))
   path.reverse();angles=np.unwrap(theta[path]);angles=np.convolve(np.pad(angles,(2,2),mode='edge'),np.array([1,4,6,4,1])/16,mode='valid');maxroll=max(s['roll'][k] for s,k in zip(samples,path));report[f'{role}_{side}']={'max_upper_roll_deg':maxroll,'samples':len(samples)}
   report[f'{role}_{side}']['wrist_flex_max_deg']=max(s['wrist'][k][0]for s,k in zip(samples,path));report[f'{role}_{side}']['wrist_roll_max_deg']=max(abs(s['wrist'][k][1])for s,k in zip(samples,path))
   cursor=0
   for fi in range(len(frames)):
    while cursor+1<len(indices)-1 and fi>indices[cursor+1]:cursor+=1
    j=cursor;blend=(fi-indices[j])/max(1,indices[j+1]-indices[j]);apply(frames[fi]);hm=world(f'B_{side}_Hand');S=world(f'B_{side}_UpperArm').translation;u=(hm.translation-S).normalized();base=samples[j]['u'].rotation_difference(u)@samples[j]['base'];angle=angles[j]*(1-blend)+angles[j+1]*blend;r=obj.pose_anatomical(hm@obj.grip_hand,hm.to_3x3(),Quaternion(u,float(angle))@base);obj.apply(r);frames[fi]=pose()
   print('ARM PATH',role,side,report[f'{role}_{side}'],flush=True)
 (P/'work/round2_arm_paths.json').write_text(json.dumps(report,indent=2))
