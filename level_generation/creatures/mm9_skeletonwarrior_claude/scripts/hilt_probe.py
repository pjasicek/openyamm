import bpy,sys,numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--')+1])
rig=bpy.data.objects['MM9_Rig']; s=bpy.data.objects['MM9_Scimitar']
dg=bpy.context.evaluated_depsgraph_get()
em=s.evaluated_get(dg).to_mesh()
v=np.array([tuple(s.matrix_world@x.co) for x in em.vertices])
print('SC bounds',v.min(0),v.max(0))
J=lambda n:np.array(rig.matrix_world@rig.data.bones[n].head_local)
for n in ('Bip01 R Hand','Bip01 R Finger0','RHand1','Bone01','Bip01 R Forearm'):print('SC',n,J(n))
b=J('Bone01')
d=np.linalg.norm(v-b,axis=1);print('SC near',np.sort(d)[[0,10,40,90]])
c=v.mean(0);u,sv,vt=np.linalg.svd(v-c,full_matrices=False);print('SC pca',vt[0],sv)
t=(v-c)@vt[0]
print('SC ends',v[np.argmin(t)],v[np.argmax(t)])
far=np.argsort(d)
print('SC far',v[far[-1]],'near',v[far[:6]])
H=rig.data.bones['Bip01 R Hand'].matrix_local
print('SC handframe',np.array(H)[:3,:3].T)
for lo,hi in ((0,.04),(.04,.1),(.1,.2),(.2,.4),(.4,.9)):
    m=(d>=lo)&(d<hi); 
    if m.any():print('SC band',lo,hi,m.sum(),v[m].mean(0))
