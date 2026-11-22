#!/usr/bin/env python3
"""D6 The Forbidden Zone's review board (A6, phase 5): plan_d6.svg -> plan_d6.png, and board_d6.html ->
board_d6.png, both with headless Chrome under its own profile (phase5/d6/.chrome, deleted after use). The two edge
strips (D1 south, D5 east) are inline SVG charts drawn from d6/edge_d1.json and d6/edge_d5.json.

    board_d6.py        (run d6_render.py first; the concepts are the highest raw/d6_<view>_vN.png)
"""
import json
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'd6'
PROFILE = OUT / '.chrome'

CSS = """
:root { --bg: #f4f1ea; --ink: #1d1d1f; --muted: #5d5a55; --rule: #d8d2c4; --accent: #7a2a08; --card: #fffdf8;
        --other: #2a78d6; --d6: #eb6834; }
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
ul.req li { font-size: 13px; margin: 4px 0; }
"""

LEGEND = """<div class="legend">
<span><i class="sw" style="background:#0b6b3a"></i>arrival / entrance</span>
<span><i class="sw" style="background:#111"></i>dungeon door, gate</span>
<span><i class="sw" style="background:#7a1f6a;border-radius:50%"></i>device (fountain, well, books, lamp, obelisk)</span>
<span><i class="sw" style="background:#1d5fa8;border-radius:50%"></i>talking person</span>
<span><i class="sw" style="background:#b8860b;transform:rotate(45deg)"></i>chest</span>
<span><i class="sw" style="background:#c06000"></i>landmark</span>
<span><i class="sw" style="background:#5a4630;border-radius:50%"></i>fork, signpost, mine mouth</span>
<span><i class="sw" style="background:rgba(208,48,42,.25);border-color:#d0302a"></i>encounter area (gazers red, robots teal, lava dwellers orange, griffins brown, archers violet)</span>
<span><i class="sw" style="background:repeating-linear-gradient(45deg,#2e8b57 0 2px,transparent 2px 6px);border-color:#2e8b57"></i>kept clear</span>
<span><i class="sw" style="background:#1f6fd1;opacity:.6"></i>MU-4 cameras</span>
<span><i class="sw" style="background:#ec6a1c"></i>lava (lavtyl)</span>
<span><i class="sw" style="background:#5fe0f0"></i>energy fields</span>
</div>"""


def chrome(page, png, width, height):
    subprocess.run(['google-chrome', '--headless=new', '--disable-gpu', '--no-sandbox', f'--user-data-dir={PROFILE}',
                    '--hide-scrollbars', f'--window-size={width},{height}', '--virtual-time-budget=6000',
                    f'--screenshot={png}', page.as_uri()], check=True, capture_output=True, timeout=180)


def plan_png():
    page = OUT / '_plan.html'
    page.write_text('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;background:#fff}'
                    'img{display:block;width:1084px;height:1084px}</style></head><body><img src="plan_d6.svg">'
                    '</body></html>')
    chrome(page, OUT / 'plan_d6.png', 1084, 1084)
    page.unlink()


