"""Read-only probe of the production master (../mm7_m422_claude/work/rig_v6.blend): objects, attributes, groups."""
import os, bpy, collections
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, '..', 'mm7_m422_claude', 'work', os.environ.get('MASTER', 'rig_v6.blend')))
for o in bpy.data.objects:
    if o.type != 'MESH':
        print('OBJ', o.name, o.type); continue
    me = o.data
    print('OBJ', o.name, 'verts', len(me.vertices), 'polys', len(me.polygons), 'mats', [m.name for m in me.materials if m])
    for a in me.attributes:
        if a.name.startswith('.'):
            continue
        info = ''
        if a.data_type in ('INT', 'BOOLEAN', 'INT8') and len(a.data):
            c = collections.Counter(d.value for d in a.data); info = dict(sorted(c.items())[:40])
        print('ATTR', o.name, a.name, a.domain, a.data_type, info)
    print('UV', [u.name for u in me.uv_layers])
    print('VG', len(o.vertex_groups), [g.name for g in o.vertex_groups][:200])
