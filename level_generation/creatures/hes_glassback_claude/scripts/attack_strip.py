"""Attack clip strip (tier B, full crest): frames of the rear-up Attack from the side and a front three-quarter, Eevee,
with the setup and lighting of viewer_export.py -> work/renders/attack_<view>_<frame>.png. Args: none"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'viewer_export.py')).read()
exec(compile(src[:src.index('SHOTLIST = {')], 'viewer_export', 'exec'))
rig, body = setup('hgb_b')
rig.animation_data.action = bpy.data.actions['Attack']
FRAMES = [1, 8, 13, 16, 20, 23, 25, 27, 31, 43]
for f in FRAMES:
    bpy.context.scene.frame_set(f)
    render(C.path(f'work/renders/attack_side_{f:02d}.png'), (6, -0.2, 0.9), (0, -0.2, 0.9), 3.6, res=(540, 420))
    render(C.path(f'work/renders/attack_quarter_{f:02d}.png'), (3.4, -4.0, 1.9), (0, -0.2, 0.7), 3.8, res=(540, 420))
print('STRIP', FRAMES)
