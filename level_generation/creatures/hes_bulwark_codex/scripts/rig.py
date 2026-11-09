"""Measured rigid four-leg rig. Analytic IK is baked without dependency-graph/action feedback."""
import json,math,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from geometry import select,render,triangles
bpy.ops.wm.open_mainfile(filepath=str(P/'work/candidate_80.blend'))
scene=bpy.context.scene;scene.render.fps=30;scene.render.fps_base=1
info=json.loads((P/'work/parts.json').read_text());joints=info['joints']
parts=[o for o in scene.objects if o.type=='MESH']
# Reduction may move a sole by millimetres. Ground each complete foot before defining the rest anchors.
for leg,j in joints.items():
    foot=bpy.data.objects[f'B_{leg}_Foot']; dz=-min(v.co.z for v in foot.data.vertices)
    for v in foot.data.vertices:v.co.z+=dz
    j['ankle'][2]+=dz;j['sole'][2]+=dz;j['reduced_foot_adjustment']=dz
arm=bpy.data.armatures.new('BulwarkRig');rig=bpy.data.objects.new('BulwarkRig',arm);scene.collection.objects.link(rig)
select([rig]);bpy.ops.object.mode_set(mode='EDIT')
def bone(name,head,tail,parent=None,deform=True):
    b=arm.edit_bones.new(name);b.head=head;b.tail=tail;b.use_deform=deform
    if parent:b.parent=arm.edit_bones[parent]
    b.align_roll(Vector((0,0,1)) if abs((b.tail-b.head).normalized().z)<.9 else Vector((0,-1,0)))
    return b
bone('B_Root',(0,0,0),(0,0,.3))
bone('B_Chassis',(0,0,1.3),(0,0,1.6),'B_Root')
bone('B_Head',(0,0,1.84),(0,0,2.14),'B_Chassis')
bars=np.array([v.co[:] for o in parts if 'Recoil' in o.name for v in o.data.vertices])
rear=bars[bars[:,1]>np.percentile(bars[:,1],90)]
# The housing pitches around the measured pair of flank trunnions, as the Ward route.
pivot=Vector((.003,.058,2.484))
bone('B_Barrel',pivot,pivot+Vector((0,-.3,0)),'B_Head')
for row in ('Upper','Lower'):bone('B_Recoil_'+row,pivot,pivot+Vector((0,-.3,0)),'B_Barrel')
for leg,j in joints.items():
    hip,knee,ankle=[Vector(j[x]) for x in ('hip','knee','ankle')]
    bone(f'B_{leg}_Upper',hip,knee,'B_Chassis')
    bone(f'B_{leg}_Lower',knee,ankle,f'B_{leg}_Upper')
    bone(f'B_{leg}_Foot',ankle,ankle+Vector((0,-.25,0)),f'B_{leg}_Lower')
sockets={}
for row in ('Upper','Lower'):
    pts=np.array([v.co[:] for v in bpy.data.objects['B_Recoil_'+row].data.vertices]);front=pts[pts[:,1]<pts[:,1].min()+.08]
    pos=Vector(((front.min(0)+front.max(0))/2).tolist());pos.y-=.02;sockets[row]=pos
    bone('Socket_Muzzle_'+row,pos,pos+Vector((0,-.1,0)),'B_Recoil_'+row,False)
pos=(sockets['Upper']+sockets['Lower'])/2
bone('Socket_Muzzle',pos,pos+Vector((0,-.1,0)),'B_Barrel',False)
bpy.ops.object.mode_set(mode='OBJECT')
for o in parts:
    group=o.vertex_groups.new(name='B_Barrel' if o.name=='B_Head' else o.name);group.add(list(range(len(o.data.vertices))),1,'REPLACE')
    m=o.modifiers.new('Rig','ARMATURE');m.object=rig;o.parent=rig
    assert all(len(v.groups)==1 and v.groups[0].weight==1 for v in o.data.vertices)
rest={b.name:b.matrix_local.copy() for b in arm.bones}
parents={b.name:b.parent.name if b.parent else None for b in arm.bones}
restrel={n:rest[parents[n]].inverted()@r if parents[n] else r for n,r in rest.items()}

