"""Clip timing (2026-10-10): copy rebuilt actions into the textured master work/rig_v8.blend in place, so the later
chain (v5-v8: Hit, Death, staff socket, textures, head split) is not replayed for a clip it does not change.
Args: -- [source blend in work/ (default rig_v4.blend)] [actions (default Attack)], e.g.
`-- rig_v6.blend Death Dead` after death_staff.py + smooth_attack.py. Cast is copied from Attack at export."""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
source = args[0] if args else 'rig_v4.blend'
names = args[1:] or ['Attack']
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'rig_v8.blend'))
for name in names:
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
with bpy.data.libraries.load(os.path.join(common.WORK, source), link=False) as (src, dst):
    dst.actions = list(names)
for act in dst.actions:
    act.use_fake_user = True
    print('TRANSPLANT', act.name, 'frames', tuple(act.frame_range), 'from', source)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v8.blend'))
