import sys, math, collections
S = sys.argv[1]
def rnd(x): return math.floor(x + 0.5)
out = []
# weapons
rows = [l.rstrip('\n').split('\t') for l in open(S + '/weapons.tsv')]
hdr = rows[0]; rows = rows[1:]
pcols = ['P0', 'P10', 'P20', 'P40', 'P60', 'P80', 'P100']
idx = [hdr.index(p) for p in pcols]
skills = {'0': 'staff', '1': 'sword', '2': 'dagger', '3': 'axe', '4': 'spear', '5': 'bow', '6': 'mace', '39': 'club'}
combos = collections.OrderedDict()
out.append('weapon_bases:  # id: [name, family, skill, hands, ladder rung, dice count]')
for r in rows:
    hands = '2H' if r[4] == '1' else '1H'
    key = '%s r%s d%s' % (hands, r[5], r[6])
    combos.setdefault(key, [r[i] for i in idx])
    name = r[1].replace('"', '')
    out.append('  %s: ["%s", "%s", %s, %s, %s, %s]' % (r[0], name, r[2], skills[r[3]], hands, r[5], r[6]))
out.append('weapon_damage_by_power:  # "hands rung dice": attack bonus and damage range at item power P (level 5P)')
out.append('  columns: [P0, P10, P20, P40, P60, P80, P100]  # P100 = cap; P120 prints the same as P100')
for k in sorted(combos, key=lambda s: (s[:2], float(s.split()[1][1:]), int(s.split()[2][1:]))):
    out.append('  "%s": [%s]' % (k, ', '.join('"%s"' % v for v in combos[k])))
# armour
arows = [l.rstrip('\n').split('\t') for l in open(S + '/armor.tsv')][1:]
powers = [0, 20, 40, 60, 80, 100, 120]
out.append('armor_bases:  # id: [name, family, slot, base AC, reference AC, AC at P0, P20, P40, P60, P80, P100, P120]')
for r in arows:
    base = int(float(r[5])); ref = int(float(r[6]))
    acs = [base if p == 0 else base + rnd(ref * p / 40) for p in powers]
    # cross-check against Lua output columns P40 (12), P100 (15), P120 (16)
    lua = {40: float(r[11]), 100: float(r[14]), 120: float(r[15])}
    for p, v in lua.items():
        assert acs[powers.index(p)] == int(v), (r, p, v, acs)
    out.append('  %s: ["%s", "%s", %s, %d, %d, %s]' % (r[0], r[1], r[2], r[3], base, ref, ', '.join(map(str, acs))))
# attack speed
base = [('dagger', 60), ('sword', 80), ('mace', 100), ('bow', 100), ('staff', 120), ('spear', 120), ('axe', 140),
        ('blaster', 40)]
levels = [0, 50, 100, 200, 300, 400, 500, 600]
out.append('attack_speed_by_item_level:  # base recovery / 100 as the tooltip prints it; columns are item levels')
out.append('  columns: [%s]' % ', '.join('L%d' % l for l in levels))
for name, b in base:
    for two in (False, True):
        if two and name in ('dagger', 'bow', 'blaster', 'mace'):
            continue
        if not two and name == 'staff':
            continue
        vals = []
        for L in levels:
            s = rnd(b * (0.75 + min(L, 600) / 500) / 10) * 10
            if two:
                s = rnd(s * 1.25 / 10) * 10
            vals.append(s / 100)
        out.append('  %s_%s: [%s]' % (name, '2h' if two else '1h', ', '.join('%g' % v for v in vals)))
print('\n'.join(out))
