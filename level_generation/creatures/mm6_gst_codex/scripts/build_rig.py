"""Fit source-frame joints, real skeletal digits and independent shroud/sleeve chains."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_bar1_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/fitted_body.blend'))
body=bpy.data.objects['Body'];me=body.data
for v in me.vertices:
 if me.attributes['part'].data[v.index].value==0 and 1.755<v.co.z<1.91 and abs(v.co.x+.014)<.145 and v.co.y<.015:v.co.y=.025
C=np.array([v.co[:] for v in me.vertices]);PA=np.array([v.value for v in me.attributes['part'].data]);E=np.array([e.vertices[:] for e in me.edges]);NV=len(C)
J=json.loads((P/'work/joints_final.json').read_text())['joints'];SRC=json.loads((P/'work/source_rest.json').read_text());B={}
def norm(v):return v/max(np.linalg.norm(v),1e-10)
def add(n,h,t,parent=None,r=None):
 h=np.array(h);t=np.array(t);y=norm(t-h)
 if r is None:
  x=norm(np.cross(y,[0,0,1])) if abs(y[2])<.95 else np.array([1.,0,0]);r=np.column_stack([x,y,np.cross(x,y)])
 B[n]={'head':h.tolist(),'tail':t.tolist(),'parent':parent,'rot':np.array(r).tolist()}
add('Root',[0,0,0],[0,0,.1]);add('BodyRoot',J['Pelvis'],np.array(J['Pelvis'])+[0,0,.1],'Root')
child={'Pelvis':'Spine','Spine':'Spine1','Spine1':'Spine2','Spine2':'Neck','Neck':'Head'}
for sd in ['L','R']:child.update({sd+'_Clavicle':sd+'_UpperArm',sd+'_UpperArm':sd+'_Forearm',sd+'_Forearm':sd+'_Hand'})
order=['Pelvis','Spine','Spine1','Spine2','Neck','Head']+[sd+'_'+x for sd in ['L','R'] for x in ['Clavicle','UpperArm','Forearm','Hand']]
for sh in order:
 n='B_'+sh;h=np.array(J[sh]);cs=child.get(sh);t=np.array(J[cs]) if cs else h+[0,0,.08];r=Matrix(SRC[n]['rot'])
 if cs:r=(Vector(SRC['B_'+cs]['head'])-Vector(SRC[n]['head'])).rotation_difference(Vector(t-h)).to_matrix()@r
 add(n,h,t,SRC[n]['parent'] if sh!='Pelvis' else 'BodyRoot',r)
digits={};digit_parts={'L':[11,5,12,8],'R':[1,3,15,9]};palm_parts={'L':4,'R':6}
for sd,sign in [('L',1),('R',-1)]:
 wr=np.array(J[sd+'_Hand']);points={}
 for f,pn in enumerate(digit_parts[sd],1):
  c=C[PA==pn];dist=np.linalg.norm(c-wr,axis=1);base=c[dist<=np.quantile(dist,.08)].mean(0);tip=c[dist>=np.quantile(dist,.95)].mean(0)
  points[f]=np.array([base,base+(tip-base)*.42,base+(tip-base)*.76,tip])
 c=C[PA==palm_parts[sd]];tip=c[c[:,2]<np.quantile(c[:,2],.05)].mean(0)
 base=np.array([sign*.578,-.028,1.480]);points[0]=np.array([base,base+(tip-base)*.50,tip])
 fo=norm(points[2][0]-wr);to=points[1][0]-points[4][0];to=norm(to-fo*(to@fo));palm=norm(np.cross(fo,to));palm*=1 if palm[1]<0 else -1
 def frame(f,t):
  f=norm(f);t=norm(t-f*(t@f));return np.column_stack([f,t,np.cross(f,t)])
 fs=np.array(SRC['B_'+sd+'_Finger2']['head'])-SRC['B_'+sd+'_Hand']['head'];ts=np.array(SRC['B_'+sd+'_Finger1']['head'])-SRC['B_'+sd+'_Finger4']['head'];swing=frame(fo,to)@frame(fs,ts).T
 B['B_'+sd+'_Hand']['rot']=(swing@np.array(SRC['B_'+sd+'_Hand']['rot'])).tolist()
 for f,pts in points.items():
  names=[]
  for i in range(len(pts)-1):
   n=f'B_{sd}_Finger{f}_{i}';y=norm(pts[i+1]-pts[i]);x=norm(np.cross(y,palm));add(n,pts[i],pts[i+1],'B_'+sd+'_Hand' if i==0 else names[-1],np.column_stack([x,y,np.cross(x,y)]));names.append(n)
  digits[sd+str(f)]={'bones':names,'pts':pts.tolist(),'part':palm_parts[sd] if f==0 else digit_parts[sd][f-1]}
# Chains follow measured robe cross sections; broad panels remain coupled by angular interpolation.
cloth=[];axis=np.array([-.014,.075]);levels=np.array([1.46,1.16,.86,.56,.26,.015])
for i,(x,y) in enumerate([(-.60,-.25),(.60,-.25),(.60,.70),(-.60,.70)]):
 a=math.atan2(x-axis[0],y-axis[1]);pts=[[x,y,float(z)] for z in levels];names=[]
 for k in range(5):
  n=f'Shroud_{i:02}_{k}';add(n,pts[k],pts[k+1],'B_Pelvis' if k==0 else names[-1]);names.append(n)
 cloth.append({'angle':a,'pts':pts,'bones':names})
sleeves=[]
for sd,sign in [('L',1),('R',-1)]:
 for j,y in enumerate([-.014,.13]):
  pts=[[sign*.37,y,1.71],[sign*.405,y+.015,1.47],[sign*.425,y+.04,1.22],[sign*.36,y+.07,.99]]
  names=[]
  for k in range(3):
   n=f'Sleeve_{sd}_{j}_{k}';add(n,pts[k],pts[k+1],'B_'+sd+'_UpperArm' if k==0 else names[-1]);names.append(n)
  sleeves.append({'side':sd,'index':j,'pts':pts,'bones':names})
add('Jaw',[-.014,.025,2.028],[-.014,-.045,1.99],'B_Head')
arm=bpy.data.armatures.new('GhostSkeleton');rig=bpy.data.objects.new('Rig',arm);bpy.context.collection.objects.link(rig);bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for n,b in B.items():
 e=arm.edit_bones.new(n);r=np.array(b['rot']);h=np.array(b['head']);e.head=h;e.tail=h+r[:,1]*max(.015,np.linalg.norm(np.array(b['tail'])-h));e.align_roll(Vector(r[:,2]));e.use_deform=n not in ('Root','BodyRoot')
 if b['parent']:e.parent=arm.edit_bones[b['parent']]
bpy.ops.object.mode_set(mode='OBJECT')
names=list(B);ni={n:i for i,n in enumerate(names)};W=np.zeros((NV,len(names)))
def smooth(v):v=np.clip(v,0,1);return v*v*(3-2*v)
def stations(ids,s,stations,ns):
 for k,n in enumerate(ns):W[ids,ni[n]]=np.interp(s,stations,np.eye(len(ns))[k])
sp=['B_'+x for x in ['Pelvis','Spine','Spine1','Spine2','Neck','Head']];ids=np.where(PA==0)[0];stations(ids,C[ids,2],[J[n[2:]][2] for n in sp],sp)
for sd,sign,fore,palm in [('L',1,7,4),('R',-1,13,6)]:
 sh=np.array(J[sd+'_UpperArm']);el=np.array(J[sd+'_Forearm']);wr=np.array(J[sd+'_Hand']);u=norm(el-sh);f=norm(wr-el)
 ids=np.where((PA==0)&(C[:,0]*sign>.15)&(C[:,2]>1.50)&(C[:,2]<1.89))[0];blend=smooth((C[ids,0]*sign-.15)/.15)*smooth((C[ids,2]-1.50)/.15)
 weights=np.zeros((len(ids),len(names)));weights[:,ni['B_'+sd+'_UpperArm']]=1;W[ids]=W[ids]*(1-blend[:,None])+weights*blend[:,None]
 W[PA==fore]=0;W[PA==fore,ni['B_'+sd+'_Forearm']]=1
 W[PA==palm]=0;W[PA==palm,ni['B_'+sd+'_Hand']]=1
 for fnum in range(5):
  d=digits[sd+str(fnum)];pts=np.array(d['pts']);ns=d['bones'];delta=pts[-1]-pts[0];s=((C-pts[0])@delta)/(delta@delta)
  if fnum:ids=np.where(PA==d['part'])[0]
  else:ids=np.where((PA==palm)&(C[:,1]<-.020)&(C[:,2]<1.487))[0]
  W[ids]=0;gn=(['B_'+sd+'_Hand']+ns) if fnum==0 else ns;st=[-.1,.15,.72] if fnum==0 else [.15,.57,.88];stations(ids,s[ids],st,gn)
# Lower shroud replaces all arm/leg weights, including the back train.
ids=np.where((PA==0)&(C[:,2]<1.51))[0]
for v in ids:
 tx=np.clip((C[v,0]+.60)/1.20,0,1);ty=np.clip((C[v,1]+.25)/.95,0,1);shares=[(1-tx)*(1-ty),tx*(1-ty),tx*ty,(1-tx)*ty];cw=np.zeros(len(names))
 for idx,share in enumerate(shares):
  c=cloth[idx];z=(levels[:-1]+levels[1:])/2
  for k,n in enumerate(c['bones']):cw[ni[n]]+=share*np.interp(C[v,2],z[::-1],np.eye(5)[k][::-1])
 blend=1-smooth((C[v,2]-1.40)/.11);W[v]=W[v]*(1-blend)+cw*blend
# Hanging sleeve strips share front/back chains, with a wide smooth shoulder transition.
for sd,sign in [('L',1),('R',-1)]:
 ids=np.where((PA==0)&(C[:,0]*sign>.25)&(C[:,2]>.98)&(C[:,2]<1.78))[0];cs=[c for c in sleeves if c['side']==sd]
 for v in ids:
  ww=np.zeros(len(names));mix=np.clip((C[v,1]+.014)/.144,0,1)
  for c,share in zip(cs,[1-mix,mix]):
   st=np.array([q[2] for q in c['pts']]);z=(st[:-1]+st[1:])/2
   for k,n in enumerate(c['bones']):ww[ni[n]]+=share*np.interp(C[v,2],z[::-1],np.eye(3)[k][::-1])
  strength=smooth((C[v,0]*sign-.25)/.10)*(1-smooth((C[v,2]-1.64)/.14))*smooth((C[v,2]-.98)/.18)
  W[v]=W[v]*(1-strength)+ww*strength
ids=np.where(PA>=100)[0];W[ids]=0
for v in ids:
 t=smooth((C[v,2]-1.86)/.11);W[v,ni['B_Head']]=t;W[v,ni['B_Spine2']]=1-t
jaw=(PA==100)&(np.abs(C[:,0]+.014)<.059)&(C[:,1]<.008)&(C[:,2]>1.974)&(C[:,2]<2.014)
for v in np.where(jaw)[0]:
 b=smooth((C[v,2]-1.974)/.012)*(1-smooth((C[v,2]-2.005)/.009));W[v]*=1-b;W[v,ni['Jaw']]+=b
assert np.min(W.sum(1))>.99,np.where(W.sum(1)<.99)
# Smooth only connected cloth to avoid seams across tiny triangles; bone pieces stay rigid.
adj=[[] for _ in C]
for a,b in E:adj[a].append(int(b));adj[b].append(int(a))
for _ in range(10):
 old=W.copy()
 for v in np.where(PA==0)[0]:
  if adj[v]:W[v]=.7*old[v]+.3*old[adj[v]].mean(0)
keep=np.argsort(W,axis=1)[:,-8:];out=np.zeros_like(W);np.put_along_axis(out,keep,np.take_along_axis(W,keep,axis=1),axis=1);W=out/out.sum(1)[:,None]
body.vertex_groups.clear()
for n in names:
 g=body.vertex_groups.new(name=n)
 for v in np.where(W[:,ni[n]]>1e-6)[0]:g.add([int(v)],float(W[v,ni[n]]),'REPLACE')
body.parent=rig;mod=body.modifiers.new('Skin','ARMATURE');mod.object=rig
for b in rig.pose.bones:b.rotation_mode='QUATERNION'
assert len(B)<=128,len(B)
D={'bones':B,'digits':digits,'cloth':cloth,'sleeves':sleeves,'joints':J,'weights':{'unweighted':0,'max_influences':8}}
(P/'work/rig.json').write_text(json.dumps(D,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'))
# Armature overlay is rendered as thin rods to expose fitted joints.
common.workbench_clay(bpy.context.scene)
for n,b in B.items():
 if n.startswith('Shroud') or n.startswith('Sleeve') or n in ('Root','BodyRoot'):continue
 a=Vector(b['head']);z=Vector(b['tail']);bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=.002,depth=(z-a).length,location=(a+z)/2);rod=bpy.context.object;rod.rotation_euler=(z-a).to_track_quat('Z','Y').to_euler()
 mat=bpy.data.materials.get('RigRods') or bpy.data.materials.new('RigRods');mat.diffuse_color=(1,.09,.01,1);rod.data.materials.append(mat)
body.show_transparent=True
common.render_views(str(P/'review/rig_hand_L'),1.47,.37,views=('front','left','back'),resolution=(650,650),target=(.61,-.02))
print('RIG',len(B),'bones',len(C),'vertices')
