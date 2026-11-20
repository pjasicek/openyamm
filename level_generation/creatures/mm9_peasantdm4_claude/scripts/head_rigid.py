"""Rigid head (VARIANTS_BRIEF, user review 2026-11-02: the whole face moves with the Head bone; Kira's jaw shear).
fit_rig.py weighted PeasantDM4's one-shell head (face, beard, hair) by the nearest MM9 bone: Bone03 (MM9's chin, turned
24-38 deg in AttackMelee and Hit), Bip01 Ponytail1 (MM9's hair, 49 deg in Talk), Neck, Spine2 and a little of both
clavicles. Here every vertex of a head-set face (attribute head = 1; the hands are hand = 1 and keep theirs):
  - Bone03, Ponytail1 and any Clavicle/UpperArm share go to Head;
  - above Z1 (Blender rest; the chin and everything above) the vertex is 100 % Head;
  - between Z0 and Z1 (the beard's and the hair's ends on the chest and shoulders) Head = t + (1 - t) x its own Head
    share, Neck and Spine2 keep (1 - t) of theirs, t = smoothstep(Z0, Z1, z), so the ends follow the chest a little.
Weights only (UVs, positions, attributes unchanged). Args (Blender): <in blend> <out blend> [z0 0.26] [z1 0.34]"""
import bpy, bmesh, sys
a = sys.argv[sys.argv.index('--') + 1:]
src, dst = a[0], a[1]
Z0 = float(a[2]) if len(a) > 2 else 0.26; Z1 = float(a[3]) if len(a) > 3 else 0.34
bpy.ops.wm.open_mainfile(filepath=src)
ob = bpy.data.objects['Body']; me = ob.data
bm = bmesh.new(); bm.from_mesh(me); hl = bm.faces.layers.int.get('head'); hal = bm.faces.layers.int.get('hand')
hv = {v.index for f in bm.faces if f[hl] == 1 and not (hal and f[hal] == 1) for v in f.verts}
bm.free()
G = {g.name: g for g in ob.vertex_groups}
head = G['Bip01 Head']
TO_HEAD = ('Bone03', 'Ponytail', 'Clavicle', 'UpperArm')
moved = 0; rigid = 0
for i in hv:
    v = me.vertices[i]
    w = {ob.vertex_groups[g.group].name: g.weight for g in v.groups}
    tot = sum(w.values()) or 1.0
    w = {k: x / tot for k, x in w.items()}
    h = sum(x for k, x in w.items() if k == 'Bip01 Head' or any(t in k for t in TO_HEAD))
    rest = {k: x for k, x in w.items() if not (k == 'Bip01 Head' or any(t in k for t in TO_HEAD))}
    z = v.co.z
    t = min(1.0, max(0.0, (z - Z0) / (Z1 - Z0))); t = t * t * (3 - 2 * t)
    nh = t + (1 - t) * h
    new = {'Bip01 Head': nh}
    for k, x in rest.items():
        new[k] = (1 - t) * x
    for k in w:
        G[k].remove([i])
    for k, x in new.items():
        if x > 1e-4:
            G[k].add([i], x, 'REPLACE')
    moved += 1; rigid += nh > 0.999
bpy.ops.wm.save_as_mainfile(filepath=dst)
print('HEAD_RIGID verts', moved, 'fully Head', rigid, 'z0', Z0, 'z1', Z1)
