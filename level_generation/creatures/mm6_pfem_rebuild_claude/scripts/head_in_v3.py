"""Aligned Meshy head (work/head_align.json) as 'Body' in a blend, for side-by-side clay looks. Args: <head npz> <align json> <out blend>"""
import bpy, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
d = np.load(a[0]); M = np.array(json.load(open(a[1]))['M'])
co = d['co'] @ M[:3, :3].T + M[:3, 3]
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('Body'); me.from_pydata(co.tolist(), [], d['tri'].tolist()); me.update()
for p in me.polygons: p.use_smooth = True
o = bpy.data.objects.new('Body', me); bpy.context.scene.collection.objects.link(o)
bpy.ops.object.select_all(action='SELECT'); bpy.context.view_layer.objects.active = o
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.remove_doubles(threshold=1e-5); bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.wm.save_as_mainfile(filepath=a[2])
