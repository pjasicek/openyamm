"""npz (co, tri[, part per tri]) -> blend with object 'Body' (face attribute 'part'), smooth shaded. Args: <npz> <out blend> [extra npz ...]"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
for k, f in enumerate([a[0]] + a[2:]):
    d = np.load(f)
    me = bpy.data.meshes.new('Body'); me.from_pydata(d['co'].tolist(), [], d['tri'].tolist()); me.update()
    if 'part' in d and len(d['part']) == len(d['tri']):
        me.attributes.new('part', 'INT', 'FACE').data.foreach_set('value', d['part'].astype(int).tolist())
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new('Body' if k == 0 else f'Extra{k}', me); bpy.context.scene.collection.objects.link(o)
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('NPZ2BLEND', a[1])
