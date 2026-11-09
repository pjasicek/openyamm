"""Fit native upright carry, planted source draw and a measured bow grip on the owned rig."""
import bpy, bmesh, json, math, sys
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector, Quaternion
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P/'scripts'))
import armik, common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilot_shoulders.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; scene = bpy.context.scene
G = json.loads((P/'work/grip_pose.json').read_text())
C, A = Vector(G['handle_centre_hand_local']), Vector(G['handle_axis_hand_local'])

def action(a):
    rig.animation_data.action = a
    if a and len(a.slots): rig.animation_data.action_slot = a.slots[0]

def get(): return {b.name:(b.rotation_quaternion.copy(), b.location.copy()) for b in rig.pose.bones}
def put(p):
    action(None)
    for n,(q,l) in p.items():
        b = rig.pose.bones[n]; b.rotation_mode='QUATERNION'; b.rotation_quaternion=q; b.location=l
    bpy.context.view_layer.update()

def sample(a,f):
    action(a); scene.frame_set(int(f), subframe=float(f%1)); return get()

raw = {a.name:[sample(a,f) for f in range(int(a.frame_range[1])+1)] for a in list(bpy.data.actions)}
put(raw['Attack'][12]); hp = rig.pose.bones['B_L_Hand'].matrix.copy()
axis = (hp.to_3x3()@A).normalized(); back = Vector((0,1,0)); back=(back-axis*back.dot(axis)).normalized()
local = hp.to_3x3().inverted() @ Matrix((back.cross(axis), back, axis)).transposed()
rest = rig.data.bones['B_L_Hand'].matrix_local @ Matrix.Translation(C) @ local.to_4x4()
action(None)
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.context.view_layer.objects.active = rig; bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones.new('Bow'); eb.head=rest.translation; eb.tail=eb.head+rest.to_3x3().col[1]*.1; eb.align_roll(rest.to_3x3().col[2])
eb.parent=rig.data.edit_bones['B_L_Hand']
for name in ['StringTop','StringBottom']:
    eb=rig.data.edit_bones.new(name); eb.head=(0,0,0); eb.tail=(0,1,0); eb.parent=rig.data.edit_bones['Bow']
bpy.ops.object.mode_set(mode='OBJECT')
for b in rig.pose.bones: b.rotation_mode='QUATERNION'

with bpy.data.libraries.load(str(P/'work/bow_v1_parts.blend')) as (src,dst):
    dst.objects=[n for n in src.objects if n.startswith('P') and n[1:].isdigit()]
bow=[]
mat=bpy.data.materials.new('BowClay'); mat.diffuse_color=(.24,.10,.035,1)
for ob in dst.objects:
    scene.collection.objects.link(ob); pid=int(ob.name[1:]); ob.name='BowPart'+str(pid)
    for v in ob.data.vertices:
        x,y,z=v.co; pos=Vector((y*.7778,(x+.056)*.7778,(z-.938)*.7778))
        if pid==2:
            pos.x=y/.044*.020; pos.y=(x+.0555)/.0485*.020
        v.co=rest@pos
    ob.data.materials.clear(); ob.data.materials.append(mat)
    ob.vertex_groups.clear(); ob.vertex_groups.new(name='Bow').add(list(range(len(ob.data.vertices))),1,'REPLACE')
    ob.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[4000]*len(ob.data.vertices))
    bow.append(ob)
tiplocal=[Vector((0,(.13+.056)*.7778,(1.75-.938)*.7778)),
          Vector((0,(.16+.056)*.7778,(.055-.938)*.7778))]
for name,pid in [('StringTop',4001),('StringBottom',4002)]:
    me=bpy.data.meshes.new(name)
    me.from_pydata([(math.cos(j*math.tau/6)*.001,math.sin(j*math.tau/6)*.001,z)
        for z in [0,1] for j in range(6)],[],[(j,(j+1)%6,(j+1)%6+6,j+6)for j in range(6)])
    ob=bpy.data.objects.new(name+'Mesh',me); scene.collection.objects.link(ob); me.materials.append(mat)
    ob.vertex_groups.new(name=name).add(list(range(12)),1,'REPLACE')
    me.attributes.new('piece','INT','POINT').data.foreach_set('value',[pid]*12); bow.append(ob)
