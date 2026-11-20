#!/usr/bin/env python3
"""Rename a Mixamo-named rig's nodes to the humanoid set's B_* names (and back), so the composer and the probes,
which address B_* joints, run on the MM6 Werewolf (Meshy auto-rig: Hips, Spine, Spine01, Spine02, neck, Head,
Left/Right{UpLeg,Leg,Foot,ToeBase,Shoulder,Arm,ForeArm,Hand}). Only node names in the JSON change; animations address
nodes by index, so the renamed file animates identically and renaming back restores the original names.

    rename_rig.py <in.glb> <out.glb> to_b|from_b
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose  # noqa: E402

MAP = {'Hips': 'B_Pelvis', 'Spine': 'B_Spine', 'Spine01': 'B_Spine1', 'Spine02': 'B_Spine2', 'neck': 'B_Neck',
       'Head': 'B_Head'}
for s, side in (('L', 'Left'), ('R', 'Right')):
    MAP.update({f'{side}UpLeg': f'B_{s}_Thigh', f'{side}Leg': f'B_{s}_Calf', f'{side}Foot': f'B_{s}_Foot',
                f'{side}ToeBase': f'B_{s}_Toe0', f'{side}Shoulder': f'B_{s}_Clavicle', f'{side}Arm': f'B_{s}_UpperArm',
                f'{side}ForeArm': f'B_{s}_Forearm', f'{side}Hand': f'B_{s}_Hand'})


def main():
    src, out, way = sys.argv[1:4]
    table = MAP if way == 'to_b' else {v: k for k, v in MAP.items()}
    glb = glb_pose.Glb(src)
    names = {n.get('name') for n in glb.json['nodes']}
    clash = names & set(table.values())
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
