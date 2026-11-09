"""Complete native right-hand swipe, hit and stone-fragment death with airborne support."""
import bpy,bmesh,json,sys,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion,kdtree
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_hands_v2.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];head=bpy.data.objects['Head'];scene=bpy.context.scene;scene.render.fps=30
rng=np.random.default_rng(541)
def setact(a):
 rig.animation_data_create();rig.animation_data.action=a
 if a and a.slots:rig.animation_data.action_slot=a.slots[0]
def sample(a,t):
 setact(a);f=t*30;scene.frame_set(math.floor(f),subframe=f%1)
 return {pb.name:(pb.rotation_quaternion.copy(),pb.location.copy(),pb.scale.copy()) for pb in rig.pose.bones}
def apply(pose):
 setact(None)
 for pb in rig.pose.bones:
    pb.rotation_mode='QUATERNION';pb.rotation_quaternion,pb.location,pb.scale=pose[pb.name]
 bpy.context.view_layer.update()
def new_action(name,end):
 a=bpy.data.actions.new(name);a.use_fake_user=True;a.use_frame_range=True;a.frame_start=0;a.frame_end=end*30;return a
def write(a,t,previous):
 setact(a)
 for pb in rig.pose.bones:
    q=pb.rotation_quaternion.copy()
    if pb.name in previous and q.dot(previous[pb.name])<0:q=-q
    previous[pb.name]=q.copy();pb.rotation_quaternion=q
    for key in ['rotation_quaternion','location','scale']:pb.keyframe_insert(key,frame=t*30,group=pb.name)
 setact(None)
def rotate(n,axis,angle):
 pb=rig.pose.bones[n];local=rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector(axis);pb.rotation_quaternion=pb.rotation_quaternion@Quaternion(local,math.radians(angle))
flight=bpy.data.actions['Flight']
# Native flight lets the shins trail nearly horizontally and the toes hang down.
flight_frames=sorted({float(k.co.x) for layer in flight.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves for k in fc.keyframe_points})
leg_samples=[(frame,sample(flight,frame/30)) for frame in flight_frames]
for frame,pose in leg_samples:
 apply(pose);setact(flight)
 for sd in ['L','R']:
    name=f'B_{sd}_Calf';rotate(name,(1,0,0),25);rig.pose.bones[name].keyframe_insert('rotation_quaternion',frame=frame,group=name)
base=sample(flight,0);apply(base)
# Native a/b -> c/d: right claw opens sideways, cuts across the front, then recovers with left-arm balance.
# Depth is reconstructed because only the front attack view is stored; elbow poles stay ahead of the wings.
setact(None);bpy.data.actions.remove(bpy.data.actions['Attack']);duration=1.5
attack=new_action('Attack',duration);previous={}
keys=np.array([
 # time, right wrist offset from shoulder, left wrist offset, chest yaw, lean, root sway
 [0,   -.269,-.121,-.397, .239,-.172,-.384,  0,0,0],
 [.18, -.37,-.18,-.20,   .25,-.17,-.36,    -4,0,-.012],
 [.48, -.46,-.20,-.06,   .24,-.19,-.34,   -12,-2,-.025],
 [.62, -.38,-.28,.03,    .23,-.23,-.30,    -8,0,-.015],
 [.75, -.05,-.48,-.02,   .26,-.25,-.19,     8,5,.018],
 [.88,  .26,-.39,-.22,   .29,-.27,-.08,    14,8,.025],
 [1.06,-.10,-.30,-.40,   .18,-.32,-.07,     7,4,.015],
 [1.28,-.23,-.15,-.40,   .07,-.28,-.17,    -3,1,-.008],
 [1.5, -.269,-.121,-.397, .239,-.172,-.384,  0,0,0],
],dtype=float)
def anchor(t):
 j=int(np.clip(np.searchsorted(keys[:,0],t,side='right')-1,0,len(keys)-2));a,b=keys[j:j+2];dt=b[0]-a[0];u=float(np.clip((t-a[0])/dt,0,1))
 m0=np.zeros(9) if j==0 else (keys[j+1,1:]-keys[j-1,1:])/(keys[j+1,0]-keys[j-1,0])
 m1=np.zeros(9) if j+2==len(keys) else (keys[j+2,1:]-keys[j,1:])/(keys[j+2,0]-keys[j,0])
 return (2*u**3-3*u*u+1)*a[1:]+(u**3-2*u*u+u)*dt*m0+(-2*u**3+3*u*u)*b[1:]+(u**3-u*u)*dt*m1

