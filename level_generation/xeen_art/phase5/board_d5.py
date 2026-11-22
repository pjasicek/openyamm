#!/usr/bin/env python3
"""D5 Desert of Doom's review board (A6, phase 5): plan_d5.svg -> plan_d5.png, and board_d5.html -> board_d5.png, both
with headless Chrome under its own profile (phase5/d5/.chrome, deleted after use). The D4 and D6 edge strips are
inline SVG charts drawn from d5/edge_d4.json and d5/edge_d6.json.

    board_d5.py        (run d5_render.py first; the concepts are the highest raw/d5_<view>_vN.png)
"""
import json
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'd5'
PROFILE = OUT / '.chrome'

CSS = """
:root { --bg: #f4f1ea; --ink: #1d1d1f; --muted: #5d5a55; --rule: #d8d2c4; --accent: #6a3410; --card: #fffdf8;
        --nb: #2a78d6; --d5: #eb6834; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 15px/1.45 "DejaVu Sans", sans-serif; }
main { width: 1800px; padding: 28px 32px 36px; }
h1 { font-size: 30px; margin: 0 0 4px; }
h2 { font-size: 17px; margin: 18px 0 8px; color: var(--accent); text-transform: uppercase; letter-spacing: .04em; }
.sub { color: var(--muted); margin-bottom: 14px; max-width: 1720px; }
.grid { display: grid; grid-template-columns: 1090px 1fr; gap: 24px; align-items: start; }
.card { background: var(--card); border: 1px solid var(--rule); border-radius: 6px; padding: 12px 14px; }
.plan img { width: 1060px; height: 1060px; display: block; }
.concept img { width: 100%; display: block; border-radius: 4px; }
.concept p { margin: 6px 0 4px; color: var(--muted); font-size: 13.5px; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { text-align: left; padding: 3px 7px; border-bottom: 1px solid var(--rule); vertical-align: top; }
th { color: var(--muted); font-weight: 600; }
td.n { text-align: right; white-space: nowrap; }
.counts td:first-child { width: 46%; }
.ok { color: #1f6b35; font-weight: 600; } .warn { color: #a05a00; font-weight: 600; }
.legend span { display: inline-block; margin: 2px 14px 2px 0; font-size: 13px; }
.sw { display: inline-block; width: 12px; height: 12px; vertical-align: -1px; margin-right: 5px; border: 1px solid #555; }
.q li { margin: 7px 0; font-size: 13.5px; } .q b { color: #5a2a08; }
.inset img { width: 100%; display: block; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.small { font-size: 12.5px; color: var(--muted); }
code { font-size: 12.5px; }
.key { font-size: 12.5px; color: var(--muted); margin: 4px 0 0; }
.key i { display: inline-block; width: 22px; height: 0; vertical-align: 4px; margin-right: 5px; }
"""

LEGEND = """<div class="legend">
<span><i class="sw" style="background:#0b6b3a"></i>edge arrival</span>
<span><i class="sw" style="background:#111"></i>dungeon door, grate</span>
<span><i class="sw" style="background:#7a1f6a;border-radius:50%"></i>device (fountain, shrine, lamp, obelisk, boulders)</span>
<span><i class="sw" style="background:#1d5fa8;border-radius:50%"></i>talking person (Gurodel)</span>
<span><i class="sw" style="background:#b8860b;transform:rotate(45deg)"></i>chest</span>
<span><i class="sw" style="background:#c06000"></i>landmark</span>
<span><i class="sw" style="background:#5a4630;border-radius:50%"></i>fork, signpost</span>
<span><i class="sw" style="background:rgba(208,48,42,.25);border-color:#d0302a"></i>encounter area (lizards red, birds brown, cyclopes violet)</span>
<span><i class="sw" style="background:repeating-linear-gradient(45deg,#2e8b57 0 2px,transparent 2px 6px);border-color:#2e8b57"></i>kept clear</span>
<span><i class="sw" style="background:#7fe0b8"></i>Parabolic Barrier</span>
<span><i class="sw" style="background:#1f6fd1;opacity:.6"></i>MU-4 cameras</span>
</div>"""


def chrome(page, png, width, height):
    subprocess.run(['google-chrome', '--headless=new', '--disable-gpu', '--no-sandbox', f'--user-data-dir={PROFILE}',
                    '--hide-scrollbars', f'--window-size={width},{height}', '--virtual-time-budget=6000',
                    f'--screenshot={png}', page.as_uri()], check=True, capture_output=True, timeout=180)


