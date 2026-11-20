"""Check gltf_pose round trip: installed Walking keys recomputed from the Blender pose match the GLB data."""
import bpy, sys, os, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from glb_io import Glb
from gltf_pose import GltfPose
glb = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
g = Glb(glb); gp = GltfPose(g.json, rig)
ch = g.channels('Walking')
times = g.read(next(s['input'] for s in g.animation('Walking')['samplers'] if s.get('interpolation', 'LINEAR') == 'LINEAR'))[:, 0]
act = next(a for a in bpy.data.actions if a.name.split('|')[-1] == 'Walking')
rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
fps = bpy.context.scene.render.fps / bpy.context.scene.render.fps_base
worst_r, worst_t = 0, 0
for k in (0, 37, 96, 150, 192):
    t = times[k]; f = act.frame_range[0] + t * fps
    bpy.context.scene.frame_set(int(f), subframe=f % 1); bpy.context.view_layer.update()
    loc = gp.node_locals()
    for (node, path), (s, out) in ch.items():
        if node not in loc or g.json['accessors'][s['input']]['count'] != len(times):
            continue
        ref = g.read(out)[k]
        if path == 'rotation':
            mine = loc[node][1]; d = min(np.abs(mine - ref).max(), np.abs(mine + ref).max()); worst_r = max(worst_r, d)
        elif path == 'translation':
            worst_t = max(worst_t, np.abs(loc[node][0] - ref).max())
print('ROUNDTRIP max quat component error', worst_r, 'max translation error', worst_t, flush=True)
