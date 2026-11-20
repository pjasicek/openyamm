"""Anatomical labels for the Smart Topology v1 pieces (examine_parts.py names, character faces -Y, its left is +X).
Each piece is rigid: 100 % weight on one bone. Head pieces are replaced by the skull-only model."""

HEAD_OLD = ['P01', 'P03', 'P06', 'P31', 'P32', 'P63', 'P64', 'P77']

BONE_OF = {
    # axial
    'P02': 'Hips',                                  # pelvis + sacrum
    'P20': 'Spine', 'P27': 'Spine',                 # lower lumbar vertebrae
    'P22': 'Spine1', 'P21': 'Spine1',               # upper lumbar vertebrae
    'P00': 'Spine2',                                # ribcage, sternum, thoracic spine
    'P07': 'Neck', 'P30': 'Neck', 'P15': 'Neck',    # cervical vertebrae
    'P14': 'Head',                                  # atlas under the skull
    # shoulders: clavicle + scapula
    'P24': 'RightShoulder', 'P33': 'RightShoulder',
    'P28': 'LeftShoulder', 'P34': 'LeftShoulder',
    # arms
    'P16': 'RightArm', 'P13': 'RightForeArm', 'P23': 'RightForeArm',
    'P18': 'LeftArm', 'P12': 'LeftForeArm', 'P25': 'LeftForeArm',
    # right hand: metacarpals on the hand, phalanges per finger (middle proximal is fused into the ring proximal)
    'P57': 'RightHand', 'P59': 'RightHand', 'P48': 'RightHand',
    'P42': 'RightHandThumb1', 'P43': 'RightHandThumb2', 'P74': 'RightHandThumb3',
    'P62': 'RightHandIndex1', 'P36': 'RightHandIndex2', 'P68': 'RightHandIndex3',
    'P44': 'RightHandMiddle2', 'P70': 'RightHandMiddle3',
    'P50': 'RightHandRing1', 'P39': 'RightHandRing2', 'P72': 'RightHandRing3',
    'P55': 'RightHandPinky1', 'P49': 'RightHandPinky2', 'P66': 'RightHandPinky3',
    # left hand
    'P60': 'LeftHand', 'P56': 'LeftHand', 'P47': 'LeftHand',
    'P41': 'LeftHandThumb1', 'P54': 'LeftHandThumb2', 'P73': 'LeftHandThumb3',
    'P58': 'LeftHandIndex1', 'P38': 'LeftHandIndex2', 'P67': 'LeftHandIndex3',
    'P45': 'LeftHandMiddle2', 'P69': 'LeftHandMiddle3',
    'P46': 'LeftHandRing1', 'P35': 'LeftHandRing2', 'P75': 'LeftHandRing3',
    'P52': 'LeftHandPinky1', 'P51': 'LeftHandPinky2', 'P65': 'LeftHandPinky3',
    # legs (femoral heads are separate balls; toes stay on the foot block)
    'P53': 'RightUpLeg', 'P08': 'RightUpLeg', 'P11': 'RightLeg', 'P17': 'RightLeg',
    'P40': 'RightFoot', 'P05': 'RightFoot', 'P29': 'RightFoot', 'P76': 'RightFoot',
    'P61': 'LeftUpLeg', 'P09': 'LeftUpLeg', 'P10': 'LeftLeg', 'P19': 'LeftLeg',
    'P37': 'LeftFoot', 'P04': 'LeftFoot', 'P26': 'LeftFoot', 'P71': 'LeftFoot',
}

# finger chains: (bone, piece giving the joint at its top end and the tail at its bottom end)
FINGERS = {
    'Right': {'Thumb': ['P42', 'P43', 'P74'], 'Index': ['P62', 'P36', 'P68'], 'Middle': ['P50', 'P44', 'P70'],
              'Ring': ['P50', 'P39', 'P72'], 'Pinky': ['P55', 'P49', 'P66']},
    'Left': {'Thumb': ['P41', 'P54', 'P73'], 'Index': ['P58', 'P38', 'P67'], 'Middle': ['P46', 'P45', 'P69'],
             'Ring': ['P46', 'P35', 'P75'], 'Pinky': ['P52', 'P51', 'P65']},
}