def plan_png():
    page = OUT / '_plan.html'
    page.write_text('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;background:#fff}'
                    'img{display:block;width:1084px;height:1084px}</style></head><body><img src="plan_d5.svg">'
                    '</body></html>')
    chrome(page, OUT / 'plan_d5.png', 1084, 1084)
    page.unlink()


def edge_chart(rows, a_key, b_key, a_name, b_name, spans, marks, caption):
    """Two border lines along y 0-127 on one axis (the neighbour's and D5's), the spans shaded, a <title> per
    sampled point for hover."""
    w, h, left, right, top, bottom = 640, 250, 46, 12, 14, 34
    pw, ph = w - left - right, h - top - bottom
    hmax = 3600

    def X(x):
        return left + x / 127 * pw

    def Y(v):
        return top + ph - v / hmax * ph
    parts = [f'<svg viewBox="0 0 {w} {h}" width="100%" font-family="DejaVu Sans, sans-serif" font-size="11">']
    shade = ['#efeae0', '#f7f4ee']
    for i, s in enumerate(spans):
        a, b = s['span']
        parts.append(f'<rect x="{X(a):.1f}" y="{top}" width="{X(min(b, 127)) - X(a):.1f}" height="{ph}" '
                     f'fill="{shade[i % 2]}"/>')
        hv = s['height']
        label = f"{hv / 1000:g}k" if not isinstance(hv, list) else f"{hv[0] / 1000:g}-{hv[1] / 1000:g}k"
        parts.append(f'<text x="{(X(a) + X(min(b, 127))) / 2:.1f}" y="{top + 11 + 11 * (i % 2)}" '
                     f'text-anchor="middle" fill="#5d5a55" font-size="9.5">{label}</text>')
    for v in range(0, hmax + 1, 800):
        parts.append(f'<line x1="{left}" x2="{w - right}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="#d8d2c4" '
                     'stroke-width="0.6"/>')
        parts.append(f'<text x="{left - 5}" y="{Y(v) + 3.5:.1f}" text-anchor="end" fill="#5d5a55">{v:,}</text>')
    for x in marks:
        parts.append(f'<text x="{X(x):.1f}" y="{h - bottom + 14}" text-anchor="middle" fill="#5d5a55">{x}</text>')
    parts.append(f'<text x="{left + pw / 2}" y="{h - 4}" text-anchor="middle" fill="#5d5a55">{caption}</text>')
    for key, colour, dash, name in ((a_key, 'var(--nb)', '', a_name), (b_key, 'var(--d5)', ' stroke-dasharray="6 3"',
                                                                         b_name)):
        pts = ' '.join(f'{X(x):.1f},{Y(v):.1f}' for x, v in zip(rows['y'], rows[key]))
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{colour}" stroke-width="2"{dash} '
                     'stroke-linejoin="round"/>')
        for x, v in zip(rows['y'][::8], rows[key][::8]):
            parts.append(f'<circle cx="{X(x):.1f}" cy="{Y(v):.1f}" r="6" fill="transparent"><title>{name}: y {x}, '
                         f'{v:,}</title></circle>')
    parts.append('</svg>')
    return '\n'.join(parts)


def span_rows(spans, a, b):
    out = ''
    for s in spans:
        hv = s['height'] if not isinstance(s['height'], list) else '-'.join(f'{v:,}' for v in s['height'])
        out += (f"<tr><td>{s['span'][0]}-{s['span'][1]}</td><td>{s['form']} {hv}</td><td class='n'>{s[a]:,}</td>"
                f"<td class='n'>{s[b]:,}</td><td class='n'>{s['mean_abs_diff']:,}</td></tr>")
    return out