bpy.ops.object.select_all(action='DESELECT'); body.select_set(True)
for ob in bow: ob.select_set(True)
bpy.context.view_layer.objects.active=body; bpy.ops.object.join()

def fingers():
    for n,q in G['finger_local'].items(): rig.pose.bones[n].rotation_quaternion=q
    bpy.context.view_layer.update()

def leg(side,T,R):
    names=[f'B_{side}_{s}' for s in ['Thigh','Calf','Foot']]
    U,F,H=[rig.pose.bones[n] for n in names]; S=U.head.copy(); E=F.head.copy(); W=H.head.copy()
    a,b=(E-S).length,(W-E).length; d=min((T-S).length,(a+b)*.999)
    direction=(T-S).normalized(); pole=Vector((0,-1,0)); pole=(pole-direction*pole.dot(direction)).normalized()
    c=float(np.clip((a*a+d*d-b*b)/(2*a*d),-1,1)); knee=S+a*(direction*c+pole*math.sqrt(1-c*c))
    for n,child,want in [(names[0],names[1],knee),(names[1],names[2],T)]:
        pb=rig.pose.bones[n]; q=(rig.pose.bones[child].head-pb.head).rotation_difference(want-pb.head)
        armik.set_world(rig,n,armik.rot_world(armik.W(rig,n),q.to_matrix()@pb.matrix.to_3x3()))
    armik.set_world(rig,names[2],armik.rot_world(armik.W(rig,names[2]),R))

carry_hand_rotation=None
def carry(p, planted=False):
    global carry_hand_rotation
    put(p); fingers()
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh=ev.to_mesh()
    xyz=np.array([tuple(v.co)for v in mesh.vertices]); ev.to_mesh_clear()
    names={g.index:g.name for g in body.vertex_groups}
    minima={}
    for sd in 'LR':
        ids=[v.index for v in body.data.vertices if sum(g.weight for g in v.groups
             if names[g.group] in [f'B_{sd}_Foot',f'B_{sd}_Toe0'])>.7]
        minima[sd]=float(xyz[ids,2].min())
    shift=min(minima.values())-.001
    pb=rig.pose.bones['B_Pelvis']; m=pb.matrix.copy(); m.translation.z-=shift; pb.matrix=m
    bpy.context.view_layer.update()
    if planted:
        for sd in 'LR':
            pb=rig.pose.bones[f'B_{sd}_Foot']; t=pb.head.copy(); t.z-=minima[sd]-shift-.001
            leg(sd,t,pb.matrix.to_3x3().copy())
    # Match the native low relaxed draw hand and upright bow held near the waist.
    for side,target in [('L',(.36,-.28,1.10)),('R',(-.300,-.065,.99))]:
        head=rig.pose.bones['B_Pelvis'].head
        t=Vector(target); t.z+=head.z-1.035
        armik.solve(rig,side,t,pole=Vector((.26 if side=='L' else -.35,.12,.85)))
        if side=='L':
            if carry_hand_rotation is None:
                carry_hand_rotation=armik.hand_for_axis(rig,side,A,(0,0,1),k_twist=.65)[0].copy()
            R=carry_hand_rotation
        else:
            F=rig.pose.bones['B_R_Forearm'].matrix.to_3x3()
            R=F@rig.data.bones['B_R_Forearm'].matrix_local.to_3x3().inverted()@rig.data.bones['B_R_Hand'].matrix_local.to_3x3()
        armik.set_world(rig,'B_'+side+'_Hand',armik.rot_world(armik.W(rig,'B_'+side+'_Hand'),R))
    return get()

homes=[carry(p,planted=True) for p in raw['Standing']]
home=homes[0]; put(home)
headrot={n:rig.pose.bones[n].matrix.to_3x3().copy()for n in ['B_Neck','B_Head']}
foot={s:(rig.pose.bones[f'B_{s}_Foot'].head.copy(),rig.pose.bones[f'B_{s}_Foot'].matrix.to_3x3().copy()) for s in 'LR'}

