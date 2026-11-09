"""Fit the rigid bow/arrow and skin the moving string. Authoring only; runtime attachments split later."""
import bpy,bmesh,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
bpy.data.actions.remove(bpy.data.actions['Running'])
G=json.loads((P/'work/grip_pose.json').read_text());C=Vector(G['handle_centre_hand_local']);U=Vector(G['handle_axis_hand_local'])
def action(name):
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];return a
def world(n):return rig.pose.bones[n].matrix.copy()
def key(n,f,location=False,scale=False):
 b=rig.pose.bones[n];b.rotation_mode='QUATERNION';b.keyframe_insert('rotation_quaternion',frame=f)
 if location:b.keyframe_insert('location',frame=f)
 if scale:b.keyframe_insert('scale',frame=f)
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
# The original carry pose deliberately keeps the bow almost edge-on, as arc1sta0 does.
# At full draw the wrist rolls the bow upright, with an arrow rest just above the grip.
a=action('Attack')
for f in range(53):
 sc.frame_set(f);w=smooth((f-18)/10)*smooth((46-f)/7)
 h=world('B_L_Hand');c=h@C;n=rig.pose.bones['B_R_Finger1'].head;d=(n-c).normalized();up=h.to_3x3()@U
 desired=(Vector((0,0,1))-d*d.z).normalized();desired=(desired+d*.065).normalized();q=Quaternion().slerp(up.rotation_difference(desired),w)
 t=h.translation.copy();h=q.to_matrix().to_4x4()@h;h.translation=t;rig.pose.bones['B_L_Hand'].matrix=h;bpy.context.view_layer.update();key('B_L_Hand',f)
sc.frame_set(36);c=world('B_L_Hand')@C;n=rig.pose.bones['B_R_Finger1'].head;d=c-n;yaw=-math.atan2(d.x,-d.y)
for f in range(53):
 sc.frame_set(f);m=world('B_Spine');t=m.translation.copy();w=smooth(f/22)*smooth((52-f)/10);m=Matrix.Rotation(yaw*w,4,'Z')@m;m.translation=t;rig.pose.bones['B_Spine'].matrix=m;bpy.context.view_layer.update();key('B_Spine',f)
print('TARGET_YAW_CORRECTION',math.degrees(yaw))
# A separate palm-forward cast; left hand retains the carry pose.
a=action('Standing');sc.frame_set(0);standing={b.name:(b.rotation_quaternion.copy(),b.location.copy())for b in rig.pose.bones}
def aim(n,direction):
 m=world(n);t=m.translation.copy();cur=(m.to_3x3()@Vector((0,1,0))).normalized();m=cur.rotation_difference(direction.normalized()).to_matrix().to_4x4()@m;m.translation=t;rig.pose.bones[n].matrix=m;bpy.context.view_layer.update()
def arm_ik(target):
 sh,el,wr=[rig.pose.bones['B_R_'+n].head.copy()for n in ['UpperArm','Forearm','Hand']];a=(el-sh).length;b=(wr-el).length;u=(target-sh).normalized();d=min((target-sh).length,(a+b)*.995);v=Vector((-1,0,0));v=(v-u*v.dot(u)).normalized();cs=(a*a+d*d-b*b)/(2*a*d);k=sh+a*(u*cs+v*math.sqrt(max(0,1-cs*cs)));aim('B_R_UpperArm',k-sh);aim('B_R_Forearm',target-rig.pose.bones['B_R_Forearm'].head)
