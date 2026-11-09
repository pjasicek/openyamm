"""Round 8: preserve accepted upper-body motion; source-profile height and natural flight."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round7/running_author.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene

def act(a):
 rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def sample(a,f):
 act(a);scene.frame_set(int(f),subframe=f%1)
 return {b.name:(b.rotation_quaternion.copy(),b.location.copy())for b in rig.pose.bones}
def apply(p):
 act(None)
 for n,(q,l) in p.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].location=l
 bpy.context.view_layer.update()
rest=sample(bpy.data.actions['Standing'],0);standing=rig.pose.bones['B_Pelvis'].head.z
old=[sample(bpy.data.actions['Running'],i/4)for i in range(97)]
# Measure fore/aft sole patch direction on the unchanged accepted body.
body=bpy.data.objects['Body'];sole_axes={}
for sd in 'LR':
 pts=[v.co for v in body.data.vertices if (v.co.x>0)==(sd=='L')and v.co.z<.06]
 yy=np.array([v.y for v in pts]);heel=sum((v for v in pts if v.y>=np.quantile(yy,.7)),Vector())/sum(yy>=np.quantile(yy,.7));toe=sum((v for v in pts if v.y<=np.quantile(yy,.3)),Vector())/sum(yy<=np.quantile(yy,.3))
 sole_axes[sd]=rig.data.bones[f'B_{sd}_Foot'].matrix_local.to_3x3().inverted()@(toe-heel)
sole={};flat={};lens={}
for sd in 'LR':
 n=f'B_{sd}_Foot';M=rig.data.bones[n].matrix_local
 sole[sd]=[M.inverted()@v.co for v in body.data.vertices if (v.co.x>0)==(sd=='L')and v.co.z<.008]
 apply(rest);W=rig.pose.bones[n].matrix;normal=(W.to_3x3()@M.to_3x3().inverted())@Vector((0,0,1));flat[sd]=normal.rotation_difference(Vector((0,0,1)))@W.to_quaternion()
 H,K,A=[rig.data.bones[f'B_{sd}_{k}'].head_local for k in ['Thigh','Calf','Foot']];lens[sd]=((K-H).length,(A-K).length)
def world(n):return rig.matrix_world@rig.pose.bones[n].matrix
def aim(n,child,direction):
 M=world(n);cur=world(child).translation-M.translation;R=cur.normalized().rotation_difference(direction.normalized()).to_matrix().to_4x4();t=M.translation.copy();M=R@M;M.translation=t;rig.pose.bones[n].matrix=rig.matrix_world.inverted()@M;bpy.context.view_layer.update()
def solve(sd,T,Q):
 th,ca,ft=[f'B_{sd}_{k}'for k in ['Thigh','Calf','Foot']];H=world(th).translation;a,b=lens[sd];d=(T-H).length
 assert abs(a-b)<d<a+b,('reach',i,sd,d,a+b)
 u=(T-H).normalized();v=Vector((0,-1,0));v=(v-u*v.dot(u)).normalized();c=(a*a+d*d-b*b)/(2*a*d);K=H+a*(u*c+v*math.sqrt(max(0,1-c*c)))
 aim(th,ca,K-H);M=world(ca);M.translation=K;rig.pose.bones[ca].matrix=rig.matrix_world.inverted()@M;bpy.context.view_layer.update();aim(ca,ft,T-K)
 M=Q.to_matrix().to_4x4();M.translation=T;rig.pose.bones[ft].matrix=rig.matrix_world.inverted()@M;bpy.context.view_layer.update()

source=json.loads((P/'review/round8/source_probe.json').read_text())['anim_library/mixamo/Standard Run.fbx'];rows=source['samples'][:96]
legscale=sum(lens['L'])/sum(np.linalg.norm(np.array(source['rest'][a])-source['rest'][b])for a,b in [('LeftUpLeg','LeftLeg'),('LeftLeg','LeftFoot')])
# Keep the source's vertical amplitude and two-step timing, remove key noise via four harmonics.
z=np.array([r['Hips'][2]for r in rows]);coef=np.fft.rfft(z)/len(z);coef[5:]=0
# The source is Warrok-retargeted and hunched even in bind pose. Rebase its vertical excursion
# onto this dwarf's upright Standing height rather than transferring Warrok's static hip offset.
def height_raw(t):return coef[0].real+sum(2*(coef[k]*np.exp(2j*np.pi*k*t)).real for k in range(1,5))
source_height=height_raw
source_values=np.array([source_height(t)for t in np.arange(192)/192])
# Match the source low point to mid-stance and its high point to flight. Expanding
# its ~28% stance to 35% needs the same timing warp for hips as for feet.
def warped_height(t):
 ph=t%.5;source_t=.32+(.28*ph/.35 if ph<.35 else .28+.22*(ph-.35)/.15)
 return (source_height(source_t)+source_height(source_t+.5))/2
warp=np.array([warped_height(t)for t in np.arange(192)/192]);hc=np.fft.rfft(warp)/192;hc[7:]=0
wv=lambda t:hc[0].real+sum(2*(hc[k]*np.exp(2j*np.pi*k*t)).real for k in range(1,7))
wr=np.array([wv(t)for t in np.linspace(0,1,1001)]);wmin,wmax=wr.min(),wr.max()
zmin,zmax=source_values.min(),source_values.max()
def height_raw(t):return zmin+(wv(t)-wmin)*(zmax-zmin)/(wmax-wmin)
# Source left landing ~0.32, toe-off ~0.60. Symmetric fitted stance is 35%.
phase_offset=.10;source_offset=.32
hipbase=standing*.925
# Average the two source legs' lift profiles in their matching phases, retaining source flight amplitude.
lifts=[]
for sd in ['Left','Right']:
 ankle=np.array([r[sd+'Foot'][2]for r in rows]);toe=np.array([r[sd+'ToeBase'][2]for r in rows]);lifts.append(np.maximum(0,np.minimum(ankle-ankle.min(),toe-toe.min())))
curve=(lifts[0]+np.roll(lifts[1],-48))/2
curve=sum(np.roll(curve,k)*w for k,w in zip(range(-2,3),[.1,.2,.4,.2,.1]))
def interp(t):
 x=(t%1)*96;j=int(x);u=x-j
 # Periodic cubic Hermite interpolation, no corners between source samples.
 y0,y1=curve[j%96],curve[(j+1)%96];m0=(curve[(j+1)%96]-curve[(j-1)%96])/2;m1=(curve[(j+2)%96]-curve[j%96])/2
 return (2*u**3-3*u*u+1)*y0+(u**3-2*u*u+u)*m0+(-2*u**3+3*u*u)*y1+(u**3-u*u)*m1
stance=.35
# Source swing runs from ~0.60 to the next heel strike at 1.32.
def lift_at(u):
 phase=.35+.65*u
 source_t=(.60+.22*(phase-.35)/.15 if phase<.5 else .82+.28*(phase-.5)/.35 if phase<.85 else 1.10+.22*(phase-.85)/.15)
 v=max(0,interp(source_t)-((1-u)*interp(.60)+u*interp(.32)))
 # Smooth departure/arrival over just the source endpoint samples.
 return legscale*v*min(1,u/.04)**2*min(1,(1-u)/.04)**2

# Measure the accepted runtime sole, including its rounded heel/toe edges.
sys.path.insert(0,str(P.parent/'claude_shared/gates'))
from run_gates import Glb
glb=Glb(P/'work/round8_before/export/mm6_dwa1.glb');attrs=glb.doc['meshes'][0]['primitives'][0]['attributes'];vv=glb.accessor(attrs['POSITION'])
for sd in 'LR':
 M=rig.data.bones[f'B_{sd}_Foot'].matrix_local
 sole[sd]=[M.inverted()@Vector((float(v[0]),float(-v[2]),float(v[1])))for v in vv if (v[0]>0)==(sd=='L')and v[1]<.06]
def foot_orientation(sd,phase):
 if phase<stance:
  u=phase/stance;pitch=-8*(1-min(1,u/.16))**2+22*max(0,(u-.65)/.35)**2
 else:
  u=(phase-stance)/(1-stance);pitch=22*(1-u)-8*u
 Q=Quaternion(Vector((1,0,0)),math.radians(pitch))@flat[sd]
 v=Q@sole_axes[sd];yaw=math.atan2(v.y,v.x)
 return Quaternion((0,0,1),-math.pi/2-yaw-(math.radians(1)if sd=='R'else 0))@Q
# Integrate rolling contact about the actual lowest sole point. Re-anchoring each
# frame to a flat boot causes creep along rounded soles; integrate instead.
plant_grid=np.linspace(0,stance,337);offsets={}
for sd in 'LR':
 qs=[foot_orientation(sd,float(t))for t in plant_grid];D=[Vector((0,0,0))]
 for q0,q1 in zip(qs,qs[1:]):
  pivot=min(sole[sd],key=lambda v:((q0@v).z+(q1@v).z));delta=q1@pivot-q0@pivot
  d=D[-1]-delta;d.z=0;D.append(d)
 offsets[sd]=np.array([list(d)for d in D])
def foot_target(sd,phase,stride):
 travel=stride*stance
 if phase<stance:
  u=phase/stance;y=-travel/2+stride*phase;lift=0
  D=Vector(tuple(np.interp(phase,plant_grid,offsets[sd][:,k])for k in range(3)))
 else:
  u=(phase-stance)/(1-stance);S=u**3*(10-15*u+6*u*u)
  y=travel/2-travel*S+stride*(1-stance)*(u*(1-u)**10-(1-u)*u**10)
  lift=lift_at(u);D=Vector(offsets[sd][-1]*(1-S))
 Q=foot_orientation(sd,phase)
 T=Vector((.135 if sd=='L'else -.135,y,.004+lift-min((Q@v).z for v in sole[sd])))+D
 return T,Q
# Find the natural-height reach envelope. Only stride changes; never lower/clamp the pelvis.
hips=[]
for i,p in enumerate(old):
 apply(p);phase=(i/96-phase_offset)%1;pel=world('B_Pelvis');pel.translation.z=hipbase+legscale*(height_raw(phase)-zmin)
 rig.pose.bones['B_Pelvis'].matrix=rig.matrix_world.inverted()@pel;bpy.context.view_layer.update();hips.append({sd:world(f'B_{sd}_Thigh').translation.copy()for sd in 'LR'})
def reachable(stride):
 return all((foot_target(sd,(i/96-phase_offset+(0 if sd=='L'else .5))%1,stride)[0]-hips[i][sd]).length<sum(lens[sd])-.003 for i in range(96)for sd in 'LR')
lo,hi=0.,2.6
assert reachable(lo),'Height/flight trajectory unreachable even at zero stride'
for _ in range(40):
 mid=(lo+hi)/2
 if reachable(mid):lo=mid
 else:hi=mid
stride=math.floor(lo*.98*1000)/1000;binding=round(stride/1.55,6);stride=binding*1.55
print('SOURCE SCALE / NATURAL STRIDE / HIP RANGE',legscale,stride,hipbase,hipbase+legscale*(zmax-zmin),flush=True)
frames=[];knees={s:[]for s in 'LR'}
for i,p in enumerate(old):
 apply(p);phase=(i/96-phase_offset)%1;pel=world('B_Pelvis');pel.translation.z=hipbase+legscale*(height_raw(phase)-zmin)
 rig.pose.bones['B_Pelvis'].matrix=rig.matrix_world.inverted()@pel;bpy.context.view_layer.update()
 for sd in 'LR':
  T,Q=foot_target(sd,(phase+(0 if sd=='L'else .5))%1,stride);solve(sd,T,Q)
  bpy.context.view_layer.update()
  h,k,a=[world(f'B_{sd}_{n}').translation for n in ['Thigh','Calf','Foot']];knees[sd].append(180-math.degrees((h-k).angle(a-k)))
 frames.append({b.name:(b.rotation_quaternion.copy(),b.location.copy())for b in rig.pose.bones})
(P/'review/round8/fitting.json').write_text(json.dumps({'source':'anim_library/mixamo/Standard Run.fbx','standing_pelvis_m':standing,'source_leg_scale':legscale,'source_hip_range_m':[float(z.min()),float(z.max())],'filtered_source_hip_range_m':[zmin,zmax],'target_pelvis_base_m':hipbase,'stride_length':binding,'runtime_run_stride_m':stride,'duration_s':.8,'stance_fraction_per_foot':stance,'phase_offset':phase_offset,'source_offset':source_offset,'peak_source_derived_swing_m':max(lift_at(u)for u in np.linspace(0,1,1001)),'knee_range_deg':{s:[min(v),max(v)]for s,v in knees.items()},'method':'Source four-harmonic hip profile rebased to 92.5% Standing; source paired foot-lift curve at leg scale; fixed 35% planted stance; stride fitted to natural-height reach, not pelvis fitted to stride. Upper-body local poses copied from accepted round7.'},indent=2))
frames[-1]=frames[0]
act(None);bpy.data.actions.remove(bpy.data.actions['Running']);a=bpy.data.actions.new('Running');a.use_fake_user=True;prev={}
worlds=[]
for i,p in enumerate(frames):
 apply(p);worlds.append({b.name:[list(r)for r in rig.matrix_world@b.matrix]for b in rig.pose.bones})
 act(a)
 for n,(q,l)in p.items():
  pb=rig.pose.bones[n]
  if n in prev and q.dot(prev[n])<0:q=-q
  prev[n]=q;pb.rotation_quaternion=q;pb.location=l
  pb.keyframe_insert('rotation_quaternion',frame=i/4);pb.keyframe_insert('location',frame=i/4)
a.use_frame_range=True;a.frame_start=0;a.frame_end=24
for lay in a.layers:
 for strip in lay.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
scene.render.fps=30
(P/'work/round8/running_world.json').write_text(json.dumps({'times':list(np.linspace(0,.8,97)),'poses':worlds,'rest':{b.name:[list(r)for r in rig.matrix_world@b.matrix_local]for b in rig.data.bones}}))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round8/running_author.blend'))
print('STANDARD RUN RETARGET READY')
