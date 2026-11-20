"""Read-only probe of the production master (../mm7_m438_claude/work/rig_v7.blend): mesh objects, sizes, attributes."""
import os, bpy
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, '..', 'mm7_m438_claude', 'work', 'rig_v7.blend'))
for o in bpy.data.objects:
    if o.type == 'MESH':
        me = o.data
        print('OBJ', o.name, len(me.vertices), len(me.polygons), [a.name + ':' + a.domain + ':' + a.data_type for a in me.attributes if not a.name.startswith('.')], [m.name for m in me.materials], [u.name for u in me.uv_layers], o.parent.name if o.parent else None)
