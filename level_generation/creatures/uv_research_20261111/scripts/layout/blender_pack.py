"""Blender's Pack Islands on fixed charts (packing study, candidate 4).

blender.sh blender_pack.py <log> <layout npz (pos, uv glTF)> <out dir> <name> shape=CONCAVE,CONVEX,AABB \
    rotate=ANY,CARDINAL,AXIS_ALIGNED margin_px=4 [margin_method=FRACTION]
Writes <out dir>/<name>_<shape>_<rotate>_m<margin>.npz (pos, uv glTF, seconds) per combination.
"""
import os
import sys
import time

import bmesh
import bpy
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT, NAME = argv[:3]
opts = dict(a.split('=', 1) for a in argv[3:])
shapes = opts.get('shape', 'CONCAVE').split(',')
rotates = opts.get('rotate', 'ANY').split(',')
margins = [float(m) for m in opts.get('margin_px', '4').split(',')]
method = opts.get('margin_method', 'FRACTION')
d = np.load(SRC)
pos, uv = d['pos'], d['uv']
keys = np.round(pos.reshape(-1, 3), 5)
uniq, inv = np.unique(keys, axis=0, return_inverse=True)
tri = inv.reshape(-1, 3)
os.makedirs(OUT, exist_ok=True)
print('ENUM shape', [i.identifier for i in bpy.ops.uv.pack_islands.get_rna_type().properties['shape_method'].enum_items])
print('ENUM rotate', [i.identifier for i in bpy.ops.uv.pack_islands.get_rna_type().properties['rotate_method'].enum_items])
print('ENUM margin', [i.identifier for i in bpy.ops.uv.pack_islands.get_rna_type().properties['margin_method'].enum_items])

for shape in shapes:
    for rot in rotates:
        for margin in margins:
            bpy.ops.wm.read_factory_settings(use_empty=True)
            me = bpy.data.meshes.new('m')
            me.from_pydata([tuple(v) for v in uniq], [], [tuple(int(x) for x in t) for t in tri])
            me.update()
            layer = me.uv_layers.new(name='UVMap')
            flat = np.zeros((len(me.loops), 2), np.float32)
            for p in me.polygons:
                f = uv[p.index].copy()
                f[:, 1] = 1.0 - f[:, 1]
                flat[list(p.loop_indices)] = f
            layer.data.foreach_set('uv', flat.ravel())
            obj = bpy.data.objects.new('o', me)
            bpy.context.scene.collection.objects.link(obj)
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.context.scene.tool_settings.use_uv_select_sync = True
            bpy.ops.mesh.select_all(action='SELECT')
            t = time.time()
            kwargs = dict(udim_source='CLOSEST_UDIM', rotate=rot != 'NONE', scale=True, merge_overlap=False,
                          margin_method=method, margin=margin / 2048, shape_method=shape)
            if rot != 'NONE':
                kwargs['rotate_method'] = rot
            bpy.ops.uv.pack_islands(**kwargs)
            seconds = time.time() - t
            bpy.ops.object.mode_set(mode='OBJECT')
            out = np.zeros(len(me.loops) * 2, np.float32)
            me.uv_layers['UVMap'].data.foreach_get('uv', out)
            out = out.reshape(-1, 2)
            res = np.array([out[list(p.loop_indices)] for p in me.polygons], np.float64)
            res[..., 1] = 1.0 - res[..., 1]
            name = f'{NAME}_{shape}_{rot}_m{margin:g}'
            np.savez(os.path.join(OUT, name + '.npz'), pos=pos, uv=res, seconds=seconds, margin=margin)
            print('PACKED', name, f'{seconds:.1f}s', flush=True)