# Cache all solved poses first, avoiding key feedback while building the cast.
cast=[]
rig.animation_data.action=None
for f in range(46):
 for n,(q,l)in standing.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].location=l
 bpy.context.view_layer.update();w=smooth(f/24)*smooth((45-f)/9);wr=rig.pose.bones['B_R_Hand'].head.copy();target=wr.lerp(Vector((-.22,-.56,1.39)),w);arm_ik(target)
 hand=rig.pose.bones['B_R_Hand'];old=hand.rotation_quaternion.copy()
 # Source-frame palm normal and finger direction define the open palm, preserving local rig calibration.
 rest=rig.data.bones['B_R_Hand'].matrix_local;long=(rig.data.bones['B_R_Finger2'].head_local-rest.translation).normalized();across=(rig.data.bones['B_R_Finger1'].head_local-rig.data.bones['B_R_Finger4'].head_local).normalized();normal=long.cross(across).normalized()
 if normal.x<0:normal=-normal
 local_long=rest.to_3x3().inverted()@long;local_normal=rest.to_3x3().inverted()@normal;basis=Matrix((local_long,local_normal,local_long.cross(local_normal))).transposed();desired=Matrix((Vector((0,0,1)),Vector((0,-1,0)),Vector((1,0,0)))).transposed();hm=(desired@basis.inverted()).to_4x4();hm.translation=hand.head;hand.matrix=hm;bpy.context.view_layer.update();hand.rotation_quaternion=old.slerp(hand.rotation_quaternion,w)
 for b in rig.pose.bones:
  if b.name.startswith('B_R_Finger'):b.rotation_quaternion=standing[b.name][0].slerp(Quaternion(),w)
 cast.append({b.name:(b.rotation_quaternion.copy(),b.location.copy())for b in rig.pose.bones})
a=action('Cast')
# Remove the old 36-frame channels completely.
rig.animation_data.action=None;bpy.data.actions.remove(a);a=bpy.data.actions.new('Cast');a.use_fake_user=True;rig.animation_data.action=a
for f,pose in enumerate(cast):
 for n,(q,l)in pose.items():
  b=rig.pose.bones[n];b.rotation_quaternion=q;b.location=l;key(n,f,n=='B_Pelvis')
a.use_frame_range=True;a.frame_start=0;a.frame_end=45
# Bow orientation is fixed in the left hand, fitted at the release frame.
a=action('Attack');sc.frame_set(36);h=world('B_L_Hand');c=h@C;z=(h.to_3x3()@U).normalized();n=rig.pose.bones['B_R_Finger1'].head;y=n-c;y=(y-z*y.dot(z)).normalized();x=y.cross(z).normalized();mat=Matrix((x,y,z)).transposed().to_4x4();mat.translation=c;local=h.inverted()@mat;rest=rig.data.bones['B_L_Hand'].matrix_local@local
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
def bone(n,m,parent):
 b=rig.data.edit_bones.new(n);b.head=m.translation;b.tail=b.head+m.to_3x3().col[1]*.05;b.align_roll(m.to_3x3().col[2]);b.parent=rig.data.edit_bones.get(parent);return b
bone('Bow',rest,'B_L_Hand')
for name,pt in [('BowTop',(0,.187,.545)),('BowBottom',(0,.187,-.545)),('BowNock',(0,.187,.085))]:
 m=rest.copy();m.translation=rest@Vector(pt);bone(name,m,'Bow')
bone('Arrow',Matrix(),'B_Pelvis');bone('Socket_Arrow_Release',Matrix(),'B_Pelvis')
# Palm socket 3 cm in front of the open right palm.
h=rig.data.edit_bones['B_R_Hand'];m=h.matrix.copy();m.translation=h.head+(rig.data.edit_bones['B_R_Finger2'].head-h.head)*.55;bone('Socket_Palm_Right',m,'B_R_Hand')
bpy.ops.object.mode_set(mode='OBJECT')
with bpy.data.libraries.load(str(P/'work/bow_clay.blend'),link=False)as(src,dst):dst.objects=['BowAsset']
prop=dst.objects[0];bpy.context.collection.objects.link(prop);parts=prop.data.attributes['bow_part'];arrowverts={v for f in prop.data.polygons if parts.data[f.index].value>=3 for v in f.vertices};vg=prop.vertex_groups.new(name='Bow');ag=prop.vertex_groups.new(name='Arrow')
for v in prop.data.vertices:
 if v.index in arrowverts:v.co.x-=.10;v.co*=1.22;ag.add([v.index],1,'REPLACE')
 else:v.co=rest@v.co;vg.add([v.index],1,'REPLACE')
