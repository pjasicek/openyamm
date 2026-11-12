"""asm-style npz (co, tri, comp) -> blend 'Body' with face attribute 'part' = comp; optional KEY env picks the coordinate array (co_up). Args: <npz> <out blend>"""
import bpy, sys, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
d = np.load(a[0]); co = d[os.environ.get('KEY', 'co')]; tri = d['tri']
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new('Body'); me.from_pydata(co.tolist(), [], tri.tolist()); me.update()
me.attributes.new('part', 'INT', 'FACE').data.foreach_set('value', d['comp'][tri[:, 0]].astype(int).tolist())
for p in me.polygons: p.use_smooth = True
o = bpy.data.objects.new('Body', me); bpy.context.scene.collection.objects.link(o)
bpy.ops.wm.save_as_mainfile(filepath=a[1])
