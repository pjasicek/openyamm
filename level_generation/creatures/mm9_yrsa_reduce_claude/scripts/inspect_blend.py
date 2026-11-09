import bpy, sys, collections
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--')+1])
for o in bpy.data.objects:
    if o.type != 'MESH': print(o.name, o.type); continue
    me = o.data
    print(o.name, 'faces', len(me.polygons), 'tris', sum(len(p.vertices)-2 for p in me.polygons), 'mats', [m.name if m else None for m in me.materials],
          'uv', [u.name for u in me.uv_layers], 'attrs', [(a.name, a.domain, a.data_type) for a in me.attributes if not a.name.startswith('.')],
          'hidden', o.hide_render)
    c = collections.Counter(p.material_index for p in me.polygons); print('  matidx', dict(c))
    for a in me.attributes:
        if a.domain == 'FACE' and a.data_type in ('INT', 'INT8') and not a.name.startswith('.'):
            print('  ', a.name, dict(collections.Counter(d.value for d in a.data)))
