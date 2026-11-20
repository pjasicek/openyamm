"""Writes tests/scenarios/solo_balance/classes_<stage>.yml: every class of MAW's test parties (classic, newclasses,
specials, hybrids) at a test stage attacks the same durable C-tier native 40 times (weapon), casters also with an attack
spell; then the effect of a Champion's Potion (Haste, Heroism, Bless) and of buff scrolls on the melee member, a second
two-handed axe in the Minotaur's off hand and a two-handed sword for the Seraph. A measurement for
devdocs/solo_action/BALANCE_AND_TALENTS.md §3.7; model/parse_classes.py reads the output. Run from the repository root."""
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
OUT = ROOT + '/tests/scenarios/solo_balance/'
STAGES = {  # stage: (map, durable C-tier target, potion power)
    'late': ('out05.odm', 192, 150),     # level 100, Nightmare Garrote Gorge: Young Dragon L133, 4,790 HP
    'endgame': ('pbp.odm', 156, 300),    # level 200: Plane Between Planes, Ether Lord L222, 17,630 HP
}
PARTIES = {
    'classic': ['Champion', 'Hero', 'MasterArcher', 'PriestLight', 'ArchMage'],
    'newclasses': ['Archangel', 'LichKing', 'Marabou', 'MasterOfElements', 'Assassin'],
    'specials': ['GreatWyrm', 'Nosferatu', 'MinotaurLord', 'WarTroll', 'Patriarch'],
    'hybrids': ['Master', 'RangerLord', 'ArchDruid', 'Lich', 'PriestDark'],
}
SPELLS = {  # member class: attack spells to try (MAW refuses one the class cannot cast; the report shows a swing)
    'ArchMage': ['Incinerate', 'Fireball', 'Lightning Bolt'], 'MasterOfElements': ['Incinerate', 'Fireball'],
    'Marabou': ['Lightning Bolt', 'Fireball'], 'PriestLight': ['Light Bolt', 'Spirit Lash'],
    'Lich': ['Incinerate', 'Fireball'], 'ArchDruid': ['Incinerate', 'Fireball'], 'PriestDark': ['Toxic Cloud', 'Spirit Lash'],
    'LichKing': ['Incinerate'], 'Hero': ['Spirit Lash'], 'Patriarch': ['Incinerate'],
}
for stage, (mapfile, target, power) in STAGES.items():
    L = ['id: solo_balance.classes_' + stage,
         f'title: "Solo balance - every test-party class at the {stage} stage against one durable target"',
         'world: mm8', 'mode: faithful', 'tags: [solo_balance, maw, measurement]',
         '# A measurement for devdocs/solo_action/BALANCE_AND_TALENTS.md section 3.7, not a regression test. Generated',
         '# by model/gen_classes.py; model/parse_classes.py reads the CONSOLE and "party_attack report" lines.',
         'steps:', '  - new_game_flow:', '      start_map: out01.odm',
         '      ruleset: {id: maw, difficulty: nightmare, progression: horizontal}']
    for party, members in PARTIES.items():
        L += [f'  - console: {{line: "testparty apply {stage} {party}", expect_contains: "items worn"}}',
              f'  - load_map: {{map: {mapfile}}}', '  - console: {line: "actor kill 200000"}',
              f'  # party {party}',
              '  - console: {line: "player sheet"}', '  - console: {line: "hp show"}',
              f'  - spawn_actor: {{monster_id: {target}, near_party: true}}']
        for k, cls in enumerate(members):
            L += [f'  - party_attack: {{actor_index: last, member_index: {k}, count: 40, report: true}}']
            for spell in SPELLS.get(cls, []):
                L += [f'  - party_attack: {{actor_index: last, member_index: {k}, count: 20, attack_spell: {spell}, report: true}}']
        if party == 'specials':  # a second two-handed axe in the Minotaur's off hand (Minotaur Herdsman Axe, level-rolled)
            L += [f'  - grant_item: {{item_id: 40, member_index: 2, roll_level: {stage == "late" and 100 or 200}, seed: 7, equip: off_hand}}',
                  '  - console: {line: "player sheet"}',
                  '  - party_attack: {actor_index: last, member_index: 2, count: 40, report: true}']
        if party == 'newclasses':  # the Seraph with a two-handed sword (Headsman's Reaver), shield taken off
            L += ['  - console: {line: "doll 1 equip offhand 0"}',
                  f'  - grant_item: {{item_id: 10, member_index: 0, roll_level: {stage == "late" and 100 or 200}, seed: 7, equip: main_hand}}',
                  '  - console: {line: "player sheet"}',
                  '  - party_attack: {actor_index: last, member_index: 0, count: 40, report: true}']
        if party == 'classic':  # buff potions and scrolls on the Champion
            L += [f'  - grant_item: {{item_id: 245, member_index: 0, power: {power}}}',
                  '  - use_item: {item_id: 245, member_index: 0}',
                  '  - party_attack: {actor_index: last, member_index: 0, count: 40, report: true}',
                  f'  - grant_item: {{item_id: 251, member_index: 0, power: {power}}}',
                  '  - use_item: {item_id: 251, member_index: 0}',
                  f'  - grant_item: {{item_id: 257, member_index: 0, power: {power}}}',
                  '  - use_item: {item_id: 257, member_index: 0}',
                  '  - console: {line: "player sheet"}', '  - console: {line: "hp show"}',
                  '  - party_attack: {actor_index: last, member_index: 0, count: 40, report: true}']
        L += ['  - console: {line: "actor kill 200000"}']
    # scrolls on a fresh classic party (scroll auras compete with potions, so apart)
    L += [f'  - console: {{line: "testparty apply {stage} classic", expect_contains: "items worn"}}',
          f'  - load_map: {{map: {mapfile}}}', '  - console: {line: "actor kill 200000"}',
          f'  - spawn_actor: {{monster_id: {target}, near_party: true}}',
          '  - party_attack: {actor_index: last, member_index: 0, count: 40, report: true}']
    # Heroism and Bless scrolls (skill 7, Master, level 40), one at a time; Haste was refused in a first run
    for scroll in (350, 345):
        L += [f'  - grant_item: {{item_id: {scroll}, member_index: 0}}', f'  - use_item: {{item_id: {scroll}, member_index: 0}}',
              '  - console: {line: "player sheet"}',
              '  - party_attack: {actor_index: last, member_index: 0, count: 40, report: true}']
    # spells, cast directly at a boss-strong target and read from its hit points (projectiles land later)
    L += ['  - console: {line: "actor kill 200000"}',
          f'  - spawn_actor: {{monster_id: {target}, near_party: true, boss_affix: 14}}']
    for member, spell in ((4, 11), (4, 2), (4, 6), (4, 18), (3, 78)):  # ArchMage Incinerate, Fire Bolt, Fireball,
        L += ['  - console: {line: "actor remaining"}']                   # Lightning Bolt; Priest of Light Light Bolt
        L += [f'  - cast_spell: {{member_index: {member}, spell_id: {spell}, actor_index: last}}'] * 5
        L += ['  - advance_runtime: {seconds: 2}', '  - console: {line: "actor remaining"}', '  - console: {line: "hp full"}']
    open(OUT + f'classes_{stage}.yml', 'w').write('\n'.join(L) + '\n')
print('ok')
