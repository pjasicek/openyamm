"""Placement of the queen in the rock: raise her onto the niche lip (QUEEN_RAISE) and offset her sideways
(QUEEN_X), both from the native frame; then set her depth so her hanging arms clear the rock face by ARM_CLEARANCE. Renders an orthographic front view at the native framing
(the whole rock) and writes work/placement.json and review/compose_front.png."""
import bpy, sys, json
import numpy as np
from pathlib import Path
from mathutils import Vector
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import common
GAME_PER_UNIT = 393.0 / 2.4
QUEEN_RAISE = 1.1 * 104.0 / GAME_PER_UNIT          # the niche lip scales with the rock (rock_load.py APPARENT)
QUEEN_X = -20.0 / GAME_PER_UNIT
ARM_CLEARANCE = 0.05
src = P / 'work' / ('step2.blend' if (P / 'work' / 'step2.blend').exists() else 'step1.blend')
bpy.ops.wm.open_mainfile(filepath=str(src))
queen = bpy.data.objects['Queen']
with bpy.data.libraries.load(str(P / 'work' / 'rock.blend')) as (data_from, data_to):
    data_to.objects = ['Rock']
rock = data_to.objects[0]
bpy.context.scene.collection.objects.link(rock)
deps = bpy.context.evaluated_depsgraph_get()
# Depth: she stands in front of the rock face with only her abdomen running back into the niche (native: her
# arms and claws hang over the rock's surface). Her arms and hands must clear the rock face by ARM_CLEARANCE: rays
# along +Y where her arms hang give the rock front, compared with her arms' rear surface.
qco = np.array([tuple(v.co) for v in queen.data.vertices])
arms = qco[(np.abs(qco[:, 0]) > 0.28) & (qco[:, 2] > 0.85)]
front = []
for x in np.linspace(-0.75, 0.75, 13):
    if abs(x) < 0.28:
        continue
    for z in np.linspace(0.85, 1.75, 7):
        ok, loc, nrm, idx = rock.ray_cast(Vector((x + QUEEN_X, -20.0, z + QUEEN_RAISE)), Vector((0, 1, 0)))
        if ok:
            front.append(loc.y)
rock_front = float(min(front))
arm_back = float(arms[:, 1].max())
dy = rock_front - ARM_CLEARANCE - arm_back
queen.location = (QUEEN_X, dy, QUEEN_RAISE)
place = {'queen_location': [QUEEN_X, dy, QUEEN_RAISE], 'rock_front_at_arms_y': rock_front, 'arm_back_y': arm_back,
         'game_units_per_model_unit': GAME_PER_UNIT}
print('PLACE', json.dumps(place))
(P / 'work' / 'placement.json').write_text(json.dumps(place, indent=1))
scene = bpy.context.scene
common.workbench_clay(scene, textured=True)
scene.display.shading.light = 'FLAT'
common.render_views(str(P / 'review' / 'compose'), 3.981 / 2, 4.6, views=('front', 'left', 'three_quarter'),
                    resolution=(908, 850), distance=30)
