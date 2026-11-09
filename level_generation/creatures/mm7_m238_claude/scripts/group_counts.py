"""Vertices per vertex group of 'Body' with weight > 0.05 (debug). Args: -- <blend> [group substring ...]"""
import bpy, sys, os
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
b = bpy.data.objects['Body']; cnt = {g.index: 0 for g in b.vertex_groups}
for v in b.data.vertices:
    for e in v.groups:
        if e.weight > 0.05:
            cnt[e.group] += 1
print('GROUPS', {g.name: cnt[g.index] for g in b.vertex_groups if not a[1:] or any(k in g.name for k in a[1:])})
