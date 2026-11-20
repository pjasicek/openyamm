#!/usr/bin/env python3
"""Write integration/actors.yml, the staged bindings of the Nobles' rows (hesper_stage/monsters.yml names an entry):
one model export/hes_noble.glb (the winged body + carapace, seven skin variants, every row's clip set), the weapons and
gear as attachments on their sockets; the source DemonFly scale 130 times the design scale (data/make_monster_tables.py);
events measured on the clips (work/events_<set>.json, probe_events.py). Args: none"""
import json, os
import yaml


class NoAlias(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BURN = {'type': 'burn', 'start': 0.0, 'end': 0.9375, 'char_width': 0.16, 'edge_width': 0.035, 'fire_width': 0.3,
        'color': [1.0, 0.55, 0.18], 'brightness': 2.4, 'flames_per_second': 220, 'flame_size': 24,
        'flame_color': [255, 170, 70], 'light': {'color': [255, 170, 90], 'radius': 450}}
part = lambda stem, node: {'model': f'worlds/hesper/models/{stem}.glb', 'node': node}


EV = json.load(open(os.path.join(HERE, 'work', 'events.json')))
STRIDES = json.load(open(os.path.join(HERE, 'work', 'strides.json')))
LOOK = {'nodes': ['B_Neck', 'B_Head'], 'max_yaw_degrees': 45, 'max_pitch_degrees': 25}   # (the game requires both limits)


def roles(prefix, grounded=False):
    """clip roles: a flying set's flight loop stands, walks, runs and fidgets; a grounded set has its own"""
    if grounded:
        c = {'standing': f'{prefix}_Standing', 'walking': f'{prefix}_Walking', 'fidget': f'{prefix}_Standing'}
    else:
        c = {'standing': f'{prefix}_Flight', 'walking': f'{prefix}_Flight', 'fidget': f'{prefix}_Flight'}
    c.update({'attack_melee': f'{prefix}_AttackMelee', 'attack_ranged': f'{prefix}_AttackRanged', 'hit': f'{prefix}_Hit',
              'dying': f'{prefix}_Death', 'dead': f'{prefix}_Dead'})
    return c


def row(descriptor, skin, scale, prefix, sockets, release, attachments, script=None, grounded=False):
    e = EV[prefix]
    anim = {'cast': f'{prefix}_Cast'}
    if grounded:
        anim.update({'run': f'{prefix}_Running', 'stride_length': STRIDES[f'{prefix}_Walking'],
                     'run_stride_length': STRIDES[f'{prefix}_Running']})
    else:
        anim.update({'run': f'{prefix}_Flight', 'stride_length': 5.6, 'gait_rate': [0.8, 1.5]})
    anim.update({'upper_body_root': 'B_Spine', 'look': LOOK, 'sockets': sockets,
                 'events': {'attack_melee': {'impact': e['attack_melee']['impact']},
                            'attack_ranged': {'impact': e['attack_ranged']['impact'], 'release': release[0]},
                            'cast': {'impact': e['cast']['impact'], 'release': release[1]}}})
    r = {'descriptor': descriptor, 'model': 'worlds/hesper/models/hes_noble.glb', 'skin': skin,
         'scale': round(130 * scale, 4), 'yaw_offset': -1.570796327, 'death_effect': BURN, 'animation': anim,
         'clips': roles(prefix, grounded)}
    if script: r['script_clips'] = script
    r['attachments'] = [part(stem, node) for stem, node in attachments]
    return r


ROWS = [row(f'Noble {t}', s, k, 'Noble', {'palm': 'Palm_L'}, ('palm', 'palm'),
            [('hes_noble_fang', 'Grip_R'), ('hes_noble_sidearm', 'Holster_L')])
        for t, s, k in (('A', 'nb_a', 1.0), ('B', 'nb_b', 1.05), ('C', 'nb_c', 1.1))]
ROWS += [
    row('Lady Ssekh', 'nb_ssekh', 1.15, 'Ssekh', {'palm': 'Palm_L', 'fang': 'Tip_Ssekh_R'}, ('fang', 'palm'),
        [('hes_ssekh_fang_r', 'Grip_R'), ('hes_ssekh_fang_l', 'Grip_L')], {'dive': 'Ssekh_Dive'}),
    row('Lord Mraal', 'nb_mraal', 1.15, 'Mraal', {'blade': 'Blade_Mraal'}, ('blade', 'blade'),
        [('hes_mraal_cleaver', 'Grip_R')], {'cleave': 'Mraal_Cleave'}, grounded=True),
    row('Lord Xith', 'nb_xith', 1.15, 'Xith', {'muzzle': 'Muzzle_Xith'}, ('muzzle', 'muzzle'),
        [('hes_xith_storm_rifle', 'Grip_R')], {'charged_shot': 'Xith_ChargedShot'}),
    row('The Gatekeeper', 'nb_gatekeeper', 1.2, 'Gate', {'muzzle': 'Muzzle_Gate'}, ('muzzle', 'muzzle'),
        [('hes_gate_carbine', 'Grip_R'), ('hes_gate_emitter', 'Emitter_L'), ('hes_gate_gorget', 'Gorget')]),
]
out = os.path.join(HERE, 'integration', 'actors.yml')
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, 'w').write('# The Nobles (hes_nobles_claude): one model, seven skins (MONSTERS.md "Kreegan skin colours", approved\n'
                     '# 2026-10-24); source DemonFly scale 130 x the design scale; burn-away death.\n'
                     + yaml.dump(ROWS, Dumper=NoAlias, sort_keys=False, width=120))
print('PUBLISHED', [r['descriptor'] for r in ROWS])
