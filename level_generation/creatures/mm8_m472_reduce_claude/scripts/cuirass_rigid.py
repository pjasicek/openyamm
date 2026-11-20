"""Cuirass rigidity of the picked candidate (work/ladder.blend Cand_62, REA_CAND): vertices of cuirass faces
(work/mesh_r62.npz group 4, plus kept source faces of that piece) and their B_Spine1 weight; source likewise."""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
d = np.load(os.path.join(HERE, 'work', 'mesh_r62.npz')); g0 = np.load(os.path.join(HERE, 'work', 'groups.npy'))
src_faces = np.load(os.path.join(HERE, 'work', 'mesh_in.npz'))['faces']
for name, faces, sel in (('source', src_faces, g0 == 4), ('Cand_62', d['faces'], None)):
    o = bpy.data.objects[name if name != 'source' else 'Body']
    if sel is None:  # candidate: decimated cuirass faces, plus kept faces whose source face was cuirass
        cen = d['verts'][faces].mean(1); scen = np.load(os.path.join(HERE, 'work', 'mesh_in.npz'))['verts'][src_faces].mean(1)
        from mathutils import kdtree
        t = kdtree.KDTree(len(scen))
        for i, c in enumerate(scen):
            t.insert(c, i)
        t.balance()
        sel = (d['group'] == 4) | np.array([(d['group'][i] == -1) and g0[t.find(cen[i])[1]] == 4 for i in range(len(faces))])
    vs = np.unique(faces[sel]); gi = o.vertex_groups['B_Spine1'].index
    w = np.array([sum(x.weight for x in o.data.vertices[int(v)].groups if x.group == gi) for v in vs])
    print('RIGID', name, len(vs), 'verts, B_Spine1 weight min', round(float(w.min()), 4), 'below 0.999:', int((w < .999).sum()))