def aim(name,child,target):
 pb=rig.pose.bones[name];current=rig.pose.bones[child].head-pb.head;desired=target-pb.head
 q=current.rotation_difference(desired);m=(q@pb.matrix.to_quaternion()).to_matrix().to_4x4();m.translation=pb.head
 location=pb.location.copy();pb.matrix=m;pb.location=location;pb.scale=(1,1,1);bpy.context.view_layer.update()
def arm(side,offset,chest):
 upper,fore,hand=[f'B_{side}_{part}' for part in ['UpperArm','Forearm','Hand']]
 shoulder=rig.pose.bones[upper].head.copy();target=shoulder+chest@Vector(offset)
 ul=(rig.data.bones[fore].head_local-rig.data.bones[upper].head_local).length
 fl=(rig.data.bones[hand].head_local-rig.data.bones[fore].head_local).length
 direction=target-shoulder;length=direction.length;assert abs(ul-fl)+.005<length<ul+fl-.002,(side,length,ul+fl)
 direction.normalize()
 # Transport the ready elbow plane: a fixed pole nearly aligns with the rising wrist and flips the elbow.
 ready_direction=(rig.pose.bones[hand].head-shoulder).normalized()
 pole=ready_direction.rotation_difference(direction)@(rig.pose.bones[fore].head-shoulder)
 pole-=direction*direction.dot(pole);assert pole.length>.005;pole.normalize()
 along=(ul*ul-fl*fl+length*length)/(2*length);elbow=shoulder+direction*along+pole*math.sqrt(max(0,ul*ul-along*along))
 aim(upper,fore,elbow);aim(fore,hand,target)
 assert (rig.pose.bones[hand].head-target).length<.0001

def arm_twists(side):
 fb,hb,ub=[rig.data.bones[f'B_{side}_{n}'] for n in ['Forearm','Hand','UpperArm']]
 seg=(fb.matrix_local.inverted()@hb.head_local).normalized();rel=(rig.pose.bones[fb.name].matrix.inverted()@rig.pose.bones[hb.name].matrix).to_quaternion();rest=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion()
 ua=(ub.matrix_local.inverted()@fb.head_local).normalized()
 for name,axis,q,factor in [(f'B_{side}_ForearmTwist',seg,rel@rest.inverted(),.7),(f'B_{side}_UpperArmTwist',ua,rig.pose.bones[ub.name].rotation_quaternion,-.45)]:
  angle=2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w);angle=(angle+math.pi)%(2*math.pi)-math.pi
  rig.pose.bones[name].rotation_quaternion=Quaternion(axis,angle*factor)

for t in np.linspace(0,duration,91):
 pose=sample(flight,float(t% .75));apply(pose)
 if 0<t<duration:
  values=anchor(t);envelope=min(1,t/.16,(duration-t)/.22);envelope=envelope*envelope*(3-2*envelope)
  yaw,lean,sway=values[6:];rotate('B_Spine1',(0,0,1),yaw*.6);rotate('B_Spine2',(0,0,1),yaw*.4);rotate('B_Spine1',(1,0,0),lean);rotate('B_Neck',(0,0,1),-yaw*.4);rotate('B_Head',(1,0,0),-lean*.45)
  pb=rig.pose.bones['B_Pelvis'];m=pb.matrix.copy();m.translation+=Vector((sway,-.015*max(0,lean)/8,0));pb.matrix=m;bpy.context.view_layer.update()
  chest=(rig.pose.bones['B_Spine2'].matrix@rig.data.bones['B_Spine2'].matrix_local.inverted()).to_3x3().normalized()
  for side,offset in [('R',values[:3]),('L',values[3:6])]:
   shoulder=rig.pose.bones[f'B_{side}_UpperArm'].head;ready=chest.inverted()@(rig.pose.bones[f'B_{side}_Hand'].head-shoulder)
   arm(side,ready.lerp(Vector(offset),envelope),chest)
   curl=max(0,1-abs(t-.78)/.28)*(10 if side=='R' else 3)
   for pb in rig.pose.bones:
    if pb.name.startswith(f'B_{side}_Finger'):pb.rotation_quaternion=pb.rotation_quaternion@Quaternion((1,0,0),math.radians(curl*.5 if 'Finger0' in pb.name else curl))
   arm_twists(side)
 write(attack,float(t),previous)
