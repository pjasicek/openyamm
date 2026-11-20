"""Foot weights: heat weights blend the feet with the Lower bones, so planted soles move whenever the knee angle changes
(-1.5 cm standing, -6 cm walking). Every vertex of a leg below its ankle joint goes 100 % to Foot_<leg>, blending to
the heat weights over the next 6 cm above it. Leg membership = the dominant bone's leg. Args: -- <in> <out>"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=C.path(src))
mesh = bpy.data.objects[C.MESH]; rig = bpy.data.objects[C.RIG]
G = {g.index: g.name for g in mesh.vertex_groups}
changed = 0
for v in mesh.data.vertices:
    if not v.groups:
        continue
    dom = G[max(v.groups, key=lambda g: g.weight).group]
    if '_' not in dom or dom.split('_')[0] not in ('Upper', 'Lower', 'Foot'):
        continue
    leg = dom.split('_')[1]
    ankle_z = rig.data.bones[f'Foot_{leg}'].head_local.z
    t = (v.co.z - ankle_z) / 0.06
    if t >= 1.0:
        continue
    f = 1.0 if t <= 0 else 1.0 - t
    w = {G[g.group]: g.weight * (1 - f) for g in v.groups}
    w[f'Foot_{leg}'] = w.get(f'Foot_{leg}', 0.0) + f
    for g in list(v.groups):
        mesh.vertex_groups[g.group].remove([v.index])
    for name, value in w.items():
        if value > 1e-4:
            mesh.vertex_groups[name].add([v.index], value, 'REPLACE')
    changed += 1
print('FEET reweighted', changed)
bpy.ops.wm.save_as_mainfile(filepath=C.path(dst))