def edge_chart(xs, other, mine, spans, other_name, mine_name, axis, marks, crossing, hmax=4000):
    """Two height series along one border: the neighbour's (installed row or shared file) and D6's plan; the rim
    spans shaded and labelled; a <title> on every eighth point for hover."""
    w, h, left, right, top, bottom = 640, 250, 46, 12, 14, 34
    pw, ph = w - left - right, h - top - bottom

    def X(x):
        return left + x / 127 * pw

    def Y(v):
        return top + ph - v / hmax * ph
    parts = [f'<svg viewBox="0 0 {w} {h}" width="100%" font-family="DejaVu Sans, sans-serif" font-size="11">']
    shade = ['#efeae0', '#f7f4ee']
    for i, s in enumerate(spans):
        a, b = s['span']
        parts.append(f'<rect x="{X(a):.1f}" y="{top}" width="{X(b) - X(a):.1f}" height="{ph}" fill="{shade[i % 2]}"/>')
        hv = s['height']
        label = f"{hv / 1000:g}k" if not isinstance(hv, list) else f"{hv[0] / 1000:g}-{hv[1] / 1000:g}k"
        parts.append(f'<text x="{(X(a) + X(b)) / 2:.1f}" y="{top + 11 + 11 * (i % 2)}" text-anchor="middle" '
                     f'fill="#5d5a55" font-size="9.5">{label}</text>')
    for v in range(0, hmax + 1, 1000):
        parts.append(f'<line x1="{left}" x2="{w - right}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="#d8d2c4" '
                     'stroke-width="0.6"/>')
        parts.append(f'<text x="{left - 5}" y="{Y(v) + 3.5:.1f}" text-anchor="end" fill="#5d5a55">{v:,}</text>')
    for x in marks:
        parts.append(f'<text x="{X(x):.1f}" y="{h - bottom + 14}" text-anchor="middle" fill="#5d5a55">{x}</text>')
    parts.append(f'<text x="{left + pw / 2}" y="{h - 4}" text-anchor="middle" fill="#5d5a55">{axis}</text>')
    parts.append(f'<line x1="{X(crossing):.1f}" x2="{X(crossing):.1f}" y1="{top}" y2="{top + ph}" stroke="#5d5a55" '
                 'stroke-width="0.8" stroke-dasharray="3 3"/>')
    for series, colour, dash, name in ((other, 'var(--other)', '', other_name),
                                       (mine, 'var(--d6)', ' stroke-dasharray="6 3"', mine_name)):
        pts = ' '.join(f'{X(x):.1f},{Y(v):.1f}' for x, v in zip(xs, series))
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{colour}" stroke-width="2"{dash} '
                     'stroke-linejoin="round"/>')
        for x, v in zip(xs[::8], series[::8]):
            parts.append(f'<circle cx="{X(x):.1f}" cy="{Y(v):.1f}" r="6" fill="transparent"><title>{name}: {x}, '
                         f'{v:,}</title></circle>')
    parts.append('</svg>')
    return '\n'.join(parts)


