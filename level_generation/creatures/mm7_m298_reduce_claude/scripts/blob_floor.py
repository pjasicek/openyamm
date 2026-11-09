"""Floor gate for the blob alone (LOD0 of a GLB): per clip, the lowest and the highest-lowest (lift) of the vertices
dominated by Body/Lump_* bones over every frame, so the hidden pod and globules do not mask a sinking or lifted
underside. Usage: blender -b -P blob_floor.py -- <label=glb,...>"""
import bpy, os, sys
import numpy as np
for item in sys.argv[sys.argv.index('--') + 1].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
    o = bpy.data.objects['Ooze']; rig = next(m.object for m in o.modifiers if m.type == 'ARMATURE')
    names = {g.index: g.name for g in o.vertex_groups}
    blob = np.array([bool(v.groups) and (lambda n: n == 'Body' or n.startswith('Lump'))(names[max(v.groups, key=lambda g: g.weight).group])
                     for v in o.data.vertices])
    out = {}
    for act in sorted(bpy.data.actions, key=lambda a: a.name):
        rig.animation_data.action = act
        if act.slots:
            rig.animation_data.action_slot = act.slots[0]
        f0, f1 = (int(x) for x in act.frame_range); lows = []
        for f in range(f0, f1 + 1):
            sc.frame_set(f); ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
            z = np.array([(ev.matrix_world @ v.co).z for v in me.vertices]); ev.to_mesh_clear(); lows.append(z[blob].min())
        out[act.name] = (round(min(lows) * 1000, 2), round(max(lows) * 1000, 2))
    print('BLOBFLOOR', label, int(blob.sum()), out, flush=True)
