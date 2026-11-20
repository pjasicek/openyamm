"""Debug: each candidate vertex against the deformed source surface point it was matched to in the rest pose
(normal_weights.py face/bary; exact source vertices against themselves). Isolates skinning error from shape error.
Usage: blender -b -P probe_weights.py -- <blend> <Cand_87> <clip:frame,...>"""
import os, sys, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; c = bpy.data.objects[a[1]]
tag = a[1].split('_')[1]
d = np.load(os.path.join(HERE, 'work', f'mesh_r{tag}.npz')); w = np.load(os.path.join(HERE, 'work', f'weights_r{tag}.npz'))
sf = np.load(os.path.join(HERE, 'work', 'mesh_in.npz'))['faces']
def ev(o):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); m = e.to_mesh()
    p = np.array([o.matrix_world @ v.co for v in m.vertices]); e.to_mesh_clear(); return p
for cf in a[2].split(','):
    clip, f = cf.split(':'); rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(int(f))
    ps, pc = ev(src), ev(c)
    target = np.einsum('vk,vkc->vc', w['bary'], ps[sf[w['face']]])
    new = d['src_index'] < 0
    dd = np.linalg.norm(pc - target, axis=1)
    print('FRAME', cf, 'new verts', new.sum(), 'max mm', round(dd[new].max() * 1000, 1), 'p99', round(np.percentile(dd[new], 99) * 1000, 2))
    for b in np.argsort(-np.where(new, dd, 0))[:5]:
        print('   ', round(dd[b] * 1000, 1), np.round(d['verts'][b], 3), 'face', w['face'][b])
