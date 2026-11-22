"""Close-up of the head in rest and in the stress 'rear' pose (review/probe_head_*.png), and the list of thin
slivers (triangles with an edge over 6 cm on the face caps or the tongue)."""
import bpy, os, sys
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C, posing as P
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
rig = bpy.data.objects['Dillo_Rig']; ob = bpy.data.objects['Dillo']; me = ob.data
for p in me.polygons:
    vs = [me.vertices[i].co for i in p.vertices]
    L = max((vs[i] - vs[(i + 1) % 3]).length for i in range(3))
    if L > 0.06 and me.vertices[p.vertices[0]].co.y < -0.9:
        print('LONG', p.index, 'part', me.attributes['part'].data[p.index].value, round(L, 3),
              [tuple(round(c, 3) for c in v) for v in vs])
X = Vector((1, 0, 0))
P.reset(rig); rig.pose.bones['Tongue'].scale = (0.05,) * 3; bpy.context.view_layer.update()
C.render((0.8, -1.0, 0.25), (0, -1.0, 0.2), 0.45, os.path.join(HERE, 'review', 'probe_head_rest.png'), res=(600, 600))
P.rotate_world(rig, 'Body', X, -14, Vector((0, 0.1, 0.05)))
rig.pose.bones['Tongue'].scale = (0.05,) * 3; bpy.context.view_layer.update()
C.render((0.8, -1.0, 0.45), (0, -1.0, 0.4), 0.6, os.path.join(HERE, 'review', 'probe_head_rear.png'), res=(600, 600))
