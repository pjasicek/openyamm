"""Native-rate wingbeat plus a source-frame Mixamo claw swipe with airborne support."""
import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene;scene.render.fps=30
OFF=json.loads(scene['rig_offsets']);RS={n:Matrix(v['R_src']) for n,v in OFF.items()}
MAP={'B_Pelvis':'Hips','B_Spine':'Spine','B_Spine1':'Spine1','B_Spine2':'Spine2','B_Neck':'Neck','B_Head':'Head'}
for sd,side in [('L','Left'),('R','Right')]:
 for a,b in [('Clavicle','Shoulder'),('UpperArm','Arm'),('Forearm','ForeArm'),('Hand','Hand'),('Thigh','UpLeg'),('Calf','Leg'),('Foot','Foot'),('Toe0','ToeBase')]:MAP[f'B_{sd}_{a}']=side+b
 for f,fn in enumerate(['Thumb','Index','Middle','Ring','Pinky']):
    nm=[f'B_{sd}_Finger{f}',f'B_{sd}_Finger{f}1',f'B_{sd}_Finger{f}2']
    if sd=='R' and f==0:nm=['B_R_Finger0','B_R_Finger0.001','B_R_Finger0.002']
    for k,n in enumerate(nm):MAP[n]=f'{side}Hand{fn}{k+1}'
LEGS=[n for n in MAP if any(x in n for x in ['Thigh','Calf','Foot','Toe'])]
def reset():
 rig.animation_data_create();rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4);pb.rotation_mode='QUATERNION'
 bpy.context.view_layer.update()
def rotation(n,axis,angle):
 pb=rig.pose.bones[n];axis=rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector(axis)
 pb.rotation_quaternion=pb.rotation_quaternion@Quaternion(axis,math.radians(angle))
def wings(t,scale=1):
 phase=2*math.pi*t/.75;stroke=scale*33*(1-math.cos(phase))
 for sd,sg in [('L',1),('R',-1)]:
    rotation(f'W_{sd}_Root',(0,1,0),sg*stroke)
    rotation(f'W_{sd}_Root',(0,0,1),sg*7*math.sin(phase))
    rotation(f'W_{sd}_Tip',(0,1,0),-sg*12*math.sin(phase-.3)*scale)
    rotation(f'W_{sd}_Upper',(0,1,0),-sg*5*math.sin(phase-.4)*scale)
    rotation(f'W_{sd}_Lower',(0,1,0),-sg*8*math.sin(phase-.6)*scale)
def root_lift(t):
 pb=rig.pose.bones['B_Pelvis'];M=pb.matrix.copy();M.translation+=Vector((0,0,.025*math.sin(2*math.pi*t/.75)));pb.matrix=M

def source_load(file):
 before=set(bpy.data.objects);old=set(bpy.data.actions)
 bpy.ops.import_scene.fbx(filepath=str(Path('anim_library/mixamo',file).resolve()))
 new=set(bpy.data.objects)-before;src=next(o for o in new if o.type=='ARMATURE');act=src.animation_data.action;S=src.matrix_world.copy()
 pre=next(b.name for b in src.data.bones if b.name.endswith('Hips'))[:-4]
 rest={n:(S@src.data.bones[pre+m].matrix_local).to_3x3().normalized().inverted() for n,m in MAP.items()}
 return src,act,S,pre,rest,new,set(bpy.data.actions)-old

def apply_source(data,time,role):
 src,act,S,pre,rest,_,_=data;start=float(act.frame_range[0]);frame=start+time*30;scene.frame_set(math.floor(frame),subframe=frame%1)
 # Cache source world rotations before touching our target's hierarchy.
 delta={n:(S@src.pose.bones[pre+MAP[n]].matrix).to_3x3().normalized()@rest[n] for n in MAP}
 f=delta['B_Pelvis']@Vector((0,-1,0));C=Matrix.Rotation(-math.atan2(f.x,-f.y),3,'Z')
 for n in MAP:
    if n in LEGS or n=='B_Pelvis':continue
    pb=rig.pose.bones[n];M=(C@delta[n]@RS[n]).to_4x4();M.translation=pb.head;pb.matrix=M
    q=pb.rotation_quaternion.copy()
    if role=='Flight':
        amount=.14 if any(x in n for x in ['UpperArm','Forearm','Hand']) else .08
        if 'Finger' in n:amount=.05
    else:
        amount=.95
        if 'Spine' in n:amount=.10
        if 'Neck' in n or 'Head' in n:amount=.15
        if 'Clavicle' in n:amount=.45
        if 'Finger' in n:amount=.20
        if n.endswith('_Hand'):amount=.65
    if 'Forearm' in n:
        twist=2*math.atan2(q.y,q.w);q=q@Quaternion((0,1,0),-twist)
    pb.rotation_quaternion=Quaternion().slerp(q,amount)
    bpy.context.view_layer.update()

