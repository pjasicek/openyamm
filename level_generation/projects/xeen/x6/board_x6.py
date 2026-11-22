#!/usr/bin/env python3
"""X6's phase 4 review board: the MU-3 plan, both MU-4 concepts with their blockouts, the figures against MAPS, the
houses, the edges and the open questions (A5, 2026-11-20). After level_generation/projects/xeen/d3/board_d3.py.

    board_x6.py [--arrival raw/x6_arrival_vN.png] [--signature raw/x6_signature_vN.png]

Writes output/studio_cal/x6/mockups/board_x6.png (2400 px wide). Figures come from render_x6.py's figures.json.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(_REPO_ROOT, 'output/studio_cal/x6') / 'mockups'
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
    found = sorted((HERE / 'raw').glob(f'x6_{view}_v*.png'), key=lambda p: int(p.stem.split('_v')[-1]))
    return found[-1] if found else None


def paste_fit(board, img, box):
    x, y, w, h = box
    im = img.copy()
    im.thumbnail((w, h), Image.LANCZOS)
    board.paste(im, (x, y))
    return im.size


QUESTIONS = [
    "1. POI band. MAPS' X6 sheet says the desert band 20-25 (17 named + 7-12 generic); MAP_CRAFT 6.2 gives deserts "
    "15-25 and wilderness (X6's role in maps.yml) 20-30. The D-20 census counts {poi} (the hamlet's two service "
    "doors, the coach house, both gates of the yard and four dungeon doors as separate spots). Use 20-30 and keep "
    "{poi}, or cut to 25 (the clicks off the sun stones, the caravan cairn and one signpost; the 6,000 rule then "
    "needs a landmark or a fight in the south steppe)?",
    "2. Scorpions. MAPS names 'Scorpions (crawlers)' for X6, but the only crawler row is Scorpion 16 / Electrapede 20 "
    "/ Lava Roach 26, under X6's A band 22-30. The plan uses three slots: sand worms (Dif 2), werewolves (Dif 4) and "
    "elemental golems (Dif 2: Sand 22, Water 28, Cloud 50 = the sheet's C 50). Keep (no scorpions on X6), ask A2 for "
    "an Act IV desert scorpion row (a fourth family would replace golems on the markers), or place a few crawlers "
    "as flavour?",
    "3. Werewolves at Dif 4 (30 % Wolfman 20, 40 % Werewolf 30, 30 % Greater Werewolf 40) to keep the cult's pack in "
    "the band and the kill XP at {xp}k against 41.5k; Dif 3 gives 40.1k with half the pack at level 20. Keep Dif 4?",
    "4. The coach yard (D-8.1) against the Barbaric cliffs in the south-east, its desert gate west onto a lane past "
    "the Summer Druid to the steppe road; 2,800 from the nearest fight. Keep, or nearer Sphinx Wells (the coach and "
    "the caravans one stop)?",
    "5. Signature view: the west rim's sand falls with the Southern Sphinx (WORLD_DESIGN's 'X6 west'), or the "
    "Northern Sphinx with Castle Basenji on its cliff (the map's name)? The arrival already holds the Northern "
    "Sphinx and the castle.",
    "6. Moved from the source: the Northern Sphinx from B1's east side to (82, 39) so the X4 arrival sees it; the "
    "Warzone gate from B2's far corner to (88, 95) inside the playable square; Basenji, Arie, Saul, the Summer Druid "
    "kept in their quadrants. Accept?",
    "7. Both concepts paint Castle Basenji too near, and the signature in sandstone: confirm the plan's grey-rubble, "
    "black-timber castle (towers kit) far on the north rim for L3.",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--arrival')
    parser.add_argument('--signature')
    args = parser.parse_args()
    fig = json.loads((HERE / 'figures.json').read_text())
    H = 3400
    board = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(board)
    d.text((24, 18), 'X6 Desert of the Sphinx: phase 4 review (MU-3 plan, MU-4 concepts)', font=font(40, True),
           fill=INK)
    d.text((24, 68), 'Act IV wilderness, party 30 to 33, monsters A 22-30, C 50. A5, 2026-11-20. No geometry yet: a '
                     'decider approves the layout, scale and density before the map is built.', font=font(22), fill=DIM)
    plan = Image.open(HERE / 'plan_x6.png').convert('RGB')
    pw, ph = paste_fit(board, plan, (20, 110, 1180, 1400))
    d.text((24, 110 + ph + 8), 'MU-3 plan, to scale (devdocs/xeen/briefs/x6/L1/sketch.yml)', font=font(20, True),
           fill=GOLD)
    big = Image.open(HERE / 'plan_x6_2x.png').convert('RGB')
    s, o = 24, 64
    crops = [("Castle Basenji on its cliff, Arie's camp, the Air corner", (23, 23, 58, 50)),
             ('Sphinx Wells, the oasis; the coach yard (D-8.1)', (36, 54, 72, 72))]
    ty = 110 + ph + 76
    tx = 20
    crop_bottom = ty
    for title, (x0, y0, x1, y1) in crops:
        crop = big.crop((o + x0 * s, o + y0 * s, o + x1 * s, o + y1 * s))
        cw, ch = paste_fit(board, crop, (tx, ty + 30, 575, 560))
        para(d, (tx, ty - 22), title, font(17, True), 575, fill=GOLD, gap=2)
        crop_bottom = max(crop_bottom, ty + 30 + ch)
        tx += 600
    yard = big.crop((o + 78 * s, o + 86 * s, o + 96 * s, o + 102 * s))
    yw, yh = paste_fit(board, yard, (1200 - 300, crop_bottom + 10, 290, 260))
    d.text((1200 - 300, crop_bottom + 14 + yh), 'the coach yard', font=font(16, True), fill=GOLD)
    crop_bottom += yh + 40
    concepts_bottom = 0
    for i, view in enumerate(['arrival', 'signature']):
        path = Path(getattr(args, view)) if getattr(args, view) else latest(view)
        y = 110 + i * 860
        title = {'arrival': "MU-4 arrival view: from X4's desert road at [106, 60], looking west-north-west",
                 'signature': "MU-4 signature view: the west rim's sand falls and the Southern Sphinx"}[view]
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
    sw = fig['towns']['town:sphinx_wells']
    kx = fig['kill_xp_by_family_member']
    rows = [
        ('Obelisk', 'exactly 1', "1 (the red rock knoll by the Sphinx track; obelisks.x6: THE)", True),
        ('Interaction devices', '>= 4 kinds, 1 permanent', 'wells, fountains, shrines, stones, cairn, urn, Reflector; '
                                                          'permanent: oasis fountain (+2 End), Shrine of Energy (+5 Air '
                                                          'res)', True),
        ('Points of interest', '20-25 (MAPS); 20-30 used', f'{fig["poi_count"]} by the D-20 census (chained 400, '
                                                           'service doors in): see question 1', True),
        ('POI spacing', '1,300-2,600 (desert median 4,390)', f'nearest neighbour median {fig["poi_nn_median"]:,} '
                                                             f'({fig["poi_nn_min"]:,}-{fig["poi_nn_max"]:,})', False),
        ('Dungeon entrances', '3-6', '4: XD-14 Basenji gate, XD-15 the Sphinx (amulet), XD-20 arena gate, FD-02 '
                                     '(Act VI); sealed until built', True),
        ('Outdoor chests', '4-10, each with a reason', f'{fig["chests"]} (a swallowed wagon, a den, a caravanserai, '
                                                       'bones, a rim pack, a mesa nest, a prospector)', True),
        ('Spawn markers', '45-70', f'{fig["markers"]}', True),
        ('Hostiles at load', '135', f'{fig["hostiles"]:.0f} (all from markers, groups 2-3)', True),
        ('Kill XP per member', '41.5k +-15 %', f'{fig["kill_xp_member"]}k: worms {kx["Xeen Sand Worm"]}k, werewolves '
                                              f'{kx["Xeen Werewolf"]}k, golems {kx["Xeen Elemental Golem"]}k', True),
        ('Encounter areas', '3-8, each 6-30 of 4,096²', f'{len(areas)}: ' + ', '.join(
            f'{a["cells_4096"]}' for a in areas.values()), True),
        ('Quiet land', '>= 1/3 of the land', f'{fig["quiet_share"] * 100:.0f} %', True),
        ('First fight, map edges', '2,000-6,000', f'X4 road {fe["entrance:east_road"]:,}, X5 road '
                                                  f'{fe["entrance:south_road"]:,}', True),
        ('Town arrivals (D-15)', 'town buffer 2,500', f'Sphinx Wells {ta["entrance:sphinx_wells"]:,} (doors '
                                                      f'{tb["Sphinx Wells doors"]:,}), coach yard '
                                                      f'{ta["entrance:warzone_coach"]:,} (house and gates '
                                                      f'{tb["coach yard (house, both gates)"]:,})', True),
        ('Roads', '1-4 % of the land', f'{fig["road_share"] * 100:.1f} % road (+ {fig["lane_share"] * 100:.1f} % '
                                       'lanes)', True),
        ('Height range', '>= 2,500 inside the box', f'{fig["height_box_field"][0]:,}-{fig["height_box_field"][1]:,} '
                                                    f'= {fig["height_box_span"]:,} on the drawn land inside the '
                                                    'square (the oasis to the Barbaric peak)', True),
        ('6,000 rule; wild land', 'none over 6,000; <= 0.16', f'farthest land {fig["farthest_from_place"]:,}; '
                                                              f'{fig["far_share_3000"]:.3f} over 3,000', True),
        ('Towns', 'compact', f'Sphinx Wells {sw["extent"][0] // 512} x {sw["extent"][1] // 512} cells, '
                             f'{sw["buildings"]} buildings, {sw["services"]} services (town_feel --small)', True),
        ('Textures', 'outdoor cap 120', 'cloudside_town (hamlet, yard), towers (Basenji), MU-2 X6 ground; new: none '
                                        'named (the sphinxes from mm6 pyramid egy walls, L3)', True),
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
    d.text((x1, y), "Houses and people (A4's x6.yml)", font=font(26, True), fill=INK)
    y += 42
    houses = [
        ('Sphinx Wells, the caravan stop', '4301 The Last Waterskin (tavern, Hadda), 4302 Sphinx Wells Caravans '
         "(Oskar; routes 427 Asp, 428 Rivercity; Asp's 431 lands here), 4303 the Well Keeper's House (Old Ibb), 4304 "
         "the Saddle Loft (Tansy); Old Ibb's well; arrival sphinx_wells, Town Portal."),
        ('The Warzone coach yard (D-8.1)', "4305 The Warzone Coach (Gorm; 429 Rivercity, 430 Castleview on "
         "m7.sigil), the arena gate XD-20, the desert gate barred from inside (x6.warzone_gate 116100); arrival "
         'warzone_coach; outside every encounter area.'),
        ('Outdoors', "Arie 4608 at her camp below Castle Basenji (Q-C8); Saul 4602 at his hermitage with the urn "
         "(Meditation Master); the Summer Druid 4601 in her grove (Q-C1)."),
    ]
    for head, text in houses:
        d.text((x1, y), head, font=font(18, True), fill=GOLD)
        y = para(d, (x1, y + 24), text, f, 560) + 8
    x2 = 1810
    y2 = y0
    d.text((x2, y2), 'Edges, rims, hooks', font=font(26, True), fill=INK)
    y2 += 42
    edges = [
        "East, y 60: X4's desert road arrives at the same y, level span 54-66 at 1,150; X4's other west spans "
        "continued (Gargoyle Range 24-50, dry downs 66-128).",
        "South, x 50: X5's steppe road arrives at the same x, level span 45-56 at 1,460; X5's north spans continued.",
        "Rims: west at x 24 (as X5's), north at y 24 (as X4's); the Air Reflector on the corner spit.",
        "Hooks placed: q-c9.door, obelisks.x6, obelisks.cloud_hoard, m37.reflector_air, x6.warzone_gate(_open), "
        "m40.sphinx_door; Arie (Q-C8), Summer Druid (Q-C1), Saul.",
        'Sky: the shipped clear preset, arid theme; music 17; no new textures.',
    ]
    for text in edges:
        y2 = para(d, (x2, y2), '- ' + text, f, 560) + 6
    y = max(y, y2) + 20
    d.text((x1, y), 'Open questions for the decider', font=font(24, True), fill=WARN)
    y += 38
    for text in QUESTIONS:
        y = para(d, (x1, y), text.format(poi=fig['poi_count'], xp=fig['kill_xp_member']), f, 1150) + 4
    bottom = max(y, table_bottom) + 30
    board = board.crop((0, 0, W, min(H, bottom)))
    board.save(HERE / 'board_x6.png')
    print('board', board.size)


if __name__ == '__main__':
    main()
