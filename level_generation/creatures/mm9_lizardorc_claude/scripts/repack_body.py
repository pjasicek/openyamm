"""Body atlas: charts are cut at limb joints and finger roots (no new flattening), so the star-shaped hands and L-shaped limbs pack. Writes work/uv_body2.npz. Args: padding fine steps"""
import numpy as np, subprocess, sys
F=np.load('work/uv_body.npz'); uv=F['u'].astype(np.float32); fo=F['o']
J=np.load('work/joined.npz'); co=J['co']; lab=J['lab']; nb=int(J['nb']); fl=np.load('work/finger_labels.npy')
L=np.zeros(len(co),int); L[:nb]=lab; L[(L>=6)&(L<=8)]=6
FL=np.zeros(len(co),int); FL[:len(fl)]=fl
reg=np.zeros(len(fo),int)
for i,f in enumerate(fo):
    v=f[f<nb] if (f<nb).any() else f
    a=L[v]; r=np.bincount(a,minlength=10).argmax(); k=FL[v].max()
    s=1 if co[v,0].mean()>0 else 2
    # hand: fingers apart
    reg[i]=(r*10+s*(r not in (0,6)))+ (100*(FL[v]>0).mean()>60)*(1000+k*10+s)
    if (v>=nb).any() or f.max()>=nb: reg[i]=7000+i//11   # spines
    # toes: by sector round the ball of the foot
    if r==9:
        c=co[v].mean(0); a_=np.degrees(np.arctan2(c[2]+.34,abs(c[0])-.27)); d_=np.hypot(c[2]+.34,abs(c[0])-.27)
        if d_>.11: reg[i]=(9000+int((a_+180)//26))*10+s
# smooth the cuts: majority over UV-adjacent faces of the original chart, then small islands join a neighbour
def adj():
    ed={}
    for i in range(len(uv)):
        for a,b in ((0,1),(1,2),(2,0)):
            pa=(round(float(uv[i,a,0]),6),round(float(uv[i,a,1]),6)); pb=(round(float(uv[i,b,0]),6),round(float(uv[i,b,1]),6))
            ed.setdefault(tuple(sorted((pa,pb))),[]).append(i)
    n=[[] for _ in range(len(uv))]
    for w in ed.values():
        if len(w)==2: n[w[0]].append(w[1]); n[w[1]].append(w[0])
    return n
nb_=adj()
for _ in range(4):
    r2=reg.copy()
    for i in range(len(reg)):
        if len(nb_[i])>=2:
            v,c=np.unique([reg[j] for j in nb_[i]],return_counts=True)
            if c.max()>=2 and v[c.argmax()]!=reg[i]: r2[i]=v[c.argmax()]
    reg=r2
for _ in range(6):
    # islands = connected faces with one region
    lab_=-np.ones(len(reg),int); c=0
    for i in range(len(reg)):
        if lab_[i]>=0: continue
        st=[i]; lab_[i]=c
        while st:
            x=st.pop()
            for y in nb_[x]:
                if lab_[y]<0 and reg[y]==reg[x]: lab_[y]=c; st.append(y)
        c+=1
    cnt=np.bincount(lab_); changed=0
    for i in np.where(cnt[lab_]<10)[0]:
        out=[reg[j] for j in nb_[i] if reg[j]!=reg[i]]
        if out: reg[i]=max(set(out),key=out.count); changed+=1
    if not changed: break
print('regions',len(np.unique(reg)),'pieces',c)
keys={}; vert=np.zeros(uv.shape[:2],np.int32)
for f in range(len(uv)):
    for c in range(3):
        k=(round(float(uv[f,c,0]),6),round(float(uv[f,c,1]),6),int(reg[f])); vert[f,c]=keys.setdefault(k,len(keys))
np.savez('work/pack_in.npz',uv=uv,vert=vert)
V='/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/xatlas_venv/bin/python'; T='/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/xatlas_charts.py'
pad,fine,steps=sys.argv[1:4]
r=subprocess.run([V,'-I',T,'pack','work/pack_in.npz','work/pack_out.npz','--size','2048','--padding',pad,'--fine',fine,'--steps',steps],capture_output=True,text=True); print(r.stdout[-260:],r.stderr[-300:])
Pk=np.load('work/pack_out.npz')['uv']; np.savez('work/uv_body2.npz',u=Pk,o=fo)
