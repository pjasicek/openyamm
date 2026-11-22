"""Clean the Smart Topology return into the octopod's modelling mesh (work/clean_v1.blend, object Octopod).

Raw (meshy/smart_topology_v1, Blender axes after import): 14,821 triangles, 133 pieces: the body (head dome and eight
tentacles in a flat star, one tentacle under the face at azimuth 0 = -Y), two eyeballs of different sizes (the
creature's right one 1.5x the left), 130 sucker blobs, and a five-face sliver strip across the front-left tentacle.
Rules (no indices):
- the face looks along -Y already (mirror symmetry of the head about x = 0 within 0.5 degrees);
- faces with an edge longer than 0.06 (raw units; median edge 0.012) are the sliver: removed, the holes they leave
  filled;
- both eyeballs are replaced by one mirrored pair of UV spheres (radius EYE_R), set into the head surface where the
  two eyes were, so the face is symmetric;
- the tentacles are lengthened along their own axes beyond the head (factor ARM_K, smooth ramp from R0 to R1 from the
  axis; across the arm nothing changes): Meshy's arms are 3.1 head widths tip to tip, the sprite's 4.8;
  each sucker blob moves rigidly with the body point under it;
- suckers decimated to about a third (edit-mode collapse);
- scaled so the head is HEAD_W m wide, the waterline (WATER_RAW: 0.33 head widths under the eye centres, as in the
  native frames) at z 0, centred on the head axis.
Face attribute `part`: 0 body, 1 sucker, 2 eye. Renders review/clean_<view>.png."""
import bpy, bmesh, os, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARM_K, R0, R1 = 1.35, 0.17, 0.27
EYE_R, EYE_X, EYE_Z = 0.040, 0.050, 0.012
HEAD_RAW_W, HEAD_W = 0.32, 0.60
WATER_RAW = -0.10

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'meshy/smart_topology_v1/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh:
        bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
mesh.name = mesh.data.name = 'Octopod'
mesh.data.materials.clear()

bm = bmesh.new(); bm.from_mesh(mesh.data)


def pieces(bm):
    bm.verts.ensure_lookup_table()
    lab = -np.ones(len(bm.verts), int); k = 0
    for v in bm.verts:
        if lab[v.index] >= 0: continue
        st = [v]; lab[v.index] = k
        while st:
            x = st.pop()
            for e in x.link_edges:
                w = e.other_vert(x)
                if lab[w.index] < 0: lab[w.index] = k; st.append(w)
        k += 1
    return lab


lab = pieces(bm)
u, cnt = np.unique(lab, return_counts=True)
main = u[np.argmax(cnt)]
big_extra = [k for k in u[np.argsort(-cnt)][1:3]]          # the two eyeballs
co = np.array([v.co[:] for v in bm.verts])
eyes_old = [co[lab == k].mean(0) for k in big_extra]
print('EYES_OLD', [e.round(3).tolist() for e in eyes_old])
# remove the old eyes
bmesh.ops.delete(bm, geom=[v for v in bm.verts if lab[v.index] in big_extra], context='VERTS')
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
# sliver: faces with a long edge
sl = [f for f in bm.faces if max(e.calc_length() for e in f.edges) > 0.06]
print('SLIVER faces', len(sl))
bmesh.ops.delete(bm, geom=sl, context='FACES')
loose = [v for v in bm.verts if not v.link_faces]
bmesh.ops.delete(bm, geom=loose, context='VERTS')
# fill the small holes that leaves (boundary loops of the body)
bnd = [e for e in bm.edges if e.is_boundary]
res = bmesh.ops.holes_fill(bm, edges=bnd, sides=12)
print('FILLED', len(res['faces']))
bmesh.ops.triangulate(bm, faces=bm.faces[:])

lab = pieces(bm)
u, cnt = np.unique(lab, return_counts=True); main = u[np.argmax(cnt)]
co = np.array([v.co[:] for v in bm.verts])
is_main = lab == main
# arm azimuths (0 = -Y, + toward +X): eight peaks of the far vertices
M = co[is_main]; rM = np.hypot(M[:, 0], M[:, 1]); azM = np.arctan2(M[:, 0], -M[:, 1])
far = rM > 0.42
arms = []
for k in range(8):
    a0 = math.radians(45 * k)
    d = np.angle(np.exp(1j * (azM[far] - a0)))
    sel = np.abs(d) < math.radians(22.5)
    w = rM[far][sel]
    arms.append(a0 + float(np.angle(np.sum(w * np.exp(1j * d[sel])))))
print('ARMS deg', [round(math.degrees(a), 1) for a in arms])


def ramp(a):
    a = np.asarray(a, float)
    return np.where(a < R0, 0.0, np.where(a < R1, (a - R0) ** 2 / (2 * (R1 - R0)), a - (R0 + R1) / 2))


