#!/usr/bin/env python3
"""XD-17's phase 5 review board: the MU-3 plan, both MU-4 concepts with their blockouts, the town figures, the doors
and ways, and the open questions (A5, 2026-11-20). After level_generation/projects/xeen/x7/board_x7.py.

    board_xd17.py [--arrival raw/xd17_arrival_vN.png] [--signature raw/xd17_signature_vN.png]

Writes output/studio_cal/xd17/mockups/board_xd17.png (2400 px wide) and board_xd17_small.jpg. Figures come from
render_xd17.py's figures.json.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import places as P

HERE = pathlib.Path(_REPO_ROOT, 'output/studio_cal/xd17') / 'mockups'
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
    found = sorted((HERE / 'raw').glob(f'xd17_{view}_v*.png'), key=lambda p: int(p.stem.split('_v')[-1]))
    return found[-1] if found else None


def paste_fit(board, img, box):
    x, y, w, h = box
    im = img.copy()
    im.thumbnail((w, h), Image.LANCZOS)
    board.paste(im, (x, y))
    return im.size


QUESTIONS = [
    "1. The well's +1 level. QUESTS has no permanent levels (X8's explorer statue became +2 Speed and an award); "
    "D-5.1 keeps 'the +1 level well', WORLD_DESIGN says 'rescaled'. (a) Experience to the drinker's next level, once "
    "per character, with an award 'Found Shangri-La'; (b) +1 base level, the source's; (c) X8's pattern, an award and "
    "+2 to one stat. Rec. (a). The map is the same either way.",
    "2. Stumpy and Lacey. (a) Both peaceful placed actors with topics (A4's plan); (b) both animated decorations whose "
    "click speaks (no AI, cannot be attacked); (c) Lacey an actor grazing within 512 of the well, Stumpy a rooted "
    "animated decoration. Rec. (c). Both need S's models either way.",
    "3. Firestone's summit over the north-east rim. (a) A backdrop cone of studio masses, 5,600 over the floor, "
    "14,300-15,400 from the cameras (view distance 1.25), drawn for the view, not X7's heights; a smoke thread only "
    "if A6/S give an effect; (b) none: the cliffs close the sky. Rec. (a), no smoke until an effect exists.",
    "4. Signature view. (a) From the library steps east-north-east across the court to the pool, the white fall, "
    "the guild's dome and the summit (drawn); (b) from the pyramid terrace south over the valley to the cave "
    "mouth. Rec. (a).",
    "5. The hidden crystal (Benedict's joke). (a) In the cliff by the cave mouth, at eye height, facing the valley: "
    "every visitor is 'broadcast' from the first step (drawn); (b) in Benedict's house front; (c) no object, the "
    "line alone. Rec. (a).",
    "6. Sky inside. (a) The fair preset, no theme, no ash (the valley clears; drawn); (b) fair with X7's ashen "
    "theme; (c) fair with the shipped lush theme, if an open-air BLV takes a theme (A1). Rec. (a); (c) if A1 "
    "confirms.",
    "7. Water. (a) A cold pool, a white fall from the east cliff (S: a waterfall preset of the sand-fall build) and "
    "a stream to a sinkhole (drawn); (b) pool and stream only, a spring under the cliff; (c) none. Rec. (a), (b) as "
    "the fallback.",
    "8. The back passage. (a) A slot open to the sky, 384 wide, 2,087 long, X7's arrival at its west end (drawn); "
    "(b) a dark tunnel with a door at the valley end. Rec. (a).",
    "9. The pyramid's far end. WORLD_DESIGN: 'in Castle Alamar's dungeon (D6)'; xeen_common.lua: alamar_gate; "
    "ROADMAP 5.6: Castle Alamar. (a) On D6 outside Alamar's gate (the Lua's name; an outdoor landing like the first "
    "pair); (b) inside DD-17. Rec. (a). Only the neighbour row changes here.",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arrival')
    parser.add_argument('--signature')
    args = parser.parse_args()
    fig = json.loads((HERE / 'figures.json').read_text())
    H = 4200
    board = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(board)
    d.text((24, 18), 'XD-17 Shangri-La: phase 5 review (MU-3 plan, MU-4 concepts)', font=font(40, True), fill=INK)
    d.text((24, 68), "Act V's hidden town, an open-air BLV valley behind the Volcano Cave (Q-C26); no monsters, music "
                     '51, map 9120. A5, 2026-11-20. No geometry yet: a decider approves layout, scale and look first.',
           font=font(22), fill=DIM)
    plan = Image.open(HERE / 'plan_xd17.png').convert('RGB')
    pw, ph = paste_fit(board, plan, (20, 110, 1180, 1700))
    d.text((24, 110 + ph + 8), 'MU-3 plan, to scale (devdocs/xeen/briefs/xd17/L1/plan.yml; places.py)',
           font=font(20, True), fill=GOLD)
    crop = plan.crop((560, 520, 2080, 1840))
    cw, ch = paste_fit(board, crop, (20, 110 + ph + 44, 1180, 1100))
    d.text((24, 110 + ph + 44 + ch + 6), 'The town, enlarged: every door with its A4 house id and door id',
           font=font(18, True), fill=GOLD)
    left_bottom = 110 + ph + 44 + ch + 40
    concepts_bottom = 0
    for i, view in enumerate(['arrival', 'signature']):
        path = Path(getattr(args, view)) if getattr(args, view) else latest(view)
        y = 110 + i * 860
        title = {'arrival': 'MU-4 arrival view: out of the cool passage (entrance:xd16_way), looking north',
                 'signature': 'MU-4 signature view: from the library steps across the valley, east-north-east'}[view]
        d.text((1220, y), title, font=font(20, True), fill=GOLD)
        if path and path.exists():
            img = Image.open(path).convert('RGB')
            cw2, ch2 = paste_fit(board, img, (1220, y + 32, 1160, 774))
            note = f'Codex concept: {path.name}'
        else:
            cw2, ch2 = 1160, 774
            d.rectangle((1220, y + 32, 1220 + cw2, y + 32 + ch2), outline=DIM, width=2)
            d.text((1240, y + 60), 'concept pending', font=font(28), fill=DIM)
            note = 'no concept yet'
        blk = Image.open(HERE / f'blockout_{view}.png').convert('RGB')
        blk.thumbnail((330, 220), Image.LANCZOS)
        bx, by = 1220 + 10, y + 32 + ch2 - blk.size[1] - 10
        d.rectangle((bx - 3, by - 3, bx + blk.size[0] + 2, by + blk.size[1] + 2), fill=(255, 255, 255))
        board.paste(blk, (bx, by))
        concepts_bottom = max(concepts_bottom, y + 32 + ch2 + 30)
        d.text((1220, y + 32 + ch2 + 6), note + "; inset: the plan's blockout from the same camera (composition "
               'reference)', font=font(17), fill=DIM)
    # right column under the concepts: doors and ways
    x1 = 1220
    y = concepts_bottom + 20
    d.text((x1, y), 'Doors (A4 towns/xd17.yml) and ways', font=font(26, True), fill=INK)
    y += 40
    f = font(17)
    for aid, house, sid, pt, face, b in P.doors():
        line = f'{house}  {aid}  {b["name"]}  at {list(pt)} facing {face}'
        if aid != sid:
            line += f'  (indoor id {sid})'
        y = para(d, (x1, y), line, f, 1160, fill=INK if aid == sid else WARN, gap=3)
    y += 10
    ways = [
        "In from XD-16: entrance:xd16_way at (-1280, -4736), floor -64, facing north; A7's cool passage end calls "
        "q-c26.way and moves the party here.",
        "Back to XD-16: the throat's back at (-1280, -5888), \"Leave Shangri-La?\" (aaze0049:32), to XD-16's "
        "entrance:xd17_way.",
        "Out to X7: the rockfall at (-7680, 3712): xd17.cleft_opened once (cleft_open 116140), then X7's "
        "entrance:xd17_cleft (4096, 8192, 2496) facing west.",
        "In from X7 (after the first exit): entrance:x7_cleft at (-7296, 3648) facing east, 1,694 from the valley.",
        "The pyramid: Xeen.travelPyramid(\"shangrila\"), m30.done; before: \"The moons are not aligned. You are unable "
        "to pass.\" (aaze0049:25); arrival entrance:d6_pyramid (0, 3200, 256) facing south.",
        "The well (0, 0): aaze0049:27 then :4, once per character (question 1). Lacey at (448, -384), Stumpy at "
        "(4608, -2304). The hidden crystal at (-832, -5216).",
    ]
    for text in ways:
        y = para(d, (x1, y), '- ' + text, f, 1160, gap=3) + 4
    right_bottom = y
    # figures table (left, under the plan)
    y0 = left_bottom + 10
    d.text((24, y0), 'Town feel (TOWN_FEEL 5c, small towns) and figures', font=font(26, True), fill=INK)
    rows = [
        ('Services', 'hidden 4-6', f'{fig["services"]}: {fig["service_kinds"]} (D-5.1)', True),
        ('Residences', '8 +- 3 (WORLD_DESIGN)', f'{fig["residences"]}: An Education, Public Library, eight hint people',
         True),
        ('Buildings; doors', "A4's 15 houses", f'{fig["buildings"]}; {fig["doors"]} (Arm and Hammer has two)', True),
        ('Weapon to armour', '384-5,830', f'{fig["weapon_to_armour"]:,} (one forge, two doors)', True),
        ('Service to nearest service, median', '854-2,424', f'{fig["service_nearest_median"]:,}', True),
        ('Farthest service', '3,203-16,598', f'{fig["farthest_service"]:,}', True),
        ('Town core radius', '2,360-6,552', f'{fig["core_radius"]:,}', True),
        ('Fringe / core; beyond 1.5 core', '1.29-3.79; 0-0.38', f'{fig["fringe_over_core"]}; {fig["beyond_1_5_core"]}',
         True),
        ('Town built share', '0.15-0.37', f'{fig["town_built_share"]}', True),
        ('Tavern rank from arrival / centre', '0.05-0.95 / 0-0.94', f'{fig["tavern_rank_from_arrival"]} / '
                                                                    f'{fig["tavern_rank_from_centre"]}', True),
        ('Temple rank from centre', '0-1.0 (apart or raised)', f'{fig["temple_rank_from_centre"]}, on the west '
                                                               'terrace (384)', True),
        ('Doors on compass axes; lane within 1,024', '0.77-1.0; 0.81-1.0', f'{fig["doors_on_axes"]}; '
                                                                         f'{fig["doors_with_lane_1024"]} (farthest '
                                                                         f'{fig["door_to_lane_max"]})', True),
        ('Door levels p10-p90', '0-680', f'{fig["door_level_p10_p90"][0]}-{fig["door_level_p10_p90"][1]}', True),
        ('Wells and fountains', '3-8 a map', '1 (the +1 level well) and the pool: exception line', False),
        ('Monsters; chests', 'none (MAPS)', '0; 0', True),
        ('Valley floor', '-', f'{fig["valley_floor_extent"][0]:,} x {fig["valley_floor_extent"][1]:,} '
                              f'(~{fig["valley_floor_cells_512"]} cells); cliffs {fig["crest_range"][0]:,}-'
                              f'{fig["crest_range"][1]:,}', True),
        ('Walks', '-', f'arrival to first door {fig["arrival_to_first_door"]:,}, to the well {fig["arrival_to_well"]:,}; '
                       f'well to pyramid {fig["well_to_pyramid_portal"]:,}; passage {fig["passage_length"]:,}', True),
        ('Textures', 'proposed cap 70 (Dungeon L)', 'estimate 40-55: Cloudside town kit, pale marble (library, '
                                                    "guild), basalt cliffs (X7's), ground layers", True),
    ]
    cols = [(24, 360), (390, 260), (660, 540)]
    y = y0 + 44
    for cx, head in zip([c[0] for c in cols], ['Figure', 'Target', 'Plan']):
        d.text((cx, y), head, font=font(19, True), fill=GOLD)
    y += 30
    ft = font(17)
    for name, target, value, ok in rows:
        a = para(d, (cols[0][0], y), name, ft, cols[0][1] - 10)
        b = para(d, (cols[1][0], y), target, ft, cols[1][1] - 10, fill=DIM)
        c = para(d, (cols[2][0], y), value, ft, cols[2][1], fill=GOOD if ok else WARN)
        y = max(a, b, c) + 6
        d.line((24, y - 3, 1190, y - 3), fill=(52, 56, 64))
    left_bottom = y
    # questions (right, under the doors)
    y = right_bottom + 20
    d.text((x1, y), 'Open questions for the decider', font=font(24, True), fill=WARN)
    y += 38
    for text in QUESTIONS:
        y = para(d, (x1, y), text, f, 1160, gap=3) + 6
    bottom = max(y, left_bottom) + 30
    board = board.crop((0, 0, W, min(H, bottom)))
    board.save(HERE / 'board_xd17.png')
    small = board.copy()
    small.thumbnail((1600, 4000), Image.LANCZOS)
    small.save(HERE / 'board_xd17_small.jpg', quality=85)
    print('board', board.size)


if __name__ == '__main__':
    main()
