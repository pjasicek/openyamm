"""Solo run talent trees for the simulation: the current tree (v1, assets_dev/engine/data_tables/talents.yml) and the
proposed tree v2 (devdocs/maw/solo_sim/proposals/TALENT_TREE_V2.md). Pure data and allocation; gen_talent_pool.py
(harness passives) and talentfight.py (actives, new talents, keystones) read it.

allocation(build, level, skills, tree) -> dict(ranks={id: rank}, keystones=[...], points=budget, spent=...)
"""
import math

# Roles and equipment of the builds (gen.py).
MELEE = {'knight_sns', 'knight_2h', 'troll_knight', 'vamp_knight', 'minotaur_dual', 'minotaur_one',
         'minotaur_knight_dual', 'dk_minotaur', 'dk_vampire', 'dk_minotaur_dual', 'troll', 'troll_staff', 'nosferatu',
         'seraph', 'monk', 'assassin', 'shaman', 'dragon'}
RANGED = {'archer'}
CASTER = {'archmage', 'elementalist', 'priest'}
SHIELD = {'knight_sns', 'troll_knight', 'troll', 'seraph', 'priest'}


def role(build):
    return 'melee' if build in MELEE else 'ranged' if build in RANGED else 'caster'


# The trees. requires: mastery of the tree's skill (2 expert, 3 master). needs: another talent's first rank.
V1 = {
    'weapon_training': dict(tree='melee', max=5), 'cleave': dict(tree='melee', max=3, requires=2),
    'whirlwind': dict(tree='melee', max=3, requires=3), 'frenzy': dict(tree='melee', max=3, requires=2),
    'charge': dict(tree='melee', max=3, requires=2), 'shield_wall': dict(tree='melee', max=3, requires=2),
    'marksman': dict(tree='ranged', max=5), 'volley': dict(tree='ranged', max=3, requires=2),
    'disengage': dict(tree='ranged', max=3, requires=2), 'pinning_shot': dict(tree='ranged', max=3, requires=2),
    'steady_aim': dict(tree='ranged', max=3),
    'attunement': dict(tree='caster', max=5), 'blink': dict(tree='caster', max=3, requires=2),
    'spell_surge': dict(tree='caster', max=3, requires=3), 'mana_font': dict(tree='caster', max=5),
    'purify': dict(tree='caster', max=3, requires=2), 'resolve': dict(tree='caster', max=5),
}
# Whirlwind, Purify and Mana Font dropped; Volley became Multishot (user, 2026-11-14).
V2 = dict({k: v for k, v in V1.items() if k not in ('whirlwind', 'volley', 'purify', 'mana_font')}, **{
    'multishot': dict(tree='ranged', max=3, requires=2),
    'sweeping_blows': dict(tree='melee', max=3, requires=2, needs='cleave'),
    'piercing_arrows': dict(tree='ranged', max=3, requires=2),
    'overload': dict(tree='caster', max=3, requires=2),
    'binding_circle': dict(tree='caster', max=3, requires=2),
    'bloodthirst': dict(tree='any', max=3),
})

# What each role buys first. Talents a build cannot use (Shield Wall without a shield) are skipped.
PRIORITY = {
    'v1': {
        'melee': [('cleave', 3), ('frenzy', 3), ('weapon_training', 5), ('shield_wall', 3), ('charge', 3),
                  ('whirlwind', 3)],
        'ranged': [('volley', 3), ('disengage', 3), ('pinning_shot', 3), ('marksman', 5), ('steady_aim', 3)],
        'caster': [('blink', 3), ('mana_font', 5), ('attunement', 5), ('spell_surge', 3), ('resolve', 5)],
    },
    'v2': {
        'melee': [('cleave', 1), ('sweeping_blows', 3), ('bloodthirst', 3), ('cleave', 3), ('frenzy', 3),
                  ('weapon_training', 5), ('shield_wall', 3), ('charge', 3),
                  # points left over go to the other trees' passives (no mastery needed)
                  ('resolve', 5), ('attunement', 5), ('marksman', 5)],
        'ranged': [('multishot', 3), ('piercing_arrows', 3), ('disengage', 3), ('pinning_shot', 3), ('bloodthirst', 3),
                   ('marksman', 5), ('steady_aim', 3), ('resolve', 5), ('attunement', 5), ('weapon_training', 5)],
        'caster': [('binding_circle', 3), ('blink', 3), ('overload', 3), ('attunement', 5),
                   ('bloodthirst', 3), ('spell_surge', 3), ('resolve', 5), ('weapon_training', 5), ('marksman', 5)],
    },
}

