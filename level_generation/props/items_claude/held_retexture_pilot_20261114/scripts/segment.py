"""Step 1b of the held-sword retexture pilot (README.md): cut the long blade islands of prep.py's layout into shorter
pieces and repack with sparrow, so a long thin prop can use the square atlas (one blade face is about 20 times longer
than wide: as one island it caps atlas use at 13-40 %).

Usage: blender --background --python segment.py -- <icon> <max_aspect> <tag> [sparrow_runs] [sparrow_seconds] [min_faces]

Reads work/<icon>/uv.blend; writes work/<icon>/uv_<tag>.blend, uv_measure_<tag>.glb, upload_<tag>.glb and
uv_<tag>.json. Each island whose UV extent along its principal axis exceeds max_aspect times its width is cut, by face
centroid along that axis, into equal pieces of at most that aspect. The 3D mesh is not changed.
"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(PROJECT, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'level_generation', 'creatures', 'claude_shared'))
import uv_atlas

argv = sys.argv[sys.argv.index('--') + 1:]
ICON, MAX_ASPECT, TAG = argv[0], float(argv[1]), argv[2]
RUNS = int(argv[3]) if len(argv) > 3 else 5
SECONDS = int(argv[4]) if len(argv) > 4 else 60
MIN_FACES = int(argv[5]) if len(argv) > 5 else 0   # islands with fewer faces are never cut (thin tubes)
OUT = os.path.join(PROJECT, 'work', ICON)
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, 'uv.blend'))
obj = next(o for o in bpy.data.objects if o.type == 'MESH')
me = obj.data
tri = np.array([p.vertices[:] for p in me.polygons], np.int32)
loops = np.array([p.loop_indices[:] for p in me.polygons], np.int64)
uvl = np.array([d.uv[:] for d in me.uv_layers['UVMap'].data], np.float64)
uv = uvl[loops]                                   # (faces, 3, 2)
island = uv_atlas._islands(uv, tri)
new_island = island.copy()
next_id = island.max() + 1
cuts = []
for i in np.unique(island):
    faces = np.nonzero(island == i)[0]
    pts = uv[faces].reshape(-1, 2)
    ctr = pts.mean(0)
    w, v = np.linalg.eigh(np.cov((pts - ctr).T))
    axis, side = v[:, 1], v[:, 0]
    along = (pts - ctr) @ axis
    across = (pts - ctr) @ side
    length, width = np.ptp(along), max(np.ptp(across), 1e-9)
    k = int(math.ceil(length / width / MAX_ASPECT))
    if k <= 1 or len(faces) < MIN_FACES:
        continue
    cen = (uv[faces].mean(1) - ctr) @ axis
    edges = np.linspace(along.min(), along.max(), k + 1)
    piece = np.clip(np.searchsorted(edges, cen, side='right') - 1, 0, k - 1)
    for p in range(1, k):
        new_island[faces[piece == p]] = next_id
        next_id += 1
    cuts.append({'island': int(i), 'faces': int(len(faces)), 'aspect': round(float(length / width), 2), 'pieces': k})
print('SEGMENT cuts', json.dumps(cuts), flush=True)
new_island = np.unique(new_island, return_inverse=True)[1].ravel()
packed, k = uv_atlas._sparrow(uv, new_island, 2048, 1.0, 4, SECONDS, RUNS, 0.66)
packed = np.asarray(packed, np.float64).reshape(-1, 3, 2)
layer = me.uv_layers['UVMap']
for f in range(len(tri)):
    for c in range(3):
        layer.data[int(loops[f, c])].uv = packed[f, c]
me.update()
p3 = np.array([v.co for v in me.vertices])[tri]
use = float(np.abs(np.cross(packed[:, 1] - packed[:, 0], packed[:, 2] - packed[:, 0])).sum() / 2)
json.dump({'max_aspect': MAX_ASPECT, 'cuts': cuts, 'islands': int(new_island.max() + 1), 'sparrow_k': k,
           'uv_sum': round(use, 4)}, open(os.path.join(OUT, f'uv_{TAG}.json'), 'w'), indent=1)
print('SEGMENT islands', int(new_island.max() + 1), 'uv sum', round(use, 4), flush=True)
for o in bpy.data.objects:
    o.select_set(o == obj)
bpy.context.view_layer.objects.active = obj
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f'uv_{TAG}.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f'uv_measure_{TAG}.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False)
R = json.load(open(os.path.join(OUT, 'orient.json')))['rotation_blender']
mats = list(me.materials)
me.materials.clear()
me.transform(Matrix(R).to_4x4())
me.update()
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f'upload_{TAG}.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_animations=False, export_materials='NONE')
print('SEGMENT done', ICON, TAG)