def save_keys(act,frame):
 rig.animation_data.action=act
 for pb in rig.pose.bones:
    pb.keyframe_insert('rotation_quaternion',frame=frame,group=pb.name)
    if pb.name=='B_Pelvis':pb.keyframe_insert('location',frame=frame,group=pb.name)
 rig.animation_data.action=None

def action(name,duration):
 if name in bpy.data.actions:bpy.data.actions.remove(bpy.data.actions[name])
 a=bpy.data.actions.new(name);a.use_fake_user=True;a.use_frame_range=True;a.frame_start=0;a.frame_end=duration*30
 return a

def cleanup(data):
 for o in data[5]:bpy.data.objects.remove(o,do_unlink=True)
 for a in data[6]:bpy.data.actions.remove(a)

reset();data=source_load('Floating.fbx');reset();apply_source(data,0,'Flight');base={pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones};cleanup(data)
flight=action('Flight',.75)
for t in sorted(set([i/30 for i in range(23)]+[.75])):
 reset()
 for pb in rig.pose.bones:pb.matrix_basis=base[pb.name]
 phase=2*math.pi*t/.75
 rotation('B_Spine1',(1,0,0),1.5*math.sin(phase));rotation('B_Head',(1,0,0),-1.3*math.sin(phase-.3))
 for sd,sg in [('L',1),('R',-1)]:
    rotation(f'B_{sd}_Forearm',(1,0,0),2*math.sin(phase-.4))
    rotation(f'B_{sd}_Calf',(1,0,0),2.5*math.sin(phase-.5))
 wings(t);bpy.context.view_layer.update();root_lift(t);save_keys(flight,t*30)
reset();data=source_load('Mutant Swiping.fbx');attack=action('Attack',2.25)
for t in sorted(set([i/30 for i in range(68)]+[2.25])):
 reset();apply_source(data,min(.4166667+t,2.6666667),'Attack')
 # Keep the source strike speed, blending only its trimmed entry and final return.
 blend=min(1,t/.18,(2.25-t)/.28);blend=max(0,blend);blend=blend*blend*(3-2*blend)
 for pb in rig.pose.bones:
    b=base[pb.name];pb.rotation_quaternion=b.to_quaternion().slerp(pb.rotation_quaternion,blend)
 wings(t,.85);bpy.context.view_layer.update();root_lift(t);save_keys(attack,t*30)
cleanup(data);reset();scene.render.fps=30;scene.render.fps_base=1
manifest={'Flight':{'duration':.75,'loop':True,'source':'Floating.fbx phase-zero ready pose, damped into native rest; locally authored native-rate wingbeat'},
'Attack':{'duration':2.25,'loop':False,'source':'Mutant Swiping.fbx','source_start_seconds':.4166667,'source_rate':1.0,'impact_seconds':.75,'support':'native suspended legs; root translation/yaw removed; entry and recovery blended'}}
(P/'work/pilot_clips.json').write_text(json.dumps(manifest,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/pilots.blend'))
rows=[]
for name,times in [('Flight',[0,.125,.25,.375,.5,.625,.75]),('Attack',[0,.25,.5,.75,1.0,1.5,2.25])]:
 a=bpy.data.actions[name];rig.animation_data.action=a
 if a.slots:rig.animation_data.action_slot=a.slots[0]
 for view in ['front','left','three_quarter']:
    row=[]
    for i,t in enumerate(times):
        f=t*30;scene.frame_set(math.floor(f),subframe=f%1)
        path=common.render_views(str(P/f'review/pilot_{name}_{view}_{i}'),1.45,4.4,views=(view,),resolution=(430,430))[0]
        row.append([path,f'{name} {view} {t:.3f}s'])
    rows.append(row)
(P/'review/pilot_frames.json').write_text(json.dumps(rows));print('PILOTS',manifest)
