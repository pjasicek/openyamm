"""Rest the hind toes on the floor in the bind pose (MM9 bind = standing feet on z = 0): Meshy's claw tips hook
up to 0.54 below the sole. Hind-leg vertices (rig group leg_l/leg_r) below LIMIT get a smooth floor clamp
z' = S*ln(1+exp(z/S)) blended in over [0, LIMIT], so the claws flatten onto the floor instead of cutting it.
Args: <in blend> <out blend>"""
import bpy, sys, math
argv = sys.argv[sys.argv.index('--') + 1:]
S, LIMIT = 0.03, 0.25
bpy.ops.wm.open_mainfile(filepath=argv[0])
ob = bpy.data.objects['Body']
ch = ob.data.attributes['chain']
moved, low = 0, 0.0
for v in ob.data.vertices:
    if ch.data[v.index].value not in (3, 4) or v.co.z >= LIMIT:
        continue
    z = v.co.z
    soft = S * math.log1p(math.exp(min(z / S, 50)))
    w = 1.0 if z <= 0 else 1.0 - z / LIMIT
    nz = w * max(soft, 0.0) + (1 - w) * z
    if abs(nz - z) > 1e-5:
        moved += 1
    low = min(low, z)
    v.co.z = nz
bpy.ops.wm.save_as_mainfile(filepath=argv[1])
print('FEET moved', moved, 'lowest before', round(low, 3), 'after', round(min(v.co.z for v in ob.data.vertices), 3))
