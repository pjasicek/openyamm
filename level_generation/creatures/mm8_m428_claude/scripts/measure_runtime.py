"""Stride (stride.py on the final rig) and the Standing-pose body height (frame 0, skinned body, no dagger) for the
actors.yml scale = native 201-unit standing height / model height."""
import runpy, sys, bpy, json
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.argv = ['stride.py', '--', str(P / 'work/rig_sim.blend'), 'Walking', 'Running', 'Standing']
runpy.run_path(str(P / 'scripts/stride.py'), run_name='__main__')
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
a = bpy.data.actions['Standing']; rig.animation_data.action = a; rig.animation_data.action_slot = a.slots[0]
hs = []
for f in range(0, 61, 10):
    bpy.context.scene.frame_set(f)
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    z = np.array([(body.matrix_world @ v.co).z for v in m.vertices]); ev.to_mesh_clear(); hs.append(float(z.max() - z.min()))
print('STANDHEIGHT', [round(h, 4) for h in hs], 'scale for 201 units', round(201 / hs[0], 6))
(P / 'work/runtime_measurements.json').write_text(json.dumps({'standing_height_m': hs, 'scale': 201 / hs[0]}, indent=1) + '\n')
