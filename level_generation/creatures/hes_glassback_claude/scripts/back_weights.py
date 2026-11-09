"""Back weights: the crest crystals are rigid on spine bones, so the hide they stand on must follow the spine only.
Heat weights let the shoulder and hip plates follow the upper legs (the outer shoulder spines opened 8x their sink in
the walk). Above z 0.92 every leg influence moves to the vertex's strongest spine/neck/tail bone, blending from
z 0.80. Args: -- <in> <out>"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=C.path(src))
mesh = bpy.data.objects[C.MESH]
G = {g.index: g.name for g in mesh.vertex_groups}
LO, HI = 0.80, 0.92
n = 0
for v in mesh.data.vertices:
    if v.co.z <= LO or not v.groups:
        continue
    f = min(1.0, (v.co.z - LO) / (HI - LO))
    w = {G[g.group]: g.weight for g in v.groups}
    legs = {k: x for k, x in w.items() if k.startswith(('Upper', 'Lower', 'Foot'))}
    if not legs:
        continue
    axial = {k: x for k, x in w.items() if k not in legs}
    target = max(axial, key=axial.get) if axial else ('Spine3' if v.co.y < -0.4 else 'Spine2' if v.co.y < 0.1 else 'Spine1')
    moved = sum(legs.values()) * f
    for k in legs:
        w[k] *= 1 - f
    w[target] = w.get(target, 0.0) + moved
    for g in list(v.groups):
        mesh.vertex_groups[g.group].remove([v.index])
    for k, x in w.items():
        if x > 1e-4:
            mesh.vertex_groups[k].add([v.index], x, 'REPLACE')
    n += 1
print('BACK reweighted', n)
bpy.ops.wm.save_as_mainfile(filepath=C.path(dst))