# Keystones: slots at these levels; each role's picks in order.
KEYSTONE_LEVELS = [150, 300, 450, 600, 750]
KEYSTONE_ORDER = {'melee': ['oath', 'unbroken', 'warlord'], 'ranged': ['oath', 'deadeye', 'unbroken'],
                  'caster': ['oath', 'archon', 'unbroken']}
# Oaths: (physical taken, magic taken) after the floor, damage multiplier; 'adjacent_free' = only with no monster adjacent.
OATH = {
    'knight_sns': ('Juggernaut', 0.7, 0.7, 1.0), 'knight_2h': ('Juggernaut', 0.7, 0.7, 1.0),
    'troll_knight': ('Juggernaut', 0.7, 0.7, 1.0), 'vamp_knight': ('Juggernaut', 0.7, 0.7, 1.0),
    'minotaur_knight_dual': ('Juggernaut', 0.7, 0.7, 1.0),
    'minotaur_dual': ('Juggernaut', 0.7, 0.7, 1.0), 'minotaur_one': ('Juggernaut', 0.7, 0.7, 1.0),
    'monk': ('Inner Peace', 0.75, 0.75, 1.0),
    # The Death Knight has no Oath: Lichborne was removed (user, 2026-11-14).
    'seraph': ('Sanctified', 0.7, 0.7, 1.0), 'nosferatu': ('Night Lord', 0.7, 0.7, 1.0),
    'troll': ('Unstoppable', 1.0, 1.0, 1.3), 'troll_staff': ('Unstoppable', 1.0, 1.0, 1.3),
    'dragon': ('Elder Wyrm', 1.0, 1.0, 1.3),
    'archer': ('Ranger', 0.7, 0.7, 1.0),   # only while no monster is adjacent (talentfight)
    'shaman': ('Storm Ward', 0.59, 0.59, 1.0), 'assassin': ('Shadow', 0.75, 0.75, 1.0),
    'archmage': ('Elemental Ward', 1.0, 0.55, 1.0), 'elementalist': ('Elemental Ward', 1.0, 0.55, 1.0),
    'priest': ('Elemental Ward', 1.0, 0.55, 1.0),
}
CLAMP = 0.25            # everything after the floor together


LEVELS_PER_POINT = {'v1': 10, 'v2': 15}   # v1: talents.yml as built; v2: one per 15 levels (user, 2026-11-14)


def talent_points(level, tree='v2'):
    """Talent points from levels. The Legend lines were dropped (user, 2026-11-14)."""
    return level//LEVELS_PER_POINT[tree]


def tree_skill_mastery(build, skills):
    """The mastery of the tree's skill: best melee weapon / Armsmaster, Bow, or best magic school (meta skills)."""
    r = role(build)
    if r == 'ranged':
        names = ['Bow']
    elif r == 'caster':
        names = ['FireMagic', 'AirMagic', 'WaterMagic', 'EarthMagic', 'SpiritMagic', 'MindMagic', 'BodyMagic',
                 'LightMagic', 'DarkMagic']
    else:
        names = ['Sword', 'Axe', 'Mace', 'Spear', 'Staff', 'Dagger', 'Unarmed', 'Armsmaster', 'Blaster']
    return max([skills.get(n, [0, 0])[1] for n in names] + [0])


def allocation(build, level, skills, tree='v2', extra_points=0):
    """Ranks and keystones a build has at a level: each role's priority list over that level's points."""
    table = V2 if tree == 'v2' else V1
    r = role(build)
    budget = talent_points(level, tree) + extra_points
    mastery = tree_skill_mastery(build, skills)
    ranks = {}
    spent = 0
    for tid, target in PRIORITY[tree][r]:
        t = table[tid]
        if tid == 'shield_wall' and build not in SHIELD:
            continue
        if t.get('requires', 0) > mastery:
            continue
        if t.get('needs') and not ranks.get(t['needs']):
            continue
        while ranks.get(tid, 0) < min(target, t['max']) and spent < budget:
            ranks[tid] = ranks.get(tid, 0) + 1
            spent += 1
    keystones = []
    if tree == 'v2':
        slots = sum(1 for lv in KEYSTONE_LEVELS if level >= lv)
        keystones = [k for k in KEYSTONE_ORDER[r] if k != 'oath' or build in OATH][:slots]
    return dict(ranks=ranks, keystones=keystones, points=budget, spent=spent, mastery=mastery, tree=tree)


def bodybuilding_cap(final_class_promoted, first_tier, class_cap):
    """Lone Discipline: one mastery above the class cap after the first promotion, Grandmaster after the final."""
    if final_class_promoted:
        return 4
    if first_tier:
        return min(4, class_cap + 1)
    return class_cap


HARNESS_PASSIVES = ('weapon_training', 'marksman', 'attunement', 'resolve', 'mana_font')
