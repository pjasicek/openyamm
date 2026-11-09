"""Fit the selected weighted run, preserving source support/flight and fixed limb lengths."""
from pathlib import Path
import bpy,math,json
from mathutils import Matrix,Vector
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilot.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene;scene.render.fps=30
mapping={'B_Pelvis':'Hips','B_Spine':'Spine','B_Spine1':'Spine1','B_Spine2':'Spine2','B_Neck':'Neck','B_Head':'Head'}
for s,long in [('L','Left'),('R','Right')]:
    for target,source in [('Clavicle','Shoulder'),('UpperArm','Arm'),('Forearm','ForeArm'),('Hand','Hand'),('Thigh','UpLeg'),('Calf','Leg'),('Foot','Foot'),('Toe0','ToeBase')]:
        mapping[f'B_{s}_{target}']='mixamorig:'+long+source
for n in list(mapping):
    if not mapping[n].startswith('mixamorig:'):mapping[n]='mixamorig:'+mapping[n]
def select(obj,act):
    obj.animation_data_create();obj.animation_data.action=act
    if act and len(act.slots):obj.animation_data.action_slot=act.slots[0]
def load(stem):
    before=set(bpy.data.objects);acts=set(bpy.data.actions)
    bpy.ops.import_scene.fbx(filepath=str(Path('anim_library/mixamo')/(stem+'.fbx')))
    new=set(bpy.data.objects)-before;src=next(o for o in new if o.type=='ARMATURE')
    return src,src.animation_data.action,new,set(bpy.data.actions)-acts
def discard(objects,actions):
    for o in objects:bpy.data.objects.remove(o,do_unlink=True)
    for a in actions:bpy.data.actions.remove(a)
select(rig,bpy.data.actions['Standing']);scene.frame_set(0)
neutral={n:rig.matrix_world@rig.pose.bones[n].matrix for n in mapping}
source,action,objects,actions=load('Standard Idle');scene.frame_set(int(action.frame_range[0]))
source_neutral={n:source.matrix_world@source.pose.bones[s].matrix for n,s in mapping.items()}
offsets={n:source_neutral[n].to_quaternion().inverted()@neutral[n].to_quaternion() for n in mapping}
# Use the anatomical palm frame for both hands; neutral motion can contain unrelated wrist bends.
for s,long in [('L','Left'),('R','Right')]:
    hand=source.data.bones[f'mixamorig:{long}Hand'].matrix_local
    inv=hand.inverted()
    sa=(inv.to_3x3()@(source.data.bones[f'mixamorig:{long}HandIndex1'].head_local-source.data.bones[f'mixamorig:{long}HandPinky1'].head_local)).normalized()
    sf=(inv@source.data.bones[f'mixamorig:{long}HandMiddle1'].head_local).normalized()
    th=rig.data.bones[f'B_{s}_Hand'].matrix_local;ti=th.inverted()
    ta=(ti.to_3x3()@(rig.data.bones[f'B_{s}_Finger1'].head_local-rig.data.bones[f'B_{s}_Finger4'].head_local)).normalized()
    tf=(ti@rig.data.bones[f'B_{s}_Finger2'].head_local).normalized()
    def basis(a,f):
        f=(f-a*a.dot(f)).normalized();return Matrix([a,f,a.cross(f)]).transposed()
    offsets[f'B_{s}_Hand']=(basis(sa,sf)@basis(ta,tf).transposed()).to_quaternion()
scale=neutral['B_Pelvis'].translation.z/source_neutral['B_Pelvis'].translation.z
neutral_floor=min(neutral[f'B_{s}_Foot'].translation.z for s in 'LR')
discard(objects,actions);select(rig,None)
source,action,objects,actions=load('Running (5)')
fps=scene.render.fps/scene.render.fps_base;assert fps==30
f0,f1=map(lambda f:int(round(f)),action.frame_range)
samples=[]
for f in range(f0,f1+1):
    scene.frame_set(f);samples.append({n:source.matrix_world@source.pose.bones[s].matrix for n,s in mapping.items()})
source_floor=[min(sample[f'B_{s}_Foot'].translation.z for s in 'LR') for sample in samples]
base_floor=min(source_floor)
discard(objects,actions)
act=bpy.data.actions.new('Running');act.use_fake_user=True;select(rig,act);previous={}
for f,sample in enumerate(samples):
    scene.frame_set(f)
    for pb in rig.pose.bones:pb.matrix_basis.identity();pb.rotation_mode='QUATERNION'
    bpy.context.view_layer.update()
    for n in mapping:
        pb=rig.pose.bones[n];m=(sample[n].to_quaternion()@offsets[n]).to_matrix().to_4x4()
        m.translation=rig.matrix_world@pb.head
        if n=='B_Pelvis':m.translation=neutral[n].translation
        pb.matrix=rig.matrix_world.inverted()@m
        if n!='B_Pelvis':pb.location=(0,0,0)
        pb.scale=(1,1,1);bpy.context.view_layer.update()
    floor=min((rig.matrix_world@rig.pose.bones[f'B_{s}_Foot'].head).z for s in 'LR')
    pelvis=rig.pose.bones['B_Pelvis'];m=pelvis.matrix.copy()
    m.translation.z+=neutral_floor+(source_floor[f]-base_floor)*scale-floor;pelvis.matrix=m
    bpy.context.view_layer.update()
    for pb in rig.pose.bones:
        q=pb.rotation_quaternion.copy()
        if pb.name in previous and q.dot(previous[pb.name])<0:q.negate()
        pb.rotation_quaternion=q;previous[pb.name]=q.copy();pb.keyframe_insert('rotation_quaternion',frame=f)
        if pb.name=='B_Pelvis':pb.keyframe_insert('location',frame=f)
act.use_frame_range=True;act.frame_start=0;act.frame_end=len(samples)-1
for layer in act.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for fc in bag.fcurves:
                for key in fc.keyframe_points:key.interpolation='LINEAR'
(p/'review/mixamo_transfer.json').write_text(json.dumps({'source':'anim_library/mixamo/Running (5).fbx','frames':len(samples),'fps':fps,'source_ankle_flight_range_m':(max(source_floor)-base_floor)*scale,'method':'Neutral-pose frame calibration; source relative ankle support height retained, fixed-length limbs; no per-frame ground clamp.'},indent=2))
select(rig,None)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/pilot.blend'))
