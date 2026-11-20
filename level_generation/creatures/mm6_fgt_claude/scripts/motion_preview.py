"""Viewer-only upright run and standing sweep on the accepted Thug rig."""
from pathlib import Path
import bpy, json, math, sys
import numpy as np
from mathutils import Matrix, Vector, Quaternion
P = Path(__file__).resolve().parents[1]
OPTIONS = '--attack-options' in sys.argv
OUT = P / ('review/attack_options' if OPTIONS else 'review/motion_preview')
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(P/'scripts'))
SRC = json.loads((P/'work/source_rest.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(P/('work/rig_motion_preview.blend' if OPTIONS else 'work/rig_revision2.blend')))
scene = bpy.context.scene
scene.render.fps = 30
scene.render.fps_base = 1
rig = bpy.data.objects['Rig']
names = [b.name for b in rig.data.bones]

def setact(obj, act):
    obj.animation_data_create()
    obj.animation_data.action = act
    if act and len(act.slots): obj.animation_data.action_slot = act.slots[0]

def snapshot():
    return {b.name: (b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones}

def apply(pose):
    for n, (q, l) in pose.items():
        b = rig.pose.bones[n]
        b.rotation_mode = 'QUATERNION'
        b.rotation_quaternion = q
        b.location = l
        b.scale = (1,1,1)
    bpy.context.view_layer.update()

setact(rig, bpy.data.actions['Standing'])
scene.frame_set(0)
idle = snapshot()
setact(rig, None)
core = {'B_Pelvis':'Hips','B_Spine':'Spine','B_Spine1':'Spine1','B_Spine2':'Spine2','B_Neck':'Neck','B_Head':'Head'}
for side, word in [('L','Left'),('R','Right')]:
    for rpg, mix in [('Clavicle','Shoulder'),('UpperArm','Arm'),('Forearm','ForeArm'),('Hand','Hand'),('Thigh','UpLeg'),('Calf','Leg'),('Foot','Foot'),('Toe0','ToeBase')]:
        core[f'B_{side}_{rpg}'] = word+mix

def basis(f, t):
    f=f.normalized(); t=(t-f*t.dot(f)).normalized()
    return Matrix((f,t,f.cross(t))).transposed()

def twist(q, axis):
    return (2*math.atan2(Vector(q[1:]).dot(axis),q.w)+math.pi)%(2*math.pi)-math.pi

def add_twist(previous):
    def continuous(key, angle):
        if key in previous: angle=previous[key]+(angle-previous[key]+math.pi)%(2*math.pi)-math.pi
        previous[key]=angle
        return angle
    for side in 'LR':
        fb, hb, ub = [rig.data.bones[f'B_{side}_{s}'] for s in ('Forearm','Hand','UpperArm')]
        axis=(fb.matrix_local.inverted()@hb.head_local).normalized()
        rel=(rig.pose.bones[fb.name].matrix.inverted()@rig.pose.bones[hb.name].matrix).to_quaternion()
        rest=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion()
        rig.pose.bones[f'B_{side}_ForearmTwist'].rotation_quaternion=Quaternion(axis,.6*continuous(side+'F',twist(rel@rest.inverted(),axis)))
        axis=(ub.matrix_local.inverted()@fb.head_local).normalized()
        rig.pose.bones[f'B_{side}_UpperArmTwist'].rotation_quaternion=Quaternion(axis,-.5*continuous(side+'U',twist(rig.pose.bones[ub.name].rotation_quaternion,axis)))
    bpy.context.view_layer.update()

def write(name, poses):
    old=bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    act=bpy.data.actions.new(name); act.use_fake_user=True
    setact(rig,act); previous={}
    for frame,pose in enumerate(poses):
        for n,(q,l) in pose.items():
            b=rig.pose.bones[n]; q=q.copy()
            if n in previous and q.dot(previous[n])<0:q.negate()
            previous[n]=q.copy()
            b.rotation_quaternion=q; b.location=l
            b.keyframe_insert('rotation_quaternion',frame=frame)
            if n in ('B_Pelvis','Mace'): b.keyframe_insert('location',frame=frame)
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:key.interpolation='LINEAR'
    act.use_frame_range=True;act.frame_start=0;act.frame_end=len(poses)-1
    setact(rig,None)
    return act

report={}
clips = [('Running',P.parents[2]/'anim_library/humanoid_set/Relax.glb','RelaxRunForward'),
         ('Attack',P.parents[2]/'anim_library/mixamo/Standing Melee Attack Horizontal.fbx',None)]
if OPTIONS:
    clips = [('AttackRPG5',P.parents[2]/'anim_library/humanoid_set/1Hand.glb','SwordAttackR5'),
             ('AttackRPG6',P.parents[2]/'anim_library/humanoid_set/1Hand.glb','SwordAttackR6'),
             ('AttackInward',P.parents[2]/'anim_library/mixamo/Stable Sword Inward Slash.fbx',None),
             ('AttackOutward',P.parents[2]/'anim_library/mixamo/Stable Sword Outward Slash.fbx',None)]
for role,path,clip in clips:
    before=set(bpy.data.objects); acts_before=set(bpy.data.actions)
    scene.render.fps=30
    if clip:bpy.ops.import_scene.gltf(filepath=str(path))
    else:bpy.ops.import_scene.fbx(filepath=str(path))
    imported=set(bpy.data.objects)-before
    source=next(o for o in imported if o.type=='ARMATURE')
    action=next(a for a in set(bpy.data.actions)-acts_before if clip is None or a.name==clip)
    setact(source,action)
    source_fps=scene.render.fps/scene.render.fps_base
    f0,f1=action.frame_range
    count=round((f1-f0)/source_fps*30)
    mapping={n:(n if clip else 'mixamorig:'+m) for n,m in core.items()}
    assert all(v in source.data.bones for v in mapping.values())
    W=source.matrix_world
    lateral=W.to_3x3()@(source.data.bones[mapping['B_L_UpperArm']].head_local-source.data.bones[mapping['B_R_UpperArm']].head_local)
    turn=Matrix.Rotation(-math.atan2(lateral.y,lateral.x),4,'Z')
    W=turn@W
    transforms={}
    for n,m in mapping.items():
        if clip: transforms[n]=Matrix.Identity(3);continue
        rest=W@source.data.bones[m].matrix_local
        rpg=Matrix(SRC[n]['rot'])
        q=Quaternion()
        child=SRC[n]['child']
        if child in mapping:
            seg=W@source.data.bones[mapping[child]].head_local-rest.translation
            q=Vector(SRC[n]['seg']).rotation_difference(seg)
        if n.endswith('_Hand'):
            side='Left' if '_L_' in n else 'Right'
            get=lambda suffix:W@source.data.bones['mixamorig:'+side+'Hand'+suffix].head_local
            fm=get('Middle1')-rest.translation
            tm=get('Index1')-get('Pinky1')
            sd='L' if side=='Left' else 'R'
            fr=Vector(SRC[f'B_{sd}_Finger2']['head'])-Vector(SRC[n]['head'])
            tr=Vector(SRC[f'B_{sd}_Finger1']['head'])-Vector(SRC[f'B_{sd}_Finger4']['head'])
            q=(basis(fm,tm)@basis(fr,tr).inverted()).to_quaternion()
        transforms[n]=rest.to_3x3().normalized().inverted()@q.to_matrix()@rpg
    k=rig.data.bones['B_Pelvis'].head_local.z/(W@source.data.bones[mapping['B_Pelvis']].head_local).z
    rows=[];root0=None
    for frame in range(count+1):
        sf=f0+frame/30*source_fps
        scene.frame_set(int(sf),subframe=sf%1)
        apply(idle)
        for n in names:
            if n not in mapping:continue
            S=W@source.pose.bones[mapping[n]].matrix
            M=(S.to_3x3().normalized()@transforms[n]).to_4x4()
            if n=='B_Pelvis':
                loc=S.translation*k
                if root0 is None:root0=loc.copy()
                loc.x-=root0.x;loc.y-=root0.y
                M.translation=loc
            else:M.translation=rig.matrix_world@rig.pose.bones[n].head
            pb=rig.pose.bones[n];pb.matrix=rig.matrix_world.inverted()@M
            bpy.context.view_layer.update()
        rows.append(snapshot())
    # Add readiness/recovery around the short RPG clips; retain their complete 30 fps swing.
    lead, tail = (12, 8) if OPTIONS and clip else (7, 9)
    if OPTIONS and clip:
        clone = lambda row: {n:(q.copy(),l.copy()) for n,(q,l) in row.items()}
        rows = [clone(rows[0]) for _ in range(lead)] + rows + [clone(rows[-1]) for _ in range(tail)]
        count = len(rows)-1
    # Remove loop travel, keeping vertical bounce and lateral weight shift.
    if role=='Running':
        drift=rows[-1]['B_Pelvis'][1]-rows[0]['B_Pelvis'][1]
        drift.z=0
        for i,row in enumerate(rows):row['B_Pelvis']=(row['B_Pelvis'][0],row['B_Pelvis'][1]-drift*i/count)
        rows[-1]={n:(q.copy(),l.copy()) for n,(q,l) in rows[0].items()}
    else:
        # Adapt the imported lunge to the user's planted, upright Thug stance.
        lower=['B_Pelvis']+[f'B_{side}_{part}' for side in 'LR' for part in ('Thigh','Calf','Foot','Toe0')]
        for row in rows:
            for n in lower:row[n]=(idle[n][0].copy(),idle[n][1].copy())
            for side in 'LR':
                n=f'B_{side}_Clavicle';row[n]=(idle[n][0].slerp(row[n][0],.7),idle[n][1].copy())
            for n in ('B_Spine','B_Spine1','B_Spine2'):
                row[n]=(idle[n][0].slerp(row[n][0],.7),row[n][1])
            for n in ('B_Neck','B_Head'):
                row[n]=(idle[n][0].slerp(row[n][0],.35),row[n][1])
        # Keep the source swing at 30 fps; transition from/to the accepted standing pose.
        for i,row in enumerate(rows):
            t=min(1,i/lead,(count-i)/tail);t=t*t*(3-2*t)
            for n in names:
                row[n]=(idle[n][0].slerp(row[n][0],t),idle[n][1].lerp(row[n][1],t))
    for o in imported:bpy.data.objects.remove(o,do_unlink=True)
    for a in set(bpy.data.actions)-acts_before:bpy.data.actions.remove(a)
    scene.render.fps=30
    # Reuse the accepted twist distribution and solved finger/prop transforms.
    fixed=[];foot_low=[];tips=[];twists={}
    body=bpy.data.objects['Body']
    foot_groups={g.index for g in body.vertex_groups if any(k in g.name for k in ('Foot','Toe0'))}
    foot_ids=[v.index for v in body.data.vertices if sum(w.weight for w in v.groups if w.group in foot_groups)>.6]
    assert foot_ids
    for row in rows:
        apply(row);add_twist(twists);fixed.append(snapshot())
        ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
        foot_low.append(min((body.matrix_world@me.vertices[i].co).z for i in foot_ids));ev.to_mesh_clear()
        tips.append(tuple(rig.pose.bones['Mace'].head+rig.pose.bones['Mace'].y_axis*.385))
    for n in names:
        steps=[math.degrees(a[n][0].rotation_difference(b[n][0]).angle) for a,b in zip(fixed,fixed[1:])]
        largest=max(min(d,360-d) for d in steps)
        if largest>60:print('FAST_STEP',role,n,round(largest,1),flush=True)
    # A constant ground offset retains the source bounce.
    offset=-min(foot_low)
    for row in fixed:
        row['B_Pelvis'][1].z+=offset
    if role!='Running':
        # Endpoints belong exactly to Standing, including the fitted pelvis height.
        for i in range(len(fixed)):
            t=min(1,i/lead,(count-i)/tail);t=t*t*(3-2*t)
            fixed[i]['B_Pelvis'][1].z-=offset*(1-t)
    act=write(role,fixed)
    speed=np.linalg.norm(np.diff(np.array(tips),axis=0),axis=1)*30
    report[role]={'source':str(path),'clip':clip or path.stem,'duration':count/30,
                  'ground_offset_m':offset,'peak_tip_time':(int(np.argmax(speed))+.5)/30}
    print('MOTION',role,report[role],flush=True)
if not OPTIONS:
    from motion_shoulder_fit import fit
    fit(P)
setact(rig,bpy.data.actions['Standing']);scene.frame_set(0)
scene.render.fps=30
bpy.ops.wm.save_as_mainfile(filepath=str(P/('work/rig_attack_options.blend' if OPTIONS else 'work/rig_motion_preview.blend')))
(OUT/'motion_sources.json').write_text(json.dumps(report,indent=2)+'\n')
# Export only replacement animation data. Geometry/materials will come byte-for-byte from accepted viewer assets.
for act in list(bpy.data.actions):
    if act.name not in report:bpy.data.actions.remove(act)
setact(rig,bpy.data.actions[clips[0][0]])
for obj in bpy.data.objects:obj.select_set(obj in (rig,bpy.data.objects['Body'],bpy.data.objects['Mace']))
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(OUT/'motion.glb'),use_selection=True,export_format='GLB',export_yup=True,
    export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,
    export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,
    export_reset_pose_bones=True,export_anim_slide_to_zero=True)
