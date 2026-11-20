"""Audit of the master's HeadUV: head faces (attribute head = 1, hand = 0) must lie inside the head square (0..0.8);
hand faces inside their squares. Prints counts and the centres of offenders. Args: -- <blend>"""
import bpy, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
me = bpy.data.objects['Body'].data
head = np.zeros(len(me.polygons), int); me.attributes['head'].data.foreach_get('value', head)
hand = np.zeros(len(me.polygons), int); me.attributes['hand'].data.foreach_get('value', hand)
uv = me.uv_layers['HeadUV'].data
bad = []
for p in me.polygons:
    if head[p.index] and not hand[p.index]:
        c = np.array([uv[li].uv[:] for li in p.loop_indices])
        if (c > 0.8 + 1e-4).any() or (c < -1e-4).any():
            bad.append((p.index, [round(x, 3) for x in p.center], c.round(3).tolist()))
print('UVAUDIT head faces', int(((head == 1) & (hand == 0)).sum()), 'outside head square', len(bad),
      'hand faces', int(hand.sum()), 'head&hand', int(((head == 1) & (hand == 1)).sum()))
for b in bad[:15]:
    print('UVBAD', b)
