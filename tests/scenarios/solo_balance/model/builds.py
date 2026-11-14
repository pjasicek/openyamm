"""Focused solo builds against MAW's expected character (devdocs/solo_action/BALANCE_AND_TALENTS.md section 3.7).

Each build: the solo's level from five times the bank's experience, its skill points spent on 2-4 core skills first
(MAW's raise cost s per level, racial +3 + 10 %), Alchemy for buff potions (a party of one gets Alchemy's mastery at
1/4/7/10 whatever the class), gear of the content's level (best of five times the drops) or crafted (item power raised
to the solo's level with Crafting Cubes), buffs from potions brewed at the content's reagent level or from its own
auras, and class factors measured in the game (classes_late.yml, classes_endgame.yml: damage and HP against the
Champion of the same test stage)."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mawmodel import *
from sim import fight, MONCD, SWING, PACK

# Measured in the game (party_attack / hp show, late and endgame test stages), relative to the Champion. Damage is per
# second against the same target; casters' figures are their best single-target spell (cast_spell batches).
CLASS = {
    #                 damage (late, endgame)  HP (late, endgame)  regeneration mastery
    'champion':      dict(dmg=(1.00, 1.00), hp=(1.00, 1.00), regen=None),
    'minotaur_dual': dict(dmg=(1.78, 1.05), hp=(1.32, 1.09), regen='E'),
    'minotaur_one':  dict(dmg=(1.12, 0.63), hp=(1.32, 1.09), regen='E'),
    'seraph_2h':     dict(dmg=(0.79, 0.88), hp=(0.39, 0.35), regen=None),
    'troll':         dict(dmg=(0.66, 0.62), hp=(1.34, 1.42), regen='G'),
    'vampire':       dict(dmg=(1.02, 0.69), hp=(0.52, 0.48), regen='G'),
    'dragon_claws':  dict(dmg=(0.44, 0.15), hp=(1.10, 1.13), regen='G'),
    'archer':        dict(dmg=(0.79, 0.30), hp=(0.56, 0.53), regen=None),   # melee measured; bow see doc
    'archmage':      dict(dmg=(2.39, 3.17), hp=(0.25, 0.35), regen=None),   # Incinerate
    'shaman':        dict(dmg=(1.47, 1.46), hp=(0.30, 0.27), regen=None),   # Marabou melee
    'elementalist':  dict(dmg=(2.39, 3.17), hp=(0.18, 0.13), regen=None),   # assumed ArchMage-like spells
    'priest':        dict(dmg=(1.04, 0.85), hp=(0.38, 0.32), regen=None),   # Light Bolt
    'monk':          dict(dmg=(1.90, 1.29), hp=(1.09, 0.83), regen='E'),
    'death_knight':  dict(dmg=(1.29, 1.69), hp=(0.57, 0.45), regen='E'),
}
CHAMPION_HP_OVER_MODEL = 1.74   # measured Champion 6,461 HP against the model's 3,707 for the same level, skill, gear

# Fireball per target over the best single-target spell, measured: late 518/1.99 s vs 1,488/2.24 s, endgame alike
FIREBALL_SHARE = 0.39


def potion_power(Lm, alchemy):
    """Reagents dropped at about half the bank level (AL:683-684), tier-5 base 30; GM Alchemy adds 2 per point."""
    B = Lm/2
    reagent = min(30*(1 + B*0.0125) + 0.75*B, 255)
    return min(reagent + 2*alchemy, 500)


def potion_buffs(P, which=('haste', 'heroism', 'bless', 'stoneskin', 'shield', 'resist', 'dotg')):
    """A potion acts as a Master caster with s = 50(f - 1) (70 for Day of the Gods), level 0.5 P f (CLASSES_SPELLS §3.6)."""
    f = 0.75 + 0.75*min(P, 200)/200
    s, lvl = 50*(f - 1), 0.5*P*f
    return {b: ((70*(f - 1)) if b == 'dotg' else s, lvl) for b in which}


def scroll_buffs(which=('haste', 'heroism', 'bless', 'stoneskin', 'shield', 'resist', 'dotg')):
    """Scroll, pedestal and temple auras: skill 7, Master, level 40 (MawSpellRules.cpp:1249)."""
    return {b: (7, 40) for b in which}


def points_to_level(p):
    return (math.sqrt(1 + 8*(p + 1)) - 1)/2


def level_cost(s):
    return max(s*(s + 1)/2 - 1, 0)


def allocate(budget, core, fixed):
    """Fixed skills (name: level) first, the rest spread evenly over the core skills."""
    left = budget - sum(level_cost(v) for v in fixed.values())
    x = points_to_level(max(left, 0)/len(core))
    out = dict(fixed); out.update({c: x for c in core})
    return out


def class_factor(cls, key, Lc):
    a, b = CLASS[cls][key]
    t = min(max((Lc - 100)/100, 0), 1)
    return a + (b - a)*t


def build(name, Lm, cls, core, armour=True, own_buffs=None, gear='content', buffs='potions', racial=None,
          extra=None):
    m = Model.preset(name, 1)
    Lc = level_for_exp(5*exp_for_level(Lm))
    budget = m.skill_points(Lc)
    alchemy = min(10 + Lm/4, 60) if buffs == 'potions' else 0
    fixed = {'Alchemy': alchemy} if alchemy else {}
    if extra: fixed.update(extra)
    sk = allocate(budget, core, fixed)
    x = sk[core[0]]
    weapon = x + (3 + x/10 if racial == core[0] else 0)
    arms = sk.get('Armsmaster', 0.5*x)
    arm = sk.get('Armour', 0.6*x) if armour else 0
    bb = sk.get('Bodybuilding', 0.5*x)
    if buffs == 'potions':
        bsrc = potion_buffs(potion_power(Lm, alchemy))
    elif buffs == 'scrolls':
        bsrc = scroll_buffs()
    elif buffs == 'party':
        bsrc = None
    else:
        bsrc = {}
    if own_buffs and isinstance(bsrc, dict):  # its own auras at its school skill, where stronger
        for b in own_buffs:
            bsrc[b] = max(bsrc.get(b, (-99, 0)), (x, Lc))
    geared = min(m.geared(Lm, drop_mult=5), 1.0) if gear != 'pimped' else 0.9
    item_level = Lc if gear in ('crafted', 'pimped') else Lm
    c = m.char(Lc, skill=weapon, gear_level=Lm, item_level=item_level, geared=geared, buffs=bsrc, vs_level=Lm,
               arms_skill=arms, arms_explicit=True, armor_skill=arm if armour else 0.0001, bb_skill=bb)
    e = m.expected_char(Lm)
    cf_d = class_factor(cls, 'dmg', Lc); cf_h = class_factor(cls, 'hp', Lc)*CHAMPION_HP_OVER_MODEL
    rp = c['power']/e['power']*cf_d
    rv = c['vitality']/(e['vitality']/e['cover'])*cf_h
    regen = 0.0
    if CLASS[cls]['regen']:
        r = sk.get('Regeneration', 0.6*x) + (3 + 0.06*x if cls == 'troll' else 0)
        rate = {'E': 0.075, 'M': 0.10, 'G': 0.10}[CLASS[cls]['regen']]
        full = c['health']*cf_h
        regen = rate*math.sqrt(Model.preset(name, 5).expected_char(max(r, 1)**1.4)['health']*full)/full
    return dict(Lc=Lc, skills=sk, weapon=weapon, rp=rp, rv=rv, regen=regen, health=c['health']*cf_h,
                P=potion_power(Lm, alchemy) if buffs == 'potions' else 0)


BUILDS = [
    # label, class, core skills (first is the attack skill), armour, own auras, racial, extra fixed skills
    ('Minotaur, two 2H axes', 'minotaur_dual', ['Axe', 'Armsmaster', 'Bodybuilding'], True, None, 'Axe', None),
    ('Knight, sword and shield', 'champion', ['Sword', 'Shield', 'Armsmaster'], True, None, None, None),
    ('Seraph, two-handed sword', 'seraph_2h', ['Sword', 'Armsmaster', 'Light'], True,
     ('bless', 'heroism', 'dotg'), None, None),
    ('Troll (Regeneration)', 'troll', ['Mace', 'Regeneration', 'Bodybuilding'], True, None, 'Mace', None),
    ('Vampire (Regeneration)', 'vampire', ['Sword', 'Regeneration', 'Dark'], True, None, None, None),
    ('Dragon (claws, no breath)', 'dragon_claws', ['Unarmed', 'DragonAbility', 'Regeneration'], False, None, None, None),
    ('Archer (melee measured)', 'archer', ['Bow', 'Armsmaster', 'Dodging'], True, None, None, None),
    ('Arch Mage, Fire', 'archmage', ['Fire', 'Learning', 'Meditation'], False,
     ('haste', 'resist'), None, None),
    ('Shaman (melee)', 'shaman', ['Staff', 'Air', 'Learning'], True, ('haste', 'stoneskin', 'resist'), None, None),
    ('Elementalist', 'elementalist', ['Fire', 'Air', 'Water', 'Earth'], False, ('haste', 'stoneskin', 'resist'),
     None, None),
    ('Priest of Light, healer', 'priest', ['Light', 'Body', 'Spirit', 'Learning'], True,
     ('bless', 'heroism', 'dotg', 'resist'), None, None),
    ('Monk', 'monk', ['Unarmed', 'Dodging', 'Armsmaster'], False, None, None, None),
    ('Death Knight', 'death_knight', ['Sword', 'Dark', 'Armsmaster'], True, None, None, None),
]


def row(name, Lm, b, gear='content', buffs='potions'):
    label, cls, core, armour, own, racial, extra = b
    r = build(name, Lm, cls, core, armour, own, gear, buffs, racial, extra)
    aoe = 1.0
    if cls in ('archmage', 'elementalist'):   # Fireball on the whole group against the best single spell
        aoe = max(1.0, FIREBALL_SHARE*PACK[name])
    # stand-and-trade HP used per average group, with this build's own damage/eHP/regeneration
    stand = fight_custom(name, Lm, r['rp'], r['rv'], r['regen'], aoe)
    party = fight(name, Lm, 'party5')
    return r, aoe, stand, party


def fight_custom(name, Lm, rp, rv, regen, aoe):
    """The fight model with the build's ratios: damage rp and effective HP rv against the expected character, its
    regeneration (share of maximum HP a second). A caster (aoe > 1) takes the better of its single-target spell and
    Fireball on the whole group at FIREBALL_SHARE of that damage per target."""
    from sim import fight as f
    N = PACK[name]
    single = f(name, Lm, 'parity', P=rp, hp_mult=rv, regen=regen)
    if aoe <= 1:
        return single
    area = f(name, Lm, 'parity', P=rp*FIREBALL_SHARE, hp_mult=rv, regen=regen, aoe_targets=int(math.ceil(N)) - 1,
             aoe_share=1.0)
    return area if area['used'] < single['used'] else single


def potions_per_group(name, Lm, r, stand_used):
    """Divine Cure (247): 50 + 35 % of the expected HP at the potion's power, one second of recovery each."""
    if r['P'] <= 0:
        return float('nan')
    heal = 50 + 0.35*Model.preset(name, 5).expected_char(max(r['P'], 1))['health']
    share = heal/r['health']
    return max(stand_used - 0.5, 0)/share   # drink to stay above half


if __name__ == '__main__':
    for name, levels in (('nightmare', (50, 100, 220)), ('madness', (100, 280, 450))):
        party = {L: fight(name, L, 'party5') for L in levels}
        print('=====', name, 'party member HP used per group', {L: round(party[L]['used']*100) for L in levels},
              'party time per group', {L: round(party[L]['ttk'], 1) for L in levels})
        for b in BUILDS:
            cells = []
            for Lm in levels:
                r, aoe, stand, _ = row(name, Lm, b)
                pots = potions_per_group(name, Lm, r, stand['used'])
                cells.append(f"L{Lm}: Lc{r['Lc']:.0f} core {r['skills'][b[2][0]]:.0f} P{r['P']:.0f} dmg x{r['rp']:.2f} eHP x{r['rv']:.2f}"
                             f" aoe x{aoe:.1f} rg {r['regen']*100:.1f}%/s | group {stand['ttk']:.0f}s {min(stand['used'],99)*100:.0f}% "
                             f"pots {pots:.1f}")
            print(f"{b[0]:28} " + ' || '.join(cells))
