# Character-grid mockup of the 640x365 bench panel: 1 column = 6 units, 1 row = 13 units.
import sys
W, H = 640, 365
CW, RH = 6, 13
cols, rows = W // CW + 1, H // RH + 1
g = [[' '] * cols for _ in range(rows)]
def c(x): return round(x / CW)
def r(y): return round(y / RH)
def text(x, y, s):
    cx, ry = c(x), r(y)
    for i, ch in enumerate(s):
        if 0 <= cx + i < cols: g[ry][cx + i] = ch
def box(x, y, w, h, label=None):
    x0, y0, x1, y1 = c(x), r(y), c(x + w) - 1, r(y + h) - 1
    for xx in range(x0, x1 + 1):
        g[y0][xx] = '-'; g[y1][xx] = '-'
    for yy in range(y0, y1 + 1):
        g[yy][x0] = '|'; g[yy][x1] = '|'
    for (xx, yy) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)): g[yy][xx] = '+'
    if label:
        for i, ch in enumerate(label[: x1 - x0 - 1]): g[y0 + 1 if y1 > y0 + 1 else y0][x0 + 1 + i] = ch
def button(x, y, w, label):
    x0, x1 = c(x), c(x + w) - 1
    yy = r(y + 6)
    s = '[' + label.center(x1 - x0 - 1) + ']'
    for i, ch in enumerate(s): g[yy][x0 + i] = ch
mode = sys.argv[1]
box(0, 0, W, H)
button(16, 4, 75, 'Alchemy'); button(95, 4, 75, '*Crafting*' if mode == 'craft' else 'Crafting')
text(282, 6, 'W o r k b e n c h')
if mode == 'craft':
    text(20, 24, 'Equipment'); text(150, 24, '38 items')
    text(18, 40, '(Worn)(Packs)(All) ')
    box(16, 53, 196, 20, ' search...')
    box(16, 77, 196, 273)
    rowsl = ['EQUIPPED - Brakus', '>Ancient Longsword    L95 ', ' Primordial Chain M. L90 ', ' Rare Helm           L60 ',
             'EQUIPPED - Ilsa', ' Epic Ring           L85 ', ' Legendary Staff     L99 ', 'PACKS', ' Common Axe          L70 ',
             ' Uncommon Boots      L40 ', ' Map: Temple (3/4)   L210', '  ...']
    for i, s in enumerate(rowsl): text(22, 84 + i * 17 if i < 7 else 84 + i * 17, s)
    text(226, 24, 'Gem: raise the weaker enchant'); text(226, 40, 'Brakus - main hand - needs L85 (ok)')
    box(230, 56, 64, 80, ' item'); text(298, 88, '+'); box(318, 56, 64, 80, ' gem T17'); text(386, 88, '=')
    box(406, 56, 64, 80, ' result')
    text(232, 140, 'Longsword'); text(320, 140, 'x7 owned'); text(408, 140, '+3 Might')
    box(484, 24, 138, 136)
    cmp = ['Before -> After', 'Damage  31-52  =', 'Might   +103 -> +106', '  cap T17: 106 (1H)', 'HP     +88   (cap 106)',
           'Special Infernos  =', 'Quality +14%  =', 'Item lv 475   =', 'Value  91k -> 93k', 'Uses 1 x Asc. Solarstone']
    for i, s in enumerate(cmp): text(490, 30 + i * 13, s)
    button(226, 166, 75, 'Apply'); button(304, 166, 75, 'Apply x2'); button(382, 166, 75, 'Combine')
    button(460, 166, 75, 'Clear'); button(547, 166, 75, 'Close')
    text(226, 198, 'Materials'); text(300, 201, 'whole party - counts')
    text(222, 214, '(All)(Gems)(Special)(Potions)(Maps)')
    box(222, 229, 402, 121)
    for i in range(8):
        for j in range(2):
            x = 225 + i * 47; y = 232 + j * 59
            box(x, y, 44, 56)
    labels = [['T14', 'x9'], ['T15', 'x4'], ['T16', 'x6'], ['*T17', 'x7'], ['Eye', 'x1'], ['Hour', 'x2'], ['Pand', 'x3'], ['Cube', 'x5']]
    for i, (a, b) in enumerate(labels):
        text(228 + i * 47, 245, a); text(228 + i * 47, 271, b)
    labels2 = [['Pearl', 'x1'], ['Orb', 'Lg19'], ['Endl', '+25'], ['Ench', 'p120'], ['', ''], ['', ''], ['', ''], ['', '']]
    for i, (a, b) in enumerate(labels2):
        text(228 + i * 47, 304, a); text(228 + i * 47, 330, b)
else:
    text(20, 24, 'Recipes'); text(150, 24, '87 known')
    text(18, 40, '(Can brew)(All known)')
    box(16, 53, 196, 20, ' search...')
    box(16, 77, 196, 273)
    rowsl = ['BOTTLE + REAGENT', ' Cure Wounds     p62  9', 'NORMAL', ' Hexbane         p58  3', 'EXPERT',
             '>Regeneration    p60 1+2', ' Enchant Item    p60  2', 'MASTER', ' Darkness  p<100 !   1', '  ...']
    for i, s in enumerate(rowsl): text(22, 84 + i * 17, s)
    text(226, 24, 'Regeneration (Expert)'); text(226, 40, 'Alchemist: Ilsa - GM 30 - all recipes known')
    box(230, 56, 64, 80, ' Blue'); text(298, 88, '+'); box(318, 56, 64, 80, ' Green'); text(386, 88, '=')
    box(406, 56, 64, 80, ' result')
    text(232, 140, 'p 58'); text(320, 140, 'p 62'); text(408, 140, 'p 60, 5 uses')
    box(484, 24, 138, 136)
    cmp = ['Regeneration, power 60', 'Regenerates 41 HP/s', 'for 6 h 0 min', '5 charges', 'Needs power: none',
           'Brews: 1 now, 2 more', '  by chaining', 'Better potion: GM', 'Ilsa adds +30 power']
    for i, s in enumerate(cmp): text(490, 30 + i * 13, s)
    button(226, 166, 75, 'Mix'); button(304, 166, 75, 'Mix All'); button(460, 166, 75, 'Clear'); button(547, 166, 75, 'Close')
    text(226, 198, 'Ingredients'); text(300, 201, 'whole party, click or drag to place')
    text(222, 214, '(All)(Potions)(Reagents)')
    box(222, 229, 402, 121)
for line in g: print(''.join(line).rstrip())
