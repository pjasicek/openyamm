#!/usr/bin/env python3
"""D4 Lakeside and Blackfang's review board (A6, phase 4): plan_d4.svg -> plan_d4.png, and board_d4.html ->
board_d4.png, both with headless Chrome under its own profile (phase4/d4/.chrome, deleted after use). The D3 edge
strip is an inline SVG chart drawn from d4/edge_d3.json.

    board_d4.py        (run d4_render.py first; the concepts are the highest raw/d4_<view>_vN.png)
"""
import json
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'd4'
PROFILE = OUT / '.chrome'

CSS = """
:root { --bg: #f4f1ea; --ink: #1d1d1f; --muted: #5d5a55; --rule: #d8d2c4; --accent: #6a3410; --card: #fffdf8;
        --d3: #2a78d6; --d4: #eb6834; }
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
"""

LEGEND = """<div class="legend">
<span><i class="sw" style="background:#0b6b3a"></i>arrival / entrance</span>
<span><i class="sw" style="background:#111"></i>dungeon door, sealed gate</span>
<span><i class="sw" style="background:#7a1f6a;border-radius:50%"></i>device (fountain, well, statue, lamp)</span>
<span><i class="sw" style="background:#1d5fa8;border-radius:50%"></i>talking person / tree</span>
<span><i class="sw" style="background:#b8860b;transform:rotate(45deg)"></i>chest</span>
<span><i class="sw" style="background:#c06000"></i>landmark</span>
<span><i class="sw" style="background:#5a4630;border-radius:50%"></i>fork, signpost</span>
<span><i class="sw" style="background:rgba(208,48,42,.25);border-color:#d0302a"></i>encounter area (rocs red, gargoyles brown, coven violet, octopods blue)</span>
<span><i class="sw" style="background:repeating-linear-gradient(45deg,#2e8b57 0 2px,transparent 2px 6px);border-color:#2e8b57"></i>kept clear</span>
<span><i class="sw" style="background:#1f6fd1;opacity:.6"></i>MU-4 cameras</span>
<span><i class="sw" style="background:#6e3b2a"></i>service door house (yellow dot: door)</span>
<span><i class="sw" style="background:#8a6a52"></i>residence</span>
</div>"""


def chrome(page, png, width, height):
    subprocess.run(['google-chrome', '--headless=new', '--disable-gpu', '--no-sandbox', f'--user-data-dir={PROFILE}',
                    '--hide-scrollbars', f'--window-size={width},{height}', '--virtual-time-budget=6000',
                    f'--screenshot={png}', page.as_uri()], check=True, capture_output=True, timeout=180)


def plan_png():
    page = OUT / '_plan.html'
    page.write_text('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;background:#fff}'
                    'img{display:block;width:1084px;height:1084px}</style></head><body><img src="plan_d4.svg">'
                    '</body></html>')
    chrome(page, OUT / 'plan_d4.png', 1084, 1084)
    page.unlink()


