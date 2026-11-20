"""Kept garment rules: pelvis-held short hem, medial shoulder fade, and rigid head accessories."""
import bpy,sys,os,json
from pathlib import Path
import numpy as np
kind=os.environ['KEPT_BODY'];src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
co=np.array([v.co[:] for v in me.vertices]);part=np.array([x.value for x in me.attributes['piece'].data]);names=[g.name for g in body.vertex_groups];gi={n:i for i,n in enumerate(names)}
w=np.zeros((len(co),len(names)))
for v in me.vertices:
 for g in v.groups:w[v.index,g.group]=g.weight
old=w.copy();J=lambda n:np.array(rig.data.bones[n].head_local)
for sd in 'LR':
 sh,cl=J(f'B_{sd}_UpperArm'),J(f'B_{sd}_Clavicle');axis=(sh-cl)/np.linalg.norm(sh-cl)
 fade=np.clip(-((co-sh)@axis)/.07,0,1)*(part==0)
 for name in (f'B_{sd}_UpperArm',f'B_{sd}_UpperArmTwist'):
  if name not in gi:continue
  moved=w[:,gi[name]]*fade;w[:,gi[name]]-=moved;w[:,gi[f'B_{sd}_Clavicle']]+=moved
# The short tunic hangs from its waist; legs must not pull its front/rear panels apart.
a=np.clip((J('B_Pelvis')[2]+.12-co[:,2])/.08,0,1)*(part==0)
a*=np.clip((.18-abs(co[:,0]-J('B_Pelvis')[0]))/.06,0,1)
w*=1-a[:,None];w[:,gi['B_Pelvis']]+=a
head_parts=(10,11) if kind=='male' else (6,8,9,10,13,14)
ids=np.where(np.isin(part,head_parts))[0];w[ids]=0;w[ids,gi['B_Head']]=1
# Jaw and neck skin retain only their anatomical head/neck blend.
ids=np.where(part==1)[0];h=np.clip((co[ids,2]-J('B_Neck')[2])/(J('B_Head')[2]-J('B_Neck')[2]),0,1)
w[ids]=0;w[ids,gi['B_Head']]=h;w[ids,gi['B_Neck']]=1-h
# Blend sleeve/chest influences through connected cloth instead of abrupt source weight bands.
edges=np.array([e.vertices[:] for e in me.edges]);edges=edges[(part[edges[:,0]]==0)&(part[edges[:,1]]==0)]
rows=np.r_[edges[:,0],edges[:,1]];cols=np.r_[edges[:,1],edges[:,0]]
count=np.bincount(rows,minlength=len(co));mask=(part==0)&(co[:,2]>J('B_Pelvis')[2]+.14)&(count>0)
for _ in range(6):
 accum=np.zeros_like(w);np.add.at(accum,rows,w[cols]);mean=accum/np.maximum(count[:,None],1)
 w[mask]=w[mask]*.4+mean[mask]*.6
w/=w.sum(1)[:,None]
for group in body.vertex_groups:group.remove(list(range(len(co))))
for i,row in enumerate(w):
 for g in np.where(row>1e-5)[0]:body.vertex_groups[int(g)].add([i],float(row[g]),'REPLACE')
assert np.allclose(w.sum(1),1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
print('GARMENT_WEIGHTS',kind,int((abs(old-w).sum(1)>1e-5).sum()),'vertices changed',flush=True)

sys.stdout.flush();sys.stderr.flush();os._exit(0)
