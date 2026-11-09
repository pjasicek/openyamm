"""Body maps into the re-packed UVMap: per body triangle, every texel's barycentric point is looked up in the Meshy
layout (UVMeshy) and sampled from the 2K return (base colour, normal, roughness, metallic). Arm/hand texels (pieces
4, 5) instead take the installed model's base colour at the nearest point of its arm surface (review: brown cuff
smudges on the new arms, and the installed arms carry ~10x the texels); compose matches its skin colour.
Writes the lookup (Blender has no PIL): work/relayout_lookup.npz (meshy_uv, inst_uv per 2048 texel, -1 = none);
tex_sample.py samples the images."""
import bpy, os, numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INST = os.path.join(os.path.dirname(HERE), 'mm6_pman_claude_20261013')
N = 2048


def rest():
    rig = bpy.data.objects['Rig']; rig.animation_data.action = None
    for pb in rig.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()


# installed arms: BVH, UVs, base colour (installed body set 1K, Meshy v1 layout after its own fixes)
bpy.ops.wm.open_mainfile(filepath=os.path.join(INST, 'work', 'textured_uv.blend')); rest()
ib = bpy.data.objects['Body']; im = ib.data; ipc = [a.value for a in im.attributes['piece'].data]
ihead = [a.value for a in im.attributes['head'].data]; im.calc_loop_triangles()
itris = [t for t in im.loop_triangles if not ihead[t.polygon_index] and ipc[t.vertices[0]] in (4, 5)]
iverts = [ib.matrix_world @ v.co for v in im.vertices]
ibvh = BVHTree.FromPolygons(iverts, [tuple(t.vertices) for t in itris])
iuv = [[tuple(im.uv_layers['UVMap'].data[l].uv) for l in t.loops] for t in itris]
itv = [[iverts[i] for i in t.vertices] for t in itris]

bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'master_r45.blend')); rest()
b = bpy.data.objects['Body']; me = b.data; me.calc_loop_triangles()
pc = [a.value for a in me.attributes['piece'].data]; head = [a.value for a in me.attributes['head'].data]
V = np.array([(b.matrix_world @ v.co)[:] for v in me.vertices])
new, old = me.uv_layers['UVMap'].data, me.uv_layers['UVMeshy'].data
meshy_uv = np.full((N, N, 2), -1.0, np.float32); inst_uv = np.full((N, N, 2), -1.0, np.float32)


for t in me.loop_triangles:
    if head[t.polygon_index]: continue
    P = np.array([new[l].uv[:] for l in t.loops]) * N; Q = np.array([old[l].uv[:] for l in t.loops])
    a, bb, c = P; den = (bb[1] - c[1]) * (a[0] - c[0]) + (c[0] - bb[0]) * (a[1] - c[1])
    if abs(den) < 1e-10: continue
    lo = np.maximum(np.floor(P.min(0) - 1).astype(int), 0); hi = np.minimum(np.ceil(P.max(0) + 1).astype(int), N - 1)
    x, y = np.meshgrid(np.arange(lo[0], hi[0] + 1) + .5, np.arange(lo[1], hi[1] + 1) + .5)
    w0 = ((bb[1] - c[1]) * (x - c[0]) + (c[0] - bb[0]) * (y - c[1])) / den; w1 = ((c[1] - a[1]) * (x - c[0]) + (a[0] - c[0]) * (y - c[1])) / den
    w2 = 1 - w0 - w1; m = (w0 > -.02) & (w1 > -.02) & (w2 > -.02)
    if not m.any(): continue
    W = np.stack([w0[m], w1[m], w2[m]], 1); uvq = W @ Q; ix = (x[m] - .5).astype(int); iy = N - 1 - (y[m] - .5).astype(int)
    meshy_uv[iy, ix] = uvq
    if pc[t.vertices[0]] in (4, 5):
        pos = W @ V[list(t.vertices)]
        for j, p in enumerate(pos):
            hit = ibvh.find_nearest(p)
            if hit[0] is None: continue
            fi = hit[2]; A, B, C = itv[fi]
            # barycentric of the nearest point in the installed triangle
            v0, v1, v2 = B - A, C - A, hit[0] - A; d00, d01, d11 = v0.dot(v0), v0.dot(v1), v1.dot(v1); d20, d21 = v2.dot(v0), v2.dot(v1)
            dn = d00 * d11 - d01 * d01 or 1e-12; bv = (d11 * d20 - d01 * d21) / dn; bw = (d00 * d21 - d01 * d20) / dn; bu = 1 - bv - bw
            uv = np.array(iuv[fi]); u, v = bu * uv[0] + bv * uv[1] + bw * uv[2]
            inst_uv[iy[j], ix[j]] = (u, v)
np.savez_compressed(os.path.join(HERE, 'work', 'relayout_lookup.npz'), meshy_uv=meshy_uv, inst_uv=inst_uv)
print('LOOKUP', int((meshy_uv[..., 0] >= 0).sum()), 'texels; arm texels from installed', int((inst_uv[..., 0] >= 0).sum()))