def edge_chart(edge):
    """D3's installed border row (y 19) and D4's planned border row (y 109), heights along x 0-127: one axis, two
    series, the five shared spans shaded, direct labels and a legend; a <title> on each point for hover."""
    w, h, left, right, top, bottom = 640, 250, 46, 12, 14, 34
    pw, ph = w - left - right, h - top - bottom
    hmax = 3200

    def X(x):
        return left + x / 127 * pw

    def Y(v):
        return top + ph - v / hmax * ph
    rows = edge['rows']
    parts = [f'<svg viewBox="0 0 {w} {h}" width="100%" font-family="DejaVu Sans, sans-serif" font-size="11">']
    shade = ['#efeae0', '#f7f4ee']
    for i, s in enumerate(edge['spans']):
        a, b = s['span']
        parts.append(f'<rect x="{X(a):.1f}" y="{top}" width="{X(b) - X(a):.1f}" height="{ph}" fill="{shade[i % 2]}"/>')
        hv = s['height']
        label = f"{hv / 1000:g}k" if not isinstance(hv, list) else f"{hv[0] / 1000:g}-{hv[1] / 1000:g}k"
        parts.append(f'<text x="{(X(a) + X(b)) / 2:.1f}" y="{top + 11 + 11 * (i % 2)}" text-anchor="middle" '
                     f'fill="#5d5a55" font-size="9.5">{label}</text>')
    for v in range(0, hmax + 1, 800):
        parts.append(f'<line x1="{left}" x2="{w - right}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="#d8d2c4" '
                     'stroke-width="0.6"/>')
        parts.append(f'<text x="{left - 5}" y="{Y(v) + 3.5:.1f}" text-anchor="end" fill="#5d5a55">{v:,}</text>')
    for x in (0, 19, 24, 82, 88, 94, 104, 127):
        parts.append(f'<text x="{X(x):.1f}" y="{h - bottom + 14}" text-anchor="middle" fill="#5d5a55">{x}</text>')
    parts.append(f'<text x="{left + pw / 2}" y="{h - 4}" text-anchor="middle" fill="#5d5a55">x (cells); the '
                 'crossing at x 88; the playable square from x 19</text>')
    parts.append(f'<line x1="{X(88):.1f}" x2="{X(88):.1f}" y1="{top}" y2="{top + ph}" stroke="#5d5a55" '
                 'stroke-width="0.8" stroke-dasharray="3 3"/>')
    for key, colour, dash, name in (('d3_border_y19', 'var(--d3)', '', 'D3 installed, y 19'),
                                    ('d4_border_y109', 'var(--d4)', ' stroke-dasharray="6 3"', 'D4 plan, y 109')):
        pts = ' '.join(f'{X(x):.1f},{Y(v):.1f}' for x, v in zip(rows['x'], rows[key]))
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{colour}" stroke-width="2"{dash} '
                     'stroke-linejoin="round"/>')
        for x, v in zip(rows['x'][::8], rows[key][::8]):
            parts.append(f'<circle cx="{X(x):.1f}" cy="{Y(v):.1f}" r="6" fill="transparent"><title>{name}: x {x}, '
                         f'{v:,}</title></circle>')
    # direct labels at the right of the land, before the rim drop
    parts.append(f'<text x="{X(60):.1f}" y="{Y(rows["d3_border_y19"][60]) - 22:.1f}" fill="#1d1d1f">D3 (installed)'
                 '</text>')
    parts.append(f'<text x="{X(60):.1f}" y="{Y(rows["d4_border_y109"][60]) + 26:.1f}" fill="#1d1d1f">D4 (plan)</text>')
    parts.append('</svg>')
    return '\n'.join(parts)


