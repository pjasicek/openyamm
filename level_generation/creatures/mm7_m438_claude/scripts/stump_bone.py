"""Right-arm stump bones (user review 2026-10-20: the four Smart Topology rods P06-P09 below the bloody stump read as
a small hand growing from the wound). On the textured master: the rods are removed and two broken bone shafts
(bone_stub.two_bones: radius and ulna, 3.4 / 2.6 cm out of the stump, 1.1 / 0.95 cm radius, side by side across the arm as m438sa0/sa1
draw them) are added at the stump end (the farthest stump skin along elbow -> old rod centroid), skinned 100 % to
B_R_Forearm, piece 6 / garment 4 (bone), UVMap into the ivory bone patch that compose_m438.py paints into free atlas
texels (work/bone_patch.json from bone_patch.py). Args: -- <in blend> <out blend>"""
import bpy, bmesh, sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bone_stub
src, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
# ---- the ivory patch in free atlas texels (bone_patch.py, from the UVMap raster of the same master)
patch = json.load(open(os.path.join(HERE, 'work', 'bone_patch.json'))); N = patch['atlas']
cy, cx = patch['row'] + patch['size'] // 2, patch['col'] + patch['size'] // 2
u0, v0 = (cx - 14) / N, 1 - (cy + 14) / N; du = 28 / N                     # UVs inside the patch's inner 28 texels
# ---- stump geometry
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
co = np.array([tuple(v.co) for v in me.vertices])
J = {k: np.array(v) for k, v in json.load(open(os.path.join(HERE, 'work', 'joints_final.json')))['joints'].items()}
E = J['R_Forearm']; rods = np.isin(pv, [6, 7, 8, 9])
ax = co[rods].mean(0) - E; ax /= np.linalg.norm(ax)
skin = co[(pv == 0) & (co[:, 0] < -0.2)]
rel = skin - E; t = rel @ ax; rad = np.linalg.norm(rel - np.outer(t, ax), axis=1)
near = (t > 0) & (rad < 0.06)
t_end = float(np.percentile(t[near], 99)); end = E + ax * t_end
ring = skin[near & (t > t_end - 0.02)]
end_c = E + ax * (t_end - 0.004)
across = np.cross(ax, (0.0, 1.0, 0.0))                                   # frontal plane: the bones show side by side from the front
print('STUMP old rods removed', int(rods.sum()), 'verts; stump end at', np.round(end, 3).tolist(), 'axis', np.round(ax, 3).tolist())
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
pl = bm.verts.layers.int['piece']; gl = bm.verts.layers.int['garment']
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[pl] in (6, 7, 8, 9)], context='VERTS')
dl = bm.verts.layers.deform.verify()
fa = body.vertex_groups['B_R_Forearm'].index
uvl = bm.loops.layers.uv['UVMap']; huv = bm.loops.layers.uv.get('HeadUV')
hl = bm.faces.layers.int.get('head')
oc = bm.verts.layers.float_vector.get('orig_co')
ntri = 0
for k, (V, F) in enumerate(bone_stub.two_bones(end_c, ax, across, seed=438)):
    vs = []
    for p in V:
        v = bm.verts.new(p); v[pl] = 6; v[gl] = 4; v[dl][fa] = 1.0
        if oc is not None:
            v[oc] = p
        vs.append(v)
    lo = V @ ax; lo = (lo - lo.min()) / max(float(np.ptp(lo)), 1e-6)
    for f in F:
        face = bm.faces.new([vs[i] for i in f]); face.smooth = True; face.material_index = 0; ntri += 1
        if hl is not None:
            face[hl] = 0
        for lp in face.loops:
            j = vs.index(lp.vert)
            ang = math.atan2(*(np.array(lp.vert.co) - V[0])[:2]) / (2 * math.pi) + 0.5
            lp[uvl].uv = (u0 + du * (0.5 * ang + 0.5 * k), v0 + du * lo[j])
            if huv is not None:
                lp[huv].uv = (0.0, 0.0)
bm.to_mesh(me); bm.free()
print('STUMP bone shafts added', ntri, 'tris; patch', patch)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
