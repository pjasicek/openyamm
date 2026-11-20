import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import *
GLOBAL = dict(P=1.2, hp_mult=1.5, taken=0.8)
MEDIUM_BUFFS = frozenset(['haste', 'heroism', 'bless', 'stoneskin'])

def build_2h(name, Lm, tier):
    m = Model.preset(name, 1)
    s = tiers(m, Lm)[tier]['skill']
    mast = m.mastery_for(s)  # thresholds: normal 4/7/10 here; horizontal NM uses 6/12/20, madness 10/24/40
    th = (6, 12, 20) if name == 'nightmare' else (10, 24, 40)
    tier_open = sum(1 for x in th if s >= x)   # 0..3 tiers open
    depth = {'under': 1, 'medium': 2, 'pimped': 3}[tier]
    k = min(tier_open, depth)
    mod = dict(P=1.0, hp_mult=1.0, taken=1.0, aoe_targets=0, aoe_share=0.0, leech=0.0, opener=1.0, opener_seconds=0.0)
    if k >= 1:  # Expert: Cleave + Brace
        mod['aoe_targets'] = 2; mod['aoe_share'] = min(0.4 + 0.004*s, 0.8)
        mod['taken'] *= 1 - min(0.05 + 0.002*s, 0.25)
    if k >= 2:  # Master: Reaving + Iron Hide
        mod['leech'] = min(0.02 + 0.0004*s, 0.06)
        mod['hp_mult'] *= 1 + min(0.10 + 0.002*s, 0.30)
    if k >= 3:  # GM: Executioner + Last Stand
        mod['P'] *= 1.107
        mod['opener'] = 0.5; mod['opener_seconds'] = 6
    return mod, s, k

def run(name, Lm, tier, glob=True, talents=True, extra=None):
    mod, s, k = build_2h(name, Lm, tier)
    if not talents:
        mod = dict(P=1.0, hp_mult=1.0, taken=1.0)
    if glob:
        mod['P'] = mod.get('P', 1)*GLOBAL['P']; mod['hp_mult'] = mod.get('hp_mult', 1)*GLOBAL['hp_mult']
        mod['taken'] = mod.get('taken', 1)*GLOBAL['taken']
        if tier == 'medium': mod['buffs'] = MEDIUM_BUFFS
    if extra: mod.update(extra)
    if mod.get('opener_seconds'):
        a = fight(name, Lm, tier, **mod); m2 = dict(mod); m2['opener'] = 1.0; m2['opener_seconds'] = 0
        b = fight(name, Lm, tier, **m2); r = dict(a); r['used'] = (a['used']+b['used'])/2; r['ttk'] = (a['ttk']+b['ttk'])/2
    else:
        r = fight(name, Lm, tier, **mod)
    r['skill'] = s; r['tiers'] = k
    return r

if __name__ == '__main__':
    for name, levels in (('nightmare', (20, 50, 100, 150, 220)), ('madness', (25, 50, 100, 200, 300, 450))):
        print('=====', name, 'party5', [round(fight(name, L, 'party5')['used']*100) for L in levels])
        for Lm in levels:
            row = []
            for tier in ('under', 'medium', 'pimped'):
                a = run(name, Lm, tier, False, False)['used']; b = run(name, Lm, tier, True, False)['used']
                c = run(name, Lm, tier, True, True)
                row.append(f"{tier}: {a*100:5.0f}->{b*100:5.0f}->{c['used']*100:4.0f}% (s{c['skill']:.0f} t{c['tiers']} ttk{c['ttk']:4.0f}s)")
            print(f"Lm{Lm:4}  " + ' | '.join(row))