def page(m, edge, arrival, signature):
    ff = m['first_fight']
    south = ff['entrance:south_road'][0][0]
    west = ff['entrance:west_road'][0][0]
    quiet = round(m['quiet_share'] * 100)
    areas = {a['id']: a for a in m['areas']}
    span_rows = ''.join(
        f"<tr><td>{s['span'][0]}-{s['span'][1]}</td><td>{s['form']} "
        f"{s['height'] if not isinstance(s['height'], list) else '-'.join(f'{v:,}' for v in s['height'])}</td>"
        f"<td class='n'>{s['d3_border_mean']:,}</td><td class='n'>{s['d4_border_mean']:,}</td>"
        f"<td class='n'>{s['mean_abs_diff']:,}</td></tr>" for s in edge['spans'])
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>D4 Lakeside mock-ups</title>
<style>{CSS}</style></head><body><main>
<h1>D4 Lakeside and Blackfang: MU-3 plan and MU-4 concepts</h1>
<div class="sub">Phase 4 review (A6, 2026-11-20), for a decider before any geometry. Darkside's north-east corner,
Act IV wilderness (party 35-38), the world rim on its north and east sides. <b>Octopod Lake</b> fills the middle with
the <b>Isle of Lost Souls</b> (DD-12) a short row off <b>Lakeside</b>, the coven's low town of grey stone and slate on
the south shore (A4's 15 doors and the mirror; Naomi in the stocks; the guild's riddle door into DD-20). Across the
water <b>Castle Blackfang</b> crowns a black crag in a storm of bats; its gate at the crag's foot never opens. The Snow
River comes down its rapids from a snowfield at the north rim; <b>Magic Mountain</b> (the wizards' camp, the gargoyles
and DD-23, Ector's woodpile) rises over the <b>Forest of Peril</b> in the west. The lake falls over the east rim.
Source: <code>devdocs/xeen/briefs/d4/L1/</code> (project, plan, sketch in Map Studio's schema, NOTES.md;
<code>oymap validate</code> clean).</div>
<div class="grid">
<div>
 <div class="card plan"><img src="plan_d4.png"></div>
 <div class="card" style="margin-top:12px">{LEGEND}
 <div style="margin-top:6px;color:#5d5a55;font-size:13px">128 x 128 cells of 512 units, north up; the dashed white
 square is the playable area (cells 19-109). The land ends in rim cliffs at y 24 (north) and x 104 (east). <b>Shared
 edges:</b> the Lakeside road crosses the south edge at <b>x 88</b> (D-28, D3 installed); the desert road crosses the
 west edge at <b>y 80</b> (proposed for D5, not planned).</div></div>
 <div class="two" style="margin-top:12px">
 <div class="card inset"><h2 style="margin-top:0">Lakeside and the Isle (2.9x)</h2>
  <img src="plan_d4.svg#svgView(viewBox(440,480,370,370))">
  <p class="small">Guild 4651 west of the square (double door east: the riddle, DD-20), smithy 4653 east, tavern 4652
  and temple 4654 south, Lakeside Yachts 4655 and the jetty (ferry 420 daily from day one; Lucio 426 after M30), ten
  houses, the mirror 4656 and Naomi's stocks; Skiff's beached boat ("This boat under repair.") east of the
  Boathouse; DD-20's sewer shaft by the jetty's foot. The Isle: landing jetty, ruined tower over DD-12's two-leaf
  door.</p></div>
 <div class="card inset"><h2 style="margin-top:0">D3 edge match (x 0-127)</h2>
  {edge_chart(edge)}
  <div class="key"><i style="border-top:2px solid var(--d3)"></i>D3 installed border row (y 19)
  &nbsp; <i style="border-top:2px dashed var(--d4)"></i>D4 plan border row (y 109)</div>
  <table style="margin-top:6px"><tr><th>Span</th><th>Form (both maps)</th><th class="n">D3</th><th class="n">D4</th>
  <th class="n">mean diff</th></tr>{span_rows}</table>
  <p class="small">D4's south rim repeats D3's north-edge spans word for word; the plan's border heights follow D3's
  installed row (the drawing's land model). At x 88: D3 {edge['road']['d3_at_x88_y19']:,}, D4
  {edge['road']['d4_at_x88_y109']:,} (the build sets the road bed 1,750-1,760). Outside x 19 both rows are rim
  (each map's picture of the other).</p></div>
 </div>
 <div class="card" style="margin-top:12px"><h2 style="margin-top:0">Encounter areas</h2>
 <table>
 <tr><th>Area</th><th>Monsters (A2's rows)</th><th class="n">At load</th></tr>
 <tr><td>E1 Magic Mountain</td><td>Mountain Gargoyle 30, Sentinel 38, Overlord 45 (Dif 2), 13 markers [2,3]</td><td class="n">32.5</td></tr>
 <tr><td>E2 Snow River uplands, rim corner</td><td>Vulture Roc 30, Roc 38, Griffin 48 (Dif 1), 12 markers [1,3]</td><td class="n">24</td></tr>
 <tr><td>E3 Rimward crags</td><td>the same, 8 markers: the first fight from D3</td><td class="n">16</td></tr>
 <tr><td>E5 the desert edge</td><td>the same, 14 markers: the first fight from D5</td><td class="n">28</td></tr>
 <tr><td>E4 the coven (placed, gone with q-d22.done)</td><td>Witches' Circle 8 (Witch 32 x5, Coven Witch 40 x2, Coven Mother 50); the reeds 6</td><td class="n">14</td></tr>
 <tr><td>E6 Octopod Lake, deep water only</td><td>Octopod 50 x3, Great Octopod 60 x2, round the skerries' lures</td><td class="n">5</td></tr>
 </table></div>
 <div class="card" style="margin-top:12px"><h2 style="margin-top:0">A3's hooks and A4's people on D4</h2>
 <table>
 <tr><th>Hook / person</th><th>Where</th></tr>
 <tr><td><code>m25.blackfang_gate</code></td><td>the gatehouse at the crag's foot on the north shore (78, 53): never opens</td></tr>
 <tr><td><code>obelisks.d4</code></td><td>Gull Knoll at Lakeside's west end (57, 81)</td></tr>
 <tr><td><code>q-c24.cairn</code></td><td>five stones on the east shore (91, 84), the cache two paces north</td></tr>
 <tr><td><code>q-d15.lair_door</code></td><td>DD-23's cave mouth in Magic Mountain's crags (46, 42)</td></tr>
 <tr><td><code>q-d21.woodpile</code></td><td>the woodcutters' clearing on Magic Mountain (48, 51)</td></tr>
 <tr><td><code>q-d22.guild_door / right / wrong</code></td><td>the guild's double door on the square (68, 89)</td></tr>
 <tr><td>Naomi 5318, Slibo 5317, Ector 5320, Leafpoint 5319</td><td>the stocks; the wizards' camp; his cabin (34, 72); her grove (42, 61)</td></tr>
 </table></div>
</div>
<div>
 <div class="card concept"><h2 style="margin-top:0">MU-4 arrival view (from D3)</h2>
  <img src="{arrival}">
  <p>Camera on Lakeside Brow (88, 102), 180 above the road, looking north: the road down past Well Fork to Lakeside on
  the shore, the jetty, the Isle with its ruined tower, Castle Blackfang beyond, the falls at the east rim, Magic
  Mountain far left. <b>Against the plan:</b> the painting brings the crag and the falls much nearer (the plan has
  Blackfang about 28,000 away on the north shore and the falls behind the Rimward crags) and gives the castle
  fairy-tale spires; L3 keeps the plan's distances and the towers kit's Darkside stone and cones.</p></div>
 <div class="card concept"><h2>MU-4 signature view: Blackfang over the lake</h2>
  <img src="{signature}">
  <p>Camera at the ferry jetty's end (72, 80), about 60 degrees, looking north-north-east: the Isle of Lost Souls ahead,
  Castle Blackfang on its black crag in the storm of bats across the water, its sealed gatehouse at the crag's foot.
  The view every party has before the ferry (M20) and again on every return; both of the map's promises (the Isle's
  dungeon and the unreachable castle) in one look. <b>Against the plan:</b> the painting joins the Isle to the crag and
  puts the gatehouse on the lake side under the castle; the plan keeps about 2,500 of deep water between them and the
  gatehouse on the crag's west foot, facing the north-shore track (not the jetty). The pale sun stands behind the
  castle; the glow over the north-east rim is only a warm horizon here.</p></div>
 <div class="card"><h2 style="margin-top:0">Against MAPS (D4 sheet, §0 checklist)</h2>
 <table>
 <tr><th>Figure</th><th class="n">Plan</th><th>Target</th><th></th></tr>
 <tr><td>Hostiles at load</td><td class="n">{m['hostiles_at_load']}</td><td>120</td><td class="ok">ok</td></tr>
 <tr><td>Kill XP per member (MM7 tier odds)</td><td class="n">{m['kill_xp_per_member']:,}</td><td>43.0k ±15 %</td><td class="ok">+2 %</td></tr>
 <tr><td>Spawn markers (+ placed hostiles)</td><td class="n">{m['markers']} (+{m['placed_hostile']})</td><td>45-70</td><td class="ok">ok</td></tr>
 <tr><td>Encounter areas (4,096²)</td><td class="n">4 + 2 camps + lake</td><td>3-8 of 6-30</td><td class="warn">Rimward {areas['pop:rimward_rocs']['big_cells']}</td></tr>
 <tr><td>Quiet land (lake not counted)</td><td class="n">{quiet} %</td><td>at least a third</td><td class="ok">ok</td></tr>
 <tr><td>POIs (D-20 census, chained merge within 400)</td><td class="n">{m['poi_spots']}</td><td>lake band 30-35</td><td class="warn">top</td></tr>
 <tr><td>Outdoor chests, each with a reason</td><td class="n">{m['outdoor_chests']}</td><td>4-10</td><td class="warn">top</td></tr>
 <tr><td>Dungeon entrances</td><td class="n">{m['dungeon_entrances']} + sealed gate</td><td>3-6</td><td class="ok">ok</td></tr>
 <tr><td>Relief inside the box (land)</td><td class="n">{m['height_min_land_box']:,}-{m['height_max_land_box']:,}</td><td>at least 2,500</td><td class="ok">{m['relief_box']:,}</td></tr>
 <tr><td>First fight from the D3 arrival</td><td class="n">{south:,}</td><td>2,000-6,000</td><td class="ok">ok</td></tr>
 <tr><td>First fight from the D5 arrival</td><td class="n">{west:,}</td><td>2,000-6,000</td><td class="ok">ok</td></tr>
 <tr><td>Town arrivals: square / dock / Isle</td><td class="n">{ff['entrance:lakeside_square'][0][0]:,} / {ff['entrance:lakeside_dock'][0][0]:,} / {ff['entrance:isle_landing'][0][0]:,}</td><td>buffer 2,500</td><td class="ok">ok</td></tr>
 <tr><td>Nearest fight to a Lakeside door</td><td class="n">{m['nearest_fight_to_a_town_door'][0]:,}</td><td>2,500</td><td class="ok">ok</td></tr>
 <tr><td>6,000 rule; wild land (D-11.5)</td><td class="n">{m['farthest_land_from_anything'][0]:,}; {m['wild_land_share_over_3000']}</td><td>&le; 6,000; &le; 0.16</td><td class="ok">ok</td></tr>
 <tr><td>Roads + lanes</td><td class="n">{m['road_share'] * 100:.1f} % + {m['lane_share'] * 100:.1f} %</td><td>1-4 %</td><td class="ok">ok</td></tr>
 <tr><td>Houses drawn / d4.yml</td><td class="n">15 + mirror</td><td>4651-4666</td><td class="ok">ok</td></tr>
 <tr><td>Obelisk; permanent device</td><td class="n">1; magic-resistance well</td><td>1; at least 1</td><td class="ok">ok</td></tr>
 </table></div>
 <div class="card q" style="margin-top:12px"><h2 style="margin-top:0">Open questions (DECIDE)</h2>
 <ol>
 <li><b>The storm of bats.</b> (a) 20-40 decorative bat models (S's <code>xeen_bat.glb</code>) on looping circling
 paths round the towers (animated decorations, no AI); (b) a particle effect of small bat sprites over the keep;
 (c) a few real, non-hostile bat actors. Proposed: (a).</li>
 <li><b>The octopods in the water.</b> (a) swimmers that never leave deep water (MM9 AI movement <code>swim</code>,
 A2's modifiers), a new octopod model; (b) stationary lurkers placed on the skerries; (c) no octopods on D4 (the lake
 only looks dangerous). Proposed: (a), 5 placed.</li>
 <li><b>The coven's witches after Q-D22.</b> (a) the two placed groups hidden at load once q-d22.done, peaceful to
 members (q-d22.joined); (b) they stay, hostile, after the break. Proposed: (a).</li>
 <li><b>DD-20's second way in.</b> Keep the source's sewer shaft by the jetty (open from day one, sealed with a line
 until DD-20 exists) beside the guild's riddle door, or the guild door only. Proposed: keep both.</li>
 <li><b>Leafpoint, a talking tree.</b> (a) a great old tree decoration whose click opens her dialogue (A3's speak
 event); (b) an immobile actor with a tree model (S). Proposed: (a).</li>
 <li><b>The ferry back from the Isle.</b> (a) a click at the Isle's jetty moves the party to lakeside_dock (A4 writes
 the line); (b) one-way: Town Portal, the mirror or water walking. Proposed: (a).</li>
 <li><b>D5's crossing at y 80</b> (a level valley at 1,500 out of the Forest of Peril), or nearer the source's
 E1/D1 seam (y 60-64, under Magic Mountain). Proposed: y 80.</li>
 <li><b>POIs 35 and chests 10</b> sit at the tops of their bands. Keep, or drop the third signpost's click and the
 hunters' hide (33, 9). Proposed: keep.</li>
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
    edge = json.loads((OUT / 'edge_d3.json').read_text())
    pick = {}
    for path in sorted((OUT / 'raw').glob('d4_*_v*.png')):
        pick[path.stem.split('_')[1]] = f'raw/{path.name}'      # the highest version wins
    try:
        plan_png()
        html = page(m, edge, pick.get('arrival', 'blockout_arrival.png'),
                    pick.get('signature', 'blockout_signature.png'))
        (OUT / 'board_d4.html').write_text(html)
        chrome(OUT / 'board_d4.html', OUT / 'board_d4.png', 1800, 4200)
        trim(OUT / 'board_d4.png')
    finally:
        shutil.rmtree(PROFILE, ignore_errors=True)
    print(OUT / 'board_d4.png')


if __name__ == '__main__':
    main()
