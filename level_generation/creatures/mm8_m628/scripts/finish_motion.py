"""Finish native-timed bow release, hit, glance, death drop and held corpse on the fitted pilots."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/equipped.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;scene.render.fps=30
G=json.loads((P/'work/grip_pose.json').read_text());bowdata=json.loads(scene['bow_local'])
piece=np.array([x.value for x in body.data.attributes['piece'].data])
body_ids=np.where(piece<4000)[0];hand_faces=[tuple(f.vertices)for f in body.data.polygons if all(piece[i]==5 for i in f.vertices)]
gn={g.index:g.name for g in body.vertex_groups}
feet=np.array([v.index for v in body.data.vertices if sum(g.weight for g in v.groups if
    gn[g.group]in ['B_L_Foot','B_R_Foot','B_L_Toe0','B_R_Toe0'])>.7])

def action(a):
    rig.animation_data.action=a
    if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]

def get():return {b.name:(b.rotation_quaternion.copy(),b.location.copy(),b.scale.copy())for b in rig.pose.bones}
def put(p):
    action(None)
    for n,(q,l,s)in p.items():
        b=rig.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=l;b.scale=s
    bpy.context.view_layer.update()

def sample(a,f):action(a);scene.frame_set(int(f),subframe=float(f%1));return get()
def mesh():
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
    co=np.empty(len(m.vertices)*3);m.vertices.foreach_get('co',co);ev.to_mesh_clear();return co.reshape(-1,3)
def smooth(x):x=float(np.clip(x,0,1));return x*x*(3-2*x)
def blend(a,b,t):return {n:(q.slerp(b[n][0],t),l.lerp(b[n][1],t),s.lerp(b[n][2],t))for n,(q,l,s)in a.items()}
raw={a.name:[sample(a,f)for f in range(int(a.frame_range[1])+1)]for a in list(bpy.data.actions)}
home=raw['Standing'][0];put(home)
carry_hand=rig.pose.bones['B_L_Hand'].matrix.copy()
put(raw['SourceDeath'][-1]);pel=rig.pose.bones['B_Pelvis'];m=pel.matrix.copy();m.translation.x*=.5;m.translation.y*=.5;pel.matrix=m
bpy.context.view_layer.update();corpse_xyz=mesh();drop_y=float(corpse_xyz[body_ids,1].min())-.30
put(home)
lead=13;release=lead+14.5
output={'Standing':raw['Standing'],'Walking':raw['Walking'],'Attack':raw['Standing'][:lead]+raw['Attack']}
hit=[];base=raw['SourceHit'][0]
for f,p in enumerate(raw['SourceHit']):
    pose={n:(q.copy(),l.copy(),s.copy())for n,(q,l,s)in home.items()}
    weight=1-smooth((f-9)/6)
    for n in pose:
        if n.startswith('B_') and not any(k in n for k in ['Thigh','Calf','Foot','Toe','Pelvis','Finger']):
            q=home[n][0]@(base[n][0].inverted()@p[n][0]);pose[n]=(home[n][0].slerp(q,weight),home[n][1],home[n][2])
    hit.append(pose)
output['Hit']=hit
glance=[]
for f in range(16):
    put(home);b=rig.pose.bones['B_Head'];m=b.matrix.copy();t=m.translation.copy()
    m=Matrix.Rotation(math.radians(8)*math.sin(math.pi*f/15)**2,4,'Z')@m;m.translation=t;b.matrix=m
    bpy.context.view_layer.update();glance.append(get())
output['Fidget']=glance
output['Death']=[blend(home,p,smooth(f/7))for f,p in enumerate(raw['SourceDeath'])]
record={};fall_start=None;final_bow=None
for name,poses in output.items():
    final=[];rows=[]
    for f,p in enumerate(poses):
        put(p)
        rig.pose.bones['Bow'].matrix_basis.identity();rig.pose.bones['Arrow'].matrix_basis.identity()
        for n,q in G['finger_local'].items():
            rig.pose.bones[n].rotation_quaternion=Quaternion(q).slerp(Quaternion(),smooth((f-8)/7)if name=='Death'else 0)
        if name=='Hit':
            recoil=math.sin(math.pi*f/max(1,len(poses)-1))**2
            target=carry_hand.translation+Vector((.07,-.10,-.025))*recoil
            armik.solve(rig,'L',target,pole=Vector((.26,.12,.85)),hand_rot=carry_hand.to_3x3())
        if name=='Death':
            b=rig.pose.bones['B_Pelvis'];m=b.matrix.copy();m.translation.x*=.5;m.translation.y*=.5;b.matrix=m
            rig.pose.bones['Jaw'].rotation_quaternion=Quaternion((1,0,0),.15*smooth((f-9)/10))
        bpy.context.view_layer.update()
        xyz=mesh();ids=body_ids if name=='Death'else feet
        correction=float(xyz[ids,2].min())-.001
        root=rig.pose.bones['B_Pelvis'];M=root.matrix.copy();M.translation.z-=correction;root.matrix=M
        bpy.context.view_layer.update()
        if name=='Death':
            if f==8:fall_start=rig.pose.bones['Bow'].matrix.copy()
            if f>8:
                if final_bow is None:
                    final_bow=Matrix.Rotation(math.pi/2,4,'Y')@Matrix.Rotation(.12,4,'Z')
                    local=np.array([tuple(rig.data.bones['Bow'].matrix_local.inverted()@v.co)
                        for v in body.data.vertices if piece[v.index]in [4000,4004]])
                    low=min((final_bow.to_3x3()@Vector(v)).z for v in local)
                    final_bow.translation=(fall_start.translation.x+.18,drop_y,-low+.002)
                t=float(np.clip((f-8)/15,0,1));q=fall_start.to_quaternion().slerp(final_bow.to_quaternion(),smooth(t))
                M=q.to_matrix().to_4x4();M.translation=fall_start.translation.lerp(final_bow.translation,t)
                M.translation.z=final_bow.translation.z+(fall_start.translation.z-final_bow.translation.z)*(1-t*t)
                rig.pose.bones['Bow'].matrix=M;bpy.context.view_layer.update()
        bm=rig.pose.bones['Bow'].matrix.copy();tips=[bm@Vector(v)for v in bowdata['tips']]
        mid=tips[0].lerp(tips[1],(.6317-.065)/(.6317+.6868))
        sf=f-lead;draw=smooth((sf-5)/3)*(1-smooth((sf-14)/.5))if name=='Attack'else 0
        target=rig.pose.bones['B_R_Finger11'].head.lerp(rig.pose.bones['B_R_Finger12'].head,.5)
        # The string touches the glove surface facing the bow, rather than the hidden joint centre.
        xyz=mesh();tree=BVHTree.FromPolygons([Vector(v)for v in xyz],hand_faces,all_triangles=False)
        direction=(bm.translation-target).normalized()
        hit=tree.ray_cast(target+direction*.06,-direction,.10)
        if hit[0] is not None:target=hit[0]+direction*.0006
        nock=mid.lerp(target,draw)
        for bn,start in zip(['StringTop','StringBottom'],tips):
            delta=nock-start;M=delta.to_track_quat('Z','Y').to_matrix().to_4x4();M.translation=start
            rig.pose.bones[bn].matrix=M@Matrix.Scale(delta.length,4)
        arrow_rest=bm@Vector((0,-.02,.065));d=arrow_rest-nock
        M=d.to_track_quat('Z','Y').to_matrix().to_4x4();M.translation=nock
        visible=name=='Attack'and 5<=sf<14.5
        rig.pose.bones['Arrow'].matrix=M@Matrix.Scale(1 if visible else .00001,4)
        bpy.context.view_layer.update();final.append(get())
        rows.append({'frame':f,'time':f/30,'floor_correction':correction,'draw':draw,'arrow_visible':visible,
            'nock':list(nock),'arrow_rest':list(arrow_rest),'arrow_pitch_degrees':math.degrees(math.atan2(d.z,math.hypot(d.x,d.y)))if visible else None})
    output[name]=final;record[name]=rows
output['Dead']=[output['Death'][-1]]*31
# Author the release halfway between source frames; dense prop keys preserve the fast string return.
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
for name,poses in output.items():
    a=bpy.data.actions.new(name);a.use_fake_user=True
    for f,p in enumerate(poses):
        put(p);action(a)
        for b in rig.pose.bones:
            if b.name=='Socket_Arrow':continue
            b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
            if b.name in ['Arrow','StringTop','StringBottom']:b.keyframe_insert('scale',frame=f)
    a.use_frame_range=True;a.frame_start=0;a.frame_end=len(poses)-1
    for layer in a.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                for fc in cb.fcurves:
                    for k in fc.keyframe_points:k.interpolation='LINEAR'
action(None)
for b in rig.pose.bones:b.matrix_basis.identity()
scene['attack_impact_seconds']=release/30
(P/'work/final_motion.json').write_text(json.dumps({'impact_seconds':release/30,'source_lead_frames':lead,
    'clips':record,'limitations':['Bow limbs are rigid; the string and nocked arrow animate independently.']},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/motion_complete.blend'))
common.workbench_clay(scene)
for name,frames in [('Attack',[20,25,27,29]),('Hit',[0,7,15]),('Death',[0,8,16,len(output['Death'])-1]),('Fidget',[7])]:
    action(bpy.data.actions[name])
    for f in frames:
        scene.frame_set(f)
        common.render_views(str(P/f'review/full_{name}_{f}'),.35 if name=='Death' else 1.0,3.5 if name=='Death'else 2.55,
            views=('front','left','three_quarter'),resolution=(800,500)if name=='Death'else(400,600))
