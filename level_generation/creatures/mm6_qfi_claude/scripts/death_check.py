"""Death review on work/anim_v2.blend with a floor plane at z = 0 (the floor hides what sinks below it in game):
Death at 0.25 / 0.6 / 1.0 / 1.3 s and Dead, front (the native view) and three-quarter. Writes review/death_<t>_<view>.png."""
import bpy, sys, json
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'anim_v2.blend'))
rig = bpy.data.objects['Rig']
bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
floor = bpy.context.active_object
m = bpy.data.materials.new('floor'); m.diffuse_color = (0.35, 0.37, 0.4, 1); floor.data.materials.append(m)
scene = bpy.context.scene
common.workbench_clay(scene)
for name, t in (('Death', 0.25), ('Death', 0.6), ('Death', 1.0), ('Death', 1.3), ('Dead', 0.0)):
    act = bpy.data.actions[name]
    rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    scene.frame_set(int(round(t * 30)))
    common.render_views(str(P / 'review' / f'death_{name}_{t:.2f}'), 1.95, 4.6, views=('front', 'three_quarter'),
                        resolution=(500, 480), distance=25)
