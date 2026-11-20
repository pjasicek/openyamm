"""Native-informed heavy gestures and distance-driven rigid roller rotation."""
import bpy,math,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_rat_claude/scripts'))
from posing import reset,rotate_world,two_bone_ik,aim_bone
rig=bpy.data.objects['JuggernautRig'];body=bpy.data.objects['Body']
FPS=48
CLIPS={'Standing':(2,True),'Walking':(1,True),'Attack':(1.25,False),'Hit':(1.125,False),'Fidget':(.625,False),'Death':(.75,False),'Dead':(1/48,False)}
roller_info=json.loads((P/'work/rig_info.json').read_text())['rollers']
roller_points={}
for r in roller_info:
 group=body.vertex_groups[r['name']].index
 roller_points[r['name']]=np.array([v.co[:] for v in body.data.vertices if any(g.group==group and g.weight>.99 for g in v.groups)])-np.array(r['centre'])
FRAGMENTS=json.loads((P/'work/fragments.json').read_text()) if (P/'work/fragments.json').exists() else []
mound_limits=[]
for r in FRAGMENTS:
 if r['kind']=='band':continue
 q=Quaternion(r['rotation']);p=np.array([q@Vector(v) for v in r['points']])*.7
 profile=math.exp(-float(r['end'][0]**2+r['end'][1]**2)/.035)
 mound_limits.append((60/199-float(np.ptp(p[:,2]))-.003)/profile)
CORPSE_MOUND=max(0,min(mound_limits)) if mound_limits else 0
def ease(x):x=max(0,min(1,x));return x*x*(3-2*x)
def curve(keys,t):
 for i in range(len(keys)-1):
  a,b=keys[i:i+2]
  if t<=b[0]:return np.array(a[1:])*(1-ease((t-a[0])/(b[0]-a[0])))+np.array(b[1:])*ease((t-a[0])/(b[0]-a[0]))
 return np.array(keys[-1][1:])
def shift(name,delta):
 b=rig.pose.bones[name];m=b.matrix.copy();m.translation+=Vector(delta);b.matrix=m;bpy.context.view_layer.update()
def arm(side,target,pole,tip=None):
 upper,fore,hand=[f'{part}_{side}' for part in ['UpperArm','Forearm','Hand']]
 two_bone_ik(rig,upper,fore,target,pole)
 if tip:aim_bone(rig,hand,tip)
def upper_pose(name,t):
 if name in ['Standing','Walking']:
  phase=2*math.pi*t/(2 if name=='Standing' else 1)
  rotate_world(rig,'Chest','X',.6*math.sin(phase));rotate_world(rig,'Head','Z',1.2*math.sin(phase) if name=='Standing' else 0)
 elif name=='Attack':
  x,y,z,lean=curve([[0,.327,-.047,.507,0],[.25,.46,.015,.80,-3],[.50,.30,-.06,.97,-4],[.85,.22,-.14,.82,3],[1,.105,-.205,.625,8],[1.065,.105,-.205,.625,9],[1.25,.327,-.047,.507,0]],t)
  rotate_world(rig,'Chest','X',lean);rotate_world(rig,'Head','X',-lean*.45)
  for side,s in [('L',1),('R',-1)]:
   tip=(s*.052,-.27,.61) if .95<t<1.10 else None
   arm(side,(s*x,y,z),(s*.6,.06,.65),tip)
 elif name=='Hit' or name=='Death':
  x,y,z,lean=curve([[0,.327,-.047,.507,0],[.125,.21,-.12,.78,-5],[.25,.27,-.075,.89,-9],[.375,.21,-.12,.78,-5],[.50,.27,-.075,.89,-9],[.70,.22,-.015,1.015,-11],[.90,.26,-.015,1.05,-9],[1.125,.327,-.047,.507,0]],t)
  rotate_world(rig,'Chest','X',lean);rotate_world(rig,'Head','X',-lean*.3)
  for side,s in [('L',1),('R',-1)]:arm(side,(s*x,y,z),(s*.55,.05,.8))
 elif name=='Fidget':
  e=math.sin(math.pi*t/.625)**2
  rotate_world(rig,'Chest','X',2*e);rotate_world(rig,'Head','X',4*e)
  for side,s in [('L',1),('R',-1)]:
   rotate_world(rig,f'UpperArm_{side}','X',-10*e);rotate_world(rig,f'Hand_{side}','X',8*e)
def pose(name,t):
 reset(rig)
 for b in rig.pose.bones:
  if b.name.startswith('D_') or b.name=='FlashControl':b.scale=(.00001,)*3
 upper_pose(name,t)
 if name in CLIPS:
  for r in roller_info:
   n=r['name'];angle=2*math.pi*t if name=='Walking' else 0;q=Quaternion((1,0,0),angle);rest=rig.data.bones[n].matrix_local
   m=(q.to_matrix()@rest.to_3x3()).to_4x4();rot=np.array([q@Vector(p) for p in roller_points[n]])*.94
   c=Vector(r['centre']);c.z=-float(rot[:,2].min())+(.001 if name=='Walking' else 0);m.translation=c;rig.pose.bones[n].matrix=m;rig.pose.bones[n].scale=(.94,1,.94)
 if name=='Attack' and 'FlashControl' in rig.pose.bones:
  amount=max(0,1-abs(t-1.02)/.075)
  pb=rig.pose.bones['FlashControl'];m=pb.matrix.copy();m.translation=(rig.pose.bones['Hand_L'].tail+rig.pose.bones['Hand_R'].tail)/2+Vector((0,-.015,0));pb.matrix=m
  pb.scale=(max(.00001,amount),)*3
 if name in ['Death','Dead'] and (name=='Dead' or t>=.25):
  rig.pose.bones['Root'].scale=(.00001,)*3
  elapsed=.5 if name=='Dead' else t-.25;travel=ease(elapsed/.5)
  for r in FRAGMENTS:
   pb=rig.pose.bones[r['bone']];q=Quaternion().slerp(Quaternion(r['rotation']),travel)
   c=np.array(r['centre']);end=np.array(r['end']);rot=np.array([q@Vector(v) for v in r['points']])
   mound=travel*CORPSE_MOUND*math.exp(-float(end[0]**2+end[1]**2)/.035)
   shrink=1 if r['kind']=='band' else 1-.30*travel
   floor=-float(rot[:,2].min())*shrink+.003+mound
   if r['kind']=='band':floor=-float(rot[:,2].min())+.025;end[1]=-.05
   position=c*(1-travel)+end*travel;position[2]=max(floor,c[2]-9*elapsed*elapsed)
   if elapsed>=.5:position[2]=floor
   m=(q.to_matrix()@rig.data.bones[pb.name].matrix_local.to_3x3()).to_4x4();m.translation=Vector(position);pb.matrix=m;pb.scale=(shrink,)*3
 bpy.context.view_layer.update()
def co():
 all=[]
 for o in [o for o in bpy.data.objects if o.type=='MESH']:
  e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();all.extend([tuple(e.matrix_world@v.co) for v in m.vertices]);e.to_mesh_clear()
 return np.array(all)
