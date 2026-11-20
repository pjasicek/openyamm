import bpy, sys, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
b = bpy.data.objects['Body']; rig = b.parent; me = b.data
pid = np.zeros(len(me.vertices), int); me.attributes['pid'].data.foreach_get('value', pid)
co = np.array([tuple(v.co) for v in me.vertices])
gn = {g.index: g.name for g in b.vertex_groups}
wr = np.array(rig.matrix_world @ rig.data.bones['Bip01 R Hand'].head_local)
idx = np.where(pid == 7)[0]
d = np.linalg.norm(co[idx] - wr, axis=1)
print('PR max dist', d.max(), 'pcts', np.percentile(d, [50, 90, 99]))
print('PR far', [(int(i), round(float(np.linalg.norm(co[i] - wr)), 3), [(gn[g.group], round(g.weight, 2)) for g in me.vertices[i].groups]) for i in idx[np.argsort(-d)[:4]]])

th = [v.index for v in me.vertices if any(gn[g.group].startswith('Bip01 R Thumb') for g in v.groups)]
print('PR thumb verts', len(th), 'ext', (co[th].max(0) - co[th].min(0)).round(3), co[th].mean(0).round(3))
for n in ('Thumb1', 'Thumb2', 'Thumb3', 'Index1', 'Index3'):
    bb = rig.data.bones['Bip01 R ' + n]; print('PR', n, np.round(bb.head_local, 3), np.round(bb.tail_local, 3), round(bb.length, 3))
print('PR hand head', np.round(wr, 3))