def page(m, e4, e6, arrival, signature):
    ff = m['first_fight']
    quiet = round(m['quiet_share'] * 100)
    areas = {a['id']: a for a in m['areas']}
    kill = m['kill_xp_per_member']
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>D5 Desert mock-ups</title>
<style>{CSS}</style></head><body><main>
<h1>D5 Desert of Doom and the Great Pyramid: MU-3 plan and MU-4 concepts</h1>
<div class="sub">Phase 5 review (A6, 2026-11-20), for a decider before any geometry. Darkside's top middle, Act V
wilderness (party 42-45), the world rim on its north side. A desert basin under the amber day: the <b>Perishing
Sands</b> east and south with a salt pan, and rising alone from the dunes the <b>Great Pyramid</b> (DD-15, m28.door);
the stony <b>Desert of Doom</b> west (the obelisk, the Last Water's +2 Endurance fountain, the Shrine of Great Power
on a mesa). The <b>Griffin Cliffs</b> lift the giants' <b>northern highlands</b>: Gurodel's hold and the great doors
of DD-24, Bosco's Hall (DD-25), the Northern Tower (DD-08) at the vertex of the <b>Parabolic Barrier</b>, a bowed line
of Ancient frames with a shimmering curtain before the rim. The <b>Quivering Forest</b> of trembling aspens holds a
wild cyclopes' lair. The seven <b>Enchanted Boulders</b> stand by the road; the broken travel pyramid's capstone hides
the obelisk hoard; DD-18's tunnel ends at a grate in the south-east. Source: <code>devdocs/xeen/briefs/d5/L1/</code>
(project, plan, sketch in Map Studio's schema, NOTES.md; <code>oymap validate</code> clean).</div>
<div class="grid">
<div>
 <div class="card plan"><img src="plan_d5.png"></div>
 <div class="card" style="margin-top:12px">{LEGEND}
 <div style="margin-top:6px;color:#5d5a55;font-size:13px">128 x 128 cells of 512 units, north up; the dashed white
 square is the playable area (cells 19-109). The land ends in the rim cliff at y 24; the strip behind the Barrier
 (410 cells) is not counted as land. <b>Shared edges:</b> the desert road crosses the east edge at <b>y 80</b> (D-36,
 D4 installed); the road crosses the west edge over the Forbidden Zone pass at <b>y 64</b>
 (<code>edge_d5_d6.json</code>, D6 planned beside this). South (D2) is closed high ground.</div></div>
 <div class="two" style="margin-top:12px">
 <div class="card inset"><h2 style="margin-top:0">D4 edge (D5 x 109 = D4 x 19)</h2>
  {edge_chart(e4['rows'], 'd4_border_x19', 'd5_border_x109', 'D4 installed x 19', 'D5 plan x 109', e4['spans'],
              (0, 24, 60, 72, 80, 88, 104, 127), 'y (cells); the crossing at y 80')}
  <div class="key"><i style="border-top:2px solid var(--nb)"></i>D4 installed (x 19)
  &nbsp; <i style="border-top:2px dashed var(--d5)"></i>D5 plan (x 109)</div>
  <table style="margin-top:6px"><tr><th>Span</th><th>Form (both maps)</th><th class="n">D4</th><th class="n">D5</th>
  <th class="n">diff</th></tr>{span_rows(e4['spans'], 'd4_border_mean', 'd5_border_mean')}</table>
  <p class="small">D5's east rim repeats D4's west-rim spans word for word; the border column carries D4's installed
  heights cell for cell (the drawing's land model; the build sets them). At the road: D4 {e4['road']['d4_at_x19_y80']:,},
  D5 {e4['road']['d5_at_x109_y80']:,}.</p></div>
 <div class="card inset"><h2 style="margin-top:0">D6 edge (shared file)</h2>
  {edge_chart(e6['rows'], 'shared_x19', 'd5_border_x19', 'edge_d5_d6.json', 'D5 plan x 19', e6['spans'],
              (0, 24, 58, 64, 70, 104, 127), 'y (cells); the pass at y 64 (1,700)')}
  <div class="key"><i style="border-top:2px solid var(--nb)"></i>edge_d5_d6.json
  &nbsp; <i style="border-top:2px dashed var(--d5)"></i>D5 plan (x 19)</div>
  <table style="margin-top:6px"><tr><th>Span</th><th>Form (both maps)</th><th class="n">file</th><th class="n">D5</th>
  <th class="n">diff</th></tr>{span_rows(e6['spans'], 'shared_mean', 'd5_border_mean')}</table>
  <p class="small">D5's west column is the shared file cell for cell (the pass 1,696 at y 62-66). D5's west rim repeats
  D6's east-rim spans and heights. South: D2's y 19 row continued, mean difference
  {m['edge_d2_south']['mean_abs_diff']} (320 only in the corner, where D6's file wins).</p></div>
 </div>
 <div class="card" style="margin-top:12px"><h2 style="margin-top:0">Encounter areas and the People</h2>
 <table>
 <tr><th>Area</th><th>Monsters (A2's rows)</th><th class="n">4,096²</th><th class="n">At load</th></tr>
 <tr><td>E1 Perishing Sands</td><td>Iguanasaurus 42 / Great 50 / Ancient 55 (Dif 3), 8 markers [2,3]: first fight from D4</td><td class="n">{areas['pop:sands_lizards']['big_cells']}</td><td class="n">20</td></tr>
 <tr><td>E2 the pyramid's dunes</td><td>the same, 7 markers</td><td class="n">{areas['pop:pyramid_lizards']['big_cells']}</td><td class="n">17.5</td></tr>
 <tr><td>E3 Griffin Cliffs</td><td>Vulture Roc 30 / Roc 38 / Griffin 48 (Dif 2), 11 markers [1,3]; 3 Griffins placed at the eyrie</td><td class="n">{areas['pop:cliff_birds']['big_cells']}</td><td class="n">25</td></tr>
 <tr><td>E4 Quivering Forest</td><td>wild Cyclops 36 / Giant 50 / Elder Giant 62 (Dif 1), 11 markers [2,3]: the source's C1 lair</td><td class="n">{areas['pop:forest_cyclopes']['big_cells']}</td><td class="n">27.5</td></tr>
 <tr><td>E5 Desert of Doom</td><td>rocs (Dif 2), 10 markers: first fight from D6</td><td class="n">{areas['pop:doom_birds']['big_cells']}</td><td class="n">20</td></tr>
 <tr><td>The People at Gurodel's hold (peaceful)</td><td>D-47's rows 11083 Cyclops 38 x3, 11084 Giant 50 x2, 11085 Elder Giant 58 x1, faction <code>xeen_giants_people</code>; Gurodel 5452 talking. Not in the 110; at war +{m['people_war_xp_per_member']:,} per member</td><td class="n">keep clear</td><td class="n">0 (6)</td></tr>
 </table></div>
 <div class="card" style="margin-top:12px"><h2 style="margin-top:0">A3's hooks and A4's people on D5</h2>
 <table>
 <tr><th>Hook / person</th><th>Where</th></tr>
 <tr><td><code>m28.door</code></td><td>the Great Pyramid's north door, green stone, two leaves (64, 80)</td></tr>
 <tr><td><code>q-d17.tower_door</code></td><td>the Northern Tower at the Barrier's vertex (69, 40), "Grnd rdr f Vwlss Knghts"</td></tr>
 <tr><td><code>q-d24.sign</code>, <code>boulder_1..7</code>, <code>answer</code></td><td>the boulder field by the road (86, 80); boulders (83-87, 81-87)</td></tr>
 <tr><td><code>obelisks.d5</code></td><td>a red knoll by the west road (46, 72)</td></tr>
 <tr><td><code>obelisks.dark_hoard</code></td><td>the broken travel pyramid's capstone in the east valley (94, 74)</td></tr>
 <tr><td><code>dd18.d5_grate</code></td><td>the tunnel grate in the south hills' foot (101, 102), arrival facing north</td></tr>
 <tr><td>DD-24 doors, <code>entrance:d5_hold</code></td><td>the hillside behind Gurodel's fire (86, 42), two leaves 384 x 512 (<code>xdgiantd</code> mirrored), return 512 south</td></tr>
 <tr><td>Gurodel 5452 (Q-D16)</td><td>at his fire (86, 46), with the People</td></tr>
 </table></div>
</div>
<div>
 <div class="card concept"><h2 style="margin-top:0">MU-4 arrival view (from D4)</h2>
  <img src="{arrival}">
  <p>Camera at the D4 arrival (105, 80), 180 above the road, looking west out of the last firs of the Forest of
  Peril: the road down past the boulder field and its sign, the Great Pyramid far off over the dunes, the broken
  travel pyramid on the right-hand slope, the Griffin Cliffs and the Barrier's frames faint on the highlands.
  <b>Against the plan:</b> the road is painted as paving (the plan has a stony earth track, MU-2's soil_stony); the
  broken pyramid stands nearer the road than its 10 cells; the boulders are fewer and smaller than the seven great
  Enchanted Boulders. L3 keeps the plan.</p></div>
 <div class="card concept"><h2>MU-4 signature view: the Great Pyramid from the dunes</h2>
  <img src="{signature}">
  <p>Camera on the great dune south-east of the pyramid (82, 98), about 60 degrees, looking north-west (11,300 from
  the apex): the pyramid alone in the sand, its gilded capstone, the robbers' tent at its corner, the pale sun in
  the amber band, the cliffs and the Barrier beyond. <b>Why this and not the boulder field:</b> the pyramid is the
  map's name and its story (M28-M30, the Pharaoh), seen from both arrivals; the boulder field is a side quest and
  gets a tour shot at L3. <b>Against the plan:</b> the courses read as steps and a carved dragon frieze runs round the
  foot (a good idea for L3: one frieze band, seamless along its axis); the trees on the left are not in the plan.</p></div>
 <div class="card"><h2 style="margin-top:0">Against MAPS (D5 sheet, §0 checklist)</h2>
 <table class="counts">
 <tr><th>Figure</th><th class="n">Plan</th><th>Target</th><th></th></tr>
 <tr><td>Hostiles at load</td><td class="n">{m['hostiles_at_load']:g}</td><td>110</td><td class="ok">ok</td></tr>
 <tr><td>Kill XP per member (MM7 tier odds)</td><td class="n">{kill:,}</td><td>52.3k ±15 %</td><td class="ok">+{(kill / 52300 - 1) * 100:.1f} %</td></tr>
 <tr><td>Spawn markers (+ placed hostiles)</td><td class="n">{m['markers']} (+{m['placed_hostile']})</td><td>45-70</td><td class="ok">ok</td></tr>
 <tr><td>Encounter areas (4,096²)</td><td class="n">5: 6.6-11.8</td><td>3-8 of 6-30</td><td class="ok">ok</td></tr>
 <tr><td>Quiet land (behind the Barrier not counted)</td><td class="n">{quiet} %</td><td>at least a third</td><td class="ok">ok</td></tr>
 <tr><td>POIs (D-20 census; the boulder field one set piece)</td><td class="n">{m['poi_spots']}</td><td>desert band 20-25</td><td class="ok">ok ({m['poi_spots_if_boulders_counted_singly']} if singly)</td></tr>
 <tr><td>Outdoor chests, each with a reason</td><td class="n">{m['outdoor_chests']}</td><td>4-10</td><td class="ok">ok</td></tr>
 <tr><td>Dungeon entrances</td><td class="n">{m['dungeon_entrances']}</td><td>3-6</td><td class="ok">ok</td></tr>
 <tr><td>Relief inside the box (land)</td><td class="n">{m['height_min_land_box']:,}-{m['height_max_land_box']:,}</td><td>at least 2,500</td><td class="ok">{m['relief_box']:,}</td></tr>
 <tr><td>First fight from the D4 arrival</td><td class="n">{ff['entrance:d4_road'][0][0]:,}</td><td>2,000-6,000</td><td class="ok">ok</td></tr>
 <tr><td>First fight from the D6 arrival</td><td class="n">{ff['entrance:d6_pass'][0][0]:,}</td><td>2,000-6,000</td><td class="ok">ok</td></tr>
 <tr><td>Nearest fight: grate / pyramid / Bosco / DD-24 doors</td><td class="n">{ff['entrance:dd18_grate'][0][0]:,} / {ff['entrance:dd15_door'][0][0]:,} /<br>{ff['entrance:dd25_door'][0][0]:,} / {ff['entrance:dd24_doors'][0][0]:,}</td><td>6,000 rule; Bosco 2,500</td><td class="ok">ok</td></tr>
 <tr><td>6,000 rule; wild land (D-11.5)</td><td class="n">{m['farthest_land_from_anything'][0]:,}; {m['wild_land_share_over_3000']}</td><td>&le; 6,000; &le; 0.16</td><td class="ok">ok</td></tr>
 <tr><td>Roads + lanes</td><td class="n">{m['road_share'] * 100:.1f} % + {m['lane_share'] * 100:.1f} %</td><td>1-4 %</td><td class="ok">ok</td></tr>
 <tr><td>Obelisk; permanent devices (Endurance +2, Air resistance +5)</td><td class="n">1; 2</td><td>1; at least 1</td><td class="ok">ok</td></tr>
 <tr><td>Device kinds (fountains, shrine, lamps, boulders, capstone, lair)</td><td class="n">6</td><td>&ge; 4</td><td class="ok">ok</td></tr>
 <tr><td>New textures (cap 12)</td><td class="n">2 proposed</td><td>&le; 12</td><td class="ok">ok</td></tr>
 </table></div>
 <div class="card q" style="margin-top:12px"><h2 style="margin-top:0">Open questions (DECIDE)</h2>
 <ol>
 <li><b>The People while peaceful.</b> (a) 6 placed at the hold (D-47's rows), not in the 110 at load, their
 {m['people_war_xp_per_member']:,} per member counted only on the war route (as D-1.2 keeps trap kills out); (b) count
 them in the 110 and trim the wild areas; (c) only Gurodel on D5. Proposed: (a).</li>
 <li><b>The Quivering Forest's giants.</b> (a) wild cyclopes on the ordinary giants rows (11080-11082) round the
 source's C1 lair with its "Destroy?" device, not the People; (b) a second People camp (peaceful, then the 27.5
 go to lizards and birds). Proposed: (a).</li>
 <li><b>The Enchanted Boulders.</b> (a) one set piece in the census (23 POIs); after the answer each of the other six
 "disappears and leaves behind..." a treasure item, no chests; (b) seven spots (30 POIs: then cut the three signpost
 clicks, the dwarf camp and a lamp); (c) six small chests at the boulders. Proposed: (a).</li>
 <li><b>The Parabolic Barrier</b> (the source has only the name, a mirror destination). (a) a landmark: a bowed line
 of Ancient frames (<code>gn_mtl</code>, <code>xaenergy</code>) with a <code>xafield</code> curtain that cannot be
 crossed, the rim behind it, no event; (b) also a device: a touch shocks (Air damage, a line); (c) also a mirror
 destination. Proposed: (a).</li>
 <li><b>Three +2 Endurance places</b> (X6's oasis, X3's spring, DD-18's brew; MAPS gives D5 a fourth). (a) keep;
 (b) D5's fountain gives another stat (Personality); (c) drop it, the energy fountain's +5 Air resistance is D5's
 permanent device. Proposed: (a), cheapest to change at L4.</li>
 <li><b>The Great Pyramid's size.</b> (a) 12 x 12 cells, about 3,600 high (Giza's slope), seen from both arrivals;
 (b) 8 x 8, 2,400. A8's DD-15 inside is independent. Proposed: (a).</li>
 <li><b>The broken travel pyramid</b> moved from the source's D1 highlands to the east valley by the road, so the
 arrival sees it and the hoard is reachable without the cliffs. Keep, or put it on the highlands. Proposed: keep.</li>
 <li><b>Rescaled devices.</b> Shrine of Great Power +15 all stats until rest, daily (the source's +15 levels; D1's
 +3 levels became +10 all); Fountain of Might +20 Might until rest, daily; energy fountain +5 Air resistance,
 permanent (D-4). Accept, or other values.</li>
 </ol></div>
</div></div></main></body></html>"""


def trim(png):
    """Cut the empty page below the last card."""
    import numpy as np
    from PIL import Image
    im = Image.open(png).convert('RGB')
    a = np.asarray(im)
    rows = np.where((a != a[-1, -1]).any(axis=(1, 2)))[0]
    im.crop((0, 0, im.width, min(im.height, int(rows.max()) + 36))).save(png)


def main():
    m = json.loads((OUT / 'measure.json').read_text())
    e4 = json.loads((OUT / 'edge_d4.json').read_text())
    e6 = json.loads((OUT / 'edge_d6.json').read_text())
    pick = {}
    for path in sorted((OUT / 'raw').glob('d5_*_v*.png')):
        pick[path.stem.split('_')[1]] = f'raw/{path.name}'      # the highest version wins
    try:
        plan_png()
        html = page(m, e4, e6, pick.get('arrival', 'blockout_arrival.png'),
                    pick.get('signature', 'blockout_signature.png'))
        (OUT / 'board_d5.html').write_text(html)
        chrome(OUT / 'board_d5.html', OUT / 'board_d5.png', 1800, 4400)
        trim(OUT / 'board_d5.png')
    finally:
        shutil.rmtree(PROFILE, ignore_errors=True)
    print(OUT / 'board_d5.png')


if __name__ == '__main__':
    main()