(P/'work/attack_v4/anchors.json').write_text(json.dumps({'duration':duration,'impact':.75,'columns':['time','R_x','R_y','R_z','L_x','L_y','L_z','chest_yaw_degrees','forward_lean_degrees','root_sway_m'],'keys':keys.tolist()},indent=2))
# Native recoil: open raised arms, head recoil, a modest rearward body shift, then recover within 0.75 s.
hit=new_action('Hit',.75);previous={}
for t in sorted(set([i/30 for i in range(23)]+[.75])):
 pose=sample(flight,t% .75);apply(pose)
 if t<.16:u=t/.16;amount=u*u*(3-2*u)
 else:u=(t-.16)/.59;amount=1-u*u*(3-2*u)
 rotate('B_Spine1',(1,0,0),-9*amount);rotate('B_Head',(1,0,0),7*amount)
 for sd,sg in [('L',1),('R',-1)]:
    rotate(f'B_{sd}_UpperArm',(0,1,0),-sg*65*amount);rotate(f'B_{sd}_Forearm',(1,0,0),-20*amount)
    rotate(f'B_{sd}_Hand',(1,0,0),-10*amount)
 pb=rig.pose.bones['B_Pelvis'];m=pb.matrix.copy();m.translation+=Vector((0,.05*amount,0));pb.matrix=m
 write(hit,t,previous)
setact(None)
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
# Cell fragments use the actual silhouette. Keep the face, hands and feet recognizable among the shards.
co=np.array([v.co[:] for v in body.data.vertices]);wing=np.array([sum(g.weight for g in v.groups if body.vertex_groups[g.group].name.startswith('W_')) for v in body.data.vertices])>.25
assigned=np.zeros(len(co),bool);chunks=[]
def owned(v,terms):return sum(g.weight for g in v.groups if any(t in body.vertex_groups[g.group].name for t in terms))
def cap_and_triangulate(obj):
 bm=bmesh.new();bm.from_mesh(obj.data);boundary=[e for e in bm.edges if e.is_boundary]
 if boundary:bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
 bmesh.ops.triangulate(bm,faces=bm.faces[:]);bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);bm.to_mesh(obj.data);bm.free()
def exact_piece(name,obj,keep,ratio=1):
 dup=obj.copy();dup.data=obj.data.copy();dup.parent=None;dup.modifiers.clear();dup.vertex_groups.clear();dup.name=name;bpy.context.scene.collection.objects.link(dup)
 bm=bmesh.new();bm.from_mesh(dup.data);bm.verts.ensure_lookup_table();bad=[v for v in bm.verts if v.index not in keep]
 if bad:bmesh.ops.delete(bm,geom=bad,context='VERTS')
 bm.to_mesh(dup.data);bm.free();cap_and_triangulate(dup)
 bpy.ops.object.select_all(action='DESELECT');dup.select_set(True);bpy.context.view_layer.objects.active=dup
 if ratio<1:
    mod=dup.modifiers.new('ShardReduction','DECIMATE');mod.ratio=ratio;bpy.ops.object.modifier_apply(modifier=mod.name)
 chunks.append((dup,'head' if obj==head else 'limb'))
for sd in ['L','R']:
 for part,terms in [('Hand',[f'B_{sd}_Hand',f'B_{sd}_Finger']),('Foot',[f'B_{sd}_Foot',f'B_{sd}_Toe'])]:
    mask=np.array([owned(v,terms)>.75 for v in body.data.vertices]);assert mask.sum()>20;assigned|=mask
    exact_piece(sd+part+'Shard',body,set(np.where(mask)[0]),.6)
