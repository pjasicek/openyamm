"""Native pilots from the selected study, on fixed-length repaired Meshy chains."""
import bpy,json,math
from pathlib import Path
from mathutils import Matrix,Quaternion,Vector
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/full_20261006')
SPEC=json.loads((OUT.parent/'stage1_20261006/motion_spec.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(OUT/'work/rig_corrected_v1.blend'))
arm=bpy.data.objects['Goblin_Rig'];body=bpy.data.objects['Goblin_Body'];sword=bpy.data.objects['Goblin_Sword'];scene=bpy.context.scene
scene.render.fps=48;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
CLIPS={c['name']:c for c in SPEC['clips']}
REST={b.name:b.matrix_local.copy() for b in arm.data.bones}
# Fit the actual curved prop tip, not a guessed straight blade axis.
BLADE_VECTOR=min(sword.data.vertices,key=lambda v:v.co.y).co-REST['RightHand'].translation
BLADE_LENGTH=BLADE_VECTOR.length;bind_blade=BLADE_VECTOR.normalized()
bind_long=Vector((0,0,-1));bind_long=(bind_long-bind_blade*bind_long.dot(bind_blade)).normalized()
BLADE_BASIS=Matrix((bind_blade,bind_long,bind_blade.cross(bind_long))).transposed()
SOLES={side:[v.co-arm.data.bones[side+'Foot'].head_local for v in body.data.vertices if any(body.vertex_groups[g.group].name==side+'Foot' and g.weight>.99 for g in v.groups)] for side in ('Right','Left')}

def update():bpy.context.view_layer.update()
def assign(name,q):
    b=arm.pose.bones[name];b.matrix=Matrix.Translation(b.head)@q.to_matrix().to_4x4();update()
def rotate(name,axis,degrees):
    b=arm.pose.bones[name];assign(name,Quaternion(Vector(axis),math.radians(degrees))@b.matrix.to_quaternion())
def reset():
    for b in arm.pose.bones:b.matrix_basis=Matrix.Identity(4)
    update()
def chain(first,second,target,pole,last=None):
    a=arm.pose.bones[first].head.copy();ra=REST[first].translation;rb=REST[second].translation
    av=rb-ra;bv=(REST[last].translation-rb) if last else arm.data.bones[second].tail_local-rb
    l1,l2=av.length,bv.length;delta=Vector(target)-a;distance=min(l1+l2-.0005,max(abs(l1-l2)+.0005,delta.length));d=delta.normalized()
    p=Vector(pole)-a;p-=d*p.dot(d)
    parent=arm.pose.bones[first].parent
    parent_delta=parent.matrix.to_quaternion()@REST[parent.name].to_quaternion().inverted() if parent else Quaternion()
    reference=(av+bv).normalized()
    preferred=Vector((0,1,-.12)) if first.endswith('Arm') else Vector((0,-1,0)) if first.endswith('UpLeg') else av-reference*av.dot(reference)
    preferred-=reference*preferred.dot(reference);preferred.normalize()
    reference=parent_delta@reference;preferred=parent_delta@preferred
    transported=reference.rotation_difference(d)@preferred
    transported-=d*transported.dot(d);transported.normalize()
    # Parallel transport supplies a stable bend plane when the guessed pole passes through the limb axis.
    p=(transported+p/max(.40,p.length)*.50).normalized();x=(distance*distance+l1*l1-l2*l2)/(2*distance);k=a+d*x+p*math.sqrt(max(0,l1*l1-x*x));tip=a+d*distance
    u=(k-a).normalized();v=(tip-k).normalized();axis=u.cross(v).normalized();rest_axis=av.cross(bv).normalized()
    if rest_axis.length<.001:rest_axis=REST[first].to_3x3()@Vector((1,0,0))
    if first.endswith('UpLeg'):
        # Imported near-straight knee landmarks do not provide a reliable axial-roll frame.
        assign(first,av.normalized().rotation_difference(u)@REST[first].to_quaternion())
        assign(second,bv.normalized().rotation_difference(v)@REST[second].to_quaternion())
        return tip
    rest_frame=Matrix((rest_axis,av.normalized(),rest_axis.cross(av.normalized()))).transposed();frame=Matrix((axis,u,axis.cross(u))).transposed()
    swing=(frame@rest_frame.transposed()).to_quaternion();assign(first,swing@REST[first].to_quaternion())
    q=Quaternion(axis,u.angle(v)-av.angle(bv))@swing@REST[second].to_quaternion();assign(second,q)
    return tip

def sample(values,t,loop=False):
    n=len(values);i=int(math.floor(t));u=t-i
    def item(j):return values[j%n] if loop else values[max(0,min(n-1,j))]
    a,b,c,d=[item(i+j) for j in (-1,0,1,2)]
    if isinstance(b,(list,tuple,Vector)):return Vector([sample([v[k] for v in values],t,loop) for k in range(len(b))])
    return .5*((2*b)+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)

def wrist_xy(clip,index,side):
    point=CLIPS[clip]['anchors'][index]['points_xy'][4 if side=='Right' else 7]
    return ((point[0]-177.5)*1.65/256,(289-point[1])*1.65/256)

TRACKS={
 'Standing':dict(rootz=[-.008],rootx=[.082],yaw=[0],lean=[0],headpitch=[3],headyaw=[0],Rdepth=[-.105],Ldepth=[-.025],blade=[(.310027,-.947980,-.072085)],freecurl=[16],fan=[2],jaw=[0]),
 'Walk':dict(rootz=[-.018,-.050,-.019,-.022,-.058,-.004],rootx=[.096,.095,.081,.070,.073,.082],yaw=[-5,-8,-3,5,9,1],lean=[3,7,5,4,8,2],headpitch=[2,-3,2,1,1,0],headyaw=[1,1,-1,-1,0,1],Rdepth=[.13,.15,.10,-.16,-.27,-.04],Ldepth=[-.24,-.34,-.30,.24,.28,.18],freecurl=[16,29,18,15,17,18],fan=[4,8,2,3,2,6],jaw=[0,1,0,0,1,0]),
 'Attack':dict(rootz=[-.006,.002,-.011,-.025,-.052,-.023,-.008],rootx=[.082,.070,.072,.080,.077,.077,.082],yaw=[12,58,50,-12,-35,-8,0],lean=[3,0,2,12,23,10,0],headpitch=[3,-7,-3,10,24,12,3],headyaw=[6,10,-45,0,-12,0,0],Rdepth=[-.21,-.35,-.40,-.28,-.29,-.13,-.105],Ldepth=[-.01,-.27,-.25,-.36,-.28,-.04,-.025],freecurl=[20,30,12,22,17,18,16],fan=[3,3,9,7,5,2,2],jaw=[2,3,3,2,1,1,0])}
# Depth signs come from genuine locomotion profiles; single-view attack depth remains inferred.
for clip,depths in [('Walk',[-1,-1,-1,-1,-1,-1]),('Attack',[-1,1,1,-1,1,-1])]:
    blade=[]
    for a,sign in zip(CLIPS[clip]['anchors'],depths):
        wrist,tip=a['points_xy'][4],a['points_xy'][13];x=(tip[0]-wrist[0])*1.65/256/BLADE_LENGTH;z=(wrist[1]-tip[1])*1.65/256/BLADE_LENGTH
        projected=math.hypot(x,z)
        if projected>.97:x*=.97/projected;z*=.97/projected
        blade.append((x,sign*math.sqrt(max(.035,1-x*x-z*z)),z))
    if clip=='Attack':blade.append(TRACKS['Standing']['blade'][0])
    TRACKS[clip]['blade']=blade

# Genuine right-side sprites keep the blade forward and the free palm cupped forward in a-c.
TRACKS['Walk']['freelong']=[(.2,-1,-.05),(.05,-1,.08),(.12,-1,-.05),(.1,.35,-1),(.1,.25,-1),(.15,.15,-1)]
TRACKS['Walk']['freepalm']=[(.2,0,1),(.2,0,1),(.1,0,1),(-1,0,.1),(-1,0,.1),(-1,0,.1)]
TRACKS['Standing']['plane']=[(1,0,0)]
TRACKS['Walk']['plane']=[(1,.1,.0)]*6
TRACKS['Attack']['plane']=[(0,1,0),(0,1,0),(0,1,0),(1,0,0),(0,0,1),(1,0,0),(1,0,0)]

def hand(side,blade=None,curl=16,fan=2,plane=None,direction=None,palm=None,orientation=None,roll=None):
    suffix='R' if side=='Right' else 'L';fore=arm.pose.bones[side+'ForeArm'];fore_direction=fore.vector.normalized()
    if blade is not None:
        across=Vector(blade).normalized();long=fore_direction-across*fore_direction.dot(across)
        if long.length<.1:long=Vector((0,0,-1))-across*across.z*-1
        long.normalize()
        if plane is not None:
            candidate=Vector(plane).cross(across).normalized()
            long=candidate
        normal=across.cross(long).normalized();wanted=Matrix((across,long,normal)).transposed()
        baseline=BLADE_BASIS
        q=orientation if orientation is not None else (wanted@baseline.transposed()@REST[side+'Hand'].to_3x3()).to_quaternion()
    else:
        baseline_long=Vector((0,0,-1));normal=Vector(palm) if palm is not None else Vector((-1 if side=='Left' else 1,0,0));long=Vector(direction).normalized() if direction is not None else fore_direction;normal=(normal-long*normal.dot(long)).normalized();across=long.cross(normal).normalized()
        baseline=Matrix((Vector((0,-1,0)),baseline_long,Vector((1,0,0)))).transposed()
        # Both meshes have the same physical rest blade/long basis; left palm normal is mirrored.
        if side=='Left':across.negate();normal.negate()
        q=orientation if orientation is not None else (Matrix((across,long,normal)).transposed()@baseline.transposed()@REST[side+'Hand'].to_3x3()).to_quaternion()
    delta=q@arm.pose.bones[side+'Hand'].matrix.to_quaternion().inverted();axis=fore.vector.normalized();angle=2*math.atan2(Vector((delta.x,delta.y,delta.z)).dot(axis),delta.w)
    angle=(angle+math.pi)%math.tau-math.pi
    if roll is not None:angle=math.radians(roll)
    previous=TWIST_HISTORY.get(side,angle)
    while angle-previous>math.pi:angle-=math.tau
    while angle-previous< -math.pi:angle+=math.tau
    TWIST_HISTORY[side]=angle
    fore_q=fore.matrix.to_quaternion()
    rotate(side+'ForeArm',axis,math.degrees(angle)*.30)
    twist=arm.pose.bones['ForearmTwist.'+suffix]
    twist_q=Quaternion(axis,angle*.85)@fore_q@REST[side+'ForeArm'].to_quaternion().inverted()@REST[twist.name].to_quaternion()
    assign(twist.name,twist_q)
    assign(side+'Hand',q)
    for label in ('Index','Middle','Ring'):
        for j,deg in enumerate(([68,85,62] if side=='Right' else [curl,curl*.7,curl*.35])):
            pb=arm.pose.bones[f'Digit.{suffix}.{label}.{j+1:02d}'];pb.rotation_quaternion=Quaternion((1,0,0),math.radians(-deg))
        if side=='Left':
            pb=arm.pose.bones[f'Digit.{suffix}.{label}.01'];pb.rotation_quaternion=Quaternion((0,0,1),math.radians(fan*{'Index':1,'Middle':0,'Ring':-1}[label]))@pb.rotation_quaternion
    update()
    if side=='Right':
        transform=arm.pose.bones[side+'Hand'].matrix@REST[side+'Hand'].inverted()
        chain('Digit.R.Thumb.01','Digit.R.Thumb.02',transform@Vector((-.573,-.12,.705)),transform@Vector((-.510,-.170,.730)))
    else:
        for j in (1,2):arm.pose.bones[f'Digit.L.Thumb.{j:02d}'].rotation_quaternion=Quaternion((1,0,0),math.radians(-10))
    update()

def foot(side,y,lift,pitch):
    rotation=Quaternion((1,0,0),math.radians(pitch));rest=REST[side+'Foot'].translation
    contact=min(SOLES[side],key=lambda v:(rotation@v).z);rotated=rotation@contact
    height=.002-rotated.z+max(0,lift);y+=contact.y-rotated.y
    target=Vector((rest.x+.082,rest.y+y,height));chain(side+'UpLeg',side+'Leg',target,(rest.x+.082,-.65,.50),side+'Foot');assign(side+'Foot',rotation@REST[side+'Foot'].to_quaternion())
    return target

TRACKS['Standing']['rollR']=[8]
TRACKS['Walk']['rollR']=[-45,-65,-35,15,55,0]
TRACKS['Attack']['rollR']=[8,45,65,-25,-45,-5,8]

ORIENTATIONS={}
LEFT_ORIENTATIONS={}
TWIST_HISTORY={}
def right_orientation(clip,phase):
    if clip not in ORIENTATIONS:
        qs=[];baseline=BLADE_BASIS
        for blade,plane in zip(TRACKS[clip]['blade'],TRACKS[clip]['plane']):
            b=Vector(blade).normalized();long=Vector(plane).cross(b).normalized();normal=b.cross(long).normalized()
            q=(Matrix((b,long,normal)).transposed()@baseline.transposed()@REST['RightHand'].to_3x3()).to_quaternion()
            if qs and qs[-1].dot(q)<0:q.negate()
            qs.append(q)
        ORIENTATIONS[clip]=qs
    qs=ORIENTATIONS[clip];loop=clip=='Walk';i=int(math.floor(phase));u=phase-i
    def at(j):return qs[j%len(qs)].copy() if loop else qs[max(0,min(len(qs)-1,j))].copy()
    def relative(q,p):
        d=q.inverted()@p
        if d.w<0:d.negate()
        return d.to_exponential_map()
    def tangent(j):
        q=at(j);return q@Quaternion(-.25*(relative(q,at(j-1))+relative(q,at(j+1))))
    return at(i).slerp(at(i+1),u)

def pose(clip,phase):
    reset();loop=clip=='Walk';track=TRACKS[clip];c={k:sample(v,phase,loop) for k,v in track.items()};root=arm.pose.bones['Hips'];root.matrix=Matrix.Translation((c['rootx'],0,c['rootz']))@root.matrix;update()
    rotate('Hips',(0,0,1),c['yaw']*.22)
    for name,share in [('Spine02',.25),('Spine01',.35),('Spine',.40)]:
        heading=Quaternion((0,0,1),math.radians(c['yaw']))
        rotate(name,(0,0,1),c['yaw']*.78*share);rotate(name,heading@Vector((1,0,0)),c['lean']*share);rotate(name,heading@Vector((0,1,0)),c.get('sidelean',0)*share)
    rotate('Head',(0,0,1),c['headyaw'])
    head_delta=arm.pose.bones['Head'].matrix.to_quaternion()@REST['Head'].to_quaternion().inverted()
    rotate('Head',head_delta@Vector((1,0,0)),c['headpitch'])
    head_delta=arm.pose.bones['Head'].matrix.to_quaternion()@REST['Head'].to_quaternion().inverted()
    rotate('Jaw',head_delta@Vector((1,0,0)),-c['jaw'])
    for side in ('Right','Left'):
        anchors=[wrist_xy(clip,i,side) for i in range(len(CLIPS[clip]['anchors']))]
        if clip in ('Attack','Hit','Fidget'):anchors.append(wrist_xy('Standing',0,side))
        x,z=sample(anchors,phase,loop);depth=c['Rdepth' if side=='Right' else 'Ldepth'];target=Vector((x,depth,z))
        pole=Vector(((-.25 if side=='Right' else .35)+c['rootx'],-.17,1.02))
        if clip=='Attack':pole=Vector(((-.04 if side=='Right' else .23)+c['rootx'],-.21,1.15)).lerp(pole,max(0,min(1,phase-5)))
        if clip=='Hit' and side=='Left':pole=Vector((-.05+c['rootx'],-.30,1.13)).lerp(pole,max(0,min(1,phase-5)))
        chain(side+'Arm',side+'ForeArm',target,pole,side+'Hand')
        left_q=None
        if side=='Left' and clip in LEFT_ORIENTATIONS:
            qs=LEFT_ORIENTATIONS[clip];i=max(0,min(len(qs)-2,int(phase)));u=max(0,min(1,phase-i));left_q=qs[i].slerp(qs[i+1],u)
        hand(side,c['blade'] if side=='Right' else None,c['freecurl'],c['fan'],plane=c.get('plane') if side=='Right' else None,direction=c.get('freelong') if side=='Left' else None,palm=c.get('freepalm') if side=='Left' else None,orientation=right_orientation(clip,phase) if side=='Right' else left_q,roll=c.get('rollR') if side=='Right' and clip!='Walk' else None)
        if side=='Right' and clip=='Walk':
            delta=arm.pose.bones['RightHand'].matrix.to_quaternion()@REST['RightHand'].to_quaternion().inverted()
            minimum=min((delta@(v.co-REST['RightHand'].translation)).z for v in sword.data.vertices)+arm.pose.bones['RightHand'].head.z
            if minimum<.022:
                target.z+=.022-minimum
                chain(side+'Arm',side+'ForeArm',target,pole,side+'Hand')
                hand(side,c['blade'],c['freecurl'],c['fan'],orientation=right_orientation(clip,phase))
        suffix='R' if side=='Right' else 'L';cap='ArmorShoulder.'+suffix
        parent=arm.pose.bones[side+'Shoulder'];parent_delta=parent.matrix.to_quaternion()@REST[parent.name].to_quaternion().inverted()
        limb_delta=arm.pose.bones[side+'Arm'].matrix.to_quaternion()@REST[side+'Arm'].to_quaternion().inverted()
        relative=parent_delta.inverted()@limb_delta
        assign(cap,parent_delta@Quaternion().slerp(relative,.28)@REST[cap].to_quaternion())
    if clip=='Walk':
        values=[(-.005,.11,-5),(-.24,.012,-20),(-.20,0,-3),(0,0,0),(.20,0,19),(.12,.055,20)]
        for side,offset in [('Right',0),('Left',3)]:
            local_phase=(phase+offset)%6;y,lift,pitch=sample(values,local_phase,True)
            if 2<=local_phase<=4:y=-.20+(local_phase-2)*.20
            foot(side,y,lift,pitch)
    else:
        foot('Right',0,0,0)
        lift=sample([0,.125,.105,.015,0,0,0],phase) if clip=='Attack' else 0
        foot('Left',-.07*min(1,lift/.10),lift,-8*min(1,lift/.10))
    for i in range(12):
        b=arm.pose.bones[f'Skirt.{i:02d}'];angle=-math.pi+(i+.5)*math.tau/12
        if clip=='Walk':
            _,lift,_=sample(values,phase+(0 if math.sin(angle)<0 else 3),True);bend=math.degrees(math.asin(min(.8,lift/.25)))*max(0,math.cos(angle))*.70
        elif clip=='Attack':bend=lift*130*max(0,math.cos(angle)) if math.sin(angle)>0 else 0
        else:bend=0
        b.rotation_quaternion=Quaternion((1,0,0),math.radians(-bend))
    skirt_follow()

def skirt_follow():
    hip_delta=arm.pose.bones['Hips'].matrix.to_quaternion()@REST['Hips'].to_quaternion().inverted()
    for i in range(12):
        angle=-math.pi+(i+.5)*math.tau/12;side='Right' if math.sin(angle)<0 else 'Left'
        direction=hip_delta.inverted()@(arm.pose.bones[side+'Leg'].head-arm.pose.bones[side+'UpLeg'].head).normalized()
        radial=Vector((math.sin(angle),-math.cos(angle),0))
        bend=math.radians(6)+math.asin(min(.9,max(0,direction.dot(radial))))*.9
        flare=Quaternion((math.cos(angle),math.sin(angle),0),-bend)
        name=f'Skirt.{i:02d}'
        assign(name,hip_delta@flare@REST[name].to_quaternion())
    update()

def build(clip_frames,filename):
    for clip,frames in clip_frames:
        TWIST_HISTORY.clear()
        arm.animation_data_create();action=bpy.data.actions.new(clip);action.use_fake_user=True;arm.animation_data.action=action
        for frame in range(frames+1):
            pose(clip,frame/6)
            for b in arm.pose.bones:
                if frame and b.rotation_quaternion.dot(previous[b.name])<0:b.rotation_quaternion.negate()
                b.keyframe_insert('location',frame=frame+1,group=b.name);b.keyframe_insert('rotation_quaternion',frame=frame+1,group=b.name)
            previous={b.name:b.rotation_quaternion.copy() for b in arm.pose.bones}
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:key.interpolation='LINEAR'
        action['native_duration_ms']=125 if clip=='Standing' else 750;action['source_anchors']=len(CLIPS[clip]['anchors']);action['mode']=CLIPS[clip]['mode']
        print('Authored',clip,frames/48,'seconds',flush=True)
    arm.animation_data.action=bpy.data.actions['Standing'];scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'work'/filename))
    (OUT/'review/pilot_authoring.json').write_text(json.dumps({'tracks':TRACKS,'basis':'Blender Z up / forward -Y / right -X','interpolation':'Catmull-Rom anatomical target paths, baked quaternion keys at 48 fps; no per-bone scaling','locomotion':'In-place. Diagnostic travel speed 1.6 m/s cancels the linear stance segment; consumer must match actor travel.','endpoint_inference':'Attack final 125 ms returns toward held Standing; source f still carries residual lean','review_status':'authored_unverified'},indent=2)+'\n')

if __name__=='__main__':build([('Standing',6),('Walk',36),('Attack',36)],'native_pilots_v1.blend')
