import sys
COLS, ROWS = 107, 29
g = [[' '] * COLS for _ in range(ROWS)]
def put(r, c, s):
    for i, ch in enumerate(s):
        g[r][c + i] = ch
def box(r0, c0, r1, c1, title=''):
    for c in range(c0, c1 + 1):
        g[r0][c] = '-'; g[r1][c] = '-'
    for r in range(r0, r1 + 1):
        g[r][c0] = '|'; g[r][c1] = '|'
    for r, c in ((r0, c0), (r0, c1), (r1, c0), (r1, c1)):
        g[r][c] = '+'
    if title:
        put(r0, c0 + 2, title)
mode = sys.argv[1]
box(0, 0, ROWS - 1, COLS - 1)
put(1, 3, '[ Alchemy  ]'); put(1, 16, '[*Crafting*]' if mode == 'c' else '[ Crafting ]')
put(1, 47, 'Workbench')
box(4, 3, 4, 34) if False else None
put(4, 3, '[ search...                    ]')
box(6, 3, 27, 34)
box(4, 38, 10, 48); put(7, 50, '+'); box(4, 53, 10, 63); put(7, 65, '='); box(4, 68, 10, 78)
box(2, 81, 12, 104)
box(18, 37, 27, 104)
if mode == 'c':
    put(2, 3, 'Equipment'); put(2, 25, '38 items')
    put(3, 3, '(Worn) (Packs) (All)')
    rows = ['WORN - BRAKUS', '>Ancient Longsword    L95', ' Primordial Chain Mail L90', ' Rare Helm             L60',
            'WORN - ILSA', ' Epic Ring             L85', ' Legendary Staff       L99', 'PACKS',
            ' Common Battle Axe     L70', ' Uncommon Boots        L40', ' Dim. Map Temple 3/4  L210', ' ...']
    for i, s in enumerate(rows): put(7 + i, 5, s)
    put(2, 38, 'Gem: raise the weaker enchant')
    put(3, 38, 'Brakus, main hand, needs L85: ok')
    put(5, 40, 'item'); put(5, 55, 'material'); put(5, 70, 'result')
    put(11, 38, 'Longsword'); put(11, 53, 'T17 x7'); put(11, 68, '+3 Might')
    cmp = [' Before -> After', ' Damage 31-52      =', ' Might +103 -> +106', '   T17 cap 106 (1H)', ' HP    +88 (78/106)',
           ' Infernos          =', ' Quality +14%      =', ' Item level 475    =', ' Value 91k -> 93k']
    for i, s in enumerate(cmp): put(3 + i, 81 + 1, s)
    put(13, 38, '[  Apply   ]'); put(13, 51, '[ Apply x2 ]'); put(13, 64, '[ Combine  ]'); put(13, 77, '[  Clear   ]'); put(13, 91, '[  Close   ]')
    put(15, 38, 'Materials    whole party, counts, tap or drag to place')
    put(16, 37, '(All) (Gems) (Special) (Potions) (Maps)')
    labels = [('T14', 'x9'), ('T15', 'x4'), ('T16', 'x6'), ('*T17', 'x7'), ('Eye', 'x1'), ('Hour', 'x2'),
              ('Pand', 'x3'), ('Cube', 'x5'), ('Pearl', 'x1'), ('Orb', 'aff19'), ('Endl', '+25'), ('Ench', 'p120'),
              ('LElem', 'p48'), ('', ''), ('', ''), ('', '')]
    for k, (a, b) in enumerate(labels):
        row = 19 if k < 8 else 23
        col = 39 + (k % 8) * 8
        box(row, col, row + 3, col + 6)
        put(row + 1, col + 1, a); put(row + 2, col + 1, b)
else:
    put(2, 3, 'Recipes'); put(2, 25, '87 known')
    put(3, 3, '(Can brew) (All known)')
    rows = ['BOTTLE + REAGENT', ' Cure Wounds      p62   9', 'NORMAL', ' Hexbane          p58   3', 'EXPERT',
            '>Regeneration     p60 1+2', ' Enchant Item     p60   2', 'MASTER', ' Darkness    p<100 !  1',
            ' Pure Power  step 2 -> 3', ' ...']
    for i, s in enumerate(rows): put(7 + i, 5, s)
    put(2, 38, 'Regeneration (Expert)')
    put(3, 38, 'Ilsa, Alchemy GM 30, all known')
    put(5, 40, 'Blue'); put(5, 55, 'Green'); put(5, 70, 'result')
    put(11, 38, 'power 58'); put(11, 53, 'power 62'); put(11, 68, 'p60, 5 uses')
    cmp = [' Regeneration, p60', ' Heals 41 HP / s', ' for 6 h 0 min', ' 5 charges', ' No power needed',
           ' Brew 1 now, +2 by', '   chaining', ' Stronger than your', '   Regeneration aura']
    for i, s in enumerate(cmp): put(3 + i, 82, s)
    put(13, 38, '[   Mix    ]'); put(13, 51, '[ Mix All  ]'); put(13, 65, '[  Clear   ]'); put(13, 91, '[  Close   ]')
    put(15, 38, 'Ingredients  whole party, click or drag to place')
    put(16, 37, '(All) (Potions) (Reagents)')
for line in g: print(''.join(line))
