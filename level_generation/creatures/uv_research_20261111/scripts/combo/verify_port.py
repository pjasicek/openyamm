"""Verification of the claude_shared/uv_atlas.py port (2026-11-12): runs the shared unwrap() on a prepared set mesh of
the combined-layout study and writes the report, a neutral upload GLB, a skinned measurement GLB and a UV layout image.

run_creature_blender.sh .../verify_port.py <prepared blend> <out dir> <name> [simulate=no_partuv|no_sparrow]
    [any unwrap option=value]
The blend is only read (outputs go to <out dir>); the prepared mesh is the largest mesh object (one texture set).
"""
import json
import os
import sys
import time

import bpy
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
BLEND, OUT, NAME = argv[0], os.path.abspath(argv[1]), argv[2]
opts = dict(a.split('=', 1) for a in argv[3:])
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../..'))
sys.path.insert(0, os.path.join(REPO, 'level_generation/creatures/claude_shared'))
import uv_atlas  # noqa: E402


def value(v):
    for cast in (int, float):
        try:
            return cast(v)
        except ValueError:
            pass
    return {'True': True, 'False': False, 'None': None}.get(v, v)


simulate = opts.pop('simulate', '')
if simulate == 'no_partuv':
    uv_atlas.PARTUV_VENV = '/nonexistent/partuv_venv/bin/python'
elif simulate == 'no_sparrow':
    uv_atlas.SPARROW_BIN = '/nonexistent/sparrow_venv/bin/sparrow'
head = tuple(g for g in opts.pop('head', '').split(',') if g)
kwargs = {k: value(v) for k, v in opts.items()}
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(BLEND))
rig = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
if rig is not None:
    if rig.animation_data:
        rig.animation_data.action = None
    for b in rig.pose.bones:
        b.matrix_basis.identity()
mesh = max((o for o in bpy.data.objects if o.type == 'MESH'), key=lambda o: len(o.data.polygons))
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o != mesh:
        bpy.data.objects.remove(o)
bpy.context.view_layer.update()
t0 = time.time()
report = uv_atlas.unwrap(mesh, head_groups=head, **kwargs)
report['seconds'] = round(time.time() - t0)
report['simulate'] = simulate
report.pop('seam_log', None)
json.dump(report, open(os.path.join(OUT, f'{NAME}_report.json'), 'w'), indent=1)
print('VERIFY', NAME, json.dumps({k: report[k] for k in ('charts_used', 'packer_used', 'fallbacks', 'charts', 'use',
                                                         'seams', 'weld', 'seconds')}), flush=True)

me = mesh.data
dup = mesh.copy()
dup.data = me.copy()
dup.modifiers.clear()
dup.parent = None
dup.matrix_world = mesh.matrix_world
dup.data.materials.clear()
bpy.context.scene.collection.objects.link(dup)
for o in bpy.data.objects:
    o.select_set(o == dup)
bpy.context.view_layer.objects.active = dup
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f'{NAME}_upload.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_skins=False, export_animations=False, export_materials='NONE',
                          export_attributes=False)
bpy.data.objects.remove(dup)
for o in bpy.data.objects:
    o.select_set(o == mesh or o == rig)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f'{NAME}_measure.glb'), use_selection=True, export_format='GLB',
                          export_yup=True, export_skins=True, export_animations=False, export_materials='NONE',
                          export_attributes=False)
# UV layout image: islands filled per chart colour
flat = np.zeros(len(me.loops) * 2, np.float32)
me.uv_layers['UVMap'].data.foreach_get('uv', flat)
flat = flat.reshape(-1, 2)
np.savez(os.path.join(OUT, f'{NAME}_uv.npz'), uv=np.array([flat[list(p.loop_indices)] for p in me.polygons]),
         tri=np.array([p.vertices[:] for p in me.polygons]), pos=np.array([v.co for v in me.vertices]))
print('VERIFY done', NAME, flush=True)