exact_piece('HeadShard',head,set(range(len(head.data.vertices))),.30)
body.data.calc_loop_triangles();uv=body.data.uv_layers.active.data;triangles=list(body.data.loop_triangles)
uvtree=kdtree.KDTree(len(triangles))
for i,tr in enumerate(triangles):uvtree.insert(Vector(co[list(tr.vertices)].mean(0)),i)
uvtree.balance()
def hull_piece(points,name,kind):
 bm=bmesh.new();cent=points.mean(0)
 # The original wings are thin; their broken edges need a small stone thickness.
 if kind=='wing':points=np.vstack([points+[0,.012,0],points-[0,.012,0]])
 if len(points)>60:points=points[np.linspace(0,len(points)-1,60).astype(int)]
 for p in points:bm.verts.new(p)
 bm.verts.ensure_lookup_table();bmesh.ops.convex_hull(bm,input=bm.verts[:],use_existing_faces=False)
 unused=[v for v in bm.verts if not v.link_faces]
 if unused:bmesh.ops.delete(bm,geom=unused,context='VERTS')
 bmesh.ops.triangulate(bm,faces=bm.faces[:]);bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:]);mesh=bpy.data.meshes.new(name);bm.to_mesh(mesh);bm.free()
 obj=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(obj);obj.data.materials.append(body.data.materials[0]);outuv=mesh.uv_layers.new(name='UVMap').data
 for p in mesh.polygons:
    _,ti,_=uvtree.find(p.center);source=triangles[ti]
    for li,sl in zip(p.loop_indices,source.loops):outuv[li].uv=uv[sl].uv
 chunks.append((obj,kind))
def partition(ids,count,prefix,kind):
 points=co[ids];centres=[points[np.argmin(points[:,2])]]
 for _ in range(count-1):
    dist=np.min([np.sum((points-c)**2,axis=1) for c in centres],axis=0);centres.append(points[np.argmax(dist)])
 centres=np.array(centres)
 for _ in range(12):
    labels=np.argmin(np.sum((points[:,None,:]-centres[None,:,:])**2,axis=2),axis=1)
    for i in range(count):
        if np.any(labels==i):centres[i]=points[labels==i].mean(0)
 for i in range(count):
    pts=points[labels==i]
    if len(pts)>=5:hull_piece(pts,prefix+str(i),kind)
partition(np.where(~wing&~assigned)[0],14,'BodyShard','body')
for sd,sg in [('L',1),('R',-1)]:partition(np.where(wing&(co[:,0]*sg>0))[0],10,sd+'WingShard','wing')
assert 30<=len(chunks)<=45,len(chunks)
# Independent fragment roots let the living skeleton disappear without moving the fragments.
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');ed=rig.data.edit_bones
records=[]
for i,(obj,kind) in enumerate(chunks):
 points=np.array([v.co[:] for v in obj.data.vertices]);centre=points.mean(0);name=f'D_{i:02d}';b=ed.new(name);b.head=centre;b.tail=centre+[0,0,.06]
 axis=rng.normal(size=3);axis/=np.linalg.norm(axis)
 if kind=='wing':q=Quaternion((1,0,0),math.pi/2+rng.uniform(-.35,.35))@Quaternion((0,0,1),rng.uniform(-1,1))
 elif kind=='head':q=Quaternion((1,0,0),math.radians(30))@Quaternion((0,0,1),.25)
 else:q=Quaternion(axis,float(rng.uniform(-2,2)))
 end=np.array([centre[0]*.45,centre[1]*.2,0])+rng.uniform(-.09,.09,3);end[2]=0
 if kind=='head':end[:2]=[.015,-.04]
 records.append({'bone':name,'kind':kind,'object':obj,'centre':centre,'points':points-centre,'end':end,'rotation':q})
bpy.ops.object.mode_set(mode='OBJECT');assert len(rig.data.bones)<=128
for r in records:
 obj=r['object'];obj.vertex_groups.clear();g=obj.vertex_groups.new(name=r['bone']);g.add(list(range(len(obj.data.vertices))),1,'REPLACE');obj.parent=rig;mod=obj.modifiers.new('Armature','ARMATURE');mod.object=rig
 for f in obj.data.polygons:f.use_smooth=False
