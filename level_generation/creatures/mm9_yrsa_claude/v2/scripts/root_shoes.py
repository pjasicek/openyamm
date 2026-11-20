"""Root Yrsa's boots in her body (texture pass session 2026-10-30, after claude_shared/detached_parts_mm9.md: both boots
are separate pieces; the right one 5.1 cm from anything at bind, the left one parting by 6.2 cm in Hit).

Args (Blender): <master blend (v2/work/head_v1.blend)> <out blend> <report json>

Why: the Meshy dress is a hollow shell (skirt and bodice; no hips or thighs inside it), and the boots are open tubes
that end at the knee inside the skirt, weighted to the back skirt chains (xbk*) at the top and the calf/foot below. So
there is no leg to root them in: the gap was between the boot top and the inside of the skirt.

Fix (as mm9_eye_claude/scripts/root_limbs.py stretches a leg's first segment into the body): each boot's top band
(the vertices within BAND of the open top ring) is stretched up along a line to a hip point under the waist
(HIP x sign, y, z), where the skirt narrows. The ring vertices move to the waist: each one is cast horizontally from
the hip point in its own direction around the boot; where the inside of the skirt is within REACH it lands
INSET inside that surface (so it touches it, from the cavity side) and takes the skirt's weights at the hit point
(barycentric); the others (the inner side, towards the other leg) sit at RADIUS and take the mean of those weights.
Band vertices move by their share of the band height (u = 0 at the cut, 1 at the ring) and blend from their own
weights to their ring vertex's new weights by smoothstep(u). The boots below the band, every other vertex, UVs,
textures and clips are unchanged; the band's leather texels stretch over the new thigh, which only shows from under
the skirt. No vertices or faces are added.
"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv
BAND = 0.06          # band below the lowest top-ring vertex that stretches
HIP = (0.065, -0.01, 0.10)   # hip point (Blender rest coordinates, x mirrored per side)
REACH = 0.12
INSET = 0.002
RADIUS = 0.05
MAX_INFLUENCES = 4


def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']
rig = body.parent
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
M = body.matrix_world
Mi = M.inverted()
names = [g.name for g in body.vertex_groups]
n = len(me.vertices)
W = np.zeros((n, len(names)))
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
comp = -np.ones(n, int)
nc = 0
for v in bm.verts:
    if comp[v.index] >= 0:
        continue
    st = [v]; comp[v.index] = nc
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0:
                comp[y.index] = nc; st.append(y)
    nc += 1
co = [M @ v.co for v in me.vertices]
boots = {}
for k in range(nc):
    ids = np.nonzero(comp == k)[0]
    if len(ids) > 400:
        continue
    top = names[int(np.argmax(W[ids].sum(0)))]
    for side in 'LR':
        if top == f'FHP {side} Foot':
            boots[side] = k
assert set(boots) == {'L', 'R'}, boots
others = [p.index for p in me.polygons if comp[p.vertices[0]] not in boots.values()]
bvh = BVHTree.FromPolygons(co, [me.polygons[i].vertices[:] for i in others])
newco = list(co)
newW = W.copy()
report = {}
for side, k in sorted(boots.items()):
    ids = np.nonzero(comp == k)[0]
    ring = [v.index for v in bm.verts if comp[v.index] == k and v.is_boundary]
    rc = sum((co[i] for i in ring), Vector()) / len(ring)
    hip = Vector((HIP[0] * (1 if rc.x > 0 else -1), HIP[1], HIP[2]))
    zr = float(np.mean([co[i].z for i in ring]))
    z_cut = min(co[i].z for i in ring) - BAND
    ring_target, ring_w, landed = {}, {}, []
    for i in ring:
        d = Vector((co[i].x - rc.x, co[i].y - rc.y, 0)).normalized()
        loc, nrm, fi, dist = bvh.ray_cast(hip, d, REACH)
        if loc is not None:
            p = loc - d * INSET
            f = me.polygons[others[fi]]
            tri = [co[j] for j in f.vertices]
            A, B, C = tri
            v0, v1, v2 = B - A, C - A, loc - A
            d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
            den = d00 * d11 - d01 * d01
            bv = (d11 * d20 - d01 * d21) / den
            bw = (d00 * d21 - d01 * d20) / den
            bary = (1 - bv - bw, bv, bw)
            ring_w[i] = sum(bary[m] * W[f.vertices[m]] for m in range(3))
            landed.append(i)
        else:
            p = hip + d * RADIUS
        ring_target[i] = p + Vector((0, 0, co[i].z - zr))
    assert landed, f'{side}: no skirt surface within {REACH} m of the hip point'
    mean_w = sum(ring_w[i] for i in landed) / len(landed)
    for i in ring:
        ring_w.setdefault(i, mean_w)
    moved = 0
    for i in ids:
        if co[i].z <= z_cut:
            continue
        if i in ring_target:
            r, u = i, 1.0
        else:
            ang = np.arctan2(co[i].y - rc.y, co[i].x - rc.x)
            r = min(ring, key=lambda j: abs((np.arctan2(co[j].y - rc.y, co[j].x - rc.x) - ang + np.pi)
                                            % (2 * np.pi) - np.pi))
            u = min(0.95, max(0.0, (co[i].z - z_cut) / (zr - z_cut)))
        newco[i] = co[i] + (ring_target[r] - co[r]) * u
        t = smooth(u)
        newW[i] = (1 - t) * W[i] + t * ring_w[r]
        moved += 1
    tw = {names[g]: round(float(mean_w[g]), 3) for g in np.argsort(-mean_w)[:5] if mean_w[g] > 0.01}
    report[side] = {'part': int(k), 'ring_vertices': len(ring), 'landed_on_skirt': len(landed), 'moved': moved,
                    'top_ring_z_before': round(zr, 4), 'hip': [round(x, 4) for x in hip],
                    'stretch_m': round(float(np.mean([(ring_target[i] - co[i]).length for i in ring])), 4),
                    'top_weights': tw}

# keep MAX_INFLUENCES, renormalise; write positions and weights
for i in range(n):
    if newco[i] is co[i]:
        continue
    w = newW[i]
    keep = np.argsort(-w)[:MAX_INFLUENCES]
    w2 = np.zeros_like(w); w2[keep] = w[keep]; w2 /= w2.sum()
    me.vertices[i].co = Mi @ newco[i]
    for g in range(len(names)):
        if w2[g] > 0:
            body.vertex_groups[g].add([i], float(w2[g]), 'REPLACE')
        elif W[i, g] > 0:
            body.vertex_groups[g].remove([i])
me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('ROOT_SHOES', json.dumps(report))
json.dump(report, open(REP, 'w'), indent=1)