def page(m, e1, e5, arrival, signature):
    ff = m['first_fight']
    quiet = round(m['quiet_share'] * 100)
    areas = {a['id']: a for a in m['areas']}
    near = m['nearest_fight_to']
    chart1 = edge_chart(e1['rows']['x'], e1['rows']['d1_border_y19'], e1['rows']['d6_border_y109'], e1['spans'],
                        'D1 installed y 19', 'D6 plan y 109', 'x (cells); the road at x 64; the box from x 19',
                        (0, 19, 24, 59, 64, 70, 80, 88, 100, 109, 127), 64)
    chart5 = edge_chart(e5['rows']['y'], e5['rows']['file_x109'], e5['rows']['d6_border_x109'], e5['spans'],
                        'edge_d5_d6.json', 'D6 plan x 109', 'y (cells); the pass at y 64; the box from y 19',
                        (0, 19, 24, 58, 64, 70, 90, 109, 127), 64)
    rows1 = ''.join(
        f"<tr><td>{s['span'][0]}-{s['span'][1]}</td><td>{s['form']} "
        f"{s['height'] if not isinstance(s['height'], list) else '-'.join(f'{v:,}' for v in s['height'])}</td>"
        f"<td class='n'>{s['d1_border_mean']:,}</td><td class='n'>{s['d6_border_mean']:,}</td>"
        f"<td class='n'>{s['mean_abs_diff']:,}</td></tr>" for s in e1['spans'])
    rows5 = ''.join(
        f"<tr><td>{s['span'][0]}-{s['span'][1]}</td><td>{s['form']} "
        f"{s['height'] if not isinstance(s['height'], list) else '-'.join(f'{v:,}' for v in s['height'])}</td>"
        f"<td class='n'>{s['file_mean']:,}</td><td class='n'>{s['d6_border_mean']:,}</td>"
        f"<td class='n'>{s['mean_abs_diff']:,}</td></tr>" for s in e5['spans'])
    corner = e5['pass']['corner_y106_109']
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>D6 Forbidden Zone mock-ups</title>
<style>{CSS}</style></head><body><main>
<h1>D6 The Forbidden Zone: MU-3 plan and MU-4 concepts</h1>
<div class="sub">Phase 5 review (A6, 2026-11-20), for a decider before any geometry. Darkside's north-west corner, Act V
trap and endgame map (party 48-51), the world rim on its north and west sides, ash falling on 40 % of days. <b>Castle
Alamar</b> (DD-17) stands on a basalt mesa in a horseshoe moat of lava north-west of the middle, every window lit,
energy fields on its approach; after M33 a ruin with the sealed stair to FD-01. The moat spills over both rims and down
the Burning Channel into <b>Corak's lava lake</b>, where Escape Pod 1 (DD-16) stands nose-up; <b>Sheltem's pod</b>
(DD-22, sealed) lies in the <b>Ancient field</b> to the north-east. <b>Necropolis</b> (A4's 12 doors and the mirror,
the pass-gate, DD-21's stair) sits walled under the east ridge by the border pass to D5. The long mountain road from
Castleview tops <b>Griffin Pass</b>, Ambrose's camp. Source: <code>devdocs/xeen/briefs/d6/L1/</code> (project, plan,
sketch, atmosphere in Map Studio's schema, NOTES.md; <code>oymap validate</code> clean).</div>
<div class="grid">
<div>
 <div class="card plan"><img src="plan_d6.png"></div>
 <div class="card" style="margin-top:12px">{LEGEND}
 <div style="margin-top:6px;color:#5d5a55;font-size:13px">128 x 128 cells of 512 units, north up; the dashed white
 square is the playable area (cells 19-109). The land ends in rim cliffs at y 24 (north) and x 24 (west). <b>Shared
 edges:</b> the mountain road crosses the south edge at <b>x 64</b> (D1 installed); the border pass crosses the east
 edge at <b>y 64</b> (<code>edge_d5_d6.json</code>, D5 planned beside this).</div></div>
 <div class="two" style="margin-top:12px">
 <div class="card inset"><h2 style="margin-top:0">Necropolis and Corak's lake (3.2x)</h2>
  <img src="plan_d6.svg#svgView(viewBox(540,500,330,330))">
  <p class="small">Walls 18 x 16 cells, one gate in the north wall (the pass, item 12336). Inside: the guild 4751 and
  the Warm Barrel 4755 (its barrel "Food for the dead, keep warm." by the door) west of the square, the Grave Market
  4753 and the Embalmer 4754 east, the Temple of the Dead 4752 south; the mirror 4756 with the talking skull; the Books
  of the Dead; six tombs 4757-4762; DD-21's crypt stair in the south-east corner. West: the pod in its lava lake, the
  hatch on the crust facing the shore (m29.pod_door; D-47: arrival entrance:d6_hatch, the way out 384 before it).</p></div>
 <div class="card inset"><h2 style="margin-top:0">Castle Alamar (3.6x)</h2>
  <img src="plan_d6.svg#svgView(viewBox(270,250,290,290))">
  <p class="small">The mesa (to 2,300) in its horseshoe moat (1,550), open to the south: the approach ramp with four
  energy-field pylons, the double gate (m33.castle_door; DD-17 throws a party without the Soul Box back out here).
  After M33 (set:alamar): a smoking ruin, fields dark, the stair to FD-01 in the broken gatehouse (m39.depths_door; one
  POI spot with the gate). Robot patrols on the mesa and the approach.</p></div>
 </div>
 <div class="two" style="margin-top:12px">
 <div class="card inset"><h2 style="margin-top:0">D1 edge (south, x 0-127)</h2>
  {chart1}
  <div class="key"><i style="border-top:2px solid var(--other)"></i>D1 installed (y 19)
  &nbsp; <i style="border-top:2px dashed var(--d6)"></i>D6 plan (y 109)</div>
  <table style="margin-top:6px"><tr><th>Span</th><th>D6 rim form</th><th class="n">D1</th><th class="n">D6</th>
  <th class="n">diff</th></tr>{rows1}</table>
  <p class="small">The border row repeats D1's installed row cell for cell (the sketch carries it as height points;
  at x 64 both {e1['road']['d1_at_x64_y19']:,}). D1's Sardaj spring pool (832, x 81-87) lies on the border: D6's
  peaks drop to it in a cliff. D6's south strip pictures D1's vale (1,100-1,600), not D1's own rim forms (those
  picture D6's peaks).</p></div>
 <div class="card inset"><h2 style="margin-top:0">D5 edge (east, y 0-127)</h2>
  {chart5}
  <div class="key"><i style="border-top:2px solid var(--other)"></i>edge_d5_d6.json (x 109)
  &nbsp; <i style="border-top:2px dashed var(--d6)"></i>D6 plan (x 109)</div>
  <table style="margin-top:6px"><tr><th>Span</th><th>D6 rim form</th><th class="n">file</th><th class="n">D6</th>
  <th class="n">diff</th></tr>{rows5}</table>
  <p class="small">Equal at every cell y 0-105 (the pass 1,696 over y 62-66). <b>The corner</b> (109, 106-109) cannot
  match both: the file says {', '.join(f'{v:,}' for v in corner['file'])}; D1's installed row says
  {corner['d1_x109_y19']:,} at (109, 109); the plan blends to D1's ({', '.join(f'{v:,}' for v in corner['d6'])}).
  See the open questions.</p></div>
 </div>
 <div class="card" style="margin-top:12px"><h2 style="margin-top:0">Encounter areas</h2>
 <table>
 <tr><th>Area</th><th>Monsters (A2's rows)</th><th class="n">4,096²</th><th class="n">At load</th></tr>
 <tr><td>E1 the Ancient field</td><td>Floating Eye 40, Terrible Eye 50, Gamma Gazer 65 (Dif 2), 17 markers [1,3]</td><td class="n">{areas['pop:field_gazers']['big_cells']}</td><td class="n">34</td></tr>
 <tr><td>E2 Alamar's mesa and approach</td><td>Patrol 50, Annihilator 62, Autobot 75 (Dif 1), 9 markers [1,3]; off after M33</td><td class="n">{areas['pop:alamar_robots']['big_cells']}</td><td class="n">18</td></tr>
 <tr><td>E3 Corak's lake (placed)</td><td>Lesser Elemental 55 x11, Elemental 62 x3: the lava dwellers' stand-in</td><td class="n">{areas['pop:lava_dwellers']['big_cells']}</td><td class="n">14</td></tr>
 <tr><td>E4a/E4b the southern peaks</td><td>Vulture Roc 30, Roc 38, Griffin 48 (Dif 5: 10/50/40), 8 + 8 markers [1,3]</td><td class="n">{areas['pop:west_griffins']['big_cells']} + {areas['pop:east_griffins']['big_cells']}</td><td class="n">32</td></tr>
 <tr><td>E6 the archers' camp (placed)</td><td>Barbarian Archer 44 x9, Archer Chief 50 x3 (new tiers asked of A2)</td><td class="n">{areas['pop:archers']['big_cells']}</td><td class="n">12</td></tr>
 </table></div>
 <div class="card" style="margin-top:12px"><h2 style="margin-top:0">A3's hooks and A4's people placed</h2>
 <table>
 <tr><th>Hook / person</th><th>Where</th></tr>
 <tr><td><code>m25.flight</code>, Ambrose 5512</td><td>Griffin Pass (61, 95): his camp and tethered griffin at the top of D1's road</td></tr>
 <tr><td><code>m29.pod_door</code> (reads 111564)</td><td>the hatch on the crust (74, 70), arrival entrance:d6_hatch (D-47); the lava there turns to crust (set:pod_lava)</td></tr>
 <tr><td><code>m33.castle_door</code></td><td>Alamar's double gate on the approach (51, 55); DD-17's refusal lands here</td></tr>
 <tr><td><code>m39.depths_door</code></td><td>the stair in the ruin's gatehouse floor (51, 55), shown after m33.done</td></tr>
 <tr><td><code>obelisks.d6</code></td><td>Obelisk Knoll by the west rim (30, 62)</td></tr>
 <tr><td>Necropolis gate (needs a hook)</td><td>the north wall's gate (91, 74): item 12336</td></tr>
 <tr><td>Q-D23: Master Morbius 5506</td><td>the Necromancers' House (4757); DD-21's stair (98, 88)</td></tr>
 <tr><td>DD-10C <code>exit:d6_adit</code></td><td>the north adit (46, 97); the return point outside it, facing north (L3)</td></tr>
 <tr><td>Freeda (no row)</td><td>her camp under the east ridge (100, 69)</td></tr>
 </table></div>
</div>
<div>
 <div class="card concept"><h2 style="margin-top:0">MU-4 arrival view (from D1)</h2>
  <img src="{arrival}">
  <p>Camera on Griffin Pass (64, 96), 180 above the saddle, looking north over the Forbidden Zone: the road down to Ash
  Fork, Corak's lava lake and pod right of centre (about 15,400 away), Castle Alamar on its mesa ringed by lava left
  of centre (about 26,500), the Northern Lava Falls at the rim, the Ancient field's metal at the right. Ambrose's camp
  is beside the camera, out of frame. <b>Against the plan:</b> the painting brings the castle nearer and builds it of
  grey Gothic stone, and lines the energy pylons along the road far in front of it (the plan: four on the approach
  ramp); L3 keeps the plan's distances and the Ancient kit's dark teal steel. The rim's lava fall, the pod in its
  crust basin and the field's surfacing metal read as planned.</p></div>
 <div class="card concept"><h2>MU-4 signature view: Corak's pod and Castle Alamar</h2>
  <img src="{signature}">
  <p>Camera on the lake's east shore by the Necropolis road (82, 72), about 60 degrees, looking west: the pod nose-up
  in the glowing lake left of centre (about 5,700), its hatch toward the shore; Castle Alamar's lit walls and energy
  fields beyond the moat right of centre (about 20,700); ash in the air. The view every party has on the way from
  Griffin Pass to Necropolis; both of the map's promises (the pod and the castle) in one look (WORLD_DESIGN 4).
  <b>Against the plan:</b> the castle stands about half its planned distance away and in grey stone (L3: 20,700 and
  teal steel; at L4 it must still read by its lit windows and fields, never moved nearer, as D-36); the islet's genie
  lamp sits beside the pod (plan: 6 cells north-west of it); the moat's lava ring is lost behind the far shore. The
  pod's scorched riveted hull, the round hatch facing the shore, the cyan fields on the ramp and the ash read as
  planned.</p>
 </div>
 <div class="card"><h2 style="margin-top:0">Against MAPS (D6 sheet, §0 checklist)</h2>
 <table>
 <tr><th>Figure</th><th class="n">Plan</th><th>Target</th><th></th></tr>
 <tr><td>Hostiles at load</td><td class="n">{m['hostiles_at_load']:g}</td><td>110, few and strong</td><td class="ok">ok</td></tr>
 <tr><td>Kill XP per member (MM7 tier odds)</td><td class="n">{m['kill_xp_per_member']:,}</td><td>71.1k ±15 %</td><td class="ok">{(m['kill_xp_per_member'] / 71100 - 1) * 100:+.0f} %</td></tr>
 <tr><td>Spawn markers (+ placed hostiles)</td><td class="n">{m['markers']} (+{m['placed_hostile']})</td><td>45-70</td><td class="warn">42 + 26 placed</td></tr>
 <tr><td>Encounter areas (4,096²)</td><td class="n">4 + 2 camps</td><td>3-8 of 6-30</td><td class="ok">ok</td></tr>
 <tr><td>Quiet land (lava not counted)</td><td class="n">{quiet} %</td><td>at least a third</td><td class="ok">ok</td></tr>
 <tr><td>POIs (D-20 census, chained merge within 400)</td><td class="n">{m['poi_spots']}</td><td>trap band 22-28</td><td class="ok">ok, with the town</td></tr>
 <tr><td>POI spacing (median)</td><td class="n">{m['poi_spacing_median']:,}</td><td>1,300-2,600</td><td class="warn">sparse (trap map, as X7)</td></tr>
 <tr><td>Outdoor chests, each with a reason</td><td class="n">{m['outdoor_chests']}</td><td>4-10</td><td class="ok">ok</td></tr>
 <tr><td>Dungeon entrances</td><td class="n">{m['dungeon_entrances']} + the pass-gate</td><td>3-6</td><td class="ok">ok</td></tr>
 <tr><td>Relief inside the box (land)</td><td class="n">{m['height_min_land_box']:,}-{m['height_max_land_box']:,}</td><td>at least 2,500</td><td class="ok">{m['relief_box']:,}</td></tr>
 <tr><td>First fight from the D1 arrival</td><td class="n">{ff['entrance:south_road'][0][0]:,}</td><td>2,000-6,000</td><td class="ok">ok</td></tr>
 <tr><td>First fight from the D5 arrival</td><td class="n">{ff['entrance:east_pass'][0][0]:,}</td><td>2,000-6,000</td><td class="ok">ok</td></tr>
 <tr><td>Town arrival (inside the gate)</td><td class="n">{ff['entrance:necropolis_gate'][0][0]:,}</td><td>buffer 2,500</td><td class="ok">ok</td></tr>
 <tr><td>Nearest fight to a Necropolis door</td><td class="n">{m['nearest_fight_to_a_town_door'][0]:,}</td><td>2,500</td><td class="ok">ok</td></tr>
 <tr><td>Ambrose's camp; the hatch (nearest placed group)</td><td class="n">{near['poi:ambrose'][0]:,}; 2,900</td><td>-</td><td class="ok">clear</td></tr>
 <tr><td>6,000 rule; wild land (D-11.5)</td><td class="n">{m['farthest_land_from_anything'][0]:,}; {m['wild_land_share_over_3000']}</td><td>&le; 6,000; &le; 0.16</td><td class="ok">ok</td></tr>
 <tr><td>Roads + lanes</td><td class="n">{m['road_share'] * 100:.1f} % + {m['lane_share'] * 100:.1f} %</td><td>1-4 %</td><td class="ok">ok</td></tr>
 <tr><td>Houses drawn / d6.yml</td><td class="n">11 + mirror</td><td>4751-4762</td><td class="ok">ok</td></tr>
 <tr><td>Obelisk; permanent device</td><td class="n">1; the Books of the Dead</td><td>1; at least 1</td><td class="ok">ok</td></tr>
 <tr><td>Lava (lavtyl, D-40)</td><td class="n">{sum(m['lava_cells'].values())} cells + rivers</td><td>never water</td><td class="ok">ok</td></tr>
 <tr><td>Textures</td><td class="n">kits only</td><td>&le; 12 new</td><td class="ok">0 made, 3 proposed</td></tr>
 </table></div>
 <div class="card" style="margin-top:12px"><h2 style="margin-top:0">Requests to other lanes</h2>
 <ul class="req">
 <li><b>A2:</b> map_stats row 9113 (Eye Dif 2, Roc Dif 5, Robot Dif 1, [1,3]); two placed barbarian tiers (Archer 44, Archer Chief 50; 11104-11105); a lava-dweller row or confirm Lesser Elemental 55 / Elemental 62; the Act V recount (73.4k, +3 %); the Books of the Dead (+3,000 XP, +8 years, x3) in the ledger.</li>
 <li><b>A3:</b> a Necropolis gate hook (pass 12336); the skull's story, the books', the zone sign's and Sheltem's sealed hatch texts; genie-lamp hooks (three); robots off after m33.done; the archers' camp burn (optional).</li>
 <li><b>A4:</b> Freeda the Mountaineer (a teacher row and her place); confirm Ambrose at Griffin Pass on the south (the top of D1's road).</li>
 <li><b>A7/A8:</b> DD-16's inside arrival entrance:d6_hatch (done by D-47); DD-17's arrival and refusal point, DD-21's stair foot, DD-10C's D6_ARRIVAL (A6 measures at L3).</li>
 <li><b>S:</b> the griffin figure for Ambrose's camp (MM7 griffin, placed, not counted); the two pods' outer hulls and Alamar's whole and ruin exteriors if not BModels; the lava-fall preset (shared with X7).</li>
 <li><b>A1:</b> the cooled-crust swap at the hatch (a lava area's tile set by qbit, or a BModel crust raised over it).</li>
 </ul></div>
 <div class="card q" style="margin-top:12px"><h2 style="margin-top:0">Open questions (DECIDE)</h2>
 <ol>
 <li><b>Griffin Pass on the south</b> (the top of D1's mountain road, as A3/A4 wrote) or in the source's north-east
 (B1, by the resistance well). Proposed: south (the arrival concept depends on it).</li>
 <li><b>Lava dwellers:</b> (a) Lesser Elementals 55 / Elementals 62 placed (A7's DD-16 choice), (b) a new lava-dweller
 family at about 44/52/60 (A2, S model), (c) Lava Golems 55. Proposed: (a) now, (b) if A2 has room.</li>
 <li><b>The archers' camp:</b> (a) two new placed barbarian tiers 44/50, (b) drop the camp (the source's barbarians
 are 14-28) and give its 12 to E1, (c) Yog's barbarians 28 as a below-band camp. Proposed: (a).</li>
 <li><b>The cooled crust:</b> (a) a crust BModel raised over the lava round the hatch on 111564, (b) a tile-set swap by
 qbit (A1), (c) a short bridge of cooled rock always there, the hatch only too hot. Proposed: (a).</li>
 <li><b>The ruin's stair</b> in the broken gatehouse (one POI with the gate) or in the castle's court. Proposed:
 gatehouse.</li>
 <li><b>The D5 corner</b> (109, 106-109): edge_d5_d6.json says 2,816-2,912; D1's installed row says 2,176 at (109, 109).
 Proposed: D1's installed value at the corner, the file's from y 105 north (both maps blend the last 4 cells).</li>
 <li><b>Lucio on D6:</b> MAPS lists him among D6's arrivals but D-5.3 gives his boats no D6 jetty. Proposed: none on
 D6 (MAPS amended).</li>
 <li><b>Spawn markers 42</b> (under 45) with 26 placed: "few and strong". Keep, or add 3 markers to E1. Proposed: keep.</li>
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
    e1 = json.loads((OUT / 'edge_d1.json').read_text())
    e5 = json.loads((OUT / 'edge_d5.json').read_text())
    pick = {}
    for path in sorted((OUT / 'raw').glob('d6_*_v*.png')):
        pick[path.stem.split('_')[1]] = f'raw/{path.name}'      # the highest version wins
    try:
        plan_png()
        html = page(m, e1, e5, pick.get('arrival', 'blockout_arrival.png'),
                    pick.get('signature', 'blockout_signature.png'))
        (OUT / 'board_d6.html').write_text(html)
        chrome(OUT / 'board_d6.html', OUT / 'board_d6.png', 1800, 4600)
        trim(OUT / 'board_d6.png')
    finally:
        shutil.rmtree(PROFILE, ignore_errors=True)
    print(OUT / 'board_d6.png')


if __name__ == '__main__':
    main()
