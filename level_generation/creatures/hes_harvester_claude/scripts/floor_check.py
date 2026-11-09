"""Floor gate: for every clip and frame of export/hes_harvester.blend, the lowest point of the hull (the vertices on
B_Body: tracks, guards, armour plates) in the deformed mesh. Below -FLOOR_TOL it sinks into the floor, above
+FLOOR_TOL it floats. The drill and boom are not counted (the dig drives the drill into the floor on purpose)."""
import json
import os

import bpy
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLOOR_TOL = 0.05
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'export', 'hes_harvester.blend'))
scene = bpy.context.scene
rig, body = bpy.data.objects['Rig'], bpy.data.objects['Harvester']
g = body.vertex_groups['B_Body'].index
hull = np.array([any(e.group == g and e.weight > 0.5 for e in v.groups) for v in body.data.vertices])
report, worst = {}, 0.0
for action in bpy.data.actions:
    rig.animation_data.action = action
    if len(action.slots):
        rig.animation_data.action_slot = action.slots[0]
    lows = []
    for f in range(int(action.frame_range[0]), int(action.frame_range[1]) + 1):
        scene.frame_set(f)
        ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        me = ev.to_mesh()
        co = np.array([v.co[:] for v in me.vertices])
        ev.to_mesh_clear()
        lows.append(float(co[hull[:len(co)], 2].min()))
    report[action.name] = [round(min(lows), 4), round(max(lows), 4)]
    worst = max(worst, abs(min(lows)), abs(max(lows)))
print('FLOOR', json.dumps(report), 'worst', round(worst, 4), 'PASS' if worst <= FLOOR_TOL else 'FAIL')