def smooth(t): t=float(np.clip(t,0,1)); return t*t*(3-2*t)
out={'Standing':homes,'Walking':[carry(p) for p in raw['Walking']]}
shot=[]
for f,p in enumerate(raw['Attack']):
    put(p); chest=rig.pose.bones['B_Spine'].matrix.to_3x3().copy()
    for sd in 'LR':
        n=f'B_{sd}_Clavicle'; rig.pose.bones[n].rotation_quaternion=home[n][0].slerp(p[n][0],.25)
    bpy.context.view_layer.update()
    b=rig.pose.bones['B_Pelvis']; b.rotation_quaternion=home['B_Pelvis'][0].slerp(p['B_Pelvis'][0],.2)
    b.location=home['B_Pelvis'][1]; bpy.context.view_layer.update()
    for side in 'LR': leg(side,*foot[side])
    armik.set_world(rig,'B_Spine',armik.rot_world(armik.W(rig,'B_Spine'),chest)); fingers()
    for n,R in headrot.items(): armik.set_world(rig,n,armik.rot_world(armik.W(rig,n),R))
    # Keep the bow vertical through the draw, with only source roll outside the aiming interval.
    b=rig.pose.bones['B_L_Hand']; a=(b.matrix.to_3x3()@A).normalized()
    w=smooth((f-3)/4)*(1-smooth((f-17)/5))
    q=Quaternion().slerp(a.rotation_difference(Vector((0,0,1))),w)
    armik.set_world(rig,b.name,armik.rot_world(b.matrix,q.to_matrix()@b.matrix.to_3x3()))
    # Keep the arrow rest level with the draw fingers after planting the source's large step.
    aiming=smooth((f-4)/4)*(1-smooth((f-14)/4))
    wrist=rig.pose.bones['B_L_Hand'].head.copy().lerp(Vector((-.055,-.51,1.51)),aiming)
    armik.solve(rig,'L',wrist,pole=Vector((.40,-.1,1.20)))
    # Blend only the approach and recovery into native carry; retain the source draw arc.
    weight=smooth(f/5)*(1-smooth((f-18)/6)); current=get()
    shot.append({n:(home[n][0].slerp(q,weight),home[n][1].lerp(l,weight)) for n,(q,l) in current.items()})
out['Attack']=shot
trace={}
for name,poses in out.items():
    old=bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    a=bpy.data.actions.new(name); a.use_fake_user=True; rows=[]
    for f,p in enumerate(poses):
        put(p); fingers(); bm=rig.pose.bones['Bow'].matrix
        tips=[bm@v for v in tiplocal]; mid=tips[0].lerp(tips[1],.48)
        draw=smooth((f-5)/3)*(1-smooth((f-14)/1)) if name=='Attack' else 0
        kn=rig.pose.bones['B_R_Finger11'].head; tip=rig.pose.bones['B_R_Finger12'].head
        nock=mid.lerp(kn.lerp(tip,.5),draw)
        for bn,start in zip(['StringTop','StringBottom'],tips):
            direction=nock-start; M=direction.to_track_quat('Z','Y').to_matrix().to_4x4()
            M.translation=start; rig.pose.bones[bn].matrix=M@Matrix.Scale(direction.length,4)
        bpy.context.view_layer.update(); action(a)
        for b in rig.pose.bones:
            b.keyframe_insert('rotation_quaternion',frame=f); b.keyframe_insert('location',frame=f)
            if b.name.startswith('String'): b.keyframe_insert('scale',frame=f)
        rows.append({'frame':f,'bow_centre':list(bm.translation),'nock':list(nock),'draw':draw})
    a.use_frame_range=True; a.frame_start=0; a.frame_end=len(poses)-1; trace[name]=rows
action(None)
for b in rig.pose.bones: b.matrix_basis.identity()
scene['bow_local']=json.dumps({'hand_rotation':[list(r) for r in local],'grip':list(C),'tips':[list(v)for v in tiplocal]})
(P/'work/pilot_bow_trace.json').write_text(json.dumps(trace,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/pilot_bow.blend'))
common.workbench_clay(scene)
for name,f in [('Standing',0),('Attack',6),('Attack',12),('Attack',16),('Walking',6)]:
    action(bpy.data.actions[name]); scene.frame_set(f)
    common.render_views(str(P/f'review/pilot_bow_{name}_{f}'),.95,2.3,
        views=('front','left','three_quarter'),resolution=(400,600))
