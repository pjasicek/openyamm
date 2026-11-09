"""Native-key clips for the male peasant (pman ANIMATION_STUDY.md): Standing (loose low fists), Fidget, Attack
(knife; same choreography as the female), Hit (5 keys, 625 ms: forearm guard over the eyes, deep squat),
DeathFull (side fall 0–500 ms, roll to the prone corpse at 625 ms, held). Uses author_clips' pose machinery."""
import bpy, sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import author_clips as A

FIST_R = {'finger': (0.05, -1.0, 0.15), 'palm': (1.0, 0.0, 0.1), 'curl': 62, 'thumb': 30}
FIST_L = {'finger': (-0.05, -1.0, 0.15), 'palm': (-1.0, 0.0, 0.1), 'curl': 62, 'thumb': 30}
STAND = {
    'arm_R': {'wrist': (-0.245, -0.40, 0.0), 'pole': (-0.5, 0.1, -0.45), **FIST_R},
    'arm_L': {'wrist': (0.245, -0.40, 0.0), 'pole': (0.5, 0.1, -0.45), **FIST_L},
}
v = A.variant
STANDING = [(1, STAND), (49, v(STAND, spine=(-0.8, 0, 0), head=(0.5, 0, 0), hips=(0, 0, -0.002))), (97, STAND)]
FIDGET = [(1, STAND), (7, v(STAND, head=(-4, 3, 9))), (10, v(STAND, head=(3, -2, 12), spine=(0, 0.5, 2))),
          (13, v(STAND, head=(-2, 1, 5))), (19, STAND)]
# Attack: native pmanat a–f match the female knife choreography; rest pose differs.
ATTACK = [(f, spec) for f, spec in A.ATTACK[:-1]] + [(19, STAND)]
GUARD_R = {'wrist': (0.11, 0.30, 0.15), 'pole': (-0.7, 0.0, 0.35), 'finger': (1.0, 0.15, 0.0), 'palm': (0, 0, -1),
           'curl': 45, 'thumb': 20}
PALM_L = {'wrist': (0.17, 0.20, 0.20), 'pole': (0.7, -0.4, 0.1), 'finger': (0.0, 1.0, 0.2), 'palm': (0, 0, 1),
          'curl': 8, 'thumb': 5}
