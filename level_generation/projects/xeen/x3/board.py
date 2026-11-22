#!/usr/bin/env python3
"""X3 review board for gate G1 (lane A5): the MU-3 plan, the two MU-4 concepts with their blockouts, the figures
against MAPS, the houses by district, the edges and the open questions, in one PNG.

    python3 level_generation/projects/xeen/x3/board.py [--arrival raw/x3_arrival_v1.png] [--signature raw/...]

Writes output/studio_cal/x3/mockups/board_x3.png (2400 wide).
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
MOCK = pathlib.Path(_REPO_ROOT, 'output/studio_cal/x3') / 'mockups'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
BG = (24, 26, 31)
INK = (232, 232, 228)
DIM = (170, 172, 176)
OK = (110, 200, 120)
WARN = (235, 180, 70)
W = 2400


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)


def fit(img, w):
    return img.resize((w, round(img.height * w / img.width)), Image.LANCZOS)


def text_block(draw, x, y, lines, size=19, gap=6, colour=INK, width=None):
    f = font(size)
    for line in lines:
        if isinstance(line, tuple):
            line, colour_l = line
        else:
            colour_l = colour
        if width:
            words, cur = line.split(' '), ''
            for word in words:
                trial = (cur + ' ' + word).strip()
                if draw.textlength(trial, font=f) > width and cur:
                    draw.text((x, y), cur, font=f, fill=colour_l)
                    y += size + gap
                    cur = '   ' + word
                else:
                    cur = trial
            line = cur
        draw.text((x, y), line, font=f, fill=colour_l)
        y += size + gap
    return y


def table(draw, x, y, rows, widths, size=18, head=True):
    f, fb = font(size), font(size, True)
    for r, row in enumerate(rows):
        cx = x
        lines_max = 1
        cells = []
        for c, (cell, w) in enumerate(zip(row, widths)):
            colour = INK
            if isinstance(cell, tuple):
                cell, colour = cell
            words, cur, lines = str(cell).split(' '), '', []
            for word in words:
                trial = (cur + ' ' + word).strip()
                if draw.textlength(trial, font=f) > w - 12 and cur:
                    lines.append(cur)
                    cur = word
                else:
                    cur = trial
            lines.append(cur)
            cells.append((lines, colour))
            lines_max = max(lines_max, len(lines))
        h = lines_max * (size + 5) + 8
        if r == 0 and head:
            draw.rectangle((x, y, x + sum(widths), y + h), fill=(44, 48, 58))
        elif r % 2 == 0:
            draw.rectangle((x, y, x + sum(widths), y + h), fill=(31, 34, 40))
        for (lines, colour), w in zip(cells, widths):
            for i, line in enumerate(lines):
                draw.text((cx + 6, y + 4 + i * (size + 5)), line, font=fb if (r == 0 and head) else f, fill=colour)
            cx += w
        y += h
    return y


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arrival', default=None)
    parser.add_argument('--signature', default=None)
    args = parser.parse_args()
    fig = json.loads((MOCK / 'figures.json').read_text())
    plan = Image.open(MOCK / 'plan_x3_full.png').convert('RGB')
    plan = fit(plan, 1420)
    concepts = {}
    for view, given in (('arrival', args.arrival), ('signature', args.signature)):
        path = Path(given) if given else None
        if path and not path.is_absolute():
            path = MOCK / path
        concepts[view] = Image.open(path).convert('RGB') if path and path.exists() else None
    H = 3150
    board = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(board)
    d.text((30, 18), 'X3 Lifeforce Lagoon: MU-3 plan and MU-4 concepts for gate G1', font=font(40, True), fill=INK)
    d.text((30, 70), ('Act II castle map (party 13-16). Lane A5, 2026-11-20. No geometry yet: brief '
                      'devdocs/xeen/briefs/x3/L1, drawings output/studio_cal/x3/mockups.'), font=font(21), fill=DIM)
    y0 = 110
    board.paste(plan, (20, y0))
    # concepts on the right
    cx, cw = 1460, 920
    y = y0
    titles = {'arrival': 'MU-4 arrival view: in from X2 on the lagoon road (camera [106, 41], eye 180)',
              'signature': "MU-4 signature view: the causeway to the Tower; Nightshadow in its mist"}
    for view in ('arrival', 'signature'):
        d.text((cx, y), titles[view], font=font(19, True), fill=INK)
        y += 28
        img = concepts[view]
        if img is not None:
            board.paste(fit(img, cw), (cx, y))
            ih = fit(img, cw).height
        else:
            ih = round(cw * 2 / 3)
            d.rectangle((cx, y, cx + cw, y + ih), outline=DIM, width=2)
            d.text((cx + 20, y + 20), 'concept pending (Codex)', font=font(24), fill=DIM)
        bo = fit(Image.open(MOCK / f'blockout_{view}.png').convert('RGB'), 300)
        board.paste(bo, (cx + cw - bo.width - 8, y + ih - bo.height - 8))
        d.rectangle((cx + cw - bo.width - 8, y + ih - bo.height - 8, cx + cw - 8, y + ih - 8), outline=(255, 255, 255),
                    width=2)
        d.text((cx + cw - bo.width - 6, y + ih - bo.height - 30), 'blockout (composition)', font=font(16),
               fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
        y += ih + 22
    # figures table under the plan
    ty = y0 + plan.height + 26
    d.text((30, ty), 'Measured figures against MAPS targets', font=font(26, True), fill=INK)
    ff = fig['first_fight']
    tf = fig['town_fight']
    camp_fight = tf["Ebenezer's camp doors"]
    rows = [
        ('figure', 'MAPS target', 'plan', ''),
        ('obelisk', 'exactly 1', '1, on a knoll in the north vale', ('ok', OK)),
        ('interaction device kinds', '>= 4, one permanent',
         '6: Marsh Well (temp. resistances), Lifeforce Spring (+2 Endurance, permanent), 2 food trees, 3 sundials, '
         'garlic shrine (cure), obelisk', ('ok', OK)),
        ('POI budget', '25-30 (swamp band)',
         f"{fig['pois']} ({fig['pois_in_town']} in Nightshadow, with A3's Q-C7 signs and town well)",
         ('ok', OK) if 25 <= fig['pois'] <= 30 else ('over', WARN)),
        ('POI spacing', '1,300-2,600 apart',
         f"census {fig['census_pois']} with service doors: nearest-neighbour median {fig['poi_nn_median']:,}",
         ('ok', OK)),
        ('dungeon entrances', '3-6', '4: XD-08, XD-11, XD-13, XD-24', ('ok', OK)),
        ('outdoor chests', '4-10, each with a reason', f"{fig['chests']}", ('ok', OK)),
        ('spawn markers', '45-70', f"{fig['markers']} (slots 2-3, 2-4, 2-3 a marker)", ('ok', OK)),
        ('hostiles at load', '135 (MAPS 0)', f"{fig['hostiles']} = markers x mean + {fig['placed']} placed "
                                             "(rangers 7, night bats 8)", ('ok', OK)),
        ('kill XP per member', '14.0k', f"about {fig['kill_xp_member']}k (slot tiers A/B/C 50/35/15)", ('ok', OK)),
        ('encounter areas', '3-8, of 6-30 blocks of 4,096',
         '5: ' + ', '.join(f'{k} {v}' for k, v in fig['area_blocks'].items()) + ' blocks', ('ok', OK)),
        ('quiet land', '>= 1/3 of land', f"{fig['quiet_cell_share']:.0%} of cells, {fig['quiet_block_share']:.0%} "
                                         'of blocks', ('ok', OK)),
        ('first fight from each arrival', '2,000-6,000',
         f"east {ff['east (X2)'][0]:,}, west {ff['west (X5)'][0]:,}, north {ff['north (X4)'][0]:,}", ('ok', OK)),
        ('nearest group to a town door', '(X1: 4,500-6,800)',
         f"Nightshadow {tf['Nightshadow doors']:,}; camp {camp_fight:,}; "
         f"Newcastle gate {tf['Newcastle gate']:,}: a safe base", ('look', WARN)),
        ('roads', '1-4 % of land', f"{fig['road_share']} %", ('ok', OK)),
        ('height range', '>= 2,500', f"land 860-3,450 by the points ({fig['height_min']:,}-{fig['height_max']:,} "
                                     'in the drawing raster)', ('ok', OK)),
        ('no 6,000 stretch', 'without a place or fight', f"farthest land {fig['far_max']:,}; "
                                                         f"{fig['far_share_3000']:.0%} beyond 3,000", ('ok', OK)),
        ('town footprint', 'compact (TOWN_FEEL)',
         f"Nightshadow {fig['ns_buildings']} buildings on {fig['ns_cells']} cells ({fig['ns_per100']} per 100; "
         f"shipped 3.6-11.2), {fig['ns_extent'][0]:,} x {fig['ns_extent'][1]:,}, square 2,560 across", ('ok', OK)),
    ]
    ty = table(d, 30, ty + 40, rows, [270, 260, 780, 90], size=17)
    # right column below the concepts: houses, edges, questions
    ry = y + 4
    d.text((cx, ry), 'Houses (A4 ids, towns/x3.yml)', font=font(24, True), fill=INK)
    ry = text_block(d, cx, ry + 36, [
        ("Ebenezer's camp (open day one): 4101 Ebenezer's Tent (tavern; the deed, M8), 4102 The Camp Shrine "
         "(temple).", INK),
        ("Nightshadow, open day one: 4103 The Moon Guild (21-6; 4104 day hours after q-c7.done), 4105 Du Monay "
         "Manor (the Count's fee).", INK),
        ("Nightshadow after q-c7.done: 4106 Temple of the Dawn, 4107 The Coffin and Candle, 4108 Treasure Trove, "
         "4109 Garlic and Grave Goods, 4110 the mirror (square), 4111 Gnome Home, 4112-4120 nine houses.", INK),
        ("Newcastle: 4121 the mirror at the gate (m11.keep); the keep's houses are XD-13's (4141-4150).", INK),
        ("Mirabeth (NPC 4202) as an actor on her rock off Nightshadow's quay.", INK),
    ], size=17, width=cw)
    ry += 14
    d.text((cx, ry), 'Edges and neighbours', font=font(24, True), fill=INK)
    ry = text_block(d, cx, ry + 36, [
        "East to X2: the road at y 40 (X2's west road [31.5, 40]-[0, 40]); level 1,024 for y 36-46, ridges "
        "2,200-3,200 north and 1,700-2,700 south as X2. X2's flooded sign at [20.6, 39.1] goes when X3 is in.",
        "West to X5: the fen road at y 59 and the Lagoon Water at y 62 (X5's lagoon road and river); fen at 900 for "
        "y 50-104, ridge 1,800-2,600 north of y 50 (X5's Ogre Hills).",
        "North to X4: the north road at x 50 (vale level 1,300 for x 42-58), ridges either side; X4's lane aligns "
        "its south road to x 50.",
        "South: the world rim, a cliff of about 900 at y 104 to the stars (0), as X2 and X5.",
        "X8: falls from the High Magic Clouds land round the Tower (reed shore by the causeway head).",
    ], size=17, width=cw)
    ry += 14
    d.text((cx, ry), 'Open questions for the user', font=font(24, True), fill=WARN)
    qy = text_block(d, cx, ry + 36, [
        "1. Signature view: the causeway to the Tower with Nightshadow in its mist across the water. Keep it, or "
        "prefer Nightshadow's square among the sundials?",
        "2. Newcastle and Ebenezer's camp moved east beside the X2 road (the source has them in C4, the west half), "
        "so the first Act II stop is close to the arrival. Fine?",
        "3. The Tower of High Magic on a rock islet with a causeway (M12's text: 'in the lagoon'; the source puts it "
        "on the north edge). Fine?",
        "4. Should Nightshadow's mist lift once the Count is dead (q-c7.done), as a visible reward? The sheet says "
        "perpetual mist.",
        "5. The camp and the Newcastle gate are a safe base: nearest monsters about 8,300. Keep it, or bring the Crow "
        "Hills' toads closer?",
        "6. The Lifeforce Spring (+2 Endurance once) is new, to give the map its permanent device. That stat, or "
        "another?",
    ], size=17, width=cw)
    board = board.crop((0, 0, W, max(ty, qy) + 30))
    board.save(MOCK / 'board_x3.png')
    print('board', board.size)


if __name__ == '__main__':
    main()
