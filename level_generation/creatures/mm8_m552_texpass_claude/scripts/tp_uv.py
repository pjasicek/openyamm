"""Texture-pass UVs (claude_shared/TEXTURE_QUALITY_PASS.md) on the welded LOD0 of work/lod0_before.npz, run in
Blender (tools/run_creature_blender.sh ... --python tp_uv.py -- out=<name> [uv_atlas.unwrap options]).

One atlas for every primitive of texpass.json atlas_prims (same triangles, same order; welded per primitive so no
chart spans two primitives), claude_shared/uv_atlas.py: xatlas charts, small charts merged and re-flattened, one
density with head islands x head_factor and the group_factors groups denser, packing into one square, 2 px margin.
Writes work/<out>.npz (uv per triangle corner, glTF v down; tri; xyz; prim), work/<out>_report.json and the static
uploads texturing/<out>_body_upload.glb (every atlas triangle) and texturing/<out>_head_upload.glb (head faces).

Never re-run an out= name once its upload went to Meshy: xatlas packs differently per run.
"""
import json
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tp_common as C  # noqa: E402
import uv_atlas  # noqa: E402

cfg = C.config()
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def value(v):
    for kind in (int, float):
        try:
            return kind(v)
        except ValueError:
            pass
    return v


options = dict(cfg.get('uv_options', {}))
options.update({k: value(v) for k, v in (a.split('=', 1) for a in argv)})
out_name = options.pop('out', 'uv_texpass')
out_npz = C.PROJECT / 'work' / f'{out_name}.npz'
if out_npz.exists():
    raise SystemExit(f'{out_npz} exists: a paint may belong to it; choose another out= name')

d = np.load(C.PROJECT / 'work' / 'lod0_before.npz')
pos, tri, weld, head_face = d['pos'], d['tri'], d['weld'], d['head_face']
nweld = int(weld.max()) + 1
wpos = np.zeros((nweld, 3))
wpos[weld] = pos
wtri = weld[tri]
blender = np.stack([wpos[:, 0], -wpos[:, 2], wpos[:, 1]], 1)     # glTF Y-up -> Blender Z-up

bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('Body')
me.from_pydata(blender.tolist(), [], wtri.tolist())
me.update()
assert len(me.polygons) == len(tri), (len(me.polygons), len(tri))
for p in me.polygons:
    assert tuple(p.vertices) == tuple(wtri[p.index])
obj = bpy.data.objects.new('Body', me)
bpy.context.scene.collection.objects.link(obj)

count = np.bincount(wtri.ravel(), minlength=nweld).astype(float)
hcount = np.bincount(wtri[head_face].ravel(), minlength=nweld).astype(float)
groups = {'HeadSet': hcount / np.maximum(count, 1)}
factors = {}
for name, (_pattern, factor) in cfg.get('group_factors', {}).items():
    w = np.zeros(nweld)
    w[weld] = d['g_' + name]
    groups[name] = w
    factors[name] = factor
for name, w in groups.items():
    vg = obj.vertex_groups.new(name=name)
    for v in np.nonzero(w > 0)[0]:
        vg.add([int(v)], float(min(w[v], 1.0)), 'REPLACE')

report = uv_atlas.unwrap(obj, head_groups=('HeadSet',), head_factor=cfg.get('head_factor', 1.8),
                         group_factors=factors, size=cfg.get('size', 2048), **options)
flat = np.zeros(len(me.loops) * 2, np.float32)
me.uv_layers['UVMap'].data.foreach_get('uv', flat)
flat = flat.reshape(-1, 2)
uv = np.array([flat[list(p.loop_indices)] for p in me.polygons], np.float64)
gl = uv.copy()
gl[..., 1] = 1 - gl[..., 1]
report.update({'head_factor': cfg.get('head_factor', 1.8), 'group_factors': factors, 'faces': len(tri),
               'options': {k: str(v) for k, v in options.items()}})
np.savez(out_npz, uv=gl, tri=tri, xyz=pos[tri], prim=d['prim'])
json.dump(report, open(str(out_npz).replace('.npz', '_report.json'), 'w'), indent=1)
print('UV_TEXPASS', json.dumps(report))

os.makedirs(C.PROJECT / 'texturing', exist_ok=True)
for name, faces in ((out_name + '_body_upload', np.ones(len(tri), bool)), (out_name + '_head_upload', head_face)):
    if not faces.any():
        continue
    sub = bpy.data.meshes.new(name)
    keep = np.nonzero(faces)[0]
    verts = np.unique(wtri[keep])
    index = np.full(nweld, -1)
    index[verts] = np.arange(len(verts))
    sub.from_pydata(blender[verts].tolist(), [], index[wtri[keep]].tolist())
    sub.update()
    for p in sub.polygons:
        p.use_smooth = True
    layer = sub.uv_layers.new(name='UVMap')
    loops = np.zeros((len(sub.loops), 2), np.float32)
    for p in sub.polygons:
        loops[list(p.loop_indices)] = uv[keep[p.index]]
    layer.data.foreach_set('uv', loops.ravel())
    ob = bpy.data.objects.new(name, sub)
    bpy.context.scene.collection.objects.link(ob)
    for o in bpy.data.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(filepath=str(C.PROJECT / 'texturing' / (name + '.glb')), use_selection=True,
                              export_format='GLB', export_yup=True, export_skins=False, export_animations=False,
                              export_materials='NONE', export_attributes=False)
    print('UPLOAD', name, len(sub.polygons))
