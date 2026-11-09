import bpy, sys, json, numpy as np, bmesh
from mathutils import Quaternion
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); P=json.load(open(a[1]))
body=bpy.data.objects['Body']; rig=body.parent
if rig.animation_data: rig.animation_data.action=None
for pb in rig.pose.bones: pb.matrix_basis.identity(); pb.rotation_mode='QUATERNION'
for k in ('grip','hand_offset'):
    for n,q in P.get(k,{}).items(): rig.pose.bones[n].rotation_quaternion=Quaternion((q[3],q[0],q[1],q[2]))
bpy.context.view_layer.update()
for xb in ('Xbase',):
    if xb in rig.pose.bones: rig.pose.bones[xb].matrix=rig.data.bones[xb].matrix_local.copy()      # the pipeline takes the wrist turn back out of Xbase: the mallet stays MM9's
bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get(); ev=body.evaluated_get(dg); em=ev.to_mesh()
X=np.array([tuple(body.matrix_world@v.co) for v in em.vertices]); ev.to_mesh_clear()
me=body.data; bm=bmesh.new(); bm.from_mesh(me); lay=bm.verts.layers.int['part']; part=np.array([v[lay] for v in bm.verts]); bm.free()
gid={g.index:g.name for g in body.vertex_groups}
dom=np.array([gid[max(v.groups,key=lambda x:x.weight).group] if v.groups else '' for v in me.vertices])
M=X[part==20]; c=M.mean(0); ax=np.linalg.svd(M-c)[2][0]
# shaft verts: those within 4 cm of the axis
d=M-c; r=np.linalg.norm(d-np.outer(d@ax,ax),axis=1); S_=M[r<0.045]; c=S_.mean(0); ax=np.linalg.svd(S_-c)[2][0]; d=S_-c; R=np.median(np.linalg.norm(d-np.outer(d@ax,ax),axis=1))
kn=X[np.where(dom=='Bip01 R Index1')[0]].mean(0)-X[np.where(dom=='Bip01 R Pinky1')[0]].mean(0)
print('CHK shaft radius cm', round(R*100,2), 'angle shaft vs posed knuckle line deg', round(float(np.degrees(np.arccos(abs(ax@kn)/np.linalg.norm(kn)))),1))
for f in ('Index','Middle','Ring','Pinky','Thumb'):
    for i in (1,2,3):
        V=X[dom==f'Bip01 R {f}{i}']; dv=V-c; rv=np.linalg.norm(dv-np.outer(dv@ax,ax),axis=1)
        print('CHK',f,i,'min to axis cm',round(rv.min()*100,2))
H=X[dom=='Bip01 R Hand']; dv=H-c; print('CHK palm min cm', round(np.linalg.norm(dv-np.outer(dv@ax,ax),axis=1).min()*100,2))
Wm=rig.matrix_world
hp=lambda n: np.array(Wm@rig.pose.bones[n].head)
knj=hp('Bip01 R Index1')-hp('Bip01 R Pinky1')
print('CHK joint knuckle line vs shaft deg', round(float(np.degrees(np.arccos(abs(ax@knj)/np.linalg.norm(knj)))),1))
for k in ('hand_offset',):
    q=P.get(k,{}).get('Bip01 R Hand'); print('CHK hand_offset', q)
pb=rig.pose.bones['Bip01 R Hand']; Rr=np.array(rig.data.bones['Bip01 R Hand'].matrix_local)[:3,:3]; Rp=np.array(pb.matrix)[:3,:3]
print('CHK hand turn applied deg', round(float(np.degrees(np.arccos(np.clip((np.trace(Rr.T@Rp)-1)/2,-1,1)))),2))
kr=np.array(Wm@rig.data.bones['Bip01 R Index1'].head_local)-np.array(Wm@rig.data.bones['Bip01 R Pinky1'].head_local)
print('CHK rest knuckle line vs shaft deg', round(float(np.degrees(np.arccos(abs(ax@kr)/np.linalg.norm(kr)))),1), 'posed vs rest kn deg', round(float(np.degrees(np.arccos((kr@knj)/np.linalg.norm(kr)/np.linalg.norm(knj)))),1))
print('CHK mallet verts', int((part==20).sum()), 'axis', np.round(ax,3))
MZ=np.load('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_giant_claude/work/mallet.npz'); Mm=MZ['M']; AXm=Mm[:3,1]/np.linalg.norm(Mm[:3,1])
print('CHK AXm', np.round(AXm,3), 'angle shaft vs AXm deg', round(float(np.degrees(np.arccos(abs(ax@AXm)))),1), 'rest kn vs AXm', round(float(np.degrees(np.arccos(abs(kr@AXm)/np.linalg.norm(kr)))),1))
