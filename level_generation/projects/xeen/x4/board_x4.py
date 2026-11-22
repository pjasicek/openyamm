#!/usr/bin/env python3
"""X4's G1 review board: the MU-3 plan, both MU-4 concepts with their blockouts, the figures against MAPS, the house
list, the edges and the open questions (A5, 2026-11-20).

    board_x4.py [--arrival raw/x4_arrival_vN.png] [--signature raw/x4_signature_vN.png]

Writes output/studio_cal/x4/mockups/board_x4.png (2400 px wide). Figures come from render_x4.py's figures.json.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(_REPO_ROOT, 'output/studio_cal/x4') / 'mockups'
W = 2400
BG = (24, 26, 31)
INK = (232, 232, 232)
DIM = (170, 174, 182)
GOLD = (236, 196, 110)
GOOD = (120, 200, 130)
WARN = (240, 170, 80)


def font(size, bold=False):
    name = 'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'
    return ImageFont.truetype(f'/usr/share/fonts/truetype/dejavu/{name}', size)


def wrap(draw, text, f, width):
    words = text.split()
    lines, line = [], ''
    for w in words:
        t = (line + ' ' + w).strip()
        if draw.textlength(t, font=f) <= width:
            line = t
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def para(draw, xy, text, f, width, fill=INK, gap=5):
    x, y = xy
    for line in wrap(draw, text, f, width):
        draw.text((x, y), line, font=f, fill=fill)
        y += f.size + gap
    return y


def latest(view):
    found = sorted((HERE / 'raw').glob(f'x4_{view}_v*.png'), key=lambda p: int(p.stem.split('_v')[-1]))
    return found[-1] if found else None


def paste_fit(board, img, box):
    x, y, w, h = box
    im = img.copy()
    im.thumbnail((w, h), Image.LANCZOS)
    board.paste(im, (x, y))
    return im.size


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arrival')
    parser.add_argument('--signature')
    args = parser.parse_args()
    fig = json.loads((HERE / 'figures.json').read_text())
    H = 3200
    board = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(board)
    d.text((24, 18), 'X4 Burlock Savannah: G1 review (MU-3 plan, MU-4 concepts)', font=font(40, True), fill=INK)
    d.text((24, 68), 'Act II, party 11 to 15, monsters 10 to 30. A5, 2026-11-20. No geometry yet: approve the '
                     'layout, scale and density before the map is built.', font=font(22), fill=DIM)

    # the plan
    plan = Image.open(HERE / 'plan_x4.png').convert('RGB')
    pw, ph = paste_fit(board, plan, (20, 110, 1180, 1400))
    d.text((24, 110 + ph + 8), 'MU-3 plan, to scale (devdocs/xeen/briefs/x4/L1/sketch.yml)', font=font(20, True),
           fill=GOLD)

    # town details from the 2x drawing (24 px per cell, 64 px margin)
    big = Image.open(HERE / 'plan_x4_2x.png').convert('RGB')
    s, o = 24, 64
    crops = [('Castle Burlock and its village, the lists', (52, 41, 77, 64)),
             ("Asp: the well's pedestal ring, the rule stone, XD-25", (33, 78, 52, 93))]
    ty = 110 + ph + 44
    tx = 20
    crop_bottom = ty
    for title, (x0, y0, x1, y1) in crops:
        crop = big.crop((o + x0 * s, o + y0 * s, o + x1 * s, o + y1 * s))
        cw, ch = paste_fit(board, crop, (tx, ty + 30, 575, 470))
        d.text((tx, ty), title, font=font(19, True), fill=GOLD)
        crop_bottom = max(crop_bottom, ty + 30 + ch)
        tx += 600

    # concepts with their blockouts
    concepts_bottom = 0
    for i, view in enumerate(['arrival', 'signature']):
        path = Path(getattr(args, view)) if getattr(args, view) else latest(view)
        y = 110 + i * 860
        title = {'arrival': 'MU-4 arrival view: from X2\'s road at [96, 107], looking north-west up the river valley',
                 'signature': 'MU-4 signature view: Castle Burlock over the jousting lists, the Gargoyle Range behind'}[view]
        d.text((1220, y), title, font=font(20, True), fill=GOLD)
        if path and path.exists():
            img = Image.open(path).convert('RGB')
            cw, ch = paste_fit(board, img, (1220, y + 32, 1160, 774))
            note = f'Codex concept: {path.name}'
        else:
            cw, ch = 1160, 774
            d.rectangle((1220, y + 32, 1220 + cw, y + 32 + ch), outline=DIM, width=2)
            d.text((1240, y + 60), 'concept pending', font=font(28), fill=DIM)
            note = 'no concept yet'
        blk = Image.open(HERE / f'blockout_{view}.png').convert('RGB')
        blk.thumbnail((330, 220), Image.LANCZOS)
        bx, by = 1220 + 10, y + 32 + ch - blk.size[1] - 10
        d.rectangle((bx - 3, by - 3, bx + blk.size[0] + 2, by + blk.size[1] + 2), fill=(255, 255, 255))
        board.paste(blk, (bx, by))
        concepts_bottom = max(concepts_bottom, y + 32 + ch + 30)
        d.text((1220, y + 32 + ch + 6), note + '; inset: the plan\'s blockout from the same camera (composition '
               'reference)', font=font(17), fill=DIM)

    # the figures table
    y0 = max(crop_bottom, concepts_bottom) + 40
    d.text((24, y0), 'Measured figures against MAPS', font=font(26, True), fill=INK)
    ff = fig['first_fight']
    areas = fig['areas']
    rows = [
        ('Obelisk', 'exactly 1', '1 (knoll north of the desert road)', True),
        ('Interaction devices', '>= 4 kinds, 1 permanent', 'wells, fountain, stat challenge, shrine, quintain, '
                                                          'pedestals; permanent: Olympian Fountain, lists, shrine', True),
        ('Points of interest', '30-40 (town and wilderness)', f'{fig["poi_count"]} (signposts 5; town wells, '
                                                                'mirrors and NPCs count)', True),
        ('POI spacing', '1,300-2,600 apart', f'nearest neighbour median {fig["poi_nn_median"]:,} '
                                             f'({fig["poi_nn_min"]:,}-{fig["poi_nn_max"]:,}): see question 1', False),
        ('Dungeon entrances', '3-6', '4: XD-07, XD-25, XD-26 (+ its sky-crack exit), XD-02 west adit', True),
        ('Outdoor chests', '4-10, each with a reason', f'{fig["chests"]} (camps 3, ruins and wrecks 7)', True),
        ('Spawn markers', '45-70', f'{fig["markers"]}', True),
        ('Hostiles at load', '135 +-15 %', f'{fig["hostiles"]:.1f} expected ({fig["hostiles_markers"]:.1f} from markers + '
                                           f'{fig["hostiles_placed"]} placed)', True),
        ('Kill XP per member', '14.0k +-15 %', f'{fig["kill_xp_member"]}k (Dif mix of balance.py)', True),
        ('Encounter areas', '3-8, each 6-30 of 4,096²', f'{len(areas)}: ' + ', '.join(
            f'{a["cells_4096"]}' for a in areas.values()), True),
        ('Quiet land', '>= 1/3 of the land', f'{fig["quiet_share"] * 100:.0f} %', True),
        ('First fight from arrivals', '2,000-6,000', f'X2 {ff["entrance:x2_road"]:,}, X3 {ff["entrance:x3_road"]:,}, '
                                                     f'X6 {ff["entrance:west_road"]:,}, X7 {ff["entrance:east_road"]:,}, '
                                                     f'landing {ff["entrance:river_landing"]:,}, Travel Pit '
                                                     f'{ff["entrance:asp_travel_pit"]:,}', True),
        ('Roads', '1-4 % of the land', f'{fig["road_share"] * 100:.1f} % road tiles (+ {fig["lane_share"] * 100:.1f} % '
                                       'lanes)', True),
        ('Height range', '>= 2,500', f'{fig["height_range"][0]:,}-{fig["height_range"][1]:,} = '
                                     f'{fig["height_span"]:,}', True),
        ('Empty stretches', 'none over 6,000', f'farthest land from a place or fight {fig["farthest_from_place"]:,}; '
                                               f'{fig["far_share_3000"] * 100:.0f} % over 3,000', True),
        ('Town footprint', 'compact (Steadwick, Alvar)', 'Burlock village 14 x 12 cells (7.2k x 6.1k), 14 houses + '
                                                         'castle, 8.3 per 100 cells; Asp 17 x 13 (8.7k x 6.7k), 16, '
                                                         '7.2 (shipped 3.6-11.2)', True),
    ]
    cols = [(24, 300), (330, 330), (670, 500)]
    y = y0 + 44
    for cx, (head) in zip([c[0] for c in cols], ['Figure', 'MAPS target', 'Plan']):
        d.text((cx, y), head, font=font(19, True), fill=GOLD)
    y += 30
    f = font(18)
    for name, target, value, ok in rows:
        top = y
        a = para(d, (cols[0][0], y), name, f, cols[0][1] - 10)
        b = para(d, (cols[1][0], y), target, f, cols[1][1] - 10, fill=DIM)
        c = para(d, (cols[2][0], y), value, f, cols[2][1], fill=GOOD if ok else WARN)
        y = max(a, b, c) + 6
        d.line((24, y - 3, 1180, y - 3), fill=(52, 56, 64))

    # houses and edges
    x1 = 1220
    y = y0
    d.text((x1, y), "Houses (A4's x4.yml ids)", font=font(26, True), fill=INK)
    y += 42
    f = font(18)
    houses = [
        ("Castle Burlock's village (no title needed)", "4151 Royal Armoury, 4152 Plate and Mail, 4153 Chapel of the "
         "Crown, 4154 The King's Lists (training 40), 4155 Royal Stables (routes 408-410), 4156 The Jousting Pig, "
         "4157 mirror (TP anchor), homes 4158-4165."),
        ('The savannah', "4166 Carlawna's Hut (range foot), 4167 Falagar's Hut (lava shoulder). Outdoor NPCs: "
         "4301 Adam and 4302 Eve by Asp's well, 4320 Joe the Merchant at his caravan, 4321 the Autumn Druid."),
        ('Asp (cursed)', '4170 Travel Pit (routes 411, 412) and 4171 Roadside Shrine at the east edge, 4172 Sarah '
         'Slither: open from day one. With q-c5.done: 4173 Snake Oil, 4174 Scale House, 4175 Earth and 4176 Body '
         'guilds, 4177 mirror, homes 4178-4186.'),
    ]
    for head, text in houses:
        d.text((x1, y), head, font=font(18, True), fill=GOLD)
        y = para(d, (x1, y + 24), text, f, 560) + 8
    x2 = 1810
    y = y0
    d.text((x2, y), 'Edges and neighbours', font=font(26, True), fill=INK)
    y += 42
    edges = [
        'South, x 36 (west half): the Asp road to X3 Lifeforce Lagoon; level span 30-42 at 1,050. X3 picks its own '
        'north crossing.',
        "South, x 79: the river leaves for X2 (X2's north_river enters at its x 30, level 576).",
        "South, x 96 (east half): the Rivercity road; level span 90-102 at 1,150, as X2's north span 58-74 "
        "(its road at x 67, sealed 'bridge out' today).",
        'West, y 60: the desert road to X6 (7 days). East, y 66: the Firestone road to X7 (5 days), the lava '
        'fields north of it.',
        'North: the world rim. The Gargoyle Range breaks off in a cliff at y 24 above water at 0.',
        "Travel: Burlock's stables to Vertigo, Rivercity, Asp; the Travel Pit to Burlock, Rivercity; "
        "Nystor's boat after Q-C23; the XD-02 adit to X1 after M3's winch.",
    ]
    for text in edges:
        y = para(d, (x2, y), '- ' + text, f, 560) + 6

    # D-4 and open questions
    y = max(y, y0 + 560)
    d.text((x1, y), 'Decision D-4 on the plan', font=font(24, True), fill=INK)
    y += 38
    d4 = [
        "Asp: eight two-colour pedestals in the cells round the well; red at the south-west one and every second "
        "one; the rule stone with the rhyme beside the XD-25 stair; Adam and Eve just off the ring.",
        "XD-07's throne fall lands at ground + 1,000 (about 2,900) beside the castle's west tower, outside the walls.",
        "XD-26's sky-crack ledge at about 3,300 on Gargoyle Peak, above the eyrie mouth (1,900).",
    ]
    for text in d4:
        y = para(d, (x1, y), '- ' + text, f, 1150) + 4
    y += 14
    d.text((x1, y), 'Open questions for you', font=font(24, True), fill=WARN)
    y += 38
    qs = [
        "1. POI spacing: MAPS asks 1,300-2,600 between POIs, but 30-40 POIs on a 90-cell square sit about 5,000 "
        "apart. Add about 20 small devices (X1 went to 52), or keep 38 and judge by the 6,000 rule (met: 5,100)?",
        "2. Signature view: the castle over the lists (drawn), or the falls under the range, or the rim seen from "
        "the sky-crack ledge?",
        "3. The castle on a rise at 1,900, 600 over its village behind a 450 step: right for XD-07's gate?",
        "4. Hostile renegade knights in the jousting fields while the King's men are friendly: keep, or another "
        "family for slot 1?",
        "5. The lava fields are only 9 cells inside the playable bounds (x 100-109): enough, or widen the box east?",
    ]
    for text in qs:
        y = para(d, (x1, y), text, f, 1150) + 4
    board = board.crop((0, 0, W, min(H, y + 30)))
    board.save(HERE / 'board_x4.png')
    print('board', board.size)


if __name__ == '__main__':
    main()
