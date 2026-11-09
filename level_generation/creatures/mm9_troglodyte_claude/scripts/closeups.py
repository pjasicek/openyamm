"""Joint-framed close-ups: prints vshots specs. Each entry: joint name(s) tracked at a clip time, a view direction in the body's frame (Bip02 Spine3 axes are not used: world dir chosen to see the crease). Args: <glb>"""
import sys, numpy as np
sys.path.insert(0, '/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/floor')
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); names = [n.get('name') for n in m.glb.json['nodes']]
B = 'Bip02 '
J = [('kneeL_crouch', 'Hit', .3, B + 'L Calf', (.6, .2, 1), .42), ('kneeL_inner', 'Hit', .3, B + 'L Calf', (-.9, .1, .3), .6), ('kneeR_death', 'Dead', .5, B + 'R Calf', (-.5, .8, .5), .45), ('kneeL_run', 'Running', .3, B + 'L Calf', (1, .2, .6), .42),
     ('groin_crouch', 'Hit', .3, B + 'L Thigh', (-.1, -.5, 1), .6), ('groin_rear', 'Hit2', .7, 'Bip01 Pelvis', (0, -.2, -1), .7), ('groin_dead', 'Dead', .5, 'Bip01 Pelvis', (.5, .8, .4), .7), ('groin_walk', 'Walking', .3, 'Bip01 Pelvis', (.3, -.5, -1), .7),
     ('armpitL_taunt', 'Taunt', .7, B + 'L UpperArm', (.6, -.4, .9), .5), ('armpitR_hit', 'Hit', .3, B + 'R UpperArm', (-.7, -.3, .8), .5), ('armpitR_attack', 'AttackMelee', .3, B + 'R UpperArm', (-.8, .2, -.6), .55), ('armpitL_attack2', 'AttackMelee2', .35, B + 'L UpperArm', (.8, .3, -.5), .55),
     ('elbowL_attack', 'AttackMelee', .25, B + 'L Forearm', (.7, .2, -.7), .4), ('elbowR_taunt', 'Taunt', .7, B + 'R Forearm', (-.6, .3, .8), .4), ('elbowR_stand', 'Standing', .5, B + 'R Forearm', (-1, .1, -.4), .4), ('elbowL_dead', 'Dead', .5, B + 'L Forearm', (.5, .8, .4), .45),
     ('neck_taunt', 'Taunt', .7, B + 'Neck', (.7, .1, -.2), .8), ('neck_hit', 'Hit', .3, B + 'Neck', (-.3, -.5, 1), .8), ('neck_back', 'Hit', .3, B + 'Neck', (.1, .6, -1), .8), ('neck_dead', 'Dead', .5, B + 'Neck', (.4, .9, .3), .8),
     ('mouth_taunt', 'Taunt', .7, 'Box05', (.2, -.3, 1), .8), ('mouth_hit', 'Hit', .3, 'Box05', (.1, -.1, 1), .8), ('mouth_side', 'AttackMelee', .35, 'Box05', (1, .1, .3), .8), ('mouth_closed', 'Standing', .5, 'Box05', (.5, 0, 1), .7), ('mouth_dead', 'Dead', .5, 'Box05', (.3, .9, .5), .8),
     ('tailroot_walk', 'Walking', .3, 'Box01', (.3, -.2, -1), .6), ('tailroot_death2', 'Death2', 1.2, 'Box01', (.3, .8, -.6), .7), ('ankle_hit', 'Hit', .3, B + 'R Foot', (-.7, .3, .8), .5), ('hand_taunt', 'Taunt', .7, B + 'L Hand', (.3, .4, 1), .5), ('hand_claws', 'Standing', .5, B + 'R Hand', (-.8, .2, .8), .5)]
out = []
for nm, clip, t, j, d, D in J:
    w = m.world(m.sample(clip, t)); p = w[names.index(j)][:3, 3]; d = np.array(d, float); d /= np.linalg.norm(d); c = p + d * D
    out.append(f"j_{nm}:{clip}:{t}:left:body:{c[0]:.3f},{c[1]:.3f},{c[2]:.3f}:{p[0]:.3f},{p[1]:.3f},{p[2]:.3f}")
print(' '.join(out))
