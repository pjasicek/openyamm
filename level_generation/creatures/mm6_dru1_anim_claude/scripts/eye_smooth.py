"""Eye caps shade smoothly (review 1 follow-up: the flat-shaded cap fans showed faceted highlights over the eyes).
In place on <blend>. Args: -- <blend>"""
import bpy, sys, os
import numpy as np
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
me = bpy.data.objects['Body'].data
ec = np.zeros(len(me.polygons), np.int32); me.attributes['eye_cap'].data.foreach_get('value', ec)
for p in me.polygons:
    if ec[p.index]:
        p.use_smooth = True
bpy.ops.wm.save_mainfile()
print('EYESMOOTH faces', int(ec.sum()))
