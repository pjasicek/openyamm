"""Side and three-quarter frames of Sprint (and Run2 for comparison) from work/rat_sprint.blend for review:
review/sprint/<clip>_<view>_<frame>.png. Args: clip names (default Run2 Sprint)."""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common_rat import render_ortho
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work/rat_sprint.blend'))
rig = bpy.data.objects['Rat_Rig']; out = os.path.join(HERE, 'review/sprint'); os.makedirs(out, exist_ok=True)
for clip in (a or ['Run2', 'Sprint']):
    act = bpy.data.actions[clip]; rig.animation_data.action = act
    f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1):
        bpy.context.scene.frame_set(f)
        for view, loc in (('side', (3, 0, 0.16)), ('tq', (2.2, -2.2, 1.0))):
            render_ortho(loc, (0, 0, 0.14), 1.25, os.path.join(out, f'{clip}_{view}_{f - f0:02d}.png'), res=(400, 300),
                         textured=True)