# One rubble mesh, retaining body/head materials and their texture layouts.
bpy.ops.object.select_all(action='DESELECT')
for obj,kind in chunks:obj.select_set(True)
bpy.context.view_layer.objects.active=chunks[0][0];bpy.ops.object.join();rubble=bpy.context.object;rubble.name='Rubble'
# Explicit reset keys on every live action prevent death state leaking back into a new action.
for act in [flight,attack,hit]:
 setact(act)
 for pb in rig.pose.bones:
    if pb.name.startswith('D_'):continue
    pb.scale=(1,1,1)
    for frame in [0,float(act.frame_end)]:pb.keyframe_insert('scale',frame=frame,group=pb.name)
    if act==flight and pb.name!='B_Pelvis':
        pb.location=base[pb.name][1]
        for frame in [0,float(act.frame_end)]:pb.keyframe_insert('location',frame=frame,group=pb.name)
 for r in records:
    pb=rig.pose.bones[r['bone']];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion();pb.location=(0,0,0);pb.scale=(.00001,)*3
    for frame in [0,float(act.frame_end)]:
        for key in ['location','rotation_quaternion','scale']:pb.keyframe_insert(key,frame=frame,group=pb.name)
# Add fragment entries to the living baseline.
base.update({r['bone']:(Quaternion(),Vector((0,0,0)),Vector((.00001,)*3)) for r in records})
death=new_action('Death',.95);previous={};final=None
for t in sorted(set([i/30 for i in range(29)]+[.099,.10,.95])):
 apply(base)
 if t>=.10:
    for pb in rig.pose.bones:
        if not pb.name.startswith('D_'):pb.rotation_quaternion=Quaternion();pb.location=(0,0,0)
    rig.pose.bones['B_Pelvis'].scale=(.00001,)*3
    root=rig.pose.bones['B_Pelvis'];rest=rig.data.bones[root.name];root.location=rest.matrix_local.to_3x3().inverted()@(-rest.head_local)
 elapsed=max(0,t-.10)
 for r in records:
    pb=rig.pose.bones[r['bone']];centre=r['centre'];travel=min(1,elapsed/.67);smooth=travel*travel*(3-2*travel);q=Quaternion().slerp(r['rotation'],smooth)
    rotated=np.array([q@Vector(v) for v in r['points']]);floor=-float(rotated[:,2].min())+.006
    if r['kind']=='head':floor+=.10
    landing=math.sqrt(max(0,2*(centre[2]-floor)/18));fall=max(floor,centre[2]-9*elapsed*elapsed)
    if elapsed>landing and elapsed<landing+.18:fall+=.035*math.sin(math.pi*(elapsed-landing)/.18)*math.exp(-8*(elapsed-landing))
    if t>=.90:fall=floor
    position=centre*(1-smooth)+r['end']*smooth;position[2]=fall
    rest=rig.data.bones[pb.name].matrix_local.to_3x3();m=(q.to_matrix()@rest).to_4x4();m.translation=Vector(position);pb.matrix=m;pb.scale=(1 if t>=.10 else .00001,)*3
 write(death,t,previous)
 if t==.95:final={pb.name:(pb.rotation_quaternion.copy(),pb.location.copy(),pb.scale.copy()) for pb in rig.pose.bones}
# Hold the settled rubble; tiny nonzero bone scale avoids singular normal matrices.
dead=new_action('Dead',1/30);previous={}
for t in [0,1/30]:apply(final);write(dead,t,previous)
setact(flight);scene.frame_set(0)
manifest={'fps':30,'bone_count':len(rig.data.bones),'fragment_count':len(records),'clips':{'Flight':{'duration':.75,'loop':True},'Attack':{'duration':duration,'loop':False,'impact':.75,'source':'Native six-frame attack study; locally authored right-hand swipe, body sway and left-arm balance'},'Hit':{'duration':.75,'loop':False},'Death':{'duration':.95,'loop':False,'fragment_switch':.10},'Dead':{'duration':1/30,'loop':False,'held':True}},'aliases':{'standing':'Flight','walk':'Flight','attack':'Attack','attack2':'Attack','fidget':'Attack','hit':'Hit','death':'Death','dead':'Dead'}}
(P/'work/animation_manifest.json').write_text(json.dumps(manifest,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/animations.blend'))
rows=[]
for name,times in [('Attack',[0,.125,7/48,8/48,.3,.62,.75,.88,1.28])]:
 for view in ['front','left','three_quarter']:
    row=[]
    for i,t in enumerate(times):
        sample(bpy.data.actions[name],t);path=common.render_views(str(P/f'review/{name}_{view}_{i}'),1.45,3.5,views=(view,),resolution=(480,480))[0];row.append([path,f'{name} {view} {t:.3f}s'])
    rows.append(row)
(P/'review/final_action_frames.json').write_text(json.dumps(rows));print('FINAL_ANIMATIONS',manifest)
