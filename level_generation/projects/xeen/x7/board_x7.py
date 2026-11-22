#!/usr/bin/env python3
"""X7's phase 5 review board: the MU-3 plan, both MU-4 concepts with their blockouts, the figures against MAPS, the
people and doors, the edges and the open questions (A5, 2026-11-20). After level_generation/projects/xeen/x6/board_x6.py.

    board_x7.py [--arrival raw/x7_arrival_vN.png] [--signature raw/x7_signature_vN.png]

Writes output/studio_cal/x7/mockups/board_x7.png (2400 px wide). Figures come from render_x7.py's figures.json.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(_REPO_ROOT, 'output/studio_cal/x7') / 'mockups'
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
    found = sorted((HERE / 'raw').glob(f'x7_{view}_v*.png'), key=lambda p: int(p.stem.split('_v')[-1]))
    return found[-1] if found else None


def paste_fit(board, img, box):
    x, y, w, h = box
    im = img.copy()
    im.thumbnail((w, h), Image.LANCZOS)
    board.paste(im, (x, y))
    return im.size


QUESTIONS = [
    "1. The south slopes' band. MAPS: orcs 5-12 (the trap map's safe edge, reached from X1 at level 4-7); x7.yml and "
    "D-5.2 call the slope 'levels 20-30' (Sablewing's Master teaching). Drawn: orcs 5-10 (Dif 1), read 20-30 as the "
    "party band for the teacher. Or the orc warband (16-26) round the west outpost, or both. Rec.: as drawn.",
    "2. Shrine of Fire twice: X4 (built) already has a permanent Shrine of Fire. Drawn: X7's shrine temporary "
    "(daily), the map's permanent device the Well of Speed (+2 Speed, the world's only permanent Speed). Or X7's "
    "permanent (the source's E2 shrine) and X4's made temporary (an X4 rebuild). Rec.: as drawn.",
    "3. Shangri-La's way back (no mirror, no Town Portal, D-5.1): drawn, a cleft east of the Volcano Cave that opens "
    "on q-c26.done; or only through XD-16 every visit (the source). Rec.: the cleft.",
    "4. The Ever-Hot Lava Rock: drawn on the cooled-flow island in D1's lava lake (MAPS), 8 placed Lava Golems (55), "
    "reached from the Gap through hydra country; q-c14's hook text says 'near the crater' (dragon country). Or a "
    "lava pool on the range's south side (safe for Q-C14's level 35). Rec.: the island; A3 rewrites the hook's place.",
    "5. North mix: hydras Dif 3 [1,3] (52 mean), dragons Dif 5 [1,2] (10 % Water 60, 50 % Acid 66, 40 % Fire 75), "
    "8 golems placed; {hostiles} hostiles, {xp}k (MAPS 90, 76.4k). MAPS' 'C 85' is the Frost Dragon tier, kept for "
    "XD-18. Rec.: as drawn.",
    "6. The tax road to the Dragon Cave crosses hydra country (dragons stay {tax:,} away). D-5.2's 'before the first "
    "dragon' read as inside XD-18. Or a keep-clear corridor along the north track. Rec.: as drawn.",
    "7. Signature: the lava cove at the north rim (earned; the falls pour toward the camera, D-35's lesson), or the "
    "whole north from the Gap (safe, falls far and side-on). Rec.: the cove; the Gap as a tour shot.",
    "8. The dwarves' watch: abandoned (x7.yml has no people; a pay chest left behind), or A4 adds one houseless "
    "dwarf lookout with a warning line. Rec.: abandoned.",
    "9. Sky: Cloudside's fair preset with A6's ashen theme and an ash-fall chance (WORLD_DESIGN 4), or MAPS' "
    "ember / plane_fire look. Rec.: fair + ashen + ash fall about 40 % of days.",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arrival')
    parser.add_argument('--signature')
    args = parser.parse_args()
    fig = json.loads((HERE / 'figures.json').read_text())
    H = 3600
    board = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(board)
    d.text((24, 18), 'X7 Mount Firestone: phase 5 review (MU-3 plan, MU-4 concepts)', font=font(40, True), fill=INK)
    d.text((24, 68), 'Act V trap and endgame, party 40 to 55 (the south slopes from level 5); south orcs 5-10, north '
                     '45-75. A5, 2026-11-20. No geometry yet: a decider approves layout, scale and density first.',
           font=font(22), fill=DIM)
    plan = Image.open(HERE / 'plan_x7.png').convert('RGB')
    pw, ph = paste_fit(board, plan, (20, 110, 1180, 1400))
    d.text((24, 110 + ph + 8), 'MU-3 plan, to scale (devdocs/xeen/briefs/x7/L1/sketch.yml)', font=font(20, True),
           fill=GOLD)
    big = Image.open(HERE / 'plan_x7_2x.png').convert('RGB')
    s, o = 24, 64
    crops = [('The north: the lava lake, the Volcano and Dragon Caves, Firestone, the cove', (18, 22, 104, 60)),
             ("The south slopes: the X1 road, the watch, Sablewing's cave, the back gate", (40, 62, 104, 110))]
    ty = 110 + ph + 76
    tx = 20
    crop_bottom = ty
    for title, (x0, y0, x1, y1) in crops:
        crop = big.crop((o + x0 * s, o + y0 * s, o + x1 * s, o + y1 * s))
        cw, ch = paste_fit(board, crop, (tx, ty + 30, 575, 560))
        para(d, (tx, ty - 22), title, font(17, True), 575, fill=GOLD, gap=2)
        crop_bottom = max(crop_bottom, ty + 30 + ch)
        tx += 600
    crop_bottom += 40
    concepts_bottom = 0
    for i, view in enumerate(['arrival', 'signature']):
        path = Path(getattr(args, view)) if getattr(args, view) else latest(view)
        y = 110 + i * 860
        title = {'arrival': "MU-4 arrival view: from X1's north road at [69, 106], looking north-north-east",
                 'signature': "MU-4 signature view: the lava cove's falls into the stars, Mount Firestone above"}[view]
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
    bf = fig['buffers']
    areas = fig['areas']
    kx = fig['kill_xp_by_family_member']
    rows = [
        ('Obelisk', 'exactly 1', "1, on the Gap's north lip (obelisks.x7: SPHINX), safe ground", True),
        ('Interaction devices', '>= 4 kinds, 1 permanent', 'well, shrine, hot spring, cairn, idols, hot rock, '
                                                          'Reflector, outpost to burn; permanent: Well of Speed (+2 '
                                                          'Speed)', True),
        ('Points of interest', '22-28 (MAPS trap band)', f'{fig["poi_count"]} by the D-20 census (chained 400; dungeon '
                                                         'doors in; Sablewing and landmarks out)', True),
        ('POI spacing', '1,300-2,600', f'nearest neighbour median {fig["poi_nn_median"]:,} '
                                       f'({fig["poi_nn_min"]:,}-{fig["poi_nn_max"]:,})', False),
        ('Dungeon entrances', '3-6', '5: XD-16 Volcano Cave, XD-17 cleft (q-c26.done), XD-18 Dragon Cave, FD-04 '
                                     'Dragon Tower, XD-05 back gate (barred from inside); sealed until built', True),
        ('Outdoor chests', '4-10, each with a reason', f'{fig["chests"]}: the watch, the outpost, the orcs\' den, a '
                                                       "miner's cache, a knight, a dragon's hoard, a wallow", True),
        ('Spawn markers', '45-70', f'{fig["markers"]}', True),
        ('Hostiles at load', '90 (trap 90-110)', f'{fig["hostiles"]:.0f}: {fig["hostiles_markers"]:.0f} from markers, '
                                                 f'{fig["hostiles_placed"]} placed (8 golems, 3 orcs)', True),
        ('Kill XP per member', '76.4k +-15 %', f'{fig["kill_xp_member"]}k: dragons {kx["Xeen Dragon"]}k, hydras '
                                              f'{kx["Xeen Hydra"]}k, golems {kx["Lava Golem (placed)"]}k, orcs '
                                              f'{fig["kill_xp_south_member"]}k', True),
        ('Encounter areas', '3-8, each 6-30 of 4,096²', f'{len(areas)}: ' + ', '.join(
            f'{a["cells_4096"]}' for a in areas.values()), True),
        ('Quiet land', '>= 1/3 of the land', f'{fig["quiet_share"] * 100:.0f} % (the range and most of the south)',
         True),
        ('First fight, map edges', '2,000-6,000', f'X1 road {fe["entrance:south_road"]:,}, X4 road '
                                                  f'{fe["entrance:west_road"]:,} (orcs)', True),
        ('Safe south', 'none of the north', f"north monsters from the X1 road {bf['north monsters from the north road']:,}"
                                            f", from the Gap {bf['north monsters from the Gap']:,}; Sablewing "
                                            f"{bf['Sablewing']:,} from any fight", True),
        ('Roads', '1-4 % of the land', f'{fig["road_share"] * 100:.1f} % road (+ {fig["lane_share"] * 100:.1f} % '
                                       'lanes)', True),
        ('Height range', '>= 2,500 inside the box', f'{fig["height_box_field"][0]:,}-{fig["height_box_field"][1]:,} '
                                                    f'= {fig["height_box_span"]:,} on the drawn land (the X4 road to '
                                                    "Firestone's rim)", True),
        ('6,000 rule; wild land', 'none over 6,000; <= 0.16', f'farthest land {fig["farthest_from_place"]:,}; '
                                                              f'{fig["far_share_3000"]:.3f} over 3,000', True),
        ('Textures', 'outdoor cap 120', 'cloudside_town fieldstone (the watch), towers (Dragon Tower), ancient '
                                        '(Reflector), MU-2 X7 ground; new: none named; lava needs a liquid set', True),
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
    d.text((x1, y), 'People and doors', font=font(26, True), fill=INK)
    y += 42
    people = [
        ('Sablewing (4720, D-5.2)', "The Dragon Hermit at his cave mouth under a red crag off the X1 road, on the "
         "safe south slope: Dragon Master. 4,400 from any fight. No houses on X7 (x7.yml)."),
        ('Doors (sealed lines until built)', 'XD-16 [66, 45] facing west between the idols; XD-17 cleft [73, 48] '
         '(q-c26.done); XD-18 [56, 30] facing south in the rim crag, the tax office inside (D-5.2); FD-04 [29, 32] '
         "on the crag over the lava lake; XD-05's back gate [88, 100], barred from inside (110051)."),
        ('Hooks', 'obelisks.x7, q-c14.lava_rock, m37.reflector_fire, x1-tam.back_gate (XD-05), q-c26.done (the cleft); '
         'new map events: the orc outpost (source E2), the idols, the cairn, the hot spring.'),
    ]
    for head, text in people:
        d.text((x1, y), head, font=font(18, True), fill=GOLD)
        y = para(d, (x1, y + 24), text, f, 560) + 8
    x2 = 1810
    y2 = y0
    d.text((x2, y2), 'Edges, rims, air', font=font(26, True), fill=INK)
    y2 += 42
    edges = [
        "South, x 69: X1's north road arrives at the same x (X1 built row 1,600, road 1,856); level span 64-74 at "
        "1,850; X1 reopens its north edge when X7 installs (A5).",
        "West, y 66: X4's Firestone road, level span 60-72 at 1,300; X4's other east spans continued (rim 0-24, lava "
        "fields 24-60, red dwarf hills 72-128).",
        "Rims: north at y 24 (as X4's), east at x 104 (as X1's); the lava cove x 68-78; the Fire corner spit.",
        'Air: fair sky, ashen theme (A6 row exists); ash fall needs a weather row (A1); music 26 (Mount Nighon).',
    ]
    for text in edges:
        y2 = para(d, (x2, y2), '- ' + text, f, 560) + 6
    y = max(y, y2) + 20
    d.text((x1, y), 'Open questions for the decider', font=font(24, True), fill=WARN)
    y += 38
    for text in QUESTIONS:
        y = para(d, (x1, y), text.format(hostiles=int(fig['hostiles']), xp=fig['kill_xp_member'],
                                         tax=bf['dragons from the tax road (north track)']), f, 1150) + 4
    bottom = max(y, table_bottom) + 30
    board = board.crop((0, 0, W, min(H, bottom)))
    board.save(HERE / 'board_x7.png')
    print('board', board.size)


if __name__ == '__main__':
    main()