def around(p,axis,angle):return Matrix.Translation(p)@Matrix.Rotation(math.radians(angle),4,axis)@Matrix.Translation(-Vector(p))
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def bone_at(name,head,tail):
    direction=rest[name].col[1].xyz.normalized();target=(tail-head).normalized()
    q=direction.rotation_difference(target)
    return Matrix.LocRotScale(head,q@rest[name].to_quaternion(),Vector((1,1,1)))

reach_max=0

def transforms(name,t,duration):
    global reach_max
    u=t/duration;phase=u%1; lift=0; yaw=0; pitch=0;recoil=0;splay=0
    feet={l:Vector(j['ankle']) for l,j in joints.items()}
    if name in ('Walking','Running'):
        running=name=='Running';duty=.44 if running else .65;stride=.9 if running else .65
        lift=(.012 if running else .006)*math.sin(4*math.pi*phase)
        for l,target in feet.items():
            q=(phase+(0 if l in ('LF','RH') else .5))%1
            stance=stride*duty
            if q<duty:dy=-stance/2+stride*q;dz=0
            else:
                v=(q-duty)/(1-duty);dy=stance/2-stance*smooth(v);dz=(.25 if running else .16)*math.sin(math.pi*v)**2
            target.y+=dy;target.z+=dz
    elif name in ('Standing','Fidget'):
        yaw=(8 if name=='Standing' else 18)*math.sin(2*math.pi*u)
        pitch=2*math.sin(4*math.pi*u)
    elif name in ('Attack','Cast'):
        shot=5/30 if name=='Attack' else .5
        k=max(0,1-abs(t-shot)/(.12 if t<shot else .32));pitch=4*k;recoil=.14*k
    elif name=='Sweep':yaw=22*math.sin(2*math.pi*u)*math.sin(math.pi*u)
    elif name=='Hit':
        k=math.sin(math.pi*u)*math.exp(-3*u);lift=-.06*k;pitch=5*k;yaw=3*k
    elif name in ('Death','Dead'):
        k=smooth((t-.1)/1.1) if name=='Death' else 1
        lift=-.52*k;pitch=-15*k;yaw=6*k;splay=.14*k
        for l,target in feet.items():target.x+=math.copysign(splay,target.x)
    chassis=Matrix.Translation((0,0,lift))
    head=chassis@around(rest['B_Head'].translation,'Z',yaw)
    barrel=head@around(pivot,'X',-pitch)
    world={'B_Root':rest['B_Root'],'B_Chassis':chassis@rest['B_Chassis'],'B_Head':head@rest['B_Head'],'B_Barrel':barrel@rest['B_Barrel']}
    for row in ('Upper','Lower'):world['B_Recoil_'+row]=barrel@Matrix.Translation((0,recoil,0))@rest['B_Recoil_'+row]
    for l,j in joints.items():
        a=Vector(j['hip'])+Vector((0,0,lift));b=Vector(j['knee']);c=Vector(j['ankle']);target=feet[l]
        la=(b-Vector(j['hip'])).length;lb=(c-b).length
        d=target-a;dist=d.length;reach_max=max(reach_max,dist/(la+lb))
        assert abs(la-lb)+1e-5<dist<la+lb-1e-5,(name,t,l,'unreachable',dist,la+lb)
        direction=d.normalized();pole=b-a;pole=(pole-direction*pole.dot(direction)).normalized()
        ca=(la*la+dist*dist-lb*lb)/(2*la*dist)
        knee=a+la*(direction*ca+pole*math.sqrt(max(0,1-ca*ca)))
        world[f'B_{l}_Upper']=bone_at(f'B_{l}_Upper',a,knee)
        world[f'B_{l}_Lower']=bone_at(f'B_{l}_Lower',knee,target)
        world[f'B_{l}_Foot']=Matrix.LocRotScale(target,rest[f'B_{l}_Foot'].to_quaternion(),Vector((1,1,1)))
    for n in rest:
        if n.startswith('Socket_'):world[n]=world[parents[n]]@restrel[n]
    return world

