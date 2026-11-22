"""Claws_L local-X curl of -60 / 0 / +60 degrees, side view of the left hand (review/curl_<deg>.png)."""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C, posing as P
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
rig = bpy.data.objects['Mole_Rig']
for d in (-60, 0, 60):
    P.reset(rig); P.rotate_local(rig, 'Claws_L', 'X', d)
    C.render((2.5, -0.5, 0.15), (0.45, -0.5, 0.15), 0.6, os.path.join(HERE, 'review', f'curl_{d}.png'), res=(400, 400))
