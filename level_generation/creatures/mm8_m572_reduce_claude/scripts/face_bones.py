"""Per-face dominant bone of work/source.blend Body (loop-triangle order = mesh_in.npz) -> work/src_face_bone.npz"""
import os, sys, bpy, numpy as np, collections
proj = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=os.path.join(proj, 'work', 'source.blend'))
o = bpy.data.objects['Body']; me = o.data; me.calc_loop_triangles()
names = [g.name for g in o.vertex_groups]
vw = [{g.group: g.weight for g in v.groups} for v in me.vertices]
lab = []
for t in me.loop_triangles:
    acc = collections.Counter()
    for vi in t.vertices:
        for g, w in vw[vi].items(): acc[g] += w
    lab.append(acc.most_common(1)[0][0] if acc else -1)
np.savez(os.path.join(proj, 'work', 'src_face_bone.npz'), bone=np.array(lab), names=np.array(names))
print('FACEBONES', len(lab), sorted(collections.Counter(names[i] for i in lab).items(), key=lambda x: -x[1])[:40])
