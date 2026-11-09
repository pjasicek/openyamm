import bpy, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def sample(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    rig = bpy.data.objects['Wyrm_Rig']; out = {}
    for a in bpy.data.actions:
        rig.animation_data.action = a
        f0, f1 = (int(x) for x in a.frame_range)
        vals = []
        for f in range(f0, f1 + 1, 3):
            bpy.context.scene.frame_set(f)
            vals += [round(x, 4) for b in ('Head', 'Spine1', 'HindPaw_L', 'Tail5') for x in rig.pose.bones[b].matrix.translation]
        out[a.name] = vals
    rest = {b.name: tuple(round(x, 5) for x in b.head_local) for b in rig.data.bones}
    return out, rest
a, ra = sample(os.path.join(HERE, 'work', 'source_snapshot.blend'))
b, rb = sample(os.path.join(os.path.dirname(HERE), 'mm6_drr1_claude', 'export', 'mm6_wyrm.blend'))
print('RESTDIFF', [k for k in ra if ra[k] != rb.get(k)])
for k in a:
    d = max((abs(x - y) for x, y in zip(a[k], b.get(k, []))), default=-1)
    print('ACTION', k, len(a[k]), len(b.get(k, [])), 'maxdiff', d)