prop.parent=rig;mod=prop.modifiers.new('Rig','ARMATURE');mod.object=rig
# Two continuous string halves, deforming only at their endpoints.
vs=[];fs=[];labels=[]
for name,pt in [('BowTop',(0,.187,.545)),('BowNock',(0,.187,.085)),('BowBottom',(0,.187,-.545))]:
 for j in range(6):vs.append(tuple(rest@(Vector(pt)+Vector((math.cos(j*math.pi/3)*.0012,math.sin(j*math.pi/3)*.0012,0)))));labels.append(name)
for k in (0,6):
 for j in range(6):fs.append((k+j,k+(j+1)%6,k+6+(j+1)%6,k+6+j))
me=bpy.data.meshes.new('BowString');me.from_pydata(vs,[],fs);me.update();string=bpy.data.objects.new('BowString',me);bpy.context.collection.objects.link(string);string.parent=rig;m=string.modifiers.new('Rig','ARMATURE');m.object=rig
for name in ['BowTop','BowNock','BowBottom']:string.vertex_groups.new(name=name).add([i for i,n in enumerate(labels)if n==name],1,'REPLACE')
sm=bpy.data.materials.new('StringReview');sm.diffuse_color=(.07,.035,.01,1);me.materials.append(sm)
report={}
for a in list(bpy.data.actions):
 action(a.name);nf=int(a.frame_range[1]);report[a.name]=[]
 for f in range(nf+1):
  sc.frame_set(f);bm=world('Bow');neutral=bm@Vector((0,.187,.085));kn=rig.pose.bones['B_R_Finger1'].head.copy();isdraw=a.name=='Attack'and 21<=f<=36
  w=smooth((f-20)/6)if isdraw else 0.;nock=neutral.lerp(kn,w)
  if a.name=='Attack'and f==37:nock=neutral.lerp(kn,.10)
  m=world('BowNock');m.translation=nock;rig.pose.bones['BowNock'].matrix=m;bpy.context.view_layer.update();key('BowNock',f,True)
  target=bm@Vector((0,0,.085));d=(target-nock).normalized();up=bm.to_3x3()@Vector((1,0,0));xx=up-d*up.dot(d);xx.normalize();yy=d.cross(xx).normalized();am=Matrix((xx,yy,d)).transposed().to_4x4();am.translation=nock+d*(.32*1.22)
  if a.name=='Attack'and 12<=f<21:
   am.translation=kn+d*(.32*1.22)
  rig.pose.bones['Arrow'].matrix=am;rig.pose.bones['Arrow'].scale=(1,1,1)if a.name=='Attack'and 12<=f<=36 else(.001,.001,.001);bpy.context.view_layer.update();key('Arrow',f,True,True)
  launch=am.copy();launch.translation=target+d*.08;rig.pose.bones['Socket_Arrow_Release'].matrix=launch;bpy.context.view_layer.update();key('Socket_Arrow_Release',f,True)
  if a.name=='Attack':report[a.name].append({'frame':f,'nock':list(nock),'direction':list(d),'target':list(target)})

# Re-bake twist after the authored wrist/upper-body edits, keeping the already-gated weights.
FA,UA=.6,.5
code=(P/'scripts/twist_bones.py').read_text();exec(code[code.index('def twist_about'):code.index('for act in [a for a in bpy.data.actions')])
for a in list(bpy.data.actions):bake_twist(a)

for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
(P/'work/shot_motion.json').write_text(json.dumps(report,indent=2));(P/'work/bow_binding.json').write_text(json.dumps({'hand_local':[list(r)for r in local],'release_frame':36,'release_seconds':1.2,'attack_yaw_correction_degrees':math.degrees(yaw)},indent=2))
action('Standing');sc.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
common.workbench_clay(sc)
for nm,frames in [('Standing',[0]),('Walking',[0,12]),('Attack',[10,24,31,36,37,44]),('Cast',[30]),('Death',[31])]:
 action(nm)
 for f in frames:
  sc.frame_set(f);common.render_views(str(P/f'review/equipped_{nm}_{f:02d}'),.9,2.5,views=('front','left','three_quarter'),resolution=(340,450))
