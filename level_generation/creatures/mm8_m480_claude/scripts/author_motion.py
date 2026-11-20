"""Fit held-club locomotion, troll posture and native one-shot endpoints on source motion."""
from pathlib import Path
import bpy,json,math,sys,ast
import numpy as np
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'));from club import add_club
import armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilot.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
scene.render.fps=30
G=json.loads((p/'work/grip_pose.json').read_text())
def select(act):
    rig.animation_data_create();rig.animation_data.action=act
    if act and len(act.slots):rig.animation_data.action_slot=act.slots[0]
def upd():bpy.context.view_layer.update()
def sample(act):
    select(act);result=[]
    for f in range(int(act.frame_range[1])+1):
        scene.frame_set(f)
        result.append({pb.name:(pb.rotation_quaternion.copy(),pb.location.copy()) for pb in rig.pose.bones})
    return result
def pose(row):
    for n,(q,v) in row.items():
        pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=v;pb.scale=(1,1,1)
    upd()
def swing(n,target):
    pb=rig.pose.bones[n];child=rig.pose.bones[{'B_R_UpperArm':'B_R_Forearm','B_R_Forearm':'B_R_Hand'}[n]]
    delta=(child.head-pb.head).rotation_difference(target-pb.head)
    m=pb.matrix.copy();rot=delta.to_matrix()@m.to_3x3();m2=rot.to_4x4();m2.translation=m.translation;pb.matrix=m2;pb.location=(0,0,0);upd()
def arm(target,pole):
    shoulder=rig.pose.bones['B_R_UpperArm'].head.copy();elbow=rig.pose.bones['B_R_Forearm'].head.copy();wrist=rig.pose.bones['B_R_Hand'].head.copy()
    a=(elbow-shoulder).length;b=(wrist-elbow).length;v=target-shoulder;d=min(v.length,a+b-.001);v.normalize()
    along=(a*a-b*b+d*d)/(2*d);height=math.sqrt(max(0,a*a-along*along))
    pole=pole-shoulder;pole=(pole-v*pole.dot(v)).normalized();e=shoulder+v*along+pole*height
    swing('B_R_UpperArm',e);swing('B_R_Forearm',shoulder+v*d)
