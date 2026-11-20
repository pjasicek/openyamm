#!/usr/bin/env python3
"""Rename a Mixamo rig's node names (`mixamorig:Hips`, ...) to the humanoid set's B_* names and back, so the composer
and the probes, which address B_* joints, run on the MM6 female peasant (pfem) and the mage (pmn2). Fingers become
`B_<s>_Finger_<Index1>`, the female's forearm twist bones `B_<s>_ForearmTwist<n>` (so the arm probes see them). Only
node names in the JSON change; animations address nodes by index, so the renamed file animates identically and
renaming back restores the original names (the binary chunk is untouched).

    rename_mixamo.py <in.glb> <out.glb> to_b|from_b
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose  # noqa: E402

P = 'mixamorig:'
MAP = {P + 'Hips': 'B_Pelvis', P + 'Spine': 'B_Spine', P + 'Spine1': 'B_Spine1', P + 'Spine2': 'B_Spine2',
       P + 'Neck': 'B_Neck', P + 'Head': 'B_Head'}
for s, side in (('L', 'Left'), ('R', 'Right')):
    MAP.update({P + f'{side}UpLeg': f'B_{s}_Thigh', P + f'{side}Leg': f'B_{s}_Calf', P + f'{side}Foot': f'B_{s}_Foot',
                P + f'{side}ToeBase': f'B_{s}_Toe0', P + f'{side}Shoulder': f'B_{s}_Clavicle',
                P + f'{side}Arm': f'B_{s}_UpperArm', P + f'{side}ForeArm': f'B_{s}_Forearm',
                P + f'{side}Hand': f'B_{s}_Hand'})
    for finger in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky'):
        for n in range(1, 5):
            MAP[P + f'{side}Hand{finger}{n}'] = f'B_{s}_Finger_{finger}{n}'
    for n in (1, 2):
        MAP[f'{side}ForeArmTwist{n}'] = f'B_{s}_ForearmTwist{n}'


def main():
    src, out, way = sys.argv[1:4]
    table = MAP if way == 'to_b' else {v: k for k, v in MAP.items()}
    glb = glb_pose.Glb(src)
    names = {n.get('name') for n in glb.json['nodes']}
    clash = names & (set(table.values()) - set(table))
    if clash:
        raise SystemExit(f'target names already present: {sorted(clash)}')
    count = 0
    for node in glb.json['nodes']:
        if node.get('name') in table:
            node['name'] = table[node['name']]
            count += 1
    glb.write(out)
    print(f'renamed {count} nodes -> {out}')


if __name__ == '__main__':
    main()
