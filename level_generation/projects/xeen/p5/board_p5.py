#!/usr/bin/env python3
"""P5's phase 6 review board: the MU-3 plan, the two MU-4 concepts with their blockouts, the figures against MAPS, the
open questions and the requests (A5 sub-agent, 2026-11-21). After X9's board_x9.py.

    board_p5.py

Writes output/studio_cal/p5/mockups/board_p5.png (2400 px wide) and board_p5_small.jpg. Figures come from
render_p5.py's figures.json; the concepts are the latest raw/p5_<view>_vN.png.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(_REPO_ROOT, 'output/studio_cal/p5') / 'mockups'
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
    found = sorted((HERE / 'raw').glob(f'p5_{view}_v*.png'), key=lambda p: int(p.stem.split('_v')[-1]))
    return found[-1] if found else None


def paste_fit(board, img, box):
    x, y, w, h = box
    im = img.copy()
    im.thumbnail((w, h), Image.LANCZOS)
    board.paste(im, (x, y))
    return im.size


QUESTIONS = [
    "1. The walk: (a) one ring round the shrine, {walk:,} from the arrival to the dais ({ws} s walking, {rs} s "
    "running), room 26 x 26 cells, three Rest Stops and the observatory (the source has eight stops on a 358-square "
    "spiral); (b) a three-quarter ring from the north-east (about 21,000); (c) a ring and a half, nearer the source "
    "(about 45,000, room about 34 cells). Rec.: (a).",
    "2. Monsters (maps.yml 0, MAPS 'none or a last guardian'): (a) none, as the source; the fight is FD-03 (45 at "
    "60-85) and the walk is the rest after it; 'don't forget to recast your spells' stays the Pharaoh's joke; (b) one "
    "last guardian, a placed Ancient sentinel boss at the causeway's foot (an A2 row, about level 85); (c) a "
    "peaceful sentinel with one line. Rec.: (a).",
    "3. Falls: (a) to X5, on Darkstone's rock 224 before the tower's north door (-4608, 2304, 1500), facing it, with "
    "falling damage; back up through FD-03 (its gong floors stay raised); (b) an invisible wall round every cloud; "
    "(c) a fall puts the party back on the crown with damage (in-map). Rec.: (a), the world's rule (WORLD_DESIGN 3.1) "
    "and X8/X9's.",
    "4. The Pharaoh's note: (a) where the source has it, on a post by the stair house's door at the start, two steps "
    "from the arrival ('It's a long road ahead ...'); A3 changes m42.pharaoh_note's `where`; (b) by the last Rest Stop "
    "as m42.yml says now; (c) both. Rec.: (a).",
    "5. The Dragon Pharaoh (npc 5453) at his shrine: (a) a peaceful placed figure behind the dais (an A2 row, S's "
    "golden dragon in a blue-and-gold headdress, shared with DD-15), uncounted; the shrine stays the click; (b) only "
    "in the cinematic; (c) a statue of him. Rec.: (a).",
    "6. Roland and Kalindra: (a) peaceful placed figures under the pavilion, hidden until m42.done, shown by the "
    "cinematic's event cue; talk later with A1's NPC-on-a-placed-monster word; (b) the pavilion alone, the couple "
    "only in the cinematic's subtitle; (c) (a) with A3 after-lines now. Rec.: (a).",
    "7. Treasure (maps.yml 6): (a) one T6 chest, the wedding gift in the pavilion, shown with it; (b) none; (c) a T6 "
    "cache at each Rest Stop (3). Rec.: (a).",
    "8. The ten boards: (a) lettered faces: one Codex board picture and the ten names lettered on it by script in a "
    "period face (no Codex letters): 11 new textures and the REST STOP sign, about 30 in all, class M (cap 45) with "
    "a new-texture exception; (b) one blank board, the names by click and hover: 2-3 new, about 20, class S (cap 30); "
    "(c) five two-sided boards (6 new). Rec.: (a): reading them as you walk is the joke.",
    "9. Sky: (a) xeencloud, as every sky map; the cinematic's fade to white is the sky turning over; (b) a finale "
    "preset (A6), a golden late-day cloud sea; (c) xeencloud, then the new preset after m42.done. Rec.: (a).",
    "10. The way out after the ending: (a) the stair house only (the source's 'Descend into Darkstone Tower?'), the "
    "walk back or a spell; (b) (a), and after m42.done a cloud-stone disc by the pavilion that moves the party to the "
    "crown; (c) the cinematic's done event moves the party home (a town the decider names). Rec.: (b).",
]

REQUESTS = [
    ('A2', "map_stats row 9119 (xeen_p5.blv: encounter 0, treasure 6, lock 0, trap 0, perception 0, refill 672, music "
           "15, PLAINS; no slots, no bolster); peaceful placed-only rows, uncounted: the Dragon Pharaoh (shared with "
           "DD-15), Prince Roland, Queen Kalindra (Q5, Q6)."),
    ('A3', "m42.pharaoh_note `where` to the stair house at the start (Q4); the eleven sign lines aazex129:0-10 as "
           "the map's text; ORIGINAL_LINES rows aazex129:0-11, :14; m42.shrine calls evt.PlayCinematic('unification') "
           "and the certificate in its done event; the disc's line for Q10 (b)."),
    ('A4', "the completion certificate (world.yml `completion`) on m42.done."),
    ('A6', "X5 entrance:p5_fall (-4608, 2304, 1500) facing south and a keep-clear point (Q3); textures: X8's cloud "
           "pair, X9's cloud-stone, X5's Darkstone set (gtrlwal1, hkm3b, xtslate), a pale gold shrine stone; new: "
           "the board (and ten faces, Q8), the REST STOP sign; register them; the finale preset if Q9 (b/c)."),
    ('A7', "FD-03's roof stair: its top entrance:p5_stair (facing down); the seal's way up to P5's entrance:fd03_roof "
           "(4608, -3968, 0) facing north (512); its gong floors stay raised (the way back up after a fall)."),
    ('A8', "DD-15: the same Dragon Pharaoh figure (Q5) if DD-15 places him as an actor."),
    ('S', "figures: the Dragon Pharaoh (with a book), Roland, Kalindra; decorations: the shrine's two stone hands, "
          "the Cube and the Scepter set in them (after m42.done), a cake on a table, a bench for the Rest Stops."),
    ('AU', "wind (X8's), four far chimes (the sleepers) and a short wedding fanfare for the cinematic; the "
           "Pharaoh's line is D-38's xeen_vo_pharaoh_unification."),
    ('A1', "confirm an event cue can show a hidden structure and placed actors during a cinematic on an open-air "
           "BLV (state:wedding); NPC on a placed monster (D-47) for Q5/Q6's talk."),
    ('O', "openAirMaps for P5; the MAPS P5 row (treasure, the note) after the answers."),
]


def concept(board, d, view, title, blockout, box, against):
    x, y, w, h = box
    d.text((x, y), title, font=font(20, True), fill=GOLD)
    path = latest(view)
    if path and path.exists():
        cw, ch = paste_fit(board, Image.open(path).convert('RGB'), (x, y + 32, w, h))
        note = f'Codex concept: {path.name} (one call, no retry)'
    else:
        cw, ch = w, h
        d.rectangle((x, y + 32, x + cw, y + 32 + ch), outline=DIM, width=2)
        note = 'no concept yet'
    blk = Image.open(HERE / blockout).convert('RGB')
    blk.thumbnail((300, 200), Image.LANCZOS)
    bx, by = x + 10, y + 32 + ch - blk.size[1] - 10
    d.rectangle((bx - 3, by - 3, bx + blk.size[0] + 2, by + blk.size[1] + 2), fill=(255, 255, 255))
    board.paste(blk, (bx, by))
    yy = para(d, (x, y + 32 + ch + 6), note + "; inset: the plan's blockout from the same camera (composition "
              'reference).', font(17), w, fill=DIM)
    return para(d, (x, yy + 4), against, font(17), w, fill=INK)


def main():
    fig = json.loads((HERE / 'figures.json').read_text())
    H = 4400
    board = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(board)
    d.text((24, 18), 'P5 Clouds of the Ancients: phase 6 review (MU-3 plan, two MU-4 concepts)', font=font(40, True),
           fill=INK)
    d.text((24, 68), "Act VI finale (M42), party 61-65, no monsters, treasure 6, music 15. An open-air BLV as X9: "
                     "reached by FD-03's roof stair, left down the stair house, by falling (to X5) or by spell. "
                     'A5, 2026-11-21. No geometry yet.', font=font(22), fill=DIM)
    plan = Image.open(HERE / 'plan_p5.png').convert('RGB')
    pw, ph = paste_fit(board, plan, (20, 110, 1180, 1180))
    d.text((24, 110 + ph + 8), 'MU-3 plan, to scale (devdocs/xeen/briefs/p5/L1/plan.yml; cells of 512, north up)',
           font=font(20, True), fill=GOLD)
    legend = ("Legend: white clouds and the cloud road (floor in brackets), its dashed cloud-stone centre line; tan "
              "band the causeway; dark dots and numbers the distance along the walk every 4,096; red bars the ten "
              "boards (their names, facing the road); brown boxes the Rest Stop huts; black disc the stair house; "
              "green square the arrival, black square the way down; ringed disc the observatory; gold box the "
              "dais and its hands; dashed gold the pavilion after m42.done (Roland and Kalindra blue, the Pharaoh "
              "gold, the gift a diamond); blue wedges the two MU-4 cameras.")
    ly = para(d, (24, 110 + ph + 40), legend, font(16), 1170, fill=DIM, gap=3)
    x1 = 1220
    cy = concept(board, d, 'walk', "MU-4 'walk': from the crown's north edge, up the east road (the long way round)",
                 'blockout_walk.png', (x1, 110, 1160, 774),
                 "Against the plan: the shrine's cloud is painted level with the road (it is 512 above the "
                 "start, so its underside shows); the observatory stands on its own cloud across a gap (the plan "
                 "widens the road round it); the north-east turn is out of frame, so the road reads as straight; "
                 "the Rest Stop is nearer and larger than drawn. Boards, hut, bench, dome, the hands and the "
                 "flagstone centre line follow the plan.")
    cy = concept(board, d, 'shrine', "MU-4 'shrine': from the causeway's head after the ceremony",
                 'blockout_shrine.png', (x1, cy + 24, 1160, 774),
                 "Against the plan: the hands stand on tall columns (the plan: 448 over a 64 dais) and the three "
                 "figures stand on the dais (the plan: the Pharaoh behind it, the couple under the pavilion "
                 "2,880 from the camera); the observatory is painted twice and given banners; the causeway reads "
                 "as a paved plaza. The Cube, the Scepter, the pavilion, the cake and the looks follow the plan.")
    # the figures
    y0 = max(ly, 110 + ph + 40) + 30
    d.text((24, y0), 'Measured figures against MAPS (render_p5.py, figures.json)', font=font(26, True), fill=INK)
    ct = fig['crown_to_last_stop']
    rows = [
        ('Size', "'small'", f"room {fig['room_cells'][0]} x {fig['room_cells'][1]} cells (13,312 a side); clouds over "
                            f"{fig['cloud_bbox_cells'][0]} x {fig['cloud_bbox_cells'][1]}", True),
        ('Walkable cloud', 'X9: 272 M; X8: 124 M', f"{fig['walk_area_m']} M units²", True),
        ('The walk', "the source: 358 squares", f"{fig['walk_length']:,} arrival to dais: {fig['walk_seconds']['walking']}"
                                                f" s walking, {fig['walk_seconds']['running']} s running; road spans "
                                                f"{fig['road_span_range'][0]:,}-{fig['road_span_range'][1]:,}, the "
                                                f"causeway {fig['causeway']:,}", True),
        ('Sky round the shrine', 'no jump across', f"{fig['shrine_sky_gap'][0]:,} at the least ("
                                                   f"{fig['shrine_sky_gap'][1].split(':')[1]})", True),
        ('No short cut', 'crown to the last stop', f"{ct['gap']:,} of sky and {ct['rise']} up", True),
        ('Monsters', 'none (or a last guardian)', '0 (Q2)', True),
        ('Points of interest', 'small', f"{fig['poi_census']} by the census (10 boards, 3 Rest Stops, the note, the "
                                        "way down, the observatory, the shrine, the gift); spacing median "
                                        f"{fig['poi_spacing']['median']:,}", True),
        ('Chests', 'treasure 6', '1 (the wedding gift, after m42.done; Q7)', True),
        ('Heights', '-', 'the crown 0; the road climbs 64 a pad to 448; the shrine 512', True),
        ('Hooks', 'm42 by name', 'm42.pharaoh_note (the note), m42.observatory (the door), m42.shrine (the dais, '
                                 'the cinematic); state:wedding on m42.done', True),
        ('Ways in and out', 'FD-03 seal', "FD-03's roof stair both ways (entrance:fd03_roof); falls to X5 (Q3); after "
                                          'the ending Q10', True),
        ('Textures', 'S 30 / M 45', 'about 20 with blank boards, about 30 with lettered ones (Q8)', False),
        ('Original lines', '>= 3', 'aazex129:0-15 (Rest Stop, ten names, the observatory, the refusal, the '
                                   "descent, the note)", True),
    ]
    cols = [(24, 260), (290, 300), (600, 580)]
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
    y += 20
    d.text((24, y), 'The ending (set:unification)', font=font(24, True), fill=INK)
    y += 38
    y = para(d, (24, y), "A3's m42.shrine starts `unification` (xeen_p5.cinematics.yml, A5 at L4; skippable, about "
             "35 s): close on the dais as the Cube and the Scepter are set in the hands and the Pharaoh's voiced line; "
             "a rising pull-back over the ring and four far chimes (the sleepers); up into the sky and a fade to "
             "white, during which an event cue shows state:wedding; fade in on the pavilion, Roland and Kalindra "
             "under it and the Pharaoh turning to them; then the party's view, and the done event gives the "
             "completion certificate.", f, 1150)
    table_bottom = y
    y = cy + 30
    d.text((x1, y), 'Open questions for the decider', font=font(24, True), fill=WARN)
    y += 38
    for text in QUESTIONS:
        y = para(d, (x1, y), text.format(walk=fig['walk_length'], ws=fig['walk_seconds']['walking'],
                                         rs=fig['walk_seconds']['running']), f, 1150) + 4
    y += 16
    d.text((x1, y), 'Requests', font=font(24, True), fill=INK)
    y += 36
    for lane, text in REQUESTS:
        d.text((x1, y), lane, font=font(18, True), fill=GOLD)
        y = para(d, (x1 + 60, y), text, f, 1090) + 4
    bottom = max(y, table_bottom) + 30
    board = board.crop((0, 0, W, min(H, bottom)))
    board.save(HERE / 'board_p5.png')
    small = board.copy()
    small.thumbnail((1400, 4000), Image.LANCZOS)
    small.save(HERE / 'board_p5_small.jpg', quality=85)
    print('board', board.size)


if __name__ == '__main__':
    main()
