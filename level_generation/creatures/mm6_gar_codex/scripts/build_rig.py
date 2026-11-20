"""Fit source rest frames to measured skin rings, then weight the intact body and wings."""
import bpy,json,sys,math,heapq
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/geometry_assembled.blend'))
body=bpy.data.objects['Body']; headobj=bpy.data.objects['Head']
SRC=json.loads((P/'work/source_rest.json').read_text())
J={'B_Pelvis':(0,.11,.97),'B_Spine':(0,.125,1.09),'B_Spine1':(0,.135,1.25),
   'B_Spine2':(0,.12,1.38),'B_Neck':(0,.04,1.53),'B_Head':(0,-.03,1.69)}
for sd,points in {
'L':[(.065,.12,1.415),(.145,.10,1.43),(.255,.13,1.17),(.350,-.005,.995),(.082,.10,.99),(.19,0,.65),(.215,.35,.26),(.285,.095,.095)],
'R':[(-.065,.12,1.415),(-.17,.10,1.46),(-.29,.10,1.19),(-.376,-.075,1.045),(-.086,.11,.99),(-.213,.02,.655),(-.30,.40,.30),(-.385,.115,.095)]}.items():
    for n,p in zip(('Clavicle','UpperArm','Forearm','Hand','Thigh','Calf','Foot','Toe0'),points): J[f'B_{sd}_{n}']=p
F={'L':[
[(.332,-.05,.966),(.305,-.112,.922),(.309,-.16,.871),(.323,-.170,.843)],
[(.394,-.097,.944),(.459,-.190,.882),(.461,-.211,.830),(.435,-.213,.793)],
[(.390,-.030,.941),(.471,-.139,.883),(.463,-.156,.786),(.434,-.151,.734)],
[(.397,.025,.933),(.461,-.073,.869),(.451,-.091,.786),(.426,-.088,.740)],
[(.407,.055,.927),(.482,.012,.864),(.481,-.010,.816),(.453,-.006,.774)]]}
F['R']=[(np.array(c)*[-1,1,1]+[-.014,-.018,.085]).tolist() for c in F['L']]
# The original right hand is smaller and sits higher; measure its native digits independently.
F['R'][0]=[[-.353,-.120,1.025],[-.336,-.155,1.003],[-.346,-.182,.971],[-.348,-.194,.946]]
F['R'][1]=[[-.425,-.142,1.014],[-.469,-.214,.964],[-.464,-.222,.909],[-.447,-.219,.875]]
F['R'][3]=[[-.435,-.078,1.004],[-.489,-.118,.947],[-.487,-.125,.889],[-.464,-.126,.849]]
F['R'][4]=[[-.444,-.033,.998],[-.505,-.051,.958],[-.509,-.056,.906],[-.488,-.054,.868]]
CHAINS={}
for sd in ('L','R'):
 for f,c in enumerate(F[sd]):
    names=[f'B_{sd}_Finger{f}',f'B_{sd}_Finger{f}1',f'B_{sd}_Finger{f}2']
    if sd=='R' and f==0:names=['B_R_Finger0','B_R_Finger0.001','B_R_Finger0.002']
    CHAINS[(sd,f)]=(names,np.array(c))
    for n,p in zip(names,c):J[n]=p
J={n:Vector(p) for n,p in J.items()}; order=list(SRC);rot={};swing={}
def basis(f,t):
 f=np.array(f);f/=np.linalg.norm(f);t=np.array(t);t-=f*(t@f);t/=np.linalg.norm(t)
 return Matrix(np.column_stack([f,t,np.cross(f,t)]).tolist())
for n in order:
 s=SRC[n]; child=s['child']; R=Matrix(s['rot'])
 q=Vector(s['seg']).rotation_difference(J[child]-J[n]) if child in J else swing.get(s['parent'],Quaternion())
 if n=='B_Pelvis':q=Quaternion()
 if n.endswith('_Hand'):
    sd=n[2];fs=Vector(SRC[f'B_{sd}_Finger2']['head'])-Vector(s['head'])
    ts=Vector(SRC[f'B_{sd}_Finger1']['head'])-Vector(SRC[f'B_{sd}_Finger4']['head'])
    q=(basis(J[f'B_{sd}_Finger2']-J[n],J[f'B_{sd}_Finger1']-J[f'B_{sd}_Finger4'])@basis(fs,ts).transposed()).to_quaternion()
 if 'Finger' in n:
    sd=n[2]; names,pts=next(v for (side,f),v in CHAINS.items() if side==sd and n in v[0]);i=names.index(n)
    seg=Vector(s['seg']) if child else Vector(s['head'])-Vector(SRC[s['parent']]['head'])
    qh=swing[f'B_{sd}_Hand'];q=(qh@seg).rotation_difference(Vector(pts[i+1])-J[n])@qh
 swing[n]=q;rot[n]=q.to_matrix()@R
