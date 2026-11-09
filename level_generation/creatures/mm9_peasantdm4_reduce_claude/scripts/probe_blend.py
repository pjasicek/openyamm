"""List objects, materials and attributes of the creature's build blend (rigid_v3n.blend)."""
import bpy, sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
for o in bpy.data.objects:
    if o.type == 'MESH':
        me = o.data
        print('OBJ', o.name, len(me.vertices), len(me.polygons), [m.name for m in me.materials])
        for a in me.attributes:
            print('  ATTR', a.name, a.domain, a.data_type)
        print('  UV', [u.name for u in me.uv_layers], 'VG', len(o.vertex_groups))
