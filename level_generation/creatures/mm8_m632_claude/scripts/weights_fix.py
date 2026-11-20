"""Dark Dwarf piece ownership; armour and sleeve roots follow their actual anatomical owner."""
import bpy,sys,json
from pathlib import Path
import numpy as np
from mathutils.kdtree import KDTree
p=Path(__file__).resolve().parents[1]
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=src)
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
co=np.array([v.co[:] for v in me.vertices]);pv=np.array([x.value for x in me.attributes['piece'].data])
names=[g.name for g in body.vertex_groups];gi={n:i for i,n in enumerate(names)}
W=np.zeros((len(co),len(names)))
for v in me.vertices:
    for g in v.groups:W[v.index,g.group]=g.weight
def rigid(ids,name):
    W[ids]=0;W[ids,gi[name]]=1
def j(name):return np.array(rig.data.bones[name].head_local)
skin=np.where(np.isin(pv,(0,5,7,8)))[0]
# Head surfaces and facial parts must never inherit arm or shoulder weights.
for i in skin:
    if co[i,2]>1.075 and abs(co[i,0])<.155:
        rigid(i,'B_Head')
# Keep the central chest out of the upper-arm roll.
for s in 'LR':
    ua=gi[f'B_{s}_UpperArm'];cl=gi[f'B_{s}_Clavicle']
    sh=j(f'B_{s}_UpperArm');axis=sh-j(f'B_{s}_Clavicle');axis/=np.linalg.norm(axis)
    m=(co[skin]-sh)@axis
    share=np.clip(-m/.055,0,1)
    move=W[skin,ua]*share
    W[skin,ua]-=move;W[skin,cl]+=move
for side,piece in [('L',7),('R',8)]:
    ids=np.where((pv==piece)&(np.linalg.norm(co-j(f'B_{side}_Hand'),axis=1)>.03))[0]
    rigid(ids,f'B_{side}_Hand')
# Meshy leaked thigh weights into the chest and lower biceps.
ids=np.where(pv==0)[0]
legcols=[i for i,n in enumerate(names) if any(k in n for k in ('Thigh','Calf','Foot','Toe'))]
leak=W[np.ix_(ids,legcols)].sum(1);W[np.ix_(ids,legcols)]=0
t=np.clip((co[ids,2]-.65)/.15,0,1);t=t*t*(3-2*t)
W[ids,gi['B_Pelvis']]+=leak*(1-t);W[ids,gi['B_Spine1']]+=leak*t
for side in 'LR':
 cols=[i for i,n in enumerate(names) if n.startswith(f'B_{side}_') and any(k in n for k in ('UpperArm','Forearm','Hand','Clavicle'))]
 ids=np.where((pv==0)&(co[:,2]>.70)&(co[:,2]<1.02))[0]
 radial=np.clip((np.abs(co[ids,0])-.16)/.15,0,1);radial=radial*radial*(3-2*radial)
 high=np.clip((co[ids,2]-.90)/.12,0,1);high=high*high*(3-2*high)
 retain=np.maximum(radial,high)
 moved=W[np.ix_(ids,cols)]*(1-retain[:,None]);W[np.ix_(ids,cols)]-=moved;W[ids,gi['B_Spine1']]+=moved.sum(1)
# Spread the shoulder transition over the connected skin rather than one triangle row.
adj=[[] for _ in co]
for edge in me.edges:
 a,b=edge.vertices;adj[a].append(b);adj[b].append(a)
smooth_ids=np.where((pv==0)&(co[:,2]>.72)&(co[:,2]<1.08)&(np.abs(co[:,0])>.10)&(np.abs(co[:,0])<.40))[0]
for _ in range(10):
 old=W.copy()
 for i in smooth_ids:
  nb=[j for j in adj[i] if pv[j]==0]
  if nb:W[i]=old[i]*.5+old[nb].mean(0)*.5
# The neck skin blends spine-to-neck-to-head, never to the clavicle.
for i in np.where((pv==0)&(co[:,2]>1.015)&(np.abs(co[:,0])<.18))[0]:
    edge=np.clip((.18-abs(co[i,0]))/.04,0,1);edge=edge*edge*(3-2*edge)
    t=np.clip((co[i,2]-1.015)/.035,0,1);t=t*t*(3-2*t)
    h=np.clip((co[i,2]-1.05)/.035,0,1);h=h*h*(3-2*h)
    W[i]*=1-edge
    W[i,gi['B_Spine2']]+=edge*(1-t);W[i,gi['B_Neck']]+=edge*t*(1-h);W[i,gi['B_Head']]+=edge*t*h
owned={}
head={1,2,3,6,9,10,13,19,20,24,25,30,33,34,35}
fixed={11:'B_Spine2',22:'B_Spine2',23:'B_Spine1',21:'B_Pelvis',15:'B_R_UpperArm',16:'B_L_UpperArm',28:'B_L_Calf',29:'B_R_Calf'}
# Studs and spikes use the same rigid transform as their host plate.
host_pieces=[11,22,15,16]
host_ids=np.where(np.isin(pv,host_pieces))[0]
host=KDTree(len(host_ids))
for k,i in enumerate(host_ids):host.insert(co[i],k)
host.balance()
for piece in sorted(set(pv)):
    ids=np.where(pv==piece)[0]
    if piece in (0,5,7,8):continue
    if piece in head:
        rigid(ids,'B_Head');owned[int(piece)]='B_Head'
    elif piece in fixed:
        rigid(ids,fixed[piece]);owned[int(piece)]=fixed[piece]
    elif piece in (17,18):
        s='R' if piece==17 else 'L';rigid(ids,f'B_{s}_UpperArm');owned[int(piece)]='sleeve: upper arm, then fitted twist distribution'
    elif piece in (12,14):
        s='R' if piece==12 else 'L';W[ids]=0
        ankle=j(f'B_{s}_Foot')[2]
        t=np.clip((co[ids,2]-ankle+.015)/.10,0,1)
        W[ids,gi[f'B_{s}_Calf']]=t;W[ids,gi[f'B_{s}_Foot']]=1-t
        owned[int(piece)]='boot: calf to foot'
    elif piece in (4,26,27,31,32):
        W[ids]=0
        a=np.clip((.65-co[ids,2])/.30,0,.65)
        left=np.clip(.5+co[ids,0]/.20,0,1)
        W[ids,gi['B_Pelvis']]=1-a
        W[ids,gi['B_L_Thigh']]=a*left
        W[ids,gi['B_R_Thigh']]=a*(1-left)
        owned[int(piece)]='skirt: pelvis to thighs'
    elif piece>=36:
        base=ids[np.argmin(co[ids,2])]
        hits=host.find_n(co[base],3)
        host_piece=int(pv[host_ids[hits[0][1]]])
        rigid(ids,fixed[host_piece]);owned[int(piece)]=fixed[host_piece]
    else:
        raise AssertionError(f'Unclassified piece {piece}')
W/=W.sum(1,keepdims=True)
assert np.isfinite(W).all() and np.max(abs(W.sum(1)-1))<1e-6
for g in list(body.vertex_groups):body.vertex_groups.remove(g)
for name in names:body.vertex_groups.new(name=name)
for i in range(len(co)):
    for k in np.where(W[i]>1e-5)[0]:body.vertex_groups[k].add([i],float(W[i,k]),'REPLACE')
(p/'work/piece_ownership.json').write_text(json.dumps(owned,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=out)
print('WEIGHTS classified',len(owned),'armour/hair/boot pieces')
