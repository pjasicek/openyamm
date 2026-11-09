"""Label the m504 body for the weight rules, texture classes and reduction: one closed stone shell (piece 0 = skin,
garment 0); the Smart Topology return has no other parts once drop_strays.py removed six surface flakes.
Writes the 'garment' point attribute and work/garments.json. Args: -- <in blend> <out blend>"""
import bpy, sys, os, json
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
me = bpy.data.objects['Body'].data
gv = np.zeros(len(me.vertices), np.int32)
a = me.attributes.get('garment') or me.attributes.new('garment', 'INT', 'POINT')
a.data.foreach_set('value', gv)
print('GARMENT counts', {0: len(gv)})
json.dump({'0': 0}, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'garments.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
