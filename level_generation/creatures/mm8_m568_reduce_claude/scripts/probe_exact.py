"""Debug: candidate vertices that are source vertices (src_index) against the evaluated source vertex, per frame.
Prints per-region max/median. Usage: blender -b -P probe_exact.py -- <blend> <Cand_85> <clip:frame,...>"""
import os, sys, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
sc = bpy.context.scene; src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; c = bpy.data.objects[a[1]]
sidx = np.load(os.path.join(HERE, 'work', f"mesh_r{a[1].split('_')[1]}.npz"))['src_index']
print('cand verts', len(c.data.vertices), 'npz', len(sidx), 'mods src', [(m.type, getattr(m, 'use_deform_preserve_volume', None)) for m in src.modifiers],
      'cand', [(m.type, getattr(m, 'use_deform_preserve_volume', None)) for m in c.modifiers], 'parent', src.parent, c.parent)
def ev(o):
    dg = bpy.context.evaluated_depsgraph_get(); e = o.evaluated_get(dg); m = e.to_mesh()
    p = np.array([o.matrix_world @ v.co for v in m.vertices]); e.to_mesh_clear(); return p
names = {g.index: g.name for g in src.vertex_groups}
dom = np.array([names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '-' for v in src.data.vertices])
for cf in a[2].split(','):
    clip, f = cf.split(':'); rig.animation_data.action = bpy.data.actions[clip]; sc.frame_set(int(f))
    ps, pc = ev(src), ev(c); m = sidx >= 0
    dd = np.linalg.norm(pc[m] - ps[sidx[m]], axis=1)
    print('FRAME', cf, 'exact verts', m.sum(), 'max mm', round(dd.max() * 1000, 1), 'median', round(np.median(dd) * 1000, 2))
    bad = np.argsort(-dd)[:8]
    for b in bad:
        print('   ', round(dd[b] * 1000, 1), dom[sidx[m][b]])
