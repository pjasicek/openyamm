#!/usr/bin/env python3
"""D7's phase 6 review board: the MU-3 plan with Olympus, the two MU-4 concepts with their blockouts, the counts
against MAPS, the hooks placed, the corner contract, the fall landings, the requests and the open questions (A6
sub-agent, 2026-11-21; after X9's board_x9.py).

    board_d7.py        level_generation/xeen_art/phase6/d7/board_d7.png (3000 px wide), board_d7_small.jpg and
                       board_d7.html (the same content, images beside it)

Figures come from d7/measure.json and d7/falls.json; the text is the short form of devdocs/xeen/briefs/d7/L1/NOTES.md.
"""
import html
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import d7_design as D

HERE = Path(__file__).resolve().parent / 'd7'
W = 3000
BG = (24, 26, 31)
INK = (232, 232, 232)
DIM = (170, 174, 182)
GOLD = (236, 196, 110)
GOOD = (120, 200, 130)
WARN = (240, 170, 80)


def font(size, bold=False):
    return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/' + ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'),
                              size)


def wrap(draw, text, f, width):
    lines, line = [], ''
    for w in text.split():
        t = (line + ' ' + w).strip()
        if draw.textlength(t, font=f) <= width:
            line = t
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def content():
    f = json.loads((HERE / 'measure.json').read_text())
    falls = json.loads((HERE / 'falls.json').read_text())
    ff = f['first_fight']
    rows = [
        ('Monsters placed', '50 (MAPS)', f"{f['placed_monsters']} in {f['groups']} groups of 2-3", True),
        ('Kill XP a member', '48.5k', f"{f['kill_xp_per_member'] / 1000:.1f}k (+0.6 %); "
                                      f"{f['kill_xp_per_member_with_megadragon'] / 1000:.1f}k with the Megadragon", True),
        ('Mix', '50-75, Megadragon 125', 'Griffins 48 x12, Sky Golems 75 x8, Cloud Dragons 70 x8, Cloud Golems 50 x22; '
                                         'Megadragon 125 (Q4)', True),
        ('Not counted', '-', 'Megadragon; 8 sky bandits, peaceful until refused (Q3)', True),
        ('Size', '~1 ODM', 'room 128 x 88 cells; the ring 190,872 round (Q1)', True),
        ('Walkable', 'X9 272 M', f"{f['walkable_area_millions']} M (roads {f['road_area_millions']}, Olympus "
                                 f"{f['olympus_area_millions']})", True),
        ('Quiet', '>= 1/3', f"{round(f['quiet_share'] * 100)} % (narrow roads; Q1)", True),
        ('First fight', '2,000-6,000', f"rope {ff['entrance:d1_rope']['distance']:,}; returns 4,222-4,720; roofs "
                                       f"3,899-5,724; sky door 2,290; Olympus town buffer (5,948)", True),
        ('Megadragon reach', '>= 5,888 (D-54)', f"{f['megadragon_clear']:,} from every other road; castaway isle "
                                                f"{f['stranded_west_from_leash']:,} (D-2: >= 5,888)", True),
        ('POIs (census)', 'X9 29; towns 35-55', f"{f['points_of_interest']} (35 roads, 21 Olympus); 18 boards "
                                                f"hover-only; NN median {f['poi_nn_median']:,} (Q7)", True),
        ('Chests', 'T6', f"{f['chests']}: hoard, two castaways, skywaymen, lost pack", True),
        ('Olympus by road', '-', 'rope 26,776; corners 39,488-50,430; roost 47,228', True),
        ('Heights', '-', 'south road 768, north road 1,280, Olympus 1,792, roost 1,536', True),
        ('Textures', 'Dungeon L 70', 'about 30 shipped (Celeste for Olympus, xccloud); 2 new', True),
    ]
    hooks = [
        "A3 by name: m31.arrival (dock), m31.soul_storage, m31.true_name_plaque, m31.statue_1-4; m38.corner_fire, "
        "_air, _earth, _water, _wrong; m30.grove_rope (D1 side, yes -> entrance:d1_rope).",
        "Read: m30.done 111600 (sky door, vault), mirror_olympus 119012. Ligono in Hera's house (Q-C19).",
        "Asked of A3: 4 tolls, 4 riddles (smoke, dust, steam, mud), 3 lamps (Q-D27 d7_tired, d7_kind, d7_angry), "
        "4 bottles, Q-D26 (hoard, key, Alamar hatch), 'Bolted from below.', scarabs (Q5), Xeen.skyFall's 6 D7 zones, "
        "ORIGINAL_LINES (aaze0089-0099, aazex100-112).",
    ]
    corners = [('Fire NW A1', '(-30464, 20480) 1,280', 'm38.corner_fire', 'P1 entrance:d7_fall', 'p1_return (-27136, 17408)'),
               ('Air NE F1', '(30464, 20480) 1,280', 'm38.corner_air', 'P2 entrance:d7_fall', 'p2_return (27136, 17408)'),
               ('Earth SE F4', '(30464, -20480) 768', 'm38.corner_earth', 'P3 entrance:d7_fall', 'p3_return (27136, -17408)'),
               ('Water SW A4', '(-30464, -20480) 768', 'm38.corner_water', 'P4 entrance:d7_fall', 'p4_return (-27136, -17408)')]
    fall_rows = []
    for z in falls:
        a = z['nearest_actor']
        fall_rows.append((z['zone'].split(':')[1].upper(), f"{tuple(z['landing'][:2])} g{z['landing'][2]}",
                          z['near'].split(':')[0].split('(')[0].strip(), f"{a['distance']:,}" if a else '-',
                          z['owner']))
    requests = [
        "A2: map_stats 9114 (T6, lock 12, trap 6, music 30) + bolster row; Act VI recount 48.8k (53.0k w/ Megadragon); "
        "Sky Bandit row ~55 (Q3); Q-D26 hoard artifact + Alamar roof key; 4 scarabs (Q5).",
        "A3: hooks above; Q-D26 file; D7 zones in Xeen.skyFall; the corners' 'What do you seek?' flow; ORIGINAL_LINES.",
        "A4: d7.yml doors as drawn (13 doors + mirror); at of olympus_square (-4608, 6400, 1792) and olympus_dock "
        "(-640, 3200, 1792).",
        "A6 (surface): entrance:d7_fall on D1, D2, D4, D5, D6 (table); D1 entrance:d7_rope at the rope foot "
        "(-8192, 14336, 1088) facing 768; register xsbarge, xsglow after approval.",
        "A5: D3 entrance:d7_fall (-15360, 11776, 1440) facing east, at D3's next install.",
        "A7: DD-06, DD-07 roof stairs up to entrance:dd06_roof / dd07_roof (Q2).",
        "A8: roof exits up from DD-02, DD-03 (stage 4), DD-05, DD-08, DD-14 (Q2); DD-15 sky door both ways "
        "(entrance:d7_sky / dd15_sky); DD-17 roof hatch (d7_roof / dd17_roof); DD-26 stair (d7_stair / dd26_stair).",
        "S: Rest Stop hut (P5's), merchants' barges, celestial boat, Megadragon binding (11654), Sky Bandit body, "
        "genie lamp (D5/D6's).   AU: wind, corner hums, dragons, bandits' whistle.   Orchestrator: openAirMaps.",
    ]
    questions = [
        ("1 Size of the ring", "(a) as drawn, 1 ODM, ring 190,872, 483 M; (b) 80 %, ring ~150k; (c) (a) + an inner "
                               "south road (Genie's Rock -> Steam Post)", "(a)", "all of L2"),
        ("2 Tower roofs", "(a) one way up (WORLD_DESIGN 3.3, D-5.3), 7 roofs; sky door and Alamar both ways; "
                          "(b) all both ways (source 'Descend to...?'; DD-14 note); (c) only Mok's towers, pyramid, "
                          "Alamar", "(a)", "A7/A8 roof rooms"),
        ("3 Sky bandits", "(a) toll hook + 2 peaceful Sky Bandits per toll (A2 row ~55), hostile on refusal, uncounted; "
                          "(b) text only; (c) hostile, counted", "(a)", "A2 row, A3 hooks, S"),
        ("4 Monster mix", "(a) Griffins, Sky/Cloud Golems, Cloud Dragons 48.8k; (b) no griffins 49.4k; "
                          "(c) +3 Green Dragons 80, 52.0k", "(a)", "A2 recount"),
        ("5 Scarab sellers", "(a) 4 A3 hooks with Xeen.payGems; (b) 4 A4 vendor houses; (c) one shop", "(a)",
         "A2 items, A3/A4"),
        ("6 Olympus' ways in", "(a) three causeways, open gilded gates; (b) the source's island + sky ferry; "
                               "(c) north causeway only", "(a)", "L2 layout"),
        ("7 POI count", "(a) 56, boards hover-only; (b) boards clickable 74; (c) ~45", "(a)", "A3 texts"),
        ("8 The Megadragon", "(a) on Alamar's roof hatch, dead-end road, 6,808 clear; hatch opens with its key; "
                             "(b) hatch sealed; (c) on the Fire Corner (blocks M38)", "(a)", "A8 DD-17, A3 Q-D26"),
        ("9 Failing sun", "(a) one preset xeen_skyroads; (b) fading/failing presets by qbit", "(a)", "A6 sky, A3 Lua"),
        ("10 Fall landings", "(a) one entrance:d7_fall per surface map by a way back up; (b) one for all (D1 jetty); "
                             "(c) X8's scaled mapping", "(a)", "six map owners"),
    ]
    return f, rows, hooks, corners, fall_rows, requests, questions


