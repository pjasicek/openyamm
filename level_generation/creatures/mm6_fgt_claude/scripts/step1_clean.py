"""Clean Thug Smart Topology: remove separate eyeballs, retain armour/scarf/sheath, record original coordinates."""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
# Separate eye shells are off-centre; the underlying sockets receive painted eyes.
for n in ('P29', 'P35'):
    bpy.data.objects.remove(P.pop(n), do_unlink=True)
for o in bpy.data.objects:
    o.select_set(False)
for n, o in P.items():
    o.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [int(n[1:])] * len(o.data.vertices))
    o.select_set(True)
bpy.context.view_layer.objects.active = P['P00']
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = body.data.name = 'Body'
body.data.materials.clear()
print('TRIS', sum(len(p.vertices) - 2 for p in body.data.polygons))
me = body.data
co = np.array([tuple(v.co) for v in me.vertices])
me.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
# Seat the already rearward sheath slightly closer to the hip to clear the walking hand.
from mathutils import Matrix,Vector
import math
pivot=Vector((.145,-.03,1.0));turn=Matrix.Rotation(math.radians(10),3,'Y')
for v in me.vertices:
    if me.attributes['piece'].data[v.index].value in (10,15):
        v.co=pivot+turn@(v.co-pivot)
# Give the front-right tasset its measured attack clearance (3.7 mm crossing).
for v in me.vertices:
    if me.attributes['piece'].data[v.index].value in (16,17,18,19,20,21,22,23,24,25,28,30,31,33,34,36,38):
        radial=Vector((v.co.x,v.co.y,0)).normalized()
        v.co += radial*.006
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
