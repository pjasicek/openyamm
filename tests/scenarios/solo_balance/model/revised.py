"""The revised compensation (BALANCE_AND_TALENTS.md §4.0) on the focused builds: R3 HP floor (a party of one has at
least 0.6 of the Champion's HP for its level), R5 native cleave for two-handed weapons (2 more targets at 35 %), R2 solo
potions (Divine Cure heals 35 % of the drinker's own maximum HP)."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import builds
from builds import *
from sim import fight as simfight

TWO_HANDED = {'minotaur_dual', 'seraph_2h', 'troll'}
HP_FLOOR = 0.6

def revised(name, Lm, b):
    label, cls, core, armour, own, racial, extra = b
    saved = dict(builds.CLASS[cls])
    lo = (max(saved['hp'][0], HP_FLOOR), max(saved['hp'][1], HP_FLOOR))
    builds.CLASS[cls] = dict(saved, hp=lo)
    try:
        r = build(name, Lm, cls, core, armour, own, 'content', 'potions', racial, extra)
    finally:
        builds.CLASS[cls] = saved
    if cls in ('archmage', 'elementalist'):
        st = fight_custom(name, Lm, r['rp'], r['rv'], r['regen'], 2.0)
    elif cls in TWO_HANDED:
        st = simfight(name, Lm, 'parity', P=r['rp'], hp_mult=r['rv'], regen=r['regen'], aoe_targets=2, aoe_share=0.35)
    else:
        st = simfight(name, Lm, 'parity', P=r['rp'], hp_mult=r['rv'], regen=r['regen'])
    pots = max(st['used'] - 0.5, 0)/0.35
    return r, st, pots

if __name__ == '__main__':
    for name, levels in (('nightmare', (50, 100, 220)), ('madness', (100, 280, 450))):
        party = {L: simfight(name, L, 'party5') for L in levels}
        print('=====', name)
        for b in BUILDS:
            if b[1] in ('dragon_claws', 'archer'):
                continue
            cells = []
            for Lm in levels:
                r0, aoe, st0, _ = row(name, Lm, b)
                r, st, pots = revised(name, Lm, b)
                cells.append(f"{min(st0['used'],99.99)*100:.0f} % -> {min(st['used'],99.99)*100:.0f} % / {st['ttk']/party[Lm]['ttk']:.1f} x / {pots:.0f}")
            print(f"| {b[0]} | " + ' | '.join(cells) + ' |')
