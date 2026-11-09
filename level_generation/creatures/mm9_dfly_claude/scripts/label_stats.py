import bpy, sys, json
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
out = {}
for o in bpy.context.scene.objects:
    if o.type != 'MESH' or o.name.startswith('Icosphere'):
        continue
    g = {}
    for v in o.data.vertices:
        for gr in v.groups:
            if gr.weight > 0.5:
                n = o.vertex_groups[gr.group].name
                p = o.matrix_world @ v.co
                g.setdefault(n, []).append(p)
    out[o.name] = {n: {'n': len(ps), 'c': [round(sum(p[i] for p in ps) / len(ps), 3) for i in range(3)],
                       'min': [round(min(p[i] for p in ps), 3) for i in range(3)],
                       'max': [round(max(p[i] for p in ps), 3) for i in range(3)]} for n, ps in g.items()}
print('STATS ' + json.dumps(out))
