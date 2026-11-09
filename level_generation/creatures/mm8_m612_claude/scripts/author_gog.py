"""Author the wingless Gog's upright idle/fidget and bind its tail and rigid facial parts."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'))
import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/animated_raw.blend'))
sc=bpy.context.scene;sc.render.fps=30
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
def action(a):
    rig.animation_data_create();rig.animation_data.action=a
    if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def reset():
    action(None)
    for pb in rig.pose.bones:pb.matrix_basis=Matrix()
    bpy.context.view_layer.update()
def snapshot():
    return {pb.name:(pb.rotation_quaternion.copy(),pb.location.copy()) for pb in rig.pose.bones}
def sample(a,f):
    action(a);sc.frame_set(int(f),subframe=f-int(f));return snapshot()
def put(p):
    action(None)
    for n,(q,l) in p.items():
        pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l
    bpy.context.view_layer.update()
def write(name,poses):
    old=bpy.data.actions.get(name)
    if old:bpy.data.actions.remove(old)
    a=bpy.data.actions.new(name);a.use_fake_user=True;action(a);prev={}
    for f,pose in enumerate(poses):
        for n,(q,l) in pose.items():
            pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION'
            if n in prev and q.dot(prev[n])<0:q=-q
            prev[n]=q.copy();pb.rotation_quaternion=q;pb.location=l
            pb.keyframe_insert('rotation_quaternion',frame=f)
            if n=='B_Pelvis':pb.keyframe_insert('location',frame=f)
    a.use_frame_range=True;a.frame_start=0;a.frame_end=len(poses)-1;action(None)
    return a
def smooth(x):
    x=np.clip(x,0,1);return float(x*x*(3-2*x))
def blend(a,b,w):
    return {n:(a[n][0].slerp(b[n][0] if a[n][0].dot(b[n][0])>=0 else -b[n][0],w),a[n][1].lerp(b[n][1],w)) for n in a}
def rotate(n,axis,deg):
    m=armik.W(rig,n);t=m.translation.copy();m=Matrix.Rotation(math.radians(deg),4,axis)@m;m.translation=t
    armik.set_world(rig,n,m)
reset()
co=np.array([tuple(v.co) for v in me.vertices])
pv=np.zeros(len(co),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
# The tail shaping mask fades out at the barb; the binding mask must include the entire tip.
tw=np.clip((co[:,1]-.17)/.10,0,1)*np.clip((.95-co[:,2])/.16,0,1)
tw*=np.maximum(np.clip((.16-np.abs(co[:,0]))/.04,0,1),np.clip((co[:,1]-.3)/.05,0,1))
tw=tw*tw*(3-2*tw)
path=np.array(json.loads((P/'work/cleanup.json').read_text())['tail_path'])
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for i,(a,b) in enumerate(zip(path[:-1],path[1:])):
    bone=rig.data.edit_bones.new(f'Tail{i:02}')
    bone.head=a;bone.tail=b
    bone.parent=rig.data.edit_bones['B_Pelvis' if i==0 else f'Tail{i-1:02}']
bpy.ops.object.mode_set(mode='OBJECT')
groups={g.name:g for g in body.vertex_groups}
for i in range(len(path)-1):groups[f'Tail{i:02}']=body.vertex_groups.new(name=f'Tail{i:02}')
def replace_weights(i,weights):
    for g in body.vertex_groups:g.remove([i])
    total=sum(weights.values());assert total>0
    for n,w in weights.items():
        if w>0.0001:groups[n].add([i],float(w/total),'REPLACE')
mid=(path[:-1]+path[1:])/2
tail_ids=set((18,21,22,24))
rigid={}
for piece in set(pv)-{0}:
    ids=np.where(pv==piece)[0]
    if piece in tail_ids:
        name=f'Tail{int(np.argmin(np.linalg.norm(mid-co[ids].mean(0),axis=1))):02}'
    else:
        assert co[ids,2].min()>1.27,(piece,co[ids,2].min())
        name='B_Head'
    rigid[int(piece)]=name
    for i in ids:replace_weights(int(i),{name:1.0})
for i in np.where((pv==0)&(tw>0.001))[0]:
    d=np.linalg.norm(mid-co[i],axis=1);nearest=np.argsort(d)[:2]
    w=1/np.maximum(d[nearest],0.005)**2;w/=w.sum()
    old={body.vertex_groups[e.group].name:e.weight*(1-tw[i]) for e in me.vertices[i].groups}
    for j,share in zip(nearest,w):old[f'Tail{j:02}']=float(share*tw[i])
    replace_weights(int(i),old)
# Remove spurious arm weight from the middle of the chest without inventing a weight boundary.
for i in np.where(pv==0)[0]:
    old={body.vertex_groups[e.group].name:e.weight for e in me.vertices[i].groups}
    arm_names=[n for n in old if 'UpperArm' in n or 'Forearm' in n]
    medial=smooth((abs(co[i,0])-.08)/.10)
    lost=sum(old[n]*(1-medial) for n in arm_names)
    if lost>0:
        for n in arm_names:old[n]*=medial
        old['B_Spine2']=old.get('B_Spine2',0)+lost
        replace_weights(int(i),old)
# A short mesh-neighbour blend removes abrupt weight changes at elbows and shoulder folds.
ordered=list(groups);gi={n:i for i,n in enumerate(ordered)}
weights=np.zeros((len(co),len(ordered)))
for v in me.vertices:
    for e in v.groups:weights[v.index,gi[body.vertex_groups[e.group].name]]=e.weight
adj=[[] for _ in co]
for edge in me.edges:
    a,b=edge.vertices
    if pv[a]==0 and pv[b]==0:adj[a].append(b);adj[b].append(a)
band=np.where((pv==0)&(co[:,2]>.90))[0]
for _ in range(10):
    nxt=weights.copy()
    for i in band:
        if adj[i]:
            rate=.45*smooth((co[i,2]-.90)/.12)*(1-smooth((co[i,2]-1.40)/.12))
            nxt[i]=(1-rate)*weights[i]+rate*weights[adj[i]].mean(0)
    weights=nxt
for i in band:replace_weights(int(i),{n:weights[i,j] for j,n in enumerate(ordered) if weights[i,j]>.0001})
# Head and neck must never inherit an arm or clavicle influence.
for i in np.where((pv==0)&(co[:,2]>1.38))[0]:
    old={body.vertex_groups[e.group].name:e.weight for e in me.vertices[i].groups}
    if old.get('B_Head',0)+old.get('B_Neck',0)<.3 and co[i,2]<1.5:continue
    unwanted=sum(v for n,v in old.items() if any(x in n for x in ('Arm','Hand','Finger','Clavicle')))
    old={n:v for n,v in old.items() if not any(x in n for x in ('Arm','Hand','Finger','Clavicle'))}
    old['B_Head']=old.get('B_Head',0)+unwanted;replace_weights(int(i),old)
(P/'work/rig_parts.json').write_text(json.dumps({'rigid_parts':rigid,'tail_bones':len(path)-1},indent=2))
# A relaxed threatening stance: upright torso, elbows forward and claws open.
reset()
for sd,sign in (('L',1),('R',-1)):
    rotate(f'B_{sd}_UpperArm','Y',sign*12)
    rotate(f'B_{sd}_Forearm','X',-28)
ST=snapshot()
poses=[]
for f in range(61):
    put(ST);phase=2*math.pi*f/60
    rotate('B_Spine','X',0.6*math.sin(phase))
    rotate('B_Spine2','X',-0.3*math.sin(phase))
    poses.append(snapshot())
write('Standing',poses)
poses=[]
for f in range(46):
    put(ST);phase=2*math.pi*f/45;envelope=math.sin(math.pi*f/45)**2
    rotate('B_Neck','Z',18*math.sin(phase)*envelope)
    rotate('B_Spine2','Z',4*math.sin(phase)*envelope)
    for sd in 'LR':rotate(f'B_{sd}_Forearm','X',-8*envelope)
    poses.append(snapshot())
write('Fidget',poses)
for name in ('Attack','Cast','Hit','Death'):
    a=bpy.data.actions[name];n=int(a.frame_range[1])
    poses=[sample(a,f) for f in range(n+1)]
    res=[]
    for i,p in enumerate(poses):
        for tail in (f'Tail{k:02}' for k in range(len(path)-1)):p[tail]=(Quaternion(),Vector())
        w=smooth(i/(5 if name=='Death' else 3))
        if name not in ('Death','Hit'):w=min(w,smooth((n-i)/4))
        if name=='Hit':w=min(w,smooth((n+8-i)/14))
        res.append(blend(ST,p,w))
    if name=='Hit':res += [blend(res[-1],ST,smooth(f/8)) for f in range(1,9)]
    if name in ('Attack','Cast'):
        # Add a native-length charge; preserve the selected clip's fast outward release.
        charge=[blend(ST,res[3],smooth(f/22)) for f in range(26)]
        res=charge+res[3:]
        assert len(res)==54
    write(name,res)
reset()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/animated_authored.blend'))
