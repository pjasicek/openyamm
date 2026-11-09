"""Save work/blob_only.blend: anim_v1.blend with the pod faces (part 1) deleted, for the AO bake (the pod stands
fully grown in the rest pose and would darken the top)."""
import bpy, bmesh, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'anim_v1.blend'))
me = bpy.data.objects['Ooze'].data
part = np.zeros(len(me.polygons), int)
me.attributes['part'].data.foreach_get('value', part)
bm = bmesh.new()
bm.from_mesh(me)
bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if part[f.index] == 1], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(me)
bm.free()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'blob_only.blend'))
print('BLOB_ONLY', len(me.polygons))
