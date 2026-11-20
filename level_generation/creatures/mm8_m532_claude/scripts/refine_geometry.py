"""Round the generated tail strips and smooth abrupt finger ownership at the palm."""
from pathlib import Path
import bpy,numpy as np,json
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv_v1.blend'))
b=bpy.data.objects['Body'];me=b.data;co=np.array([v.co[:]for v in me.vertices]);comp=np.array([x.value for x in me.attributes['component'].data]);count=0
for c in np.unique(comp):
    ids=np.where(comp==c)[0];v=co[ids]
    if c==0 or v[:,1].min()<.83 or np.ptp(v[:,2])<.35:continue
    z0=v[:,2].min();z1=v[:,2].max();w=np.clip((v[:,2]-z0)/min(.32,(z1-z0)*.4),0,1);taper=.17+.83*w
    center=v[np.argsort(v[:,2])[:max(3,len(v)//5)]].mean(0)
    v[:,:2]=center[:2]+(v[:,:2]-center[:2])*taper[:,None];v[:,0]*=.88
    for i,p in zip(ids,v):me.vertices[i].co=p
    count+=len(ids)
names={g.index:g.name for g in b.vertex_groups};groups={g.name:g for g in b.vertex_groups};w=[{names[g.group]:g.weight for g in v.groups}for v in me.vertices];adj=[set()for _ in w]
for e in me.edges:a,c=e.vertices;adj[a].add(c);adj[c].add(a)
digits=('Thumb','Index','Middle','Ring','Pinky');affected=set()
def smooth(x):
    x=np.clip(x,0,1);return x*x*(3-2*x)
# The belly bridge belongs to the pelvis; opposing lower-leg weights tear it during a trot.
for i,(x,y,z) in enumerate(co):
    if y<.15 or z<.72:continue
    high=smooth((z-.72)/.20);middle=1-smooth((abs(x)-.06)/.16);moved=0
    for name in list(w[i]):
        if name.startswith('HindLower'):factor=high
        elif name.startswith('HindUpper'):factor=max(high*middle,smooth((z-1.05)/.25))
        else:continue
        delta=w[i][name]*factor;w[i][name]-=delta;moved+=delta
    if moved:
        w[i]['HorsePelvis']=w[i].get('HorsePelvis',0)+moved;affected.add(i)

for _ in range(3):
    out=[x.copy()for x in w]
    for i,p in enumerate(co):
        if abs(p[0])<.93 or p[2]>1.7:continue
        side='L'if p[0]>0 else'R';allowed={side+'Hand',side+'ForeArm'}
        present={n for j in [i,*adj[i]]for n in w[j]if n.startswith(side)and any(d in n for d in digits)}
        if not present:continue
        dominant=max(present,key=lambda n:sum(w[j].get(n,0)for j in [i,*adj[i]]));digit=next(d for d in digits if d in dominant)
        allowed|={side+digit+str(k)for k in (1,2,3)}
        new={n:.55*w[i].get(n,0)+.45*sum(w[j].get(n,0)for j in adj[i])/len(adj[i])for n in allowed}
        total=sum(new.values())
        if total>.1:out[i]={n:a/total for n,a in new.items()if a>.001};affected.add(i)
    w=out
for i in affected:
    for g in list(me.vertices[i].groups):b.vertex_groups[g.group].remove([i])
    total=sum(w[i].values())
    for n,a in w[i].items():groups[n].add([i],a/total,'REPLACE')
assert all(v.groups for v in me.vertices)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/corrected_uv_v2.blend'))
print('REFINED',count,'tail vertices;',len(affected),'hand vertices')
