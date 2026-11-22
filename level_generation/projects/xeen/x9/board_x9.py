#!/usr/bin/env python3
"""X9's phase 5 review board: the MU-3 plan, the MU-4 concept with its blockout, the figures against MAPS, the open
questions and the requests (A5, 2026-11-20). After level_generation/projects/xeen/x7/board_x7.py.

    board_x9.py [--signature raw/x9_signature_vN.png]

Writes output/studio_cal/x9/mockups/board_x9.png (2400 px wide) and board_x9_small.jpg. Figures come from
render_x9.py's figures.json.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(_REPO_ROOT, 'output/studio_cal/x9') / 'mockups'
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
    found = sorted((HERE / 'raw').glob(f'x9_{view}_v*.png'), key=lambda p: int(p.stem.split('_v')[-1]))
    return found[-1] if found else None


def paste_fit(board, img, box):
    x, y, w, h = box
    im = img.copy()
    im.thumbnail((w, h), Image.LANCZOS)
    board.paste(im, (x, y))
    return im.size


QUESTIONS = [
    "1. The unseen way ('Xeen--9N.'): (a) a faint way: a 512-wide path nine cells due north from the sign, its top a "
    "wispy cloud texture that is hard to see; the sign is the clue, a fall costs the climb back through XD-12 (Darzog's "
    "disc and the cloud stair); (b) a plain causeway or rope bridge (no puzzle); (c) truly invisible faces (a new "
    "studio word, A1). Both chains are a visible way round. Rec.: (a), reversible by a texture.",
    "2. Falls land on X2: (a) one point on Darzog's island between the tower's east door and the jetty, ground 768, "
    "falling damage; the way back up is ten steps away; (b) Lake Darzog's water east of the island (no damage, X8's "
    "middle zone; Medin's boat or Water Walk to reach the island); (c) the X9 position scaled over X2's lake. Rec.: (a).",
    "3. 'Xeen's Aviary' (aaze0027:9): (a) on X9 at the head of the aviary stair, by the roc rookery (the source's "
    "(26,26), at eye height); (b) on the castle shell's wall, naming XD-19's inner aviary (A7's note); (c) both. "
    "Rec.: (a); XD-19 may sign its own court inside.",
    "4. Monsters (50, MAPS 35-55): (a) Rocs 38 x38, Griffins 48 x6 (the aviary), Cloud Golems 50 x6 (back lot and the "
    "castle's apron): {xp}k (-0.4 %); (b) the source's two kinds only, Rocs x40 and Cloud Golems x10: 25.7k; (c) (a) "
    "with two Lesser Air Elementals 55 (XD-19's) for two golems: 26.3k, reaching the band's top. Rec.: (a).",
    "5. Offering statues and nests: the source has 9 offering statues and 7 roc nests. Drawn: 6 offerings (one per "
    "chain cloud, an item for Crusaders once per party) and 5 nests (2 south, 3 in the aviary). Or the source's 9 and "
    "7, or X8's 2 and 3. Rec.: as drawn (POIs {pois} by the census).",
    "6. Slick: (a) a peaceful placed figure behind the prize stand (an A2 row on a recoloured shipped merchant, not "
    "counted); the booths and the stand stay the clicks; (b) no figure, Slick speaks through his booths only (m34 as "
    "written); (c) an NPC with a portrait at the stand (A4 id; A3 makes the stand a topic). Rec.: (a), (b) until S "
    "has the binding.",
    "7. Size and fill: room 88 x 84 cells (70 % of an outdoor side, X8's rule), cloud {area} M units² walkable "
    "(X8: 124 for 60 monsters), {quiet} % of it over 2,048 from any group (the stair head, the brink, the landing, "
    "the plaza and the gate are quiet by design). (a) as drawn; (b) islands 15 % smaller (about 190 M; spans up to "
    "4,500); (c) as drawn plus 6 rocs over the plaza's edges (kill XP +2.7k). Rec.: (a).",
    "8. The Dragon Clouds (Q-F1): (a) built now at 2,048 above the aviary's north-east, 3,900 from it, empty and "
    "sealed, with FD-04's arrival named entrance:fd04_roof; Q-F1's riddle, runes and dragons added with its brief; "
    "(b) only reserved now, built later (an X9 rebuild). Rec.: (a): a landmark now, cheap to fill.",
]

REQUESTS = [
    ('A2', "map_stats row 9107 (encounter 0, treasure 5, lock 10, trap 5, perception 5, refill 672, music 21, PLAINS; "
           "slots Xeen Roc tier 1 [2,3] 80, Xeen Elemental Golem tier 2 [1,3] 20); bolster row; the Act V recount "
           "(26.0k); for Q6 (a) a peaceful placed-only Slick row (not counted)."),
    ('A3', "hooks: five roc nests (aaze0027:0, Yes/No, XP) and six offering statues (as X8's); the four sign texts, "
           "aaze0027:44 for the castle-gone spot and a first-arrival line; ORIGINAL_LINES rows aaze0027:0, :6-9, :33, "
           ":44; m34's booth `where` texts to the drawn booths; the Linguist gate (shared with X8)."),
    ('A4', "none (no town on X9); for Q6 (c) an NPC id for Slick."),
    ('A6', "textures: X8's xccloud/xccloudsd, 7tws1f flags; new: the striped awning canvas, a straw bullseye, a wispy "
           "top for the unseen way (Q1 a); the castle shell in XD-19's exterior kit; sky preset xeencloud (exists); "
           "register the new ones."),
    ('A7', "XD-19's gate footprint (width, height, the two leaf pictures both sides) and the shell's outside "
           "(7,168 x 6,656, walls 2,688 for four floors); point XD-19's exit and the scepter's leave at "
           "entrance:xd19_gate (0, 11264, 768) facing south (1536); X9's door goes to entrance:x9_gate."),
    ('A8', "XD-12's exit:clouds_of_xeen to X9's entrance:xd12_roof (0, -17920, 320) facing north (512), once X9 is "
           "installed."),
    ('S', "Slick's figure binding (Q6 a); optional: a doll shelf for the prize stand, a high-striker (bell pole), "
          "ground models of the doll items 12367-12371 if missing; the Dragon Clouds' dragon-head rock (with Q-F1)."),
    ('AU', "wind (X8's), roc cries, the high-striker's DING, a fairground loop at the plaza."),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--signature')
    args = parser.parse_args()
    fig = json.loads((HERE / 'figures.json').read_text())
    H = 3800
    board = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(board)
    d.text((24, 18), 'X9 Clouds of Xeen: phase 5 review (MU-3 plan, MU-4 concept)', font=font(40, True), fill=INK)
    d.text((24, 68), "Act V sky map, party 46 to 48, monsters 35-55, 50 placed, treasure 5. An open-air BLV as X8: "
                     "reached from XD-12's roof, left by falling (to X2) or through Castle Xeen. A5, 2026-11-20. No "
                     'geometry yet.', font=font(22), fill=DIM)
    plan = Image.open(HERE / 'plan_x9.png').convert('RGB')
    pw, ph = paste_fit(board, plan, (20, 110, 1180, 1140))
    d.text((24, 110 + ph + 8), 'MU-3 plan, to scale (devdocs/xeen/briefs/x9/L1/plan.yml; cells of 512, north up)',
           font=font(20, True), fill=GOLD)
    legend = ('Legend: white clouds (walkable, floor in brackets); striped brown rope bridges with rim-to-rim '
              'lengths; stone bands the Xeen road and the aviary stair; dashed pale squares the unseen way; discs '
              'monster groups (teal rocs, orange griffins, grey cloud golems; count inside; ring 1,536); green '
              'squares arrival and XD-19 return; red triangles roc nests; blue dots rhyming statues; purple dots '
              'offering statues; striped squares the four booths and the prize stand; gold diamonds chests; brown '
              'posts signs; hatched: the sealed Dragon Clouds; blue wedge and dashes: the MU-4 camera.')
    ly = para(d, (24, 110 + ph + 40), legend, font(16), 1170, fill=DIM, gap=3)
    # the concept
    y = 110
    d.text((1220, y), "MU-4 signature view: from the 'Xeen--9N.' sign on the brink, north over the gap to Castle Xeen",
           font=font(20, True), fill=GOLD)
    path = Path(args.signature) if args.signature else latest('signature')
    if path and path.exists():
        img = Image.open(path).convert('RGB')
        cw, ch = paste_fit(board, img, (1220, y + 32, 1160, 774))
        note = f'Codex concept: {path.name}'
    else:
        cw, ch = 1160, 774
        d.rectangle((1220, y + 32, 1220 + cw, y + 32 + ch), outline=DIM, width=2)
        note = 'no concept yet'
    blk = Image.open(HERE / 'blockout_signature.png').convert('RGB')
    blk.thumbnail((330, 220), Image.LANCZOS)
    bx, by = 1220 + 10, y + 32 + ch - blk.size[1] - 10
    d.rectangle((bx - 3, by - 3, bx + blk.size[0] + 2, by + blk.size[1] + 2), fill=(255, 255, 255))
    board.paste(blk, (bx, by))
    cy = para(d, (1220, y + 32 + ch + 6), note + f"; inset: the plan's blockout from the same camera, at "
              f"{tuple(fig['signature']['at'])}, eye z {fig['signature']['z']}, the gate {fig['signature']['to_gate']:,} "
              'away (composition reference).', font(17), 1160, fill=DIM)
    against = ("Against the plan: the castle is painted about twice as large and nearer than the blockout (at "
               "23,000 it spans 18 degrees); the four booths stand in one row (the plan spreads them over the plaza); "
               "the unseen way reads as a cloud path (Q1 decides how faint); a banner on the right and gryphon "
               "statues at the gate are the painter's. Its clouds, cloud-stone, castle colours, booths, aviary and "
               "Dragon Clouds follow the plan.")
    cy = para(d, (1220, cy + 6), against, font(17), 1160, fill=INK)
    # the figures
    y0 = max(ly, cy) + 30
    d.text((24, y0), 'Measured figures against MAPS (render_x9.py, figures.json)', font=font(26, True), fill=INK)
    ff = fig['first_fight']
    rows = [
        ('Monsters placed', '50 (sky maps 50-60, all placed)', f"{fig['monsters']} in {fig['groups']} groups of 2-3",
         True),
        ('Kill XP per member', '26.1k', f"{fig['kill_xp_member'] / 1000:.1f}k: Rocs 38 x38 69.3k, Griffins 48 x6 "
                                        f"16.7k, Cloud Golems 50 x6 18.0k (party)", True),
        ('Monster band', '35-55', 'Rocs 38 (B), Griffins 48 (C), Cloud Golems 50; the source: Rocs and Cloud Golems',
         True),
        ('Size', '~70 % of an ODM (X8: 76 x 64 for 60 %)',
         f"room 88 x 84 cells (45,056 x 43,008); clouds over {fig['cloud_bbox_cells'][0]} x "
         f"{fig['cloud_bbox_cells'][1]}", True),
        ('Walkable cloud', 'X8: 124 M units²', f"{fig['walk_area_m']} M units² (+ the castle shell "
                                              f"{fig['castle_area_m']} M); Q7", False),
        ('Quiet cloud', '>= 1/3', f"{fig['quiet_share'] * 100:.0f} % over 2,048 from any group", True),
        ('First fight', '2,000-6,000 from arrivals', f"stair head {ff['entrance:xd12_roof'][0]:,} (two rocs by the "
                                                    f"west statues); XD-19 return {ff['entrance:xd19_gate'][0]:,} "
                                                    '(the apron golems)', True),
        ('Spans (D-6.2: 3,500-4,000)', 'rope bridges', f"{fig['bridge_range'][0]:,}-{fig['bridge_range'][1]:,}; "
                                                       f"aviary stair {fig['links']['link:aviary_stair']['length']:,}; "
                                                       "cloud necks 2,200-3,300", True),
        ('The unseen way', "'Xeen--9N.': nine cells", f"{fig['unseen_way']:,} (9 x 512), falling 192", True),
        ('Points of interest', "X8's L1: 13", f"{fig['poi_census']} by the census (4 signs, 4 rhymes, 5 nests, "
                                                    '6 offerings, 4 booths, the stand, the gate, 4 chests); '
                                                    f"spacing median {fig['poi_spacing']['median']:,}", True),
        ('Chests', 'treasure 5', '4: the south-west hollow, the NW cache, the east pack, the rocs\' hoard (T5)', True),
        ('Heights', '-', 'stair head 320, south 384-512, chains 384-704, landing 256, plaza 448, gate 704, castle '
                          f"768 (walls to 3,456, keep to 4,480), aviary 1,024, Dragon Clouds 2,048", True),
        ('Ways in and out', 'XD-12 roof; falls to X2', "XD-12's cloud stair (one way up); XD-19's gate both ways; "
                                                       'FD-04 roof (sealed); every fall to X2, Darzog\'s island '
                                                       '(-14592, 2816)', True),
        ('Original lines', '>= 3', 'aaze0027:0, 2-5, 6-9, 10, 12-26, 31, 33, 40-44', True),
    ]
    cols = [(24, 290), (320, 330), (660, 520)]
    y = y0 + 44
    for cx_, head in zip([c[0] for c in cols], ['Figure', 'Target', 'Plan']):
        d.text((cx_, y), head, font=font(19, True), fill=GOLD)
    y += 30
    f = font(18)
    for name, target, value, ok in rows:
        a = para(d, (cols[0][0], y), name, f, cols[0][1] - 10)
        b = para(d, (cols[1][0], y), target, f, cols[1][1] - 10, fill=DIM)
        c = para(d, (cols[2][0], y), value, f, cols[2][1], fill=GOOD if ok else WARN)
        y = max(a, b, c) + 6
        d.line((24, y - 3, 1180, y - 3), fill=(52, 56, 64))
    table_bottom = y
    # D-47 and the questions on the right
    x1 = 1220
    y = y0
    d.text((x1, y), "Castle Xeen's gate (D-47)", font=font(26, True), fill=INK)
    y += 42
    gate = ("Two leaves in the shell's south wall at (0, 11776), XD-19's door, condition m34.gate ('No one may enter "
            "Castle Xeen without a cupie doll!'). The return point entrance:xd19_gate (0, 11264, 768) facing south, "
            "512 before the leaves, for XD-19's exit and the scepter cinematic's leave. state:castle_gone on m35.done "
            "(111707): the shell hidden, the gate sealed, the spot reads 'The great Castle Xeen recently stood here.' "
            "(aaze0027:44). 'Xeen's Aviary' at the aviary stair's head (Q3). Slick's prize stand on the causeway's "
            "west side; the gate and the plaza are quiet.")
    y = para(d, (x1, y), gate, f, 1150) + 16
    d.text((x1, y), 'Open questions for the decider', font=font(24, True), fill=WARN)
    y += 38
    for text in QUESTIONS:
        y = para(d, (x1, y), text.format(xp=f"{fig['kill_xp_member'] / 1000:.1f}", pois=fig['poi_census'],
                                         area=fig['walk_area_m'], quiet=round(fig['quiet_share'] * 100)),
                 f, 1150) + 4
    y += 16
    d.text((x1, y), 'Requests', font=font(24, True), fill=INK)
    y += 36
    for lane, text in REQUESTS:
        d.text((x1, y), lane, font=font(18, True), fill=GOLD)
        y = para(d, (x1 + 60, y), text, f, 1090) + 4
    bottom = max(y, table_bottom) + 30
    board = board.crop((0, 0, W, min(H, bottom)))
    board.save(HERE / 'board_x9.png')
    small = board.copy()
    small.thumbnail((1400, 4000), Image.LANCZOS)
    small.save(HERE / 'board_x9_small.jpg', quality=85)
    print('board', board.size)


if __name__ == '__main__':
    main()
