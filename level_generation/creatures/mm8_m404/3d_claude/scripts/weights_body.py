"""Assign component ownership before fingers; closed bracers remain rigid."""
import bpy,numpy as np,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=src)
o=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=o.data
co=np.array([v.co[:] for v in me.vertices]);piece=np.array([v.value for v in me.attributes['piece'].data])
names=[g.name for g in o.vertex_groups];gi={n:i for i,n in enumerate(names)};w=np.zeros((len(co),len(names)))
for v in me.vertices:
 for g in v.groups:w[v.index,g.group]=g.weight
# Beyond the wrist, palm and claw skin follows the hand hierarchy, not the forearm's counter-roll.
for side in ('L','R'):
 wrist=np.array(rig.data.bones['B_'+side+'_Hand'].head_local);elbow=np.array(rig.data.bones['B_'+side+'_Forearm'].head_local)
 direction=(wrist-elbow)/np.linalg.norm(wrist-elbow)
 amount=np.clip(((co-wrist)@direction+.02)/.025,0,1)*(np.linalg.norm(co-wrist,axis=1)<.27)*(piece==0)*(co[:,0]*(1 if side=='L' else -1)>.3)
 hand=[i for n,i in gi.items() if n=='B_'+side+'_Hand' or n.startswith('B_'+side+'_Finger')]
 other=[i for i in range(len(names)) if i not in hand];total=w[:,hand].sum(1);moved=w[:,other].sum(1)*amount
 w[:,other]*=1-amount[:,None]
 factor=np.divide(total+moved,total,out=np.ones_like(total),where=total>1e-7)
 w[:,hand]*=factor[:,None];w[total<=1e-7,gi['B_'+side+'_Hand']]+=moved[total<=1e-7]
# Shoulder and torso smoothing belongs to the final pass, after twist helpers exist.
if 'B_R_ForearmTwist' in gi:
 # Upper-arm weights fade onto the clavicle inside the shoulder joint.
 for side in ('L','R'):
  sh=np.array(rig.data.bones['B_'+side+'_UpperArm'].head_local)
  cl=np.array(rig.data.bones['B_'+side+'_Clavicle'].head_local);d=(sh-cl)/np.linalg.norm(sh-cl)
  fade=np.clip((.09-(co-sh)@d)/.16,0,1)*(piece==0)
  for n in ('UpperArm','UpperArmTwist'):
   key='B_'+side+'_'+n
   if key in gi:
    moved=w[:,gi[key]]*fade;w[:,gi[key]]-=moved;w[:,gi['B_'+side+'_Clavicle']]+=moved
 # Remove leg contamination from the upper torso, then blend smoothly into the neck.
 legs=[i for n,i in gi.items() if any(x in n for x in ('Thigh','Calf','Foot','Toe')) or n=='B_Pelvis']
 amount=np.clip((co[:,2]-1.10)/.12,0,1)*(piece==0)
 moved=w[:,legs].sum(1)*amount;w[:,legs]*=(1-amount[:,None]);w[:,gi['B_Spine']]+=moved
 amount=np.clip((co[:,2]-1.40)/.14,0,1)*np.clip((.18-abs(co[:,0]+.009))/.08,0,1)*(piece==0)
 w*=1-amount[:,None];w[:,gi['B_Neck']]+=amount
mask=piece==7;a=np.clip((co[:,2]-1.56)/.065,0,1)
w[mask]=0;w[mask,gi['B_Neck']]=1-a[mask];w[mask,gi['B_Head']]=a[mask]
# The short mantle follows the chest, with a gradual shoulder share toward its outer edge.
mask=piece==1;w[mask]=0
side=np.where(co[:,0]<0,'R','L');outer=np.clip((abs(co[:,0])-.12)/.20,0,1)
neck=np.clip((co[:,2]-1.54)/.07,0,1)*.35
for i in np.where(mask)[0]:
 w[i,gi['B_Spine2']]=1-neck[i]-.45*outer[i]
 w[i,gi['B_Neck']]=neck[i]
 w[i,gi['B_'+side[i]+'_Clavicle']]=.30*outer[i]
 w[i,gi['B_'+side[i]+'_UpperArm']]=.15*outer[i]
for part,side in ((3,'R'),(4,'L')):
 mask=piece==part;n='B_'+side+'_ForearmTwist' if 'B_'+side+'_ForearmTwist' in gi else 'B_'+side+'_Forearm'
 w[mask]=0;w[mask,gi[n]]=1
mask=np.isin(piece,[2,6]);w[mask]=0;w[mask,gi['B_Pelvis']]=1
mask=piece==5;a=np.clip((1.10-co[:,2])/.37,0,1)*.65
w[mask]=0;w[mask,gi['B_Pelvis']]=1-a[mask];w[mask,gi['B_L_Thigh']]=a[mask]*.5;w[mask,gi['B_R_Thigh']]=a[mask]*.5
if 'B_R_ForearmTwist' in gi:
 # A physical-radius kernel avoids weight jumps across tiny triangles in the armpits.
 from mathutils.kdtree import KDTree
 ids=np.where((piece==0)&(co[:,2]>1.12))[0];tree=KDTree(len(ids))
 for i in ids:tree.insert(co[i],int(i))
 tree.balance();source=w.copy()
 for i in ids:
  blend=float(np.clip((co[i,2]-1.14)/.12,0,1)*np.clip((1.60-co[i,2])/.12,0,1))
  if blend==0:continue
  hits=tree.find_range(co[i],.09);js=np.array([h[1] for h in hits]);d=np.array([h[2] for h in hits]);k=np.exp(-.5*(d/.035)**2)
  average=(source[js]*k[:,None]).sum(0)/k.sum();w[i]=source[i]*(1-blend)+average*blend
if 'B_R_ForearmTwist' in gi:
 # The clavicle ends at the shoulder; lower biceps skin must follow the upper arm.
 for side in ('L','R'):
  sh=np.array(rig.data.bones['B_'+side+'_UpperArm'].head_local)
  el=np.array(rig.data.bones['B_'+side+'_Forearm'].head_local);direction=(el-sh)/np.linalg.norm(el-sh)
  upper=w[:,gi['B_'+side+'_UpperArm']]+w[:,gi['B_'+side+'_UpperArmTwist']]
  amount=np.clip(((co-sh)@direction-.02)/.10,0,1)*(piece==0)*(upper>.1)
  moved=w[:,gi['B_'+side+'_Clavicle']]*amount
  w[:,gi['B_'+side+'_Clavicle']]-=moved;w[:,gi['B_'+side+'_UpperArm']]+=moved
if 'B_R_ForearmTwist' in gi:
 # Fit contact surfaces with the same four influences that the runtime consumes.
 keep=np.argsort(w,axis=1)[:,-4:];reduced=np.zeros_like(w)
 np.put_along_axis(reduced,keep,np.take_along_axis(w,keep,axis=1),axis=1);w=reduced
w/=np.maximum(w.sum(1,keepdims=True),1e-9)
assert np.all(w.sum(1)>.99)
for g in o.vertex_groups:g.remove(list(range(len(co))))
for vi,row in enumerate(w):
 for j in np.where(row>1e-5)[0]:o.vertex_groups[j].add([vi],float(row[j]),'REPLACE')
print('COMPONENT_WEIGHTS',len(co),'vertices')
bpy.ops.wm.save_as_mainfile(filepath=out)
