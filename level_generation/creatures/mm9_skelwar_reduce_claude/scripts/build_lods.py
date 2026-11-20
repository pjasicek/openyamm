"""tools/build_actor_lods.py as the Skeleton Warrior's build_runtime.sh ran it (4 influences), with protected points: every
vertex within 4 mm of the rest floor (soles: the floor contact), the top 1 cm (the helmet spike: picking bounds and the
native-height checks use the coarsest LOD) and the two highest vertices of every small piece reaching above HORN_Z (the
three helmet horns: at the default ratios the reduced LOD2 lost a horn's tip). Ratios LOD_RATIOS (default 0.5/0.18/0.075:
with the tool's default 0.06 the reduced LOD3 lost the thighs and forearms, which the installed 578-triangle LOD3 kept).
Usage: blender -b -P build_lods.py -- <lod0.glb> <dst.glb> <mesh node>"""
import os, sys
from pathlib import Path
import bmesh, bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
import build_actor_lods as L  # noqa: E402
src, dst, node = sys.argv[sys.argv.index('--') + 1:][:3]
RATIOS = tuple(float(x) for x in os.environ.get('LOD_RATIOS', '0.5,0.18,0.075').split(','))
HORN_Z = float(os.environ.get('HORN_Z', '1.9'))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(src).resolve()))
body = bpy.data.objects[node]
rig = next(m.object for m in body.modifiers if m.type == 'ARMATURE'); rig.animation_data_clear()
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
W = [body.matrix_world @ v.co for v in body.data.vertices]
top = max(w.z for w in W); floor = min(w.z for w in W)
crown = [w for w in W if w.z > top - 0.01]
soles = [w for w in W if w.z < floor + 0.004]
# small pieces (position-welded components) reaching above HORN_Z: their two highest vertices
key = {}
for i, w in enumerate(W):
    key.setdefault(tuple(round(c, 6) for c in w), []).append(i)
par = list(range(len(W)))
def find(x):
    while par[x] != x:
        par[x] = par[par[x]]; x = par[x]
    return x
for ids in key.values():
    for j in ids[1:]:
        par[find(j)] = find(ids[0])
for e in body.data.edges:
    a, b = find(e.vertices[0]), find(e.vertices[1]); par[a] = b
comps = {}
for i in range(len(W)):
    comps.setdefault(find(i), []).append(i)
tips = []
for ids in comps.values():
    if len(ids) <= 120 and max(W[i].z for i in ids) > HORN_Z:
        tips += [W[i] for i in sorted(ids, key=lambda i: -W[i].z)[:2]]
pts = {tuple(round(c, 7) for c in w): w.copy() for w in crown + soles + tips}
print('PROTECT crown', len(crown), 'soles', len(soles), 'horn tips', len(tips), 'unique', len(pts), 'top', round(top, 4), 'floor', round(floor, 4))
bpy.ops.wm.read_factory_settings(use_empty=True)
L.generate(Path(src).resolve(), Path(dst).resolve(), node, ratios=RATIOS, max_influences=4, protected_points=list(pts.values()))
