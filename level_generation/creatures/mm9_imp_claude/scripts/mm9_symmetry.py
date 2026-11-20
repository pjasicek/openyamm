import bpy, sys, numpy as np
from mathutils.kdtree import KDTree
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
arm = bpy.data.objects['MM9_Rig']
for n in ['Bip01 Pelvis','Bip01 L Thigh','Bip01 R Thigh','Bip01 L Calf','Bip01 R Calf','Bip01 L Foot','Bip01 R Foot','Bip01 L Toe1','Bip01 R Toe1','Bip01 L UpperArm','Bip01 R UpperArm','Bip01 L Hand','Bip01 R Hand','Bip01 Neck','Bip01 Head','Bip01 Tail','Bip01 Tail4','Yweaponbase','Xpiv']:
    print(n, [round(x,3) for x in arm.data.bones[n].head_local], [round(x,2) for x in (arm.data.bones[n].tail_local-arm.data.bones[n].head_local).normalized()])
o = bpy.data.objects['body.mesh']
P = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
k = KDTree(len(P))
for i,p in enumerate(P): k.insert(Vector(p),i)
k.balance()
d = np.array([k.find(Vector((-p[0],p[1],p[2])))[2] for p in P])
print('mirror residual mean %.4f p90 %.4f max %.4f'%(d.mean(),np.percentile(d,90),d.max()))
m = d>0.01
print('asym verts',m.sum(), 'z range', P[m,2].min() if m.any() else None, P[m,2].max() if m.any() else None)
