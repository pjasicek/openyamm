"""Geometry-only edits of work/graft.blend (same topology as work/uv.blend): copy uv.blend's UVs onto it and save it
as the new work/uv.blend, so the Meshy texture stays valid.
Usage: blender -b work/uv.blend -P carry_uv.py -- dump ; blender -b work/graft.blend -P carry_uv.py -- apply"""
import os, sys, bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); F = os.path.join(HERE, 'work', 'uv_carry.npz')
me = bpy.data.objects['Body'].data
if sys.argv[sys.argv.index('--') + 1] == 'dump':
    uv = np.zeros(len(me.loops) * 2); me.uv_layers.active.data.foreach_get('uv', uv)
    np.savez(F, uv=uv, polys=np.array([v for p in me.polygons for v in p.vertices]))
else:
    d = np.load(F)
    assert np.array_equal(d['polys'], np.array([v for p in me.polygons for v in p.vertices])), 'topology changed'
    me.uv_layers.active.data.foreach_set('uv', d['uv'])
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'uv.blend'))
    print('UV carried', len(d['uv']) // 2, 'loops')