ad=bpy.data.armatures.new('Rig');rig=bpy.data.objects.new('Rig',ad);bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for n in order:
 eb=ad.edit_bones.new(n);c=SRC[n]['child'];length=(J[c]-J[n]).length if c in J else .045
 eb.head=J[n];eb.tail=J[n]+rot[n].col[1]*length;eb.align_roll(rot[n].col[2])
 if SRC[n]['parent'] in ad.edit_bones:eb.parent=ad.edit_bones[SRC[n]['parent']]
WINGS={}
for sd,sign in [('L',1),('R',-1)]:
 root=Vector((sign*.105,.255,1.55)); bend=Vector((sign*.32,.38,2.23))
 defs=[('Root',root,bend,'B_Spine2'),('Tip',bend,Vector((sign*.92,.59,2.98)),f'W_{sd}_Root'),
       ('Upper',bend,Vector((sign*.91,.49,2.35)),f'W_{sd}_Root'),
       ('Lower',bend,Vector((sign*.97,.41,1.92)),f'W_{sd}_Root'),
       ('Web',root,Vector((sign*.075,.30,1.18)),f'W_{sd}_Root')]
 for name,a,b,parent in defs:
    n=f'W_{sd}_{name}';eb=ad.edit_bones.new(n);eb.head=a;eb.tail=b;eb.parent=ad.edit_bones[parent]
    WINGS[n]=(np.array(a),np.array(b));eb.use_deform=False
for n in order:ad.edit_bones[n].use_deform='Finger' not in n
bpy.ops.object.mode_set(mode='OBJECT')
err=max(math.degrees(ad.bones[n].matrix_local.to_quaternion().rotation_difference(rot[n].to_quaternion()).angle) for n in order)
assert err<.1,err
# The generated torso defeated heat weighting; use measured anatomical chains with joint-centred blends.
body.parent=rig;mod=body.modifiers.new('Armature','ARMATURE');mod.object=rig
co=np.array([v.co[:] for v in body.data.vertices]);nv=len(co);wn=np.load(P/'work/wing_mask.npy');assert len(wn)==nv
names=list(ad.bones.keys());idx={n:i for i,n in enumerate(names)};weights=np.zeros((nv,len(names)))
def segment(p,a,b):
 ab=b-a;t=np.clip((p-a)@ab/(ab@ab),0,1);return np.linalg.norm(p-a-t[:,None]*ab,axis=1),t