HIT = [
    (1, {'arm_R': {'wrist': (0.02, -0.12, 0.17), 'pole': (-0.5, -0.2, 0.0), 'finger': (0.7, 0.1, -0.2),
                   'palm': (0, 0, -1), 'curl': 40}, 'arm_L': STAND['arm_L'], 'spine': (10, 0, 0), 'head': (12, 0, 0),
         'hips': (0, 0.01, -0.01)}),
    (4, {'arm_R': GUARD_R, 'arm_L': v(PALM_L, wrist=(0.14, -0.05, 0.22)), 'spine': (14, 0, 0), 'head': (16, 0, 0),
         'hips': (0, 0.03, -0.06)}),
    (7, {'arm_R': GUARD_R, 'arm_L': PALM_L, 'spine': (22, -4, 0), 'head': (18, 0, 0), 'hips': (0, 0.06, -0.20),
         'feet_offset': {'Right': (-0.05, 0, 0)}}),
    (10, {'arm_R': GUARD_R, 'arm_L': PALM_L, 'spine': (16, -3, 0), 'head': (14, 0, 0), 'hips': (0, 0.04, -0.13),
          'feet_offset': {'Right': (-0.05, 0, 0)}}),
    (13, {'arm_R': {'wrist': (-0.20, -0.25, 0.12), 'pole': (-0.5, 0, -0.3), **FIST_R},
          'arm_L': {'wrist': (0.20, -0.25, 0.12), 'pole': (0.5, 0, -0.3), **FIST_L},
          'spine': (8, 0, 0), 'head': (6, 0, 0), 'hips': (0, 0.02, -0.06)}),
    (16, STAND),
]
import os as _os
SIDE_HIPS = tuple(float(x) for x in _os.environ.get('SIDE_HIPS', '0.40,0.02,-0.74').split(','))
SIDE_ROT = tuple(float(x) for x in _os.environ.get('SIDE_ROT', '0,0,-85').split(','))
DEATH = [
    (1, {'arm_R': {'wrist': (0.0, -0.08, 0.17), 'pole': (-0.5, -0.2, 0.0), 'finger': (0.7, 0.1, -0.2),
                   'palm': (0, 0, -1), 'curl': 40}, 'arm_L': STAND['arm_L'], 'spine': (10, 0, 0), 'head': (14, 0, 0),
         'hips': (0, 0.01, -0.02)}),
    (4, {'arm_R': GUARD_R, 'arm_L': PALM_L, 'spine': (16, 0, 0), 'head': (16, 0, 0), 'hips': (0, 0.04, -0.12)}),
    (7, {'arm_R': GUARD_R, 'arm_L': PALM_L, 'spine': (12, 18, 0), 'head': (8, 10, 0), 'hips': (0.10, 0.02, -0.28),
         'hips_rot': (0, 0, -25), 'legs': 'fk',
         'leg_fk': {'Right': {'hip': 10, 'knee': 10, 'abduct': 25}, 'Left': {'hip': 60, 'knee': 95}}}),
    (10, {'arm_R': {'wrist': (-0.05, 0.42, 0.10), 'pole': (-0.5, 0.3, 0), 'finger': (0, 1, 0), 'palm': (1, 0, 0), 'curl': 20},
          'arm_L': {'wrist': (0.30, 0.30, 0.05), 'pole': (0.6, 0.2, 0), 'finger': (0.3, 1, 0), 'palm': (0, 0, 1), 'curl': 15},
          'spine': (8, 14, 0), 'head': (4, 12, 0), 'hips': (0.28, 0.02, -0.55), 'hips_rot': (0, 0, -60), 'legs': 'fk',
          'leg_fk': {'Right': {'hip': 15, 'knee': 5, 'abduct': 20}, 'Left': {'hip': 70, 'knee': 110}}}),
    (13, {'arm_R': {'wrist': (-0.05, 0.40, 0.18), 'pole': (-0.5, 0.2, 0), 'finger': (0, 1, 0), 'palm': (1, 0, 0), 'curl': 25},
          'arm_L': {'wrist': (0.12, -0.30, 0.15), 'pole': (0.5, 0, -0.2), 'finger': (0, -1, 0), 'palm': (-1, 0, 0), 'curl': 30},
          'spine': (4, 6, 0), 'head': (0, 15, 0), 'hips': SIDE_HIPS, 'hips_rot': SIDE_ROT, 'legs': 'fk',
          'leg_fk': {'Right': {'hip': 20, 'knee': 8, 'abduct': 12}, 'Left': {'hip': 55, 'knee': 90}}}),
    (16, {'arm_R': {'wrist': (-0.42, 0.18, 0.05), 'pole': (-0.4, -0.2, -0.3), 'finger': (-1, 0.3, 0), 'palm': (0, 0, -1), 'curl': 25},
          'arm_L': {'wrist': (0.42, 0.18, 0.05), 'pole': (0.4, -0.2, -0.3), 'finger': (1, 0.3, 0), 'palm': (0, 0, -1), 'curl': 25},
          'spine': (2, 0, 0), 'head': (0, 22, 62), 'hips': A.CORPSE_HIPS, 'hips_rot': (-55, 88, 0), 'legs': 'fk',
          'leg_fk': {'Left': {'hip': 0, 'knee': 4, 'ankle': A.ANKLE_PRONE, 'abduct': 12},
                     'Right': {'hip': 0, 'knee': 3, 'ankle': A.ANKLE_PRONE, 'abduct': 10}}}),
]
DEATH_FULL = DEATH + [(40, DEATH[-1][1])]

if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    which = args[0].split(',') if args else ['Standing', 'Fidget', 'Attack', 'Hit', 'DeathFull']
    table = {'Standing': (STANDING, True), 'Fidget': (FIDGET, False), 'Attack': (ATTACK, False),
             'Hit': (HIT, False), 'DeathFull': (DEATH_FULL, False)}
    for name in which:
        keys, loop = table[name]
        A.key_clip(name, keys, loop=loop)
        print('AUTHORED', name, keys[-1][0])
    bpy.ops.wm.save_mainfile()
