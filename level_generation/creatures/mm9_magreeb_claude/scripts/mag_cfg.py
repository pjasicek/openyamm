"""MM9 MAGREEB.abc bone chains shared by fit_magreeb.py and rig_body.py (order = 'chain' attribute index).
Legs: four 4-bone chains (Bone56/61 on +X, Bone108/114 on -X; 56 and 108 are the long rear legs).
Arms: two pincer arms (shoulder, upper arm, forearm, claw base, then the two blade chains)."""
LEGS = [
    ['Bone56', 'Bone57', 'Bone58', 'Bone59'],
    ['Bone61', 'Bone62', 'Bone63', 'Bone64'],
    ['Bone108', 'Bone109', 'Bone110', 'Bone111'],
    ['Bone114', 'Bone115', 'Bone116', 'Bone117'],
]
ARMS = [
    ['Bone39', 'Bone12', 'Bone13', 'Bone14', 'Bone15', 'Bone16', 'Bone18', 'Bone19'],   # -X
    ['Bone38', 'Bone21', 'Bone22', 'Bone23', 'Bone24', 'Bone25', 'Bone27', 'Bone28'],   # +X
]
CHAINS = LEGS + ARMS
HEAD = ['Bone36', 'Bone04', 'Bone05', 'Bone06', 'Bone07', 'Bone01', 'Bone02', 'Bone09']
JAW = {'Bone01', 'Bone02'}
RELABEL = {}
