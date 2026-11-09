"""Close renders of chosen pieces of work/step1.blend from several directions. Args: -- <out prefix> <piece,...> [views]"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
out, pieces = a[0], [int(x) for x in a[1].split(',')]
views = a[2].split(',') if len(a) > 2 else ['front', 'left', 'back', 'right']
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'step1.blend'))
b = bpy.data.objects['Body']; me = b.data
pv = np.array([x.value for x in me.attributes['piece'].data])
import bmesh
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[v for v in bm.verts if pv[v.index] not in pieces], context='VERTS'); bm.to_mesh(me); bm.free()
co = np.array([v.co[:] for v in me.vertices]); c = (co.min(0) + co.max(0)) / 2; size = float((co.max(0) - co.min(0)).max()) * 1.25
scene = bpy.context.scene; common.workbench_clay(scene)
b.show_wire = True
common.render_views(out, float(c[2]), size, views=tuple(views), resolution=(500, 500), target=(float(c[0]), float(c[1])))
