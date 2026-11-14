import os, sys, csv; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calib import *
from golden_ratio import spell_ratio
# Archetype modifiers on the 2H melee character (see the doc, section 4.4):
#  archer: no cleave; Volley (Master) = 1 extra target at 60 %; 3 s of free fire before melee contact (outdoors),
#          leather: 0.85 x EHP of the melee build.
#  caster: spell/melee power ratio from MAW's model (golden CSV), area spell hits the whole pack at 50 %;
#          0.55 x HP (Sorcerer 3 HP/level against the model's 9), Mana Shield GM adds SP x efficiency (see doc).
def run_arch(name, Lm, tier, arch, comp=True):
    mod, s, k = build_2h(name, Lm, tier)
    base = dict(P=1.0, hp_mult=1.0, taken=1.0)
    m = mod if comp else base
    if comp:
        m['P'] *= GLOBAL['P']; m['hp_mult'] *= GLOBAL['hp_mult']; m['taken'] *= GLOBAL['taken']
        if tier == 'medium': m['buffs'] = MEDIUM_BUFFS
    N = PACK[name]
    if arch == 'archer':
        m['aoe_targets'] = 1 if (comp and k >= 2) else 0; m['aoe_share'] = 0.6
        m['free_seconds'] = 3.0; m['hp_mult'] = m.get('hp_mult', 1)*0.85
    if arch == 'caster':
        m['P'] = m.get('P', 1)*spell_ratio(name, Lm)
        m['aoe_targets'] = int(N); m['aoe_share'] = 0.5
        m['hp_mult'] = m.get('hp_mult', 1)*0.55
        m['leech'] = 0
    return fight(name, Lm, tier, **m)

if __name__ == '__main__':
    for name, levels in (('nightmare', (20, 100, 220)), ('madness', (50, 200, 450))):
        for Lm in levels:
            for arch in ('2h', 'archer', 'caster'):
                cells = []
                for tier in ('under', 'medium', 'pimped'):
                    a = run_arch(name, Lm, tier, arch, False); c = run_arch(name, Lm, tier, arch, True)
                    cells.append(f"{tier}: {min(a['used'],99.99)*100:5.0f}% -> {min(c['used'],99.99)*100:4.0f}%")
                print(f"{name:9} Lm{Lm:4} {arch:6} " + ' | '.join(cells))
