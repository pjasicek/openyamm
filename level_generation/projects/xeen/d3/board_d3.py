#!/usr/bin/env python3
"""D3's phase 3 review board: the MU-3 plan, both MU-4 concepts with their blockouts, the figures against MAPS, the
houses, the edges and the open questions (A5, 2026-11-20). After level_generation/projects/xeen/x4/board_x4.py.

    board_d3.py [--arrival raw/d3_arrival_vN.png] [--signature raw/d3_signature_vN.png]

Writes output/studio_cal/d3/mockups/board_d3.png (2400 px wide). Figures come from render_d3.py's figures.json.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(_REPO_ROOT, 'output/studio_cal/d3') / 'mockups'
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
    lines, line = [], ''
    for w in text.split():
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
    found = sorted((HERE / 'raw').glob(f'd3_{view}_v*.png'), key=lambda p: int(p.stem.split('_v')[-1]))
    return found[-1] if found else None


def paste_fit(board, img, box):
    x, y, w, h = box
    im = img.copy()
    im.thumbnail((w, h), Image.LANCZOS)
    board.paste(im, (x, y))
    return im.size


QUESTIONS = [
    "1. POI band: MAPS' D3 sheet says 30-40 (town and wilderness); D-20 set 35-55 for X4, the other two-town map, "
    "once service doors count. The census gives {poi} (Sandcaster {sc}, the Crossroads {xr}, the wild {wild}). Keep "
    "{poi} under D-20's 35-55, or cut to about 40 (take the clicks off the 5 signposts and 3 small devices)?",
    "2. Celia and Derek's cottage: A3's q-c22 hook puts it by the Crossroads (drawn, 1,500 from the ring); the "
    "source has it in F4 by Venom Pond. Keep it by the Crossroads?",
    "3. Sandcaster's caravan yard (stables 4611) stands outside the south gate, so the caravan from Castleview does "
    "not bypass the pass (Q-D8); the mirror, Town Portal and Lucio arrive inside and the gates open from inside "
    "(as D1). Keep, or the yard inside the walls?",
    "4. Two forbidden fruit huts (+2 Might and Weak by the river, +2 Intellect and Insane in the Aging Forest, D2's "
    "rule) beside D2's one: keep two, or one?",
    "5. Families above the sheet's A band 20-28: cobras A 30 (MAPS names them 30/38/45) and placed Hell Hornets 35 "
    "(no Hornet Queen 50). Kill XP 37.4k against 34.8k (+7 %). Keep, or cobras Dif 0?",
    "6. D4 crossing at x 88 (D4 is not planned) and an arrival for Lucio's boat back from Olympus "
    "(sandcaster_jetty, A4's d3.yml has none): confirm both.",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arrival')
    parser.add_argument('--signature')
    args = parser.parse_args()
    fig = json.loads((HERE / 'figures.json').read_text())
    inside = lambda c, r: r[0] <= c['at'][0] <= r[2] and r[1] <= c['at'][1] <= r[3]
    n_sc = sum(1 for c in fig['poi_components'] if inside(c, (26, 19, 48, 43)))
    n_xr = sum(1 for c in fig['poi_components'] if inside(c, (55, 39, 65, 49)))
    H = 3400
    board = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(board)
    d.text((24, 18), 'D3 Sandcaster and the Aging Forest: phase 3 review (MU-3 plan, MU-4 concepts)',
           font=font(40, True), fill=INK)
    d.text((24, 68), 'Act III, party 27 to 30, monsters 20 to 45 (A 22-35, C 45). A5, 2026-11-20. No geometry yet: a '
                     'decider approves the layout, scale and density before the map is built.', font=font(22), fill=DIM)
    plan = Image.open(HERE / 'plan_d3.png').convert('RGB')
    pw, ph = paste_fit(board, plan, (20, 110, 1180, 1400))
    d.text((24, 110 + ph + 8), 'MU-3 plan, to scale (devdocs/xeen/briefs/d3/L1/sketch.yml)', font=font(20, True),
           fill=GOLD)
    big = Image.open(HERE / 'plan_d3_2x.png').convert('RGB')
    s, o = 24, 64
    crops = [("Sandcaster: guild row, the square, the quarter (DD-19), DD-18's shaft by the gym, the gates",
              (25, 18, 50, 45)),
             ('The Crossroads: six stalls, six roads; the cottage, Wrath Bridge', (53, 37, 79, 53))]
    ty = 110 + ph + 76
    tx = 20
    crop_bottom = ty
    for title, (x0, y0, x1, y1) in crops:
        crop = big.crop((o + x0 * s, o + y0 * s, o + x1 * s, o + y1 * s))
        cw, ch = paste_fit(board, crop, (tx, ty + 30, 575, 560))
        para(d, (tx, ty - 22), title, font(17, True), 575, fill=GOLD, gap=2)
        crop_bottom = max(crop_bottom, ty + 30 + ch)
        tx += 600
    concepts_bottom = 0
    for i, view in enumerate(['arrival', 'signature']):
        path = Path(getattr(args, view)) if getattr(args, view) else latest(view)
        y = 110 + i * 860
        title = {'arrival': "MU-4 arrival view: from D2's caravan road at [15, 44], looking east-north-east",
                 'signature': 'MU-4 signature view: the River of Wrath falls off the east rim; the glow beyond'}[view]
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
        d.text((1220, y + 32 + ch + 6), note + "; inset: the plan's blockout from the same camera (composition "
               'reference)', font=font(17), fill=DIM)
    y0 = max(crop_bottom, concepts_bottom) + 40
    d.text((24, y0), 'Measured figures against MAPS', font=font(26, True), fill=INK)
    fe = fig['first_fight_edges']
    ta = fig['first_fight_town_arrivals']
    tb = fig['town_buffers']
    areas = fig['areas']
    sc = fig['towns']['town:sandcaster']
    xr = fig['towns']['town:crossroads']
    rows = [
        ('Obelisk', 'exactly 1', "1 (dune knoll outside the east gate: 'Obelisk by Sandcaster', THE)", True),
        ('Interaction devices', '>= 4 kinds, 1 permanent', 'wells, fountains, shrines, fruit huts, cairn, oak; '
                                                          'permanent: fruit huts (+2), Fountain of Youth (Q-D18)', True),
        ('Points of interest', '30-40 (MAPS); 35-55 (D-20)', f'{fig["poi_count"]} by the D-20 census (chained 400, '
                                                             'service doors in): see question 1', True),
        ('POI spacing', '1,300-2,600 apart', f'nearest neighbour median {fig["poi_nn_median"]:,} '
                                             f'({fig["poi_nn_min"]:,}-{fig["poi_nn_max"]:,})', True),
        ('Dungeon entrances', '3-6', '3: DD-18 street shaft (D-27), DD-19 guild gate, DD-07 door (key); sealed '
                                     'until built', True),
        ('Outdoor chests', '4-10, each with a reason', f'{fig["chests"]} (wrecks, a mound, a skeleton, a cart, a '
                                                       'courier, a rope, the Rim Watch)', True),
        ('Spawn markers', '45-70', f'{fig["markers"]}', True),
        ('Hostiles at load', '135', f'{fig["hostiles"]:.1f} ({fig["hostiles_markers"]:.1f} from markers + '
                                    f'{fig["hostiles_placed"]} placed hornets)', True),
        ('Kill XP per member', '34.8k +-15 %', f'{fig["kill_xp_member"]}k (+7 %; Dif 1 mix)', True),
        ('Encounter areas', '3-8, each 6-30 of 4,096²', f'{len(areas)} + 3 nests: ' + ', '.join(
            f'{a["cells_4096"]}' for a in areas.values()), True),
        ('Quiet land', '>= 1/3 of the land', f'{fig["quiet_share"] * 100:.0f} %', True),
        ('First fight, map edges', '2,000-6,000', f'D2 road {fe["entrance:west_road"]:,}, D4 road '
                                                  f'{fe["entrance:north_road"]:,}', True),
        ('Town arrivals (D-15)', 'town buffer 2,500', f'square {ta["entrance:sandcaster_square"]:,}, caravans '
                                                      f'{ta["entrance:sandcaster_stables"]:,} (the jetty departs only, '
                                                      f'D-28); nearest fight to a city '
                                                      f'door {tb["Sandcaster doors"]:,}, to a stall '
                                                      f'{tb["Crossroads stalls"]:,}', True),
        ('Roads', '1-4 % of the land', f'{fig["road_share"] * 100:.1f} % road tiles (+ {fig["lane_share"] * 100:.1f} % '
                                       'lanes)', True),
        ('Height range', '>= 2,500', f'inside the box {fig["height_range_box"][0]:,}-{fig["height_range_box"][1]:,} = '
                                     f'{fig["height_range_box"][1] - fig["height_range_box"][0]:,} (D-28: the Wrath '
                                     'crest, the Howling ridge)', True),
        ('6,000 rule; wild land', 'none over 6,000; <= 0.16', f'farthest land {fig["farthest_from_place"]:,}; '
                                                              f'{fig["far_share_3000"]:.3f} over 3,000', True),
        ('Towns', 'compact', f'Sandcaster {sc["extent"][0] // 512} x {sc["extent"][1] // 512} cells, {sc["buildings"]} '
                             f'buildings, {sc["per_100"]} per 100 cells (shipped 3.6-11.2), {sc["services"]} '
                             f'services; Crossroads {xr["buildings"]} stalls in a ring of radius 2.8', True),
    ]
    cols = [(24, 300), (330, 330), (670, 500)]
    y = y0 + 44
    for cx, head in zip([c[0] for c in cols], ['Figure', 'Target', 'Plan']):
        d.text((cx, y), head, font=font(19, True), fill=GOLD)
    y += 30
    f = font(18)
    for name, target, value, ok in rows:
        a = para(d, (cols[0][0], y), name, f, cols[0][1] - 10)
        b = para(d, (cols[1][0], y), target, f, cols[1][1] - 10, fill=DIM)
        c = para(d, (cols[2][0], y), value, f, cols[2][1], fill=GOOD if ok else WARN)
        y = max(a, b, c) + 6
        d.line((24, y - 3, 1180, y - 3), fill=(52, 56, 64))
    table_bottom = y
    x1 = 1220
    y = y0
    d.text((x1, y), "Houses (A4's d3.yml ids), all on plots", font=font(26, True), fill=INK)
    y += 42
    houses = [
        ('Sandcaster (pass at the gates, Q-D8)', '4601 blades, 4602 armour, 4603 Aladdin, 4604 Vulture Repellant, '
         '4605 temple, 4606 tavern (first inside the south gate), 4607 Barticus\' Gym (training 80) with DD-18\'s '
         'shaft, 4608-4610 Mind, Spirit, Light guilds, 4611 caravans (outside), 4612 mirror (thing), 4649 '
         "Lucio's Jetty on the Sky Stair (m30.done), homes 4618-4640 (Astra, Natasha, the schools ...)."),
        ('The wizard quarter (q-d14.done)', '4613 Guild of Night, 4614 Esoterica, 4615-4617 the three towers; '
         "the guild gate into DD-19 open from the start (q-d14.quarter_gate)."),
        ('The Crossroads and the wild', "4641-4646 the stalls (Caleb's workshop the sixth, Q-D15); 4647 Celia and "
         "Derek's cottage (q-c22.cottage); 4648 Thaddeus's hut by the Fountain of Youth (q-d18.fountain); "
         'Cornelius (5247) outdoors in his glade.'),
    ]
    for head, text in houses:
        d.text((x1, y), head, font=font(18, True), fill=GOLD)
        y = para(d, (x1, y + 24), text, f, 560) + 8
    x2 = 1810
    y2 = y0
    d.text((x2, y2), 'Edges, rims, constraints', font=font(26, True), fill=INK)
    y2 += 42
    edges = [
        "West, y 44: D2's caravan road arrives at the same y (D2 L1 edge:east), level span 32-56 at 1,300; D2's "
        "other spans continued (crags, wooded hills, rim from 104).",
        'North, x 88: the Lakeside road to D4 (D4 aligns to it).',
        "Rims (D-23): east at x 104 with the bright face's glow above, south at y 104 as D1 and D2.",
        'The River of Wrath rises at the Wrath Spring (81, 21) and falls off the east rim at y 64: it touches '
        'no map edge; nothing crosses D2\'s edge.',
        "DD-18 (D-27): a street shaft against Barticus' Gym, the entrance preset \"Descend to the sewer?\", off "
        "the door and lane lines; sealed until A8 gives the inside point.",
        'DD-19 and DD-07 sealed until their maps exist. Sky xeendark1. Textures: the sandcaster kit only, no new.',
    ]
    for text in edges:
        y2 = para(d, (x2, y2), '- ' + text, f, 560) + 6
    y = max(y, y2) + 20
    d.text((x1, y), 'Open questions for the decider', font=font(24, True), fill=WARN)
    y += 38
    for text in QUESTIONS:
        y = para(d, (x1, y), text.format(poi=fig['poi_count'], sc=n_sc, xr=n_xr, wild=fig['poi_count'] - n_sc - n_xr),
                 f, 1150) + 4
    bottom = max(y, table_bottom) + 30
    board = board.crop((0, 0, W, min(H, bottom)))
    board.save(HERE / 'board_d3.png')
    print('board', board.size)


if __name__ == '__main__':
    main()