def hand_axis(axis):
    pb=rig.pose.bones['B_R_Hand'];m=pb.matrix.copy();current=(m.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized()
    rot=current.rotation_difference(axis).to_matrix()@m.to_3x3();n=rot.to_4x4();n.translation=m.translation;pb.matrix=n;pb.location=(0,0,0);upd()
def localrow():return {pb.name:(pb.rotation_quaternion.copy(),pb.location.copy()) for pb in rig.pose.bones}
source={name:sample(bpy.data.actions[name]) for name in ('Standing','Walking','Running','Attack','Hit','Death','Fidget')}
select(None)
# Drinking lifts the human chin far back; the native troll bites with a near-neutral gaze.
for row in source['Fidget']:
    for name in ('B_Neck','B_Head'):
        row[name]=(source['Standing'][0][name][0].slerp(row[name][0],.2),row[name][1])
for i in range(9):
    row=source['Death'][i];t=i/8
    source['Death'][i]={n:(source['Standing'][0][n][0].slerp(q,t),source['Standing'][0][n][1].lerp(v,t)) for n,(q,v) in row.items()}
pose(source['Standing'][0]);standing_pelvis=rig.pose.bones['B_Pelvis'].matrix.copy()
# Cloth panels have their own hip hinges, never a width-wise mixture of opposite thighs.
pose(source['Standing'][0]);select(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
upd();bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for name,y in [('LoinFront',-.13),('LoinBack',.16)]:
    b=rig.data.edit_bones.new(name);b.head=(0,y,.85);b.tail=(0,y,.55);b.parent=rig.data.edit_bones['B_Pelvis']
bpy.ops.object.mode_set(mode='OBJECT')
for n in ('LoinFront','LoinBack'):body.vertex_groups.new(name=n)
for v in body.data.vertices:
    piece=body.data.attributes['piece'].data[v.index].value
    if piece not in (1,2,16,17,65):continue
    for g in body.vertex_groups:g.remove([v.index])
    blend=float(np.clip((.85-v.co.z)/.13,0,1))
    if piece in (16,17):name='B_R_Thigh' if piece==16 else 'B_L_Thigh'
    else:name='LoinBack' if piece==2 or (piece==1 and v.co.y>.045) else 'LoinFront'
    body.vertex_groups['B_Pelvis'].add([v.index],1-blend,'REPLACE');body.vertex_groups[name].add([v.index],blend,'REPLACE')
pelrest=rig.data.bones['B_Pelvis'].matrix_local
axes={n:(rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector((1,0,0))).normalized() for n in ('LoinFront','LoinBack')}
restangles={}
for s in 'LR':
    d=rig.data.bones[f'B_{s}_Calf'].head_local-rig.data.bones[f'B_{s}_Thigh'].head_local;restangles[s]=math.atan2(-d.y,-d.z)
def cloth():
    undo=(rig.pose.bones['B_Pelvis'].matrix@pelrest.inverted()).inverted().to_3x3();angles=[]
    for s in 'LR':
        d=undo@(rig.pose.bones[f'B_{s}_Calf'].head-rig.pose.bones[f'B_{s}_Thigh'].head);angles.append(math.atan2(-d.y,-d.z)-restangles[s])
    for n,angle in [('LoinFront',-max(0,*angles)*1.10-math.radians(5)),('LoinBack',-min(0,*angles)*1.10+math.radians(5))]:
        rig.pose.bones[n].rotation_mode='QUATERNION';rig.pose.bones[n].rotation_quaternion=Quaternion(axes[n],angle)
death_reference=[{n:(q.copy(),v.copy()) for n,(q,v) in row.items()} for row in source['Death']]
arm_choices={}
for role,rows in source.items():
    pose(rows[0]);origin=rig.pose.bones['B_R_Hand'].head.copy()
    frames=[]
    height=[]
    for row in rows:
        pose(row);height.append(rig.pose.bones['B_R_Hand'].head.z)
    for i,row in enumerate(rows):
        pose(row)
        if role in ('Standing','Walking','Running','Fidget'):
            delta=rig.pose.bones['B_R_Hand'].head-origin
            target=Vector((-.40,-.15,.83))+delta*(.35 if role=='Standing' else .55)
            target.x=min(target.x,-.40)
            direction=Vector((-.08,-.60,.796)).normalized()
            factor=0.
            if role=='Death':
                pelvis=rig.pose.bones['B_Pelvis'];carry=pelvis.matrix@standing_pelvis.inverted()
                fraction=max(0,min(1,(i-5)/8))
                target=(carry@Vector((-.40,-.15,.83))).lerp(rig.pose.bones['B_R_Hand'].head,fraction)
                current=(rig.pose.bones['B_R_Hand'].matrix.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized()
                direction=(carry.to_3x3()@direction).lerp(current,fraction).normalized()
            if role=='Fidget':
                factor=max(0,min(1,(height[i]-height[0])/max(max(height)-height[0],.001)))
                direction=direction.lerp(Vector((.985,-.06,.16)).normalized(),factor).normalized()
                head=rig.pose.bones['B_Head'];mouth=head.matrix@head.bone.matrix_local.inverted()@Vector((-.035,-.275,1.355))
                # The meat meets the mouth broadside; the upper end clears the face laterally.
                aim=mouth-direction*.28+Vector((0,0,.085))
                target=Vector((-.40,-.15,.83)).lerp(aim,factor)
                target.y-=.24*math.sin(math.pi*factor)
                target.x-=.08*math.sin(math.pi*factor)
            shoulder=rig.pose.bones['B_R_UpperArm'].head
            elbow=rig.pose.bones['B_R_Forearm'].head;wrist=rig.pose.bones['B_R_Hand'].head
            reach=.94*((elbow-shoulder).length+(wrist-elbow).length)
            if (target-shoulder).length>reach:target=shoulder+(target-shoulder).normalized()*reach
            armik.solve(rig,'R',target,pole=Vector((-.65,-.10,1.05)) if role=='Death' else Vector((-.51,-.02,1.05)))
            snap={pb.name:pb.matrix_basis.copy() for pb in rig.pose.bones}
            frames.append({'snap':snap,'wrist':target,'dir':direction,'factor':factor})
    if frames:
        if role=='Death':frames[0]['initial_psi']=arm_choices['Standing'][0]['psi']
        path=armik.arm_dp(rig,'R',frames,G['handle_axis_hand_local'],phis=range(-40,41,10),psis=range(0,360,10),k_twist=.6,k_dphi=1.,k_dpsi=1.)
        if role in ('Standing','Walking','Running'):
            for fr in (frames[0],frames[-1]):
                fr['initial_psi']=path[0]['psi'];fr['initial_phi']=path[0]['phi']
            path=armik.arm_dp(rig,'R',frames,G['handle_axis_hand_local'],phis=range(-40,41,10),psis=range(0,360,10),k_twist=.6,k_dphi=1.,k_dpsi=1.)
        # Refine the feeding contact using the selected hand orientation, retaining the global continuous choice.
        if role=='Fidget':
            for fr,choice in zip(frames,path):
                armik.apply_arm(rig,'R',fr['snap'],fr['wrist'],G['handle_axis_hand_local'],fr['dir'],choice['phi'],choice['psi'])
                h=rig.pose.bones['B_R_Hand'];head=rig.pose.bones['B_Head']
                mouth=head.matrix@head.bone.matrix_local.inverted()@Vector((-.035,-.275,1.355))
                target=mouth-h.matrix.to_3x3()@Vector(G['handle_centre_hand_local'])-fr['dir']*.28
                fr['wrist']=fr['wrist'].lerp(target,fr['factor']**4)
        for i,(fr,choice) in enumerate(zip(frames,path)):
            armik.apply_arm(rig,'R',fr['snap'],fr['wrist'],G['handle_axis_hand_local'],fr['dir'],choice['phi'],choice['psi'])
            rows[i]=localrow()
        arm_choices[role]=path
        print('ARM FIT',role,'max wrist',max(x['swing'] for x in path),'max twist',max(abs(x['twist']) for x in path),flush=True)
    if role=='Death':
        previous={}
        for i,row in enumerate(rows):
            t=max(0,min(1,i/14));t=t*t*(3-2*t)
            for part in ('Clavicle','UpperArm','Forearm','Hand'):
                n='B_R_'+part;start=source['Standing'][0][n][0];end=death_reference[i][n][0]
                delta=start.inverted()@end
                if (n in previous and delta.dot(previous[n])<0) or (n not in previous and delta.w<0):delta.negate()
                previous[n]=delta.copy();axis,angle=delta.to_axis_angle()
                row[n]=(start@Quaternion(axis,angle*t),row[n][1])
    for i,row in enumerate(rows):
        pose(row)
        for n,q in G['finger_local'].items():rig.pose.bones[n].rotation_quaternion=Quaternion(q)
        for pb in rig.pose.bones:
            if pb.name.startswith('B_L_Finger'):pb.rotation_quaternion=Quaternion()
        if role!='Death' or i<12:
            # Long arms and a broad belly need the native outward free-arm carriage.
            pb=rig.pose.bones['B_L_UpperArm'];m=pb.matrix.copy()
            chest=rig.pose.bones['B_Spine2'];axis=(chest.matrix@chest.bone.matrix_local.inverted()).to_3x3()@Vector((0,-1,0))
            r=Matrix.Rotation(math.radians(50 if role=='Running' else 22*(1-i/12) if role=='Death' else 22),3,axis)@m.to_3x3();n=r.to_4x4();n.translation=m.translation;pb.matrix=n;pb.location=(0,0,0);upd()
        # Preserve the source roll while easing the small extreme wrist bend.
        for side in 'LR':
            h=rig.pose.bones[f'B_{side}_Hand'];fa=rig.pose.bones[f'B_{side}_Forearm']
            fdir=(h.matrix@h.bone.matrix_local.inverted()@rig.data.bones[f'B_{side}_Finger2'].head_local)-h.head
            axis=(h.head-fa.head).normalized();fd=fdir.normalized();angle=axis.angle(fd)
            if angle>math.radians(58):
                desired=axis.slerp(fd,math.radians(58)/angle)
                m=h.matrix.copy();r=fd.rotation_difference(desired).to_matrix()@m.to_3x3();n=r.to_4x4();n.translation=m.translation;h.matrix=n;h.location=(0,0,0);upd()
        cloth();upd();rows[i]=localrow()
# Remove the small non-cyclic drift in the imported run across the complete period.
rows=source['Running'];first,last=rows[0],rows[-1]
for i,row in enumerate(rows):
    t=i/(len(rows)-1)
    for n,(q,v) in list(row.items()):
        correction=last[n][0].inverted()@first[n][0]
        row[n]=(q@Quaternion().slerp(correction,t),v+(first[n][1]-last[n][1])*t)
standing=source['Standing'][0]
def blend(a,b,t):return {n:(a[n][0].slerp(b[n][0],t),a[n][1].lerp(b[n][1],t)) for n in a}
# Native descriptor attack is 1 s to damage; source strike crosses forward at ~0.27 s.
attack=source['Attack'];lead=22
source['Attack']=[blend(standing,attack[0],i/lead) for i in range(lead)]+attack+[blend(attack[-1],standing,(i+1)/7) for i in range(7)]
# Preserve source hit speed inside its native 0.625 s window.
source['Hit']=[blend(standing,source['Hit'][0],i/3) for i in range(3)]+source['Hit']
source['Hit'][-3:]=[blend(source['Hit'][-3],standing,(i+1)/3) for i in range(3)]
source['Fidget']=[blend(standing,source['Fidget'][0],i/5) for i in range(5)]+source['Fidget']+[blend(source['Fidget'][-1],standing,(i+1)/5) for i in range(5)]
source['Death']=[blend(standing,source['Death'][0],i/4) for i in range(4)]+source['Death']
# Runtime and Blender must evaluate the same four influences.
for v in body.data.vertices:
    weights=sorted([(g.group,g.weight) for g in v.groups if g.weight>1e-6],key=lambda x:-x[1])[:4]
    assert weights
    for group in body.vertex_groups:group.remove([v.index])
    total=sum(w for _,w in weights)
    for g,w in weights:body.vertex_groups[g].add([v.index],w/total,'REPLACE')
sole=[v.index for v in body.data.vertices if v.co.z<.055 and body.data.attributes['piece'].data[v.index].value==0]
def floor(ids):
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();value=min((body.matrix_world@mesh.vertices[i].co).z for i in ids);ev.to_mesh_clear();return value
report={}
for role,rows in source.items():
    mins=[]
    for row in rows:pose(row);mins.append(floor(sole))
    offset=-mins[0] if role=='Death' else -min(mins)
    if role=='Death':
        # Ground the actual back/crest during the authored collapse, with the source floor trajectory retained.
        offsets=[]
        for i,row in enumerate(rows):
            pose(row);low=floor(range(len(body.data.vertices)));offsets.append(max(offset,-low+.003))
    elif role=='Running':offsets=[offset]*len(rows)
    else:offsets=[-z+.001 for z in mins]
    for row,dz in zip(rows,offsets):
        pose(row);pb=rig.pose.bones['B_Pelvis'];m=pb.matrix.copy();m.translation.z+=dz;pb.matrix=m;row['B_Pelvis']=(pb.rotation_quaternion.copy(),pb.location.copy())
    report[role]={'duration':(len(rows)-1)/30,'sole_min_before':min(mins),'sole_max_min_before':max(mins),'root_offset':offset}
source['Dead']=[source['Death'][-1],source['Death'][-1]]
for role,rows in source.items():
    old=bpy.data.actions.get(role)
    if old:bpy.data.actions.remove(old)
    act=bpy.data.actions.new(role);act.use_fake_user=True;select(act);prev={}
    for f,row in enumerate(rows):
        pose(row)
        for pb in rig.pose.bones:
            q=pb.rotation_quaternion.copy()
            if pb.name in prev and q.dot(prev[pb.name])<0:q.negate()
            pb.rotation_quaternion=q;prev[pb.name]=q.copy();pb.keyframe_insert('rotation_quaternion',frame=f)
            if pb.name=='B_Pelvis':pb.keyframe_insert('location',frame=f)
    act.use_frame_range=True;act.frame_start=0;act.frame_end=len(rows)-1
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for key in fc.keyframe_points:key.interpolation='LINEAR'
# Recompute twist rotations without applying the skin ramps a second time.
tree=ast.parse((p/'scripts/twist_bones.py').read_text());functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('twist_about','bake_twist')]
exec(compile(ast.Module(body=functions,type_ignores=[]),'twist_bones.py','exec'),globals());FA=UA=.5
for role in source:bake_twist(bpy.data.actions[role])
select(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
upd();add_club(rig)
select(bpy.data.actions['Standing']);scene.frame_set(0)
(p/'review/arm_choices.json').write_text(json.dumps(arm_choices,indent=2,default=float))
(p/'review/authored_motion.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/authored.blend'))
