"""Blender, background: -- <in.blend> <out.json>. The cloth chain definitions a robed project's robe_sim.py reads
(scene properties cloak_chains / sheet_chains: rest joint points, bone names, outward heading) and its armature's
world matrix, as JSON for the numpy port (cloth_sim.py)."""
import bpy, sys, json
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=src)
scene = bpy.context.scene
arm = bpy.data.objects['Rig']
data = {'matrix_world': [list(r) for r in arm.matrix_world]}
for key in ('cloak_chains', 'sheet_chains', 'banner_chains'):
    if key in scene:
        data[key] = json.loads(scene[key])
json.dump(data, open(out, 'w'))
print('CHAINS', {k: len(v) for k, v in data.items() if k != 'matrix_world'})
