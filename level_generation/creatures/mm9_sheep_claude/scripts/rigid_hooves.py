"""Hooves rigid on their foot bones: diffusion left the small hoof shared with the ankle, so it turned up to 16 degrees
off MM9's rigid foot in Running (orient_gate.py). Below z = HOOF_TOP the weight is 1 on the foot bone (by side and
end), blending back to the existing weights over BLEND above it. Weights only. Args: <in blend> <out blend>"""
import bpy, sys
argv = sys.argv[sys.argv.index('--') + 1:]
HOOF_TOP, BLEND = 0.07, 0.035
bpy.ops.wm.open_mainfile(filepath=argv[0])
o = bpy.data.objects['Body']; me = o.data
names = {g.index: g.name for g in o.vertex_groups}
n = 0
for v in me.vertices:
    z = v.co.z
    if z > HOOF_TOP + BLEND:
        continue
    bone = ('Xffoot' if v.co.y < 0 else 'Xbfoot') + ('01' if v.co.x > 0 else '')
    a = 1.0 if z <= HOOF_TOP else 1 - (z - HOOF_TOP) / BLEND
    a = a * a * (3 - 2 * a)
    old = {names[g.group]: g.weight for g in v.groups}
    for k in old:
        o.vertex_groups[k].remove([v.index])
    new = {k: w * (1 - a) for k, w in old.items()}
    new[bone] = new.get(bone, 0.0) + a
    top = sorted(new.items(), key=lambda t: -t[1])[:4]
    tot = sum(w for _, w in top)
    for k, w in top:
        if w / tot > 1e-3:
            o.vertex_groups[k].add([v.index], w / tot, 'REPLACE')
    n += 1
print('HOOVES', n)
bpy.ops.wm.save_as_mainfile(filepath=argv[1])
