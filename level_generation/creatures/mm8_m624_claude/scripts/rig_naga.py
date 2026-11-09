import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/fitted_body.blend'))
body=bpy.data.objects['Body'];me=body.data;co=np.array([v.co[:]for v in me.vertices]);pa=np.array([a.value for a in me.attributes['part'].data]);edges=np.array([e.vertices[:]for e in me.edges])
J=json.loads((P/'work/joints_final.json').read_text())['joints'];F=json.loads((P/'work/fingers_fit.json').read_text());T=json.loads((P/'work/tail_rest.json').read_text());line=np.array(T['joints']);K=T['root_index'];bones={};hands={}
def unit(v):return v/max(np.linalg.norm(v),1e-10)
def add(n,h,t,parent=None,palm=None):
    h=np.array(h);t=np.array(t);y=unit(t-h);z=np.array([0.,-1,0]) if palm is None else np.array(palm);z=unit(z-y*np.dot(z,y));x=unit(np.cross(y,z));z=np.cross(x,y)
    bones[n]={'head':h,'tail':t,'parent':parent,'rot':np.column_stack([x,y,z])}
add('Root',line[K],line[K]+[0,0,.08])
for i in list(range(K-1,-1,-1))+list(range(K,len(line)-1)):
    h,t=(line[i+1],line[i]) if i<K else (line[i],line[i+1]);parent='Root' if i in [K-1,K] else f'Serpent_{i+1:02}' if i<K else f'Serpent_{i-1:02}'
    add(f'Serpent_{i:02}',h,t,parent)
sp=[('Pelvis',line[0]),('Spine',[-.025,.045,1.32]),('Chest',[-.025,.05,1.51]),('UpperChest',[-.025,.07,1.70]),('Neck',[-.025,.025,1.83]),('Head',[-.025,.005,1.94])]
for i,(n,h) in enumerate(sp):add(n,h,sp[i+1][1] if i<len(sp)-1 else [-.025,-.02,2.11],'Serpent_00' if i==0 else sp[i-1][0])
for sd in F:
    sh,el,wr=[np.array(J[sd+'_'+n])for n in ['UpperArm','Forearm','Hand']];fj=F[sd];mid=np.array(fj['middle'][0]);across=np.array(fj['index'][0])-np.array(fj['pinky'][0]);direction=unit(mid-wr);normal=unit(np.cross(direction,across));normal*=1 if normal[1]<0 else -1
    hands[sd]={'forward':direction.tolist(),'across':unit(across).tolist(),'normal':normal.tolist()}
    add(sd+'_Shoulder',[-.025,.07,sh[2]],sh,'UpperChest' if sd[1]=='1' else 'Chest',normal)
    add(sd+'_UpperArm',sh,el,sd+'_Shoulder',normal);add(sd+'_Forearm',el,wr,sd+'_UpperArm',normal);add(sd+'_Hand',wr,mid,sd+'_Forearm',normal)
    for digit in ['thumb','index','middle','ring','pinky']:
        pts=np.array(fj[digit])
        for k in range(2):add(sd+'_'+digit+str(k),pts[k],pts[k+1],sd+'_Hand' if k==0 else sd+'_'+digit+'0',normal)
    # Separate rigid attachment bone, with handle axis across the palm.
    hc=wr+direction*.12+normal*.04;add(sd+'_Sword',hc,hc+unit(across)*.18,sd+'_Hand',normal)
hairpts=[[-.025,.16,2.08],[-.025,.31,1.85],[-.025,.4,1.6],[-.025,.44,1.35],[-.025,.43,1.06]]
for i in range(4):add(f'Hair_{i}',hairpts[i],hairpts[i+1],'Head' if i==0 else f'Hair_{i-1}')
arm=bpy.data.armatures.new('NagaSkeleton');rig=bpy.data.objects.new('Rig',arm);bpy.context.collection.objects.link(rig);bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for n,b in bones.items():
    e=arm.edit_bones.new(n);e.head=b['head'];e.tail=b['tail'];e.align_roll(Vector(b['rot'][:,2]));e.use_deform=n!='Root' and not n.endswith('Sword')
    if b['parent']:e.parent=arm.edit_bones[b['parent']]
bpy.ops.object.mode_set(mode='OBJECT');names=list(bones);ni={n:i for i,n in enumerate(names)};W=np.zeros((len(co),len(names)))
def closest(p,pts):
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))];ds=np.full(len(p),1e9);ss=np.zeros(len(p))
    for i,(a,b) in enumerate(zip(pts[:-1],pts[1:])):
        d=b-a;t=np.clip((p-a)@d/(d@d),0,1);dd=np.linalg.norm(p-a-t[:,None]*d,axis=1);m=dd<ds;ds[m]=dd[m];ss[m]=arc[i]+t[m]*(arc[i+1]-arc[i])
    return ss,ds,arc
def chain(ids,ns,pts,root=None):
    ids=np.array(ids,int)
    if not len(ids):return
    s,d,a=closest(co[ids],np.array(pts));mid=(a[:-1]+a[1:])/2;stations=np.r_[0,mid] if root else mid;nodes=([root]+ns)if root else ns
    W[ids]=0
    for k,n in enumerate(nodes):W[ids,ni[n]]=np.interp(s,stations,np.eye(len(nodes))[k])