CLIPS={'Standing':4.,'Walking':1.2,'Running':.8,'Attack':.6,'Cast':1.,'Sweep':1.5,'Hit':.6,'Death':1.4,'Dead':1.,'Fidget':4.}
for name,duration in CLIPS.items():
    action=bpy.data.actions.new(name);action.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=action
    previous={}
    for f in range(round(duration*30)+1):
        world=transforms(name,f/30,duration)
        for b in rig.pose.bones:
            n=b.name;parent=parents[n]
            basis=restrel[n].inverted()@(world[parent].inverted()@world[n] if parent else world[n])
            loc,rot,scale=basis.decompose()
            if n in previous and rot.dot(previous[n])<0:rot.negate()
            previous[n]=rot.copy();b.rotation_mode='QUATERNION';b.location=loc;b.rotation_quaternion=rot;b.scale=(1,1,1)
            b.keyframe_insert('location',frame=f);b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('scale',frame=f)
    action.use_frame_range=True;action.frame_start=0;action.frame_end=round(duration*30)
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for key in fc.keyframe_points:key.interpolation='LINEAR'
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
select(parts+[rig]);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/bulwark_rig.blend'))
# Check the actual evaluated skin, including interpolation between the authored frames.
report={'triangles':sum(triangles(o) for o in parts),'bones':len(arm.bones),'max_influences':1,'joints':joints,'barrel_pivot':list(pivot),'ik_max_reach_ratio':reach_max,'clips':{},'loops':{},'rigid_weights':True,'pitch_assembly':'housing and barrels around flank trunnions; recoil children slide separately','limits':{'floor_min_m':-.015,'rigid_edge_relative_error':1e-4}}
base_edges={o.name:np.array([(o.data.vertices[e.vertices[0]].co-o.data.vertices[e.vertices[1]].co).length for e in o.data.edges]) for o in parts}
for name,duration in CLIPS.items():
    action=bpy.data.actions[name];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
    minimum=1e9;maxedge=0;foot_floor={l:[1e9,-1e9] for l in joints};first=None;last=None
    for f in np.arange(0,round(duration*30)+.01,.5):
        scene.frame_set(int(f),subframe=float(f%1));dg=bpy.context.evaluated_depsgraph_get();allco=[]
        for o in parts:
            ev=o.evaluated_get(dg);me=ev.to_mesh();co=np.array([v.co[:] for v in me.vertices]);allco.append(co);minimum=min(minimum,float(co[:,2].min()))
            edge=np.array([np.linalg.norm(co[e.vertices[0]]-co[e.vertices[1]]) for e in me.edges]);orig=base_edges[o.name];valid=orig>1e-5
            maxedge=max(maxedge,float(np.max(abs(edge[valid]/orig[valid]-1))))
            if o.name.endswith('_Foot'):
                l=o.name.split('_')[1];z=float(co[:,2].min());foot_floor[l][0]=min(foot_floor[l][0],z);foot_floor[l][1]=max(foot_floor[l][1],z)
            ev.to_mesh_clear()
        pos=np.concatenate(allco)
        if first is None:first=pos
        last=pos
    report['clips'][name]={'duration_s':duration,'samples':round(duration*60)+1,'minimum_z_m':minimum,'rigid_edge_relative_error':maxedge,'foot_floor_range_m':foot_floor}
    assert minimum>=-.015,(name,'floor',minimum)
    assert maxedge<1e-4,(name,'rigid distortion',maxedge)
    if name in ('Standing','Walking','Running','Fidget'):
        error=float(np.max(np.linalg.norm(last-first,axis=1)));report['loops'][name]=error;assert error<1e-4
    if name=='Death':death_end=last
    if name=='Dead':report['death_dead_error_m']=float(np.max(np.linalg.norm(first-death_end,axis=1)));assert report['death_dead_error_m']<1e-4
    if name in ('Walking','Running','Attack','Death'):
        scene.frame_set({'Walking':9,'Running':7,'Attack':5,'Death':42}[name]);render('rig_'+name)
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];scene.frame_set(0)
select(parts+[rig]);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/bulwark_rig.blend'))
bpy.ops.export_scene.gltf(filepath=str(P/'review/bulwark_rig_preview.glb'),use_selection=True,export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
(P/'review/geometry/rig_gate.json').write_text(json.dumps(report,indent=2)+'\n')
print('RIG_PASS',report['triangles'],report['bones'],reach_max,flush=True)
