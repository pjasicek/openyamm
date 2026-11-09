"""Pirate garment and prosthesis weights, over the fitted Meshy seed and twist distribution."""
import bpy,sys,numpy as np
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=src)
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
co=np.array([v.co[:] for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data])
names=[g.name for g in body.vertex_groups];gi={n:i for i,n in enumerate(names)}
w=np.zeros((len(co),len(names)))
for v in me.vertices:
 for ge in v.groups:w[v.index,ge.group]=ge.weight
J=lambda n:np.array(rig.data.bones[n].head_local)
def rigid(mask,bone):
 w[mask]=0;w[mask,gi[bone]]=1
# Head accessories are rigid; exposed chest/neck retain the fitted axial blend.
rigid(np.isin(pv,[4,13,14,17,18,21,23,24]),'B_Head')
axial=[gi[n] for n in names if n in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2','B_Neck','B_Head']]
mask=pv==1
for j in range(len(names)):
 if j not in axial:w[mask,j]=0
rigid((pv==1)&(co[:,2]>J('B_Head')[2]),'B_Head')
# The left prosthesis and folded cuffs are rigid shells carried by forearm pronation.
rigid(np.isin(pv,[7,10]),'B_L_ForearmTwist');rigid(pv==9,'B_R_ForearmTwist')
# Hand skin has no upper-arm contamination; only the proximal wrist blends with its sleeve.
mask=pv==3;wr=J('B_R_Hand');el=J('B_R_Forearm');d=(wr-el)/np.linalg.norm(wr-el)
t=np.clip(((co-wr)@d+0.01)/0.035,0,1)
w[mask]=0;w[mask,gi['B_R_Hand']]=t[mask];w[mask,gi['B_R_ForearmTwist']]=1-t[mask]
# Boot shafts follow the calf, soles follow the foot, with one broad ankle transition.
for sd,piece in [('L',5),('R',6)]:
 mask=pv==piece;z=J('B_'+sd+'_Foot')[2];t=np.clip((co[:,2]-z-0.025)/0.10,0,1)
 w[mask]=0;w[mask,gi['B_'+sd+'_Calf']]=t[mask];w[mask,gi['B_'+sd+'_Foot']]=1-t[mask]
# Sash tails: one pelvis/thigh mix across each strip so the cloth cannot split along the midline.
rigid(np.isin(pv,[11,20,22]),'B_Pelvis')
for piece in (12,19):
 mask=pv==piece;t=np.clip((1.01-co[:,2])/0.28,0,0.45)
 w[mask]=0;w[mask,gi['B_Pelvis']]=1-t[mask];w[mask,gi['B_L_Thigh']]=t[mask]
# Fade shoulder influence toward the clavicle only on the shirt's torso side.
for sd in ('L','R'):
 sh,cl=J('B_'+sd+'_UpperArm'),J('B_'+sd+'_Clavicle');d=(sh-cl)/np.linalg.norm(sh-cl)
 t=np.clip(1+((co-sh)@d)/0.07,0,1);mask=(pv==0)
 for suffix in ('UpperArm','UpperArmTwist'):
  a=gi['B_'+sd+'_'+suffix];b=gi['B_'+sd+'_Clavicle'];dw=w[:,a]*(1-t)*mask;w[:,a]-=dw;w[:,b]+=dw
assert np.all(w.sum(1)>1e-5)
w/=w.sum(1,keepdims=True)
for g in list(body.vertex_groups):body.vertex_groups.remove(g)
for n in names:body.vertex_groups.new(name=n)
for i,row in enumerate(w):
 for j in np.where(row>1e-5)[0]:body.vertex_groups[int(j)].add([i],float(row[j]),'REPLACE')
print('WEIGHTS pirate rules',len(co),'vertices; max sum error',float(abs(w.sum(1)-1).max()))
bpy.ops.wm.save_as_mainfile(filepath=out)