ids=np.where(pa==0)[0]
for k,(n,h)in enumerate(sp):W[ids,ni[n]]=np.interp(co[ids,2],[s[1][2]for s in sp],np.eye(len(sp))[k])
chain(T['vertices'],[f'Serpent_{i:02}'for i in range(len(line)-1)],line)
arm_dist=[]
for sd in F:
    pts=np.array([J[sd+'_'+n]for n in ['UpperArm','Forearm','Hand']]);arm_dist.append(closest(co,pts)[1])
owner=np.argmin(arm_dist,axis=0)
for k,sd in enumerate(F):
    pts=np.array([J[sd+'_'+n]for n in ['UpperArm','Forearm','Hand']]+[bones[sd+'_Hand']['tail']]);sh=pts[0];v=co[:,0]-sh[0];side=1 if sd[0]=='L'else -1
    ids=np.where((pa==0)&(owner==k)&(v*side>-.07)&(co[:,2]>1.02)&(co[:,2]<1.83)&(np.array(arm_dist)[k]<.105))[0]
    before=W[ids].copy();chain(ids,[sd+'_'+n for n in ['UpperArm','Forearm','Hand']],pts)
    f=np.clip((v[ids]*side+.07)/.15,0,1);f=f*f*(3-2*f);f*=np.maximum(np.clip((np.abs(co[ids,0])-.25)/.07,0,1),np.clip((co[ids,1]+.035)/.09,0,1));W[ids]=W[ids]*f[:,None]+before*(1-f[:,None])
    handids=np.array(F[sd]['hand_verts']);W[handids]=0;W[handids,ni[sd+'_Hand']]=1
    # Partition digits by connectivity first, then blend along their own two joints.
    allowed=set(map(int,handids));owned={int(v):d for d in F[sd]['verts']for v in F[sd]['verts'][d]};adj=[[]for _ in co]
    for a,b in edges:adj[a].append(int(b));adj[b].append(int(a))
    for _ in range(10):
        new={}
        for v,d in owned.items():
            pp=np.array(F[sd][d]);direction=unit(pp[-1]-pp[0])
            for w in adj[v]:
                if w in allowed and w not in owned and w not in new and (co[w]-pp[0])@direction>-.006:new[w]=d
        if not new:break
        owned.update(new)
    for d in F[sd]['verts']:chain([v for v,di in owned.items()if di==d],[sd+'_'+d+str(i)for i in range(2)],F[sd][d],sd+'_Hand')
    # Bracelets follow one rigid segment, never a changing mixture across their shell.
    wp=[4,31,26,6,22,20][k];up=[21,16,7,2,25,1][k]
    for part,n in [(wp,sd+'_Forearm'),(up,sd+'_UpperArm')]:ii=np.where(pa==part)[0];W[ii]=0;W[ii,ni[n]]=1
for part in np.unique(pa):
    if part in [0,100,101,102,4,31,26,6,22,20,21,16,7,2,25,1]:continue
    ids=np.where(pa==part)[0]
    if part in [3,8,9,11,13,15]:W[ids,ni['Head']]=1
    else:chain(ids,[f'Hair_{i}'for i in range(4)],hairpts,'Head')
# Diffuse only each connected hand's weights to remove jumps at the digit webs.
for sd in F:
    ids=np.array(F[sd]['hand_verts'],int);allowed=set(map(int,ids));adj={int(i):[] for i in ids}
    for a,b in edges:
        if int(a) in allowed and int(b) in allowed:adj[int(a)].append(int(b));adj[int(b)].append(int(a))
    for _ in range(12):
        old=W.copy()
        for i in ids:
            if adj[int(i)]:W[i]=.3*old[i]+.7*np.mean(old[adj[int(i)]],axis=0)
assert np.all(W.sum(1)>.99),(np.where(W.sum(1)<.99)[0]).tolist()
keep=np.argpartition(W,-4,axis=1)[:,-4:];mask=np.zeros_like(W,bool);np.put_along_axis(mask,keep,True,axis=1);W[~mask]=0;W/=W.sum(1)[:,None]
for n in names:
    g=body.vertex_groups.new(name=n)
    for i in np.where(W[:,ni[n]]>1e-6)[0]:g.add([int(i)],float(W[i,ni[n]]),'REPLACE')
mod=body.modifiers.new('NagaSkin','ARMATURE');mod.object=rig;body.parent=rig;rig.show_in_front=True
for pb in rig.pose.bones:pb.rotation_mode='QUATERNION'
assert len(bones)<=128,len(bones)
data={'bones':{n:{k:v.tolist() if isinstance(v,np.ndarray)else v for k,v in b.items()}for n,b in bones.items()},'tail':T,'joints':J,'hands':hands,'fingers':F,'bone_count':len(bones)}
(P/'work/rig.json').write_text(json.dumps(data,indent=2));np.savez(P/'work/rig_weights.npz',co=co,weights=W,parts=pa,edges=edges,names=np.array(names))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'));print('RIG',len(bones),'bones;',len(co),'vertices, no unweighted vertices')
