import bpy,numpy as np,json,sys,runpy
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v6t.blend'));ob=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=ob.data
pv=np.array([a.value for a in me.attributes['piece'].data]);co=np.array([tuple(v.co)for v in me.vertices]);gs={g.name:g for g in ob.vertex_groups};names={g.index:g.name for g in ob.vertex_groups}
def put(i,w):
 for e in me.vertices[i].groups[:]:ob.vertex_groups[e.group].remove([i])
 w=dict(sorted([(n,float(v))for n,v in w.items()if v>1e-6],key=lambda x:-x[1])[:4]);tot=sum(w.values());assert tot>0
 for n,v in w.items():gs[n].add([i],v/tot,'REPLACE')
def smooth(x):x=float(np.clip(x,0,1));return x*x*(3-2*x)
def torso(z):
 zs=[.70,.83,.91,.99];ns=['B_Pelvis','B_Spine','B_Spine1','B_Spine2'];k=int(np.clip(np.searchsorted(zs,z)-1,0,2));t=float(np.clip((z-zs[k])/(zs[k+1]-zs[k]),0,1));return{ns[k]:1-t,ns[k+1]:t}
for i in np.where(pv==1)[0]:
 x,y,z=co[i];side='L'if x>0 else'R';t=float(np.clip((abs(x)-.075)/.255,0,1))*float(np.clip((z-.65)/.20,0,1));w={n:v*(1-t)for n,v in torso(z).items()};w[f'B_{side}_UpperArmTwist']=t;b=float(np.clip((z-.765)/.095,0,1));w={n:v*b for n,v in w.items()};w['B_Pelvis']=w.get('B_Pelvis',0)+1-b;put(int(i),w)
# Nape braid follows the collar at its lower end, then the head above the neck.
for i in np.where((pv==0)&(co[:,1]>.055)&(co[:,2]<1.17))[0]:
 z=co[i,2];t=smooth((z-1.08)/.09);put(int(i),{'B_Head':t,'B_Spine2':1-t})
# The yoke sits over the shirt; the nearby beard is not its skinning surface.
k=KDTree(int((pv==1).sum()))
for i in np.where(pv==1)[0]:k.insert(co[i],int(i))
k.balance()
for i in np.where(pv==8)[0]:
 near=k.find_n(co[i],4);w={}
 for _,j,d in near:
  for e in me.vertices[j].groups:w[names[e.group]]=w.get(names[e.group],0)+e.weight
 put(int(i),w)
# One shell owner per metal stud. A tiny stud must never bridge different anatomical surfaces.
main=[0,1,2,3,4,5,6,7,8,9,10,11];trees={}
for p in main:
 ids=np.where(pv==p)[0];k=KDTree(len(ids))
 for i in ids:k.insert(co[i],int(i))
 k.balance();trees[p]=k
owners={}
for p in sorted(set(pv.tolist())):
 if p<14 or p in [16,67]:continue
 ids=np.where(pv==p)[0];owner=min(main,key=lambda q:np.median([trees[q].find(co[i])[2]for i in ids]));owners[int(p)]=owner
 w={}
 for i in ids:
  _,j,_=trees[owner].find(co[i])
  for e in me.vertices[j].groups:w[names[e.group]]=w.get(names[e.group],0)+e.weight
 for i in ids:put(int(i),w)
(P/'work/stud_owners.json').write_text(json.dumps(owners,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_fixed.blend'))
