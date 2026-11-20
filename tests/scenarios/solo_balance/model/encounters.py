import os, sys, csv; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calib import *
from montable import load
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
O = ROOT + '/output/solo_balance/'
TSV = {'nightmare': O+'monsters_nightmare_horizontal_solo.tsv', 'madness': O+'monsters_madness_solo.tsv'}
MON = load()
ENC = [  # (label, map, B-tier monster id)
    ('Goblinwatch (MM6), goblin shamans', '6d01.blv', 551),
    ('Shadow Guild Hideout (MM6), ruffians', '6d03.blv', 539),
    ('Ravenshore (MM8), mercenaries', 'out02.odm', 194),
    ("Dragoons' Caverns (MM6), swordsmen", '6d06.blv', 587),
    ("Necromancers' Guild (MM8), necromancers", 'd19.blv', 56),
    ('Garrote Gorge (MM8), dragonettes', 'out05.odm', 191),
    ('Dragon Cave (MM8), flightleaders', 'd17.blv', 71),
    ("Plane of Fire (MM8), fire elementals", 'elemf.odm', 74),
    ("Titans' Stronghold (MM7), storm titans", '7d09.blv', 410),
    ('Colony Zod (MM7), devil warriors', '7d27.blv', 221),
    ('The Hive (MM6), devil masters', 'hive.blv', 500),
    ('Dragon Caves (MM7), blue dragons', 'mdt12.blv', 224),
]
def row(name, mapfile, mid):
    for r in csv.DictReader(open(TSV[name]), delimiter='\t'):
        if r['map'] == mapfile and int(r['monster_id']) == mid:
            return int(r['level']), int(r['hp']), float(r['attack_damage'])

def encounter(name, label, mapfile, mid, boss=False, archetype='2h'):
    L, hp, dmg = row(name, mapfile, mid)
    m = Model.preset(name, 1)
    hpf = hp/m.monster_hp(L); dmgf = dmg/m.monster_dmg(L)
    rec = int(MON[mid]['rec'] or 80); cd = max(0.3, rec/128*2.133333)*1.05
    out = {}
    for tier in ('under', 'medium', 'pimped'):
        for cfg in ('now', 'comp'):
            mod, s, k = build_2h(name, L, tier)
            if cfg == 'now':
                mod = dict(P=1.0, hp_mult=1.0, taken=1.0)
            else:
                mod['P'] *= GLOBAL['P']; mod['hp_mult'] *= GLOBAL['hp_mult']; mod['taken'] *= GLOBAL['taken']
                if tier == 'medium': mod['buffs'] = MEDIUM_BUFFS
            # the GM opener (Last Stand, 60 s) is up for every other pack: average both
            if mod.get('opener_seconds'):
                a = fight(name, L, tier, hp_factor=hpf, dmg_factor=dmgf, moncd=cd, boss=boss, **mod)
                mod2 = dict(mod); mod2['opener'] = 1.0; mod2['opener_seconds'] = 0
                b = fight(name, L, tier, hp_factor=hpf, dmg_factor=dmgf, moncd=cd, boss=boss, **mod2)
                r = dict(a); r['used'] = (a['used']+b['used'])/2; r['ttk'] = (a['ttk']+b['ttk'])/2
            else:
                r = fight(name, L, tier, hp_factor=hpf, dmg_factor=dmgf, moncd=cd, boss=boss, **mod)
            # time to die against the whole pack at once (no kills)
            N = PACK[name]
            r['ttd'] = (1.0)/((N + (0.3 if boss else 0))*(dmgf/(HitsChar[m.d]*r['rv']))/cd)
            out[(tier, cfg)] = r
    return L, hpf, dmgf, cd, out

if __name__ == '__main__':
    for name in ('nightmare', 'madness'):
        print('=====', name)
        for label, mapfile, mid in ENC:
            L, hpf, dmgf, cd, out = encounter(name, label, mapfile, mid)
            cells = []
            for tier in ('under', 'medium', 'pimped'):
                a = out[(tier, 'now')]; c = out[(tier, 'comp')]
                cells.append(f"{tier[0]}: {a['ttk']:4.0f}s/{a['ttd']:4.1f}s {min(a['used'],99.99)*100:5.0f}% -> {c['ttk']:4.0f}s/{c['ttd']:4.1f}s {min(c['used'],99.99)*100:4.0f}%")
            print(f"{label[:38]:38} L{L:4} hp x{hpf:.2f} dmg x{dmgf:.2f} cd {cd:.2f} | " + ' | '.join(cells))