def board():
    f, rows, hooks, corners, fall_rows, requests, questions = content()
    plan = Image.open(HERE / 'plan_d7.png')
    oly = Image.open(HERE / 'plan_olympus.png')
    arr = Image.open(HERE / 'raw/d7_arrival_v1.png')
    sig = Image.open(HERE / 'raw/d7_signature_v1.png')
    barr = Image.open(HERE / 'blockout_arrival.png')
    bsig = Image.open(HERE / 'blockout_signature.png')
    pad = 30
    pw = 1900
    plan_s = plan.resize((pw, int(plan.size[1] * pw / plan.size[0])), Image.LANCZOS)
    cw = W - pw - pad * 3
    oly_s = oly.resize((cw, int(oly.size[1] * cw / oly.size[0])), Image.LANCZOS)
    hw = (W - pad * 3) // 2
    arr_s = arr.resize((hw, int(arr.size[1] * hw / arr.size[0])), Image.LANCZOS)
    sig_s = sig.resize((hw, int(sig.size[1] * hw / sig.size[0])), Image.LANCZOS)
    bw = 420
    barr_s = barr.resize((bw, int(barr.size[1] * bw / barr.size[0])))
    bsig_s = bsig.resize((bw, int(bsig.size[1] * bw / bsig.size[0])))
    H = 5200
    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)
    y = pad
    d.text((pad, y), 'D7 The Skyroads - phase 6 L1 review board (MU-3 plan, MU-4 concepts)', font=font(40, True), fill=GOLD)
    y += 56
    d.text((pad, y), "A6 sub-agent, 2026-11-21. Act V-VI sky map over the whole Darkside (party 55-58): a ring of cloud "
                     "road with the four element corners (to P1-P4), Olympus on its marble cloud (M31), the Megadragon "
                     "off a dead-end road. Brief: devdocs/xeen/briefs/d7/L1 (validate: no issues).",
           font=font(21), fill=DIM)
    y += 46
    img.paste(plan_s, (pad, y))
    ox = pad * 2 + pw
    img.paste(oly_s, (ox, y))
    ty = y + oly_s.size[1] + 24
    d.text((ox, ty), 'Counts against MAPS', font=font(28, True), fill=GOLD)
    ty += 42
    cols = [ox, ox + 250, ox + 520]
    fs = font(18)
    for name, target, plan_v, ok in rows:
        d.text((cols[0], ty), name, font=font(18, True), fill=INK)
        d.text((cols[1], ty), target, font=fs, fill=DIM)
        lines = wrap(d, plan_v, fs, W - pad - cols[2])
        for i, ln in enumerate(lines):
            d.text((cols[2], ty + i * 23), ln, font=fs, fill=GOOD if ok else WARN)
        ty += max(1, len(lines)) * 23 + 8
    y += max(plan_s.size[1], ty - y) + pad
    # concepts
    d.text((pad, y), 'MU-4 arrival: the Dark Grove rope (one codex exec, first attempt)', font=font(26, True), fill=GOLD)
    d.text((pad * 2 + hw, y), "MU-4 signature: Olympus across the cloud roads (one codex exec, first attempt)",
           font=font(26, True), fill=GOLD)
    y += 40
    img.paste(arr_s, (pad, y))
    img.paste(sig_s, (pad * 2 + hw, y))
    img.paste(barr_s, (pad + hw - bw - 10, y + arr_s.size[1] - barr_s.size[1] - 10))
    img.paste(bsig_s, (pad * 2 + hw * 2 - bw - 10, y + sig_s.size[1] - bsig_s.size[1] - 10))
    y += arr_s.size[1] + 10
    cap_a = ("Why the rope: the dock lands inside Olympus (a town arrival, and the signature shows the city); the rope "
             "lands on the open Skyroad and teaches the map in one look. Camera (-24576, -6656), eye 1,200, facing "
             "24 degrees. Against the plan: Olympus painted larger and nearer (it is 25,600 away), a winged statue "
             "added, the launch an arched bridge-head, the road fully paved (plan: cloud with a paved band).")
    cap_s = ("Why Olympus: the map's identity and main story stop (M31); the Megadragon's road is an optional dead end. "
             "Camera on the east causeway (6144, 4608), eye 1,616, facing 164 degrees; the city's middle 11,000 away. "
             "Against the plan: gilded gate leaves and griffin statues (plan: open posts), the temple on the gate's "
             "axis (plan: the square's north side), carved kerbs, cypresses and flowers (none planned).")
    for x0, cap in ((pad, cap_a), (pad * 2 + hw, cap_s)):
        for i, ln in enumerate(wrap(d, cap, font(18), hw)):
            d.text((x0, y + i * 24), ln, font=font(18), fill=DIM)
    y += 5 * 24 + pad
    # three columns of text
    colw = (W - pad * 4) // 3
    xs = [pad, pad * 2 + colw, pad * 3 + colw * 2]
    ys = [y, y, y]

    def block(ci, title, paras, size=18, colour=INK):
        d.text((xs[ci], ys[ci]), title, font=font(26, True), fill=GOLD)
        ys[ci] += 38
        for p in paras:
            for ln in wrap(d, p, font(size), colw):
                d.text((xs[ci], ys[ci]), ln, font=font(size), fill=colour)
                ys[ci] += size + 6
            ys[ci] += 6
        ys[ci] += 16

    block(0, 'Hooks placed', hooks)
    block(0, 'The corner contract (corners.yml, unchanged)',
          [f"{a}: tip {b}; {c}; -> {e_}; return {r}" for a, b, c, e_, r in corners] +
          ["Each tip asks 'What do you seek?'; another answer runs m38.corner_wrong; a plain fall lands on the "
           "surface. Default way out: the plane returns the party to its corner's return point."])
    block(1, 'Fall landings (entrance:d7_fall, one per surface map)',
          [f"{z}: {l}; {n}; nearest actor {a}; {o}" for z, l, n, a, o in fall_rows] +
          ["3 x 2 zones by the source squares (A-B, C-D, E-F; rows 1-2 / 3-4). Damage about a third of HP (D-6.2). "
           "Owners confirm a whole cell, flat, 256 clear, no water or lava. D1 moved off the grove (7 electrapedes)."])
    block(1, 'Requests to other lanes', requests)
    block(2, 'DECIDE (the plan is drawn on each default)',
          [f"{q}: {o}. Default {dft}; depends: {dep}." for q, o, dft, dep in questions])
    y = max(ys) + pad
    img = img.crop((0, 0, W, y))
    img.save(HERE / 'board_d7.png')
    img.convert('RGB').resize((W // 2, y // 2), Image.LANCZOS).save(HERE / 'board_d7_small.jpg', quality=88)
    return f, rows, hooks, corners, fall_rows, requests, questions


def page(f, rows, hooks, corners, fall_rows, requests, questions):
    e = html.escape

    def table(head, body):
        h = ''.join(f'<th>{e(x)}</th>' for x in head)
        b = ''.join('<tr>' + ''.join(f'<td>{e(str(c))}</td>' for c in r) + '</tr>' for r in body)
        return f'<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'
    parts = [
        '<!doctype html><html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<title>D7 Skyroads Board</title><style>',
        ':root{--bg:#f6f4ef;--ink:#1d1f24;--dim:#5b606b;--gold:#9a6a10;--line:#d9d4c8;--card:#fffdf8}',
        '@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#181a1f;--ink:#e8e8e8;'
        '--dim:#aab0ba;--gold:#ecc46e;--line:#33363d;--card:#202329}}',
        ':root[data-theme="dark"]{--bg:#181a1f;--ink:#e8e8e8;--dim:#aab0ba;--gold:#ecc46e;--line:#33363d;--card:#202329}',
        'body{background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,sans-serif;margin:0;padding:16px}',
        'main{max-width:1500px;margin:auto}h1,h2{color:var(--gold)}img{max-width:100%;height:auto;'
        'border:1px solid var(--line)}.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));'
        'gap:16px}table{border-collapse:collapse;width:100%;margin:8px 0}td,th{border:1px solid var(--line);'
        'padding:4px 6px;text-align:left;vertical-align:top}th{background:var(--card)}.wrap{overflow-x:auto}'
        'p.cap{color:var(--dim)}</style></head><body><main>',
        '<h1>D7 The Skyroads: phase 6 L1 review</h1>',
        '<p>A6 sub-agent, 2026-11-21. Brief: <code>devdocs/xeen/briefs/d7/L1</code> (oymap validate: no issues). '
        'The plan is drawn on every question\'s default.</p>',
        '<h2>MU-3 plan</h2><a href="plan_d7_2x.png"><img src="plan_d7.png" alt="D7 plan"></a>',
        '<p class="cap">SVG: <a href="plan_d7.svg">plan_d7.svg</a>, Olympus: <a href="plan_olympus.svg">plan_olympus.svg</a></p>',
        '<img src="plan_olympus.png" alt="Olympus plan">',
        '<h2>MU-4 concepts</h2><div class="two"><figure><img src="raw/d7_arrival_v1.png" alt="arrival concept">'
        '<figcaption>The arrival: the Dark Grove rope (blockout: <a href="blockout_arrival.png">blockout_arrival.png</a>)'
        '</figcaption></figure><figure><img src="raw/d7_signature_v1.png" alt="signature concept"><figcaption>The '
        'signature: Olympus across the cloud roads (blockout: <a href="blockout_signature.png">blockout_signature.png'
        '</a>)</figcaption></figure></div>',
        '<h2>Counts against MAPS</h2><div class="wrap">' + table(['Figure', 'Target', 'Plan'],
                                                                 [(a, b, c) for a, b, c, ok in rows]) + '</div>',
        '<h2>Hooks placed</h2><ul>' + ''.join(f'<li>{e(h)}</li>' for h in hooks) + '</ul>',
        '<h2>Corner contract</h2><div class="wrap">' + table(['Corner', 'Tip', 'Hook', 'Plane arrival', 'Return'],
                                                             corners) + '</div>',
        '<h2>Fall landings</h2><div class="wrap">' + table(['Zone', 'Landing (ground)', 'Near', 'Nearest actor', 'Owner'],
                                                           fall_rows) + '</div>',
        '<h2>Requests to other lanes</h2><ul>' + ''.join(f'<li>{e(r)}</li>' for r in requests) + '</ul>',
        '<h2>DECIDE</h2><div class="wrap">' + table(['Question', 'Options', 'Default', 'Depends'], questions) + '</div>',
        '<p class="cap">Full notes: devdocs/xeen/briefs/d7/L1/NOTES.md; measured figures: measure.json, falls.json.</p>',
        '</main></body></html>']
    (HERE / 'board_d7.html').write_text('\n'.join(parts))


def main():
    page(*board())
    print('board', HERE / 'board_d7.png')


if __name__ == '__main__':
    main()
