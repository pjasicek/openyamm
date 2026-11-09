"""Close-up spots for the MM7 Zombie (faces -y, right side -x; right arm a stump, the forearm prop in the left fist):
name -> (clip, frame, centre bone or 'A+B' midpoint, ortho size m, view direction). Shared by close_m438.py and
glb_close.py."""
SPOTS = {
    'face_front': ('Standing', 0, 'B_Head', .36, (0, -1, .1)), 'face_q34': ('Standing', 0, 'B_Head', .36, (-.7, -.7, .15)),
    'face_l': ('Standing', 0, 'B_Head', .4, (1, -.1, .05)), 'head_back': ('Standing', 0, 'B_Head', .45, (.2, 1, .25)),
    'chest': ('Standing', 0, 'B_Spine1', .6, (0, -1, .1)), 'back': ('Standing', 0, 'B_Spine1', .7, (0, 1, .2)),
    'flank_r': ('Standing', 0, 'B_Spine', .55, (-1, -.35, .1)), 'stump': ('Standing', 0, 'B_R_Forearm', .32, (-.6, -.8, .1)),
    'stump_end': ('Standing', 0, 'B_R_Forearm', .3, (-.3, -.6, -.9)), 'fist': ('Standing', 0, 'B_L_Hand', .28, (.5, -.8, .3)),
    'fist_back': ('Standing', 0, 'B_L_Hand', .28, (.4, .8, .2)), 'fist_atk': ('Attack', 22, 'B_L_Hand', .4, (.4, -.8, .3)),
    'trousers_front': ('Standing', 0, 'B_L_Thigh+B_R_Thigh', .75, (0, -1, .05)),
    'trousers_back': ('Standing', 0, 'B_L_Thigh+B_R_Thigh', .75, (0, 1, .05)),
    'knees': ('Standing', 0, 'B_L_Calf+B_R_Calf', .6, (0, -1, .1)), 'shin_r': ('Standing', 0, 'B_R_Calf', .42, (-.6, -.8, .1)),
    'shin_r_back': ('Standing', 0, 'B_R_Calf', .42, (-.3, 1, .1)), 'feet': ('Standing', 0, 'B_L_Foot+B_R_Foot', .6, (0, -1, .5)),
    'rope': ('Standing', 0, 'B_Pelvis', .4, (0, -1, .1)), 'neck_fidget': ('Fidget', 27, 'B_Neck', .6, (0, 1, .5)),
    'attack': ('Attack', 22, 'B_Spine1', 1.9, (-.7, -.7, .3)), 'walk': ('Walking', 20, 'B_Spine', 1.9, (.7, -.7, .2)),
    'death': ('Death', 80, 'B_Pelvis', 2.0, (.6, -.6, .6)), 'run_knee': ('Running', 15, 'B_L_Calf', .6, (.8, -.6, .2)),
}


def centre(rig, spec):
    pb = rig.pose.bones
    pts = [rig.matrix_world @ ((pb[n].head + pb[n].tail) / 2) for n in spec.split('+')]
    return sum(pts[1:], pts[0]) / len(pts)
