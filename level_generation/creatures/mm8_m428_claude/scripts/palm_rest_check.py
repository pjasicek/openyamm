"""Rest-pose check of the right palm direction: knuckle-plane normal vs the mean normal of the hand's palm-side
skin (vertices of the right hand whose normal points away from the back of the hand). Args: -- <blend>"""
import bpy, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); body = bpy.data.objects.get('Body') or bpy.data.objects.get('M428')
rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
H = lambda n: np.array(rig.data.bones[n].head_local)
f = H('B_R_Finger2') - H('B_R_Hand'); t = H('B_R_Finger1') - H('B_R_Finger4'); n = np.cross(f, t); n /= np.linalg.norm(n)
print('REST f', np.round(f / np.linalg.norm(f), 2), 't(thumb side)', np.round(t / np.linalg.norm(t), 2), 'f x t', np.round(n, 2))
g = body.vertex_groups['B_R_Hand'].index
c = H('B_R_Hand') + f * 0.5
vs = [v for v in body.data.vertices if any(e.group == g and e.weight > 0.6 for e in v.groups)]
co = np.array([v.co[:] for v in vs]); nr = np.array([v.normal[:] for v in vs])
side = (co - co.mean(0)) @ n
print('REST hand verts', len(vs), 'normals on the +n side mean', np.round(nr[side > 0.005].mean(0), 2), 'on the -n side mean', np.round(nr[side < -0.005].mean(0), 2))
print('REST thumb tip x', round(float(H('B_R_Finger0.002')[0] if 'B_R_Finger0.002' in rig.data.bones else 0), 3), 'hand x', round(float(H('B_R_Hand')[0]), 3), 'thumb root y', round(float(H('B_R_Finger0')[1]), 3), 'hand y', round(float(H('B_R_Hand')[1]), 3))