chains={'torso':(['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head'],[J[n] for n in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']]+[Vector((0,-.03,1.82))])}
for sd in ['L','R']:
 for part,nn in [('arm',['Clavicle','UpperArm','Forearm','Hand']),('leg',['Thigh','Calf','Foot','Toe0'])]:
    nm=[f'B_{sd}_{n}' for n in nn];pts=[J[n] for n in nm]
    pts.append(J[f'B_{sd}_Finger2'] if part=='arm' else pts[-1]+Vector((0,-.13,-.04)))
    chains[sd+part]=(nm,pts)
fields=[];scores=[]
for key,(nm,pts) in chains.items():
 ds=[];ts=[]
 for a,b in zip(pts,pts[1:]):
    d,t=segment(co,np.array(a),np.array(b));ds.append(d);ts.append(t)
 ds=np.array(ds);ts=np.array(ts)
 lengths=np.array([(b-a).length for a,b in zip(pts,pts[1:])]);cum=np.r_[0,np.cumsum(lengths)]
 soft=1/(ds*ds+.035**2)**4;soft/=soft.sum(0)
 arc=((cum[:-1,None]+ts*lengths[:,None])*soft).sum(0)
 near=np.clip(np.searchsorted(cum,arc)-1,0,len(nm)-1);field=np.zeros_like(weights)
 for vi,j in enumerate(near):
    t=float(np.clip((arc[vi]-cum[j])/lengths[j],0,1));blend=.48
    if t<blend and j>0:field[vi,idx[nm[j-1]]]=.5-.5*t/blend;field[vi,idx[nm[j]]]=.5+.5*t/blend
    elif t>1-blend and j<len(nm)-1:field[vi,idx[nm[j+1]]]=(t-(1-blend))/(2*blend);field[vi,idx[nm[j]]]=1-(t-(1-blend))/(2*blend)
    else:field[vi,idx[nm[j]]]=1
 score=1/(ds.min(0)**2+.045**2)**3
 if key.endswith('leg'):score*=np.clip((1.06-co[:,2])/.18,0,1);score*=np.clip((co[:,0]*(1 if key[0]=='L' else -1)+.04)/.08,0,1)
 elif key.endswith('arm'):score*=np.clip((co[:,2]-.80)/.15,0,1);score*=np.clip((co[:,0]*(1 if key[0]=='L' else -1)-.08)/.10,0,1)
 else:score*=np.clip((co[:,2]-.74)/.18,0,1)
 fields.append(field);scores.append(score)
scores=np.array(scores);assert np.all(scores.sum(0)>0);scores/=scores.sum(0)
for field,score in zip(fields,scores):weights+=field*score[:,None]
for sd,sg in [('L',1),('R',-1)]:
    wr=np.array(J[f'B_{sd}_Hand']);direction=wr-np.array(J[f'B_{sd}_Forearm']);direction/=np.linalg.norm(direction)
    h=(np.linalg.norm(co-wr,axis=1)<.40)&(co[:,0]*sg>.26)&~wn
    ramp=np.clip(((co-wr)@direction+.05)/.08,0,1)
    weights[h]*=(1-ramp[h,None]);weights[h,idx[f'B_{sd}_Hand']]+=ramp[h]
for sd,sg in [('L',1),('R',-1)]:
 ids=np.where(wn&(co[:,0]*sg>0))[0];pos=co[ids];w=np.zeros((len(ids),len(names)))
 active=[n for n in WINGS if f'_{sd}_' in n]
 for n in active:
    a,b=WINGS[n];d,t=segment(pos,a,b);w[:,idx[n]]=1/(d*d+.018**2)**1.5
 w/=w.sum(1)[:,None]
 # A broad root transition avoids a hard hinge across the lower membrane attachment.
 influence=np.clip(np.maximum((abs(pos[:,0])-.06)/.22,(pos[:,2]-1.58)/.22),0,1);influence=influence**2*(3-2*influence)
 w*=influence[:,None]
 for j,pp in enumerate(pos):
    chest=float(np.clip((pp[2]-1.25)/.13,0,1));w[j,idx['B_Spine2']]+=(1-influence[j])*chest;w[j,idx['B_Spine1']]+=(1-influence[j])*(1-chest)
 weights[ids]=w
# Finger ownership is grown over connected edges from each fingertip, bounded by its measured knuckle.
adj=[[] for _ in co]
for e in body.data.edges:
 a,b=e.vertices;d=float(np.linalg.norm(co[a]-co[b]));adj[a].append((b,d));adj[b].append((a,d))
labels=np.full(nv,-1,dtype=int);finger_report={}
for sd,sg in [('L',1),('R',-1)]:
 wr=np.array(J[f'B_{sd}_Hand']);hand=(np.linalg.norm(co-wr,axis=1)<.38)&(co[:,0]*sg>.28)&~wn
 distance=np.full((5,nv),np.inf)
 for f in range(5):
    nm,pts=CHAINS[(sd,f)];d0=pts[1]-pts[0];along=(co-pts[0])@d0/(d0@d0)
    nearest=np.min([segment(co,pts[j],pts[j+1])[0] for j in range(3)],axis=0)
    allowed=hand&(along>-.18)&(nearest<.05)
    candidates=np.where(allowed)[0];assert len(candidates)>10,(sd,f)
    seed=int(candidates[np.argmin(np.linalg.norm(co[candidates]-pts[-1],axis=1))]);q=[(0.,seed)];distance[f,seed]=0
    while q:
        dist,v=heapq.heappop(q)
        if dist!=distance[f,v]:continue
        for nb,d in adj[v]:
            dd=dist+d*(1+nearest[nb]*15)
            if allowed[nb] and dd<distance[f,nb]:distance[f,nb]=dd;heapq.heappush(q,(dd,nb))
 ids=np.where(np.isfinite(distance).any(0))[0]
 for vi in ids:
    f=int(np.argmin(distance[:,vi]));nm,pts=CHAINS[(sd,f)];d0=pts[1]-pts[0];along=float((co[vi]-pts[0])@d0/(d0@d0))
    ds,ts=zip(*[(float(d[0]),float(t[0])) for d,t in [segment(co[vi:vi+1],pts[j],pts[j+1]) for j in range(3)]])
    j=int(np.argmin(ds));t=ts[j];w=np.zeros(len(names));into=float(np.clip((along+.18)/.48,0,1))
    w[idx[f'B_{sd}_Hand']]=1-into
    if t<.3 and j>0:w[idx[nm[j-1]]]=into*(.5-.5*t/.3);w[idx[nm[j]]]=into*(.5+.5*t/.3)
    elif t>.7 and j<2:w[idx[nm[j+1]]]=into*(t-.7)/.6;w[idx[nm[j]]]=into*(1-(t-.7)/.6)
    else:w[idx[nm[j]]]=into
    weights[vi]=w;labels[vi]=f+(0 if sd=='L' else 5)
 finger_report[sd]={str(f):int(np.sum(labels==f+(0 if sd=='L' else 5))) for f in range(5)}
 assert min(finger_report[sd].values())>=12,finger_report[sd]
web=set()
for vi in range(nv):
    if labels[vi]>=0 and any(labels[nb]>=0 and labels[nb]!=labels[vi] for nb,d in adj[vi]):web.add(vi)
for _ in range(3):web|={nb for vi in list(web) for nb,d in adj[vi] if labels[nb]>=0}
for _ in range(8):
    nw=weights.copy()
    for vi in web:
        ns=[nb for nb,d in adj[vi]]
        if ns:nw[vi]=weights[vi]*.5+weights[ns].mean(0)*.5
    weights=nw
for _ in range(4):
    nw=weights.copy()
    for vi in range(nv):
        finger_channels=[j for n,j in idx.items() if 'Finger' in n]
        fw=weights[vi,finger_channels].sum()
        is_web=fw>.0001 and weights[vi,idx['B_L_Hand']]+weights[vi,idx['B_R_Hand']]>.05
        is_back=co[vi,1]>.17 and abs(co[vi,0])<.26 and 1.02<co[vi,2]<1.65
        if (is_web or is_back) and adj[vi]:
            ns=[v for v,d in adj[vi]];nw[vi]=weights[vi]*.5+weights[ns].mean(0)*.5
    weights=nw
# Normalize and keep the renderer's strongest eight influences.
for vi in range(nv):
 w=weights[vi];w[w<.0001]=0
 if np.count_nonzero(w)>8:w[np.argsort(w)[:-8]]=0
 assert w.sum()>.001,vi
 weights[vi]=w/w.sum()
body.vertex_groups.clear();groups={n:body.vertex_groups.new(name=n) for n in names}
for vi,w in enumerate(weights):
 for j in np.where(w>0)[0]:groups[names[j]].add([vi],float(w[j]),'REPLACE')
for b in ad.bones:b.use_deform=True
headobj.vertex_groups.clear();hg={n:headobj.vertex_groups.new(name=n) for n in ['B_Head','B_Neck','B_Spine2']}
for v in headobj.data.vertices:
 # Neck weights blend only behind the jaw, never across teeth or the projecting muzzle.
 back=float(np.clip((v.co.y+.16)/.09,0,1));neck=back*float(np.clip((1.68-v.co.z)/.10,0,1));chest=neck*float(np.clip((1.58-v.co.z)/.09,0,1))
 for n,w in [('B_Head',1-neck),('B_Neck',neck-chest),('B_Spine2',chest)]:
    if w>0:hg[n].add([v.index],w,'REPLACE')
headobj.parent=rig;mod=headobj.modifiers.new('Armature','ARMATURE');mod.object=rig
bpy.context.scene['rig_offsets']=json.dumps({n:{'q':list(swing[n]),'R_src':SRC[n]['rot']} for n in order})
(P/'work/joints_final.json').write_text(json.dumps({'joints':{n:list(p) for n,p in J.items()}},indent=2))
(P/'work/finger_chains.json').write_text(json.dumps({sd:F[sd] for sd in F},indent=2))
(P/'work/rig_checks.json').write_text(json.dumps({'bone_count':len(names),'rest_frame_error_degrees':err,'finger_vertices':finger_report,'wing_vertices':int(wn.sum()),'maximum_influences':int((weights>0).sum(1).max())},indent=2))
np.save(P/'work/finger_labels.npy',labels)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_high.blend'))
# Reduction follows weight transfer; retain the high-resolution head for the detail bake.
bpy.context.view_layer.objects.active=headobj
mod=headobj.modifiers.new('HeadProductionReduction','DECIMATE');mod.ratio=6000/sum(len(p.vertices)-2 for p in headobj.data.polygons)
bpy.ops.object.modifier_apply(modifier=mod.name)
for p in headobj.data.polygons:p.use_smooth=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'))
print('RIG',len(names),'bones; frame error',err,'finger vertices',finger_report,'head triangles',sum(len(p.vertices)-2 for p in headobj.data.polygons))
common.render_views(str(P/'review/rig_rest'),1.5,3.3,views=('front','left','three_quarter'),resolution=(800,1100))
