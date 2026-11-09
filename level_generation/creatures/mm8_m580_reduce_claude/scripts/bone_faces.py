"""Faces per dominant bone of the rest mesh (work/source.blend) -> print, and work/face_bone.npy (dominant bone
name per face) for keep sets."""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
src = bpy.data.objects['Body']; me = src.data; me.calc_loop_triangles()
names = [g.name for g in src.vertex_groups]
W = np.zeros((len(me.vertices), len(names)))
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
F = np.array([t.vertices[:] for t in me.loop_triangles])
dom = W[F].sum(1).argmax(1)
np.save(os.path.join(HERE, 'work', 'face_bone.npy'), np.array(names)[dom])
for i in np.argsort(-np.bincount(dom, minlength=len(names))):
    print('BONE', names[i], int((dom == i).sum()))
