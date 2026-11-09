"""Third pass (2026-11-01): the Meshy mallet (Smart Topology from references_mallet/00_three_quarter.png) fitted to MM9's mallet frame and
our fists, with uv_atlas.py UVs. Meshy's mallet stands on Blender Z (head up, its long axis on X, its hexagon in Y-Z). Our frame is MM9's
Xhammer at our 0.3 scale (make_mallet.py): head along x (+-0.2525), shaft along +y from the head (head top y -0.353, bottom -0.029), hexagon
depth on z. Fit: uniform scale by the head's length (MM9's 0.505 m); below the head the shaft is stretched along y so its tip lands on
TIP (MM9 slides the shaft through the right fist up to 1.18 m; the master's shaft is 3.5 head heights, ours needs 4.1) and scaled
radially so its grip section has radius R (the fists' solve, fist_giant.py). Writes work/mallet.npz (V, F, UVc, M from the true source,
UV = per-vertex copy) and texturing/mallet_upload_v1.glb (the fitted mesh with its UVs, for the retexture). Args: <meshy glb> <true glb>
<out npz> <out upload glb>"""
import bpy, bmesh, sys, os, json
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
MESHY, TRUE, OUT, UPLOAD = a[:4]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'claude_shared')); import uv_atlas
R, TIP, HEADLEN, HEAD_TOP, HEAD_BOT = float(os.environ.get("R_SHAFT", 0.030)), 1.33, 0.505, -0.353, -0.029      # tip later pulled to 1.24 in mallet.npz (third pass: the end stays out of the chest)
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=MESHY)
ob = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
bpy.context.view_layer.objects.active = ob
for o in bpy.context.scene.objects: o.select_set(o is ob)
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM'); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = ob.data; V = np.array([v.co for v in me.vertices])
# head: the slices whose spread off the Z axis is far beyond the shaft's
cx, cy = np.median(V[:, 0]), np.median(V[:, 1]); rr = np.hypot(V[:, 0] - cx, V[:, 1] - cy)
zs = np.linspace(V[:, 2].min(), V[:, 2].max(), 200); spread = np.array([rr[np.abs(V[:, 2] - z) < (zs[1] - zs[0])].max() if (np.abs(V[:, 2] - z) < (zs[1] - zs[0])).any() else 0 for z in zs])
shaft_r0 = np.median(spread[(zs > np.percentile(V[:, 2], 30)) & (zs < np.percentile(V[:, 2], 60))])
headz = zs[spread > 3 * shaft_r0]; z_hb, z_ht = headz.min(), headz.max()
hv = V[:, 2] >= z_hb
hx = V[hv, 0]; s = HEADLEN / (hx.max() - hx.min())
print('FIT head z', round(z_hb, 3), round(z_ht, 3), 'head length', round(hx.max() - hx.min(), 3), 'scale', round(s, 3), 'meshy shaft r', round(shaft_r0, 4))
# local frame: x = X, y = -Z, z = Y (right-handed), head bottom face on y = HEAD_BOT, centred on the shaft's axis
L = np.c_[(V[:, 0] - cx), -(V[:, 2] - z_hb), (V[:, 1] - cy)] * s
L[:, 1] += HEAD_BOT
hx0 = (L[hv, 0].max() + L[hv, 0].min()) / 2; L[:, 0] -= hx0 * 0          # the shaft's axis stays at x = 0 (the head may sit a little off)
below = L[:, 1] > HEAD_BOT
tip0 = L[:, 1].max(); k = (TIP - HEAD_BOT) / (tip0 - HEAD_BOT)
L[below, 1] = HEAD_BOT + (L[below, 1] - HEAD_BOT) * k
# radial: the grip section (y 0.4 .. 1.2) to radius R; a smooth blend over the first 6 cm under the head (the collar keeps the head's scale)
rad = np.hypot(L[:, 0], L[:, 2]); grip = below & (L[:, 1] > 0.4) & (L[:, 1] < 1.2)
rg = np.median(rad[grip]); kr = R / rg
blend = np.clip((L[:, 1] - HEAD_BOT) / 0.06, 0, 1) * below
fac = 1 + (kr - 1) * blend
L[:, 0] *= fac; L[:, 2] *= fac
print('FIT shaft stretch', round(k, 3), 'grip radius before', round(rg, 4), 'radial', round(kr, 3), 'head top y', round(L[hv, 1].min(), 3), 'extent', np.round(L.min(0), 3), np.round(L.max(0), 3))
for v, p in zip(me.vertices, L): v.co = Vector(p.tolist())
me.update()
# triangulate, UVs
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
while me.uv_layers: me.uv_layers.remove(me.uv_layers[0])
me.uv_layers.new(name='UVMap')
rep = uv_atlas.unwrap(ob, size=int(os.environ.get('UVSIZE', 1024)), merge_below=12)
print('FIT uv', {k_: rep[k_] for k_ in ('charts', 'use') if k_ in rep})
uv = me.uv_layers['UVMap'].data
F = np.array([list(p.vertices) for p in me.polygons]); UVc = np.array([[uv[l].uv[:] for l in p.loop_indices] for p in me.polygons])
Vf = np.array([v.co[:] for v in me.vertices])
sys.path.insert(0, os.path.join(HERE, '..', 'claude_shared', 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(TRUE)); names = [n.get('name') for n in m.glb.json['nodes']]
X = m.world({})[names.index('Xhammer')]
B = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1.0]])
UVv = np.zeros((len(Vf), 2))
for f, c in zip(F, UVc): UVv[f] = c
np.savez(OUT, V=Vf, F=F, UV=UVv, UVc=UVc, M=B @ X)
json.dump(rep, open(os.path.join(HERE, 'work', 'uv_mallet_meshy.json'), 'w'), indent=1, default=str)
# upload copy for the retexture: back to Meshy's upright frame (Z up, head on top) so the reference views line up
for v, p in zip(me.vertices, Vf): v.co = Vector((p[0], p[2], -p[1]))
me.update()
bpy.ops.export_scene.gltf(filepath=UPLOAD, export_format='GLB', use_selection=True, export_normals=True, export_materials='NONE')
print('FIT done verts', len(Vf), 'tris', len(F))
