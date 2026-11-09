"""Write the ready Lancer and Forgemaster runtime bindings."""
from pathlib import Path
import yaml
import sys

P = Path(__file__).resolve().parents[1]
models = 'worlds/hesper/models/'
entries = []
for tier in ('a', 'b', 'c'):
    entry = {'descriptor': 'Lancer '+tier.upper(), 'model': models+'hes_lancer.glb',
             'skin': 'lancer_'+tier, 'scale': 104.8623316, 'yaw_offset': -1.570796327,
             'animation': {'run': 'Lancer_Running', 'stride_length': 1.348, 'run_stride_length': 2.049,
                           'upper_body_root': 'B_Spine',
                           'look': {'nodes': ['B_Neck', 'B_Head'], 'max_yaw_degrees': 45, 'max_pitch_degrees': 25},
                           'sockets': {'muzzle': 'Socket_Muzzle_Left' if tier == 'b' else 'Socket_Muzzle'},
                           'events': {'attack_melee': {'impact': .367},
                                      'attack_ranged': {'impact': .367, 'release': 'muzzle'}}},
             'clips': {key: 'Carbine_'+role for key, role in [('standing','Standing'), ('walking','Walking'),
                       ('attack_melee','Attack'), ('attack_ranged','Attack'), ('hit','Hit'),
                       ('dying','Death'), ('dead','Dead'), ('fidget','Fidget')]},
             'attachments': [{'model': models+('hes_ion_lance_twin.glb' if tier == 'b' else 'hes_ion_lance.glb'),
                              'node': 'Rifle'}]}
    if tier == 'c':
        entry['attachments'].append({'model': models+'hes_lancer_graft.glb', 'node': 'Ancient_Graft'})
    entries.append(entry)
entries.append({'descriptor': 'Forgemaster', 'model': models+'hes_forgemaster.glb', 'skin': 'forgemaster',
                'scale': 157.2934974, 'yaw_offset': -1.570796327,
                'animation': {'run': 'Forge_Running', 'cast': 'Forge_Cast', 'stride_length': 1.217,
                              'run_stride_length': 2.049, 'upper_body_root': 'B_Spine',
                              'look': {'nodes': ['B_Neck','B_Head'], 'max_yaw_degrees': 35, 'max_pitch_degrees': 20},
                              'sockets': {'maul': 'Socket_Maul_Impact', 'cast_hand': 'Socket_Forge_Cast'},
                              'events': {'attack_melee': {'impact': 1.75},
                                         'attack_ranged': {'impact': 1.75, 'release': 'maul'},
                                         'cast': {'impact': .87, 'release': 'cast_hand'}}},
                'clips': {key: 'Forge_'+role for key,role in [('standing','Standing'), ('walking','Walking'),
                          ('attack_melee','Attack'), ('attack_ranged','Attack'), ('hit','Hit'),
                          ('dying','Death'), ('dead','Dead'), ('fidget','Fidget')]},
                'attachments': [{'model': models+'hes_thunder_maul.glb', 'node': 'Thunder_Maul'}]})
assert len({e['descriptor'] for e in entries}) == len(entries)
text = '# Ready Hesper Lancers 10020–10022 and Forgemaster 10110. Project exports; no assets_dev installation.\n'
text += '# Strides measured on the fitted clips; nominal Lancer scale ×1.0, boss ×1.5 (approved concept brief).\n'
(P/'integration/actors.yml').write_text(text+yaml.safe_dump(entries, sort_keys=False, width=110))
