"""Sample clips of a creature GLB: per-frame world matrices of every bone, local rotations, and the lowest sole /
body / sword vertex. Usage: blender -b -P sample_clips.py -- <glb> <out.npz> <clip>[,<clip>...] [fps]"""
import bpy, sys, numpy as np
from mathutils import Matrix

args = sys.argv[sys.argv.index('--') + 1:]
glb, out, clips = args[0], args[1], args[2].split(',')
fps = float(args[3]) if len(args) > 3 else 120.0
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
scene = bpy.context.scene
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body = max((o for o in bpy.data.objects if o.type == 'MESH'), key=lambda o: len(o.data.polygons))
names = [b.name for b in rig.pose.bones]
groups = [g.name for g in body.vertex_groups]
sole = {}
rest = np.array([v.co[:] for v in body.data.vertices])
for s in 'LR':
    mask = np.array([sum(g.weight for g in v.groups if groups[g.group] in (f'B_{s}_Foot', f'B_{s}_Toe0')) > .5
                     for v in body.data.vertices])
    sole[s] = np.where(mask)[0]
acts = {a.name.split('|')[-1]: a for a in bpy.data.actions}
scene_fps = scene.render.fps / scene.render.fps_base
data = {'names': np.array(names)}
for clip in clips:
    act = acts[clip]
    rig.animation_data.action = act
    if len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    duration = (f1 - f0) / scene_fps
    n = int(round(duration * fps)) + 1
    world, local, loc, lows = [], [], [], []
    for i in range(n):
        t = min(i / fps, duration)
        f = f0 + t * scene_fps
        scene.frame_set(int(f), subframe=f % 1)
        bpy.context.view_layer.update()
        world.append([np.array(rig.matrix_world @ pb.matrix) for pb in rig.pose.bones])
        local.append([pb.rotation_quaternion[:] for pb in rig.pose.bones])
        loc.append([pb.location[:] for pb in rig.pose.bones])
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        m = ev.to_mesh()
        co = np.array([(body.matrix_world @ v.co)[:] for v in m.vertices])
        ev.to_mesh_clear()
        lows.append([co[sole['L'], 2].min(), co[sole['R'], 2].min(), co[:, 2].min()])
    data[clip + '_world'] = np.array(world)
    data[clip + '_local'] = np.array(local)
    data[clip + '_loc'] = np.array(loc)
    data[clip + '_lows'] = np.array(lows)
    data[clip + '_duration'] = duration
    print('SAMPLED', clip, duration, n, flush=True)
np.savez(out, **data)