def stretch(P):
    """Move points along their tentacle's axis (nearest arm azimuth)."""
    P = P.copy()
    az = np.arctan2(P[:, 0], -P[:, 1])
    A = np.array(arms)
    k = np.argmin(np.abs(np.angle(np.exp(1j * (az[:, None] - A[None, :])))), axis=1)
    dirs = np.stack([np.sin(A[k]), -np.cos(A[k])], -1)
    along = (P[:, :2] * dirs).sum(-1)
    P[:, :2] += dirs * ((ARM_K - 1) * ramp(along))[:, None]
    return P


new_main = stretch(co[is_main])
disp = np.zeros_like(co); disp[is_main] = new_main - co[is_main]
# suckers move rigidly with the nearest body vertex
idx_main = np.where(is_main)[0]
for k in u:
    if k == main: continue
    sel = lab == k
    nn = int(np.argmin(((co[is_main] - co[sel].mean(0)) ** 2).sum(-1)))
    disp[sel] = disp[idx_main[nn]]
for v in bm.verts:
    v.co = Vector(co[v.index] + disp[v.index])

# part attribute
part = bm.faces.layers.int.new('part')
for f in bm.faces:
    f[part] = 0 if lab[f.verts[0].index] == main else 1

# decimate the suckers: write, then edit-mode collapse on their faces
bm.to_mesh(mesh.data); bm.free()
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
pa = mesh.data.attributes['part'].data
for p in mesh.data.polygons:
    p.select = pa[p.index].value == 1
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.decimate(ratio=0.36)
bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.quads_convert_to_tris()
bpy.ops.object.mode_set(mode='OBJECT')

# eyes: a mirrored pair of spheres set into the head surface
bm = bmesh.new(); bm.from_mesh(mesh.data)
part = bm.faces.layers.int.get('part')
co = np.array([v.co[:] for v in bm.verts])
body = np.array([any(f[part] == 0 for f in v.link_faces) for v in bm.verts])
B = co[body]
for sx in (-1, 1):
    x = sx * EYE_X
    near = B[(np.abs(B[:, 0] - x) < 0.012) & (np.abs(B[:, 2] - EYE_Z) < 0.012) & (B[:, 1] < 0) & (np.hypot(B[:, 0], B[:, 1]) < 0.2)]
    ys = near[:, 1].min()
    c = Vector((x, ys + 0.45 * EYE_R, EYE_Z))
    m = Matrix.Translation(c) @ Matrix.Rotation(math.radians(90), 4, 'X') @ Matrix.Rotation(math.radians(sx * 18), 4, 'Y')
    ret = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=EYE_R, matrix=m)
    fs = {f for v in ret['verts'] for f in v.link_faces}
    for f in fs:
        f[part] = 2
    print('EYE', sx, [round(t, 3) for t in c], 'surface y', round(float(ys), 3))
bmesh.ops.triangulate(bm, faces=bm.faces[:])
bm.to_mesh(mesh.data); bm.free()

# scale, waterline, centre
k = HEAD_W / HEAD_RAW_W
mesh.data.transform(Matrix.Scale(k, 4) @ Matrix.Translation((0, 0, -WATER_RAW)))
for p in mesh.data.polygons:
    p.use_smooth = True
co = np.array([v.co[:] for v in mesh.data.vertices])
counts = {}
for p in mesh.data.polygons:
    v = mesh.data.attributes['part'].data[p.index].value; counts[v] = counts.get(v, 0) + 1
print('SIZE', (co.max(0) - co.min(0)).round(3).tolist(), 'min', co.min(0).round(3).tolist(), 'max', co.max(0).round(3).tolist(),
      'tris', len(mesh.data.polygons), 'by part', counts)
json.dump({'arms_deg': [math.degrees(a) for a in arms], 'scale': k, 'water_raw': WATER_RAW, 'arm_k': ARM_K,
           'eye_r': EYE_R * k, 'eye_x': EYE_X * k}, open(os.path.join(HERE, 'work', 'clean_info.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
for name, (loc, tgt, s) in {'front': ((0, -6, 0.15), (0, 0, 0.15), 2.6), 'face': ((0, -6, 0.15), (0, 0, 0.15), 0.9),
                            'side': ((-6, 0, 0.15), (0, 0, 0.15), 2.6), 'top': ((0, 0, 6), (0, 0, 0), 2.6),
                            'quarter': ((-3.2, -4.0, 2.8), (0, 0, 0), 2.6)}.items():
    C.render(loc, tgt, s, os.path.join(HERE, 'review', f'clean_{name}.png'), res=(700, 500), floor=False)
print('CLEANED')
