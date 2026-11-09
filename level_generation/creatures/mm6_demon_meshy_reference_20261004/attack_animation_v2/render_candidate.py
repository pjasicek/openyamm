import bpy
import sys
import numpy as np
from pathlib import Path
stage = Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_demon_meshy_reference_20261004/attack_animation_v2')
sys.path.insert(0,str(stage))
sys.modules.pop('motion',None)
import motion
scene, rig, mesh = motion.objects()
scene.render.resolution_x = 1300
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
rig.hide_set(False)
rig.animation_data.action = None
for track in rig.animation_data.nla_tracks:
    track.mute = True
motion.TWIST_HISTORY.clear()
selected = (0,6,12,18,19,20,21,22,23,24,26,28,30)
output = stage / 'candidate_frames'
output.mkdir(exist_ok=True)
for frame in range(37):
    motion.pose_at(frame)
    if frame in selected:
        motion.render('candidate_frames/front_'+f'{frame:02d}')
        motion.render('candidate_frames/side_'+f'{frame:02d}',(6,0,0))
        motion.render('candidate_frames/opposite_'+f'{frame:02d}',(-6,0,0))
print('Rendered targeted candidate front/both profiles:',selected)
