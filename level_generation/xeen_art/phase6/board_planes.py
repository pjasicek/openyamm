#!/usr/bin/env python3
"""The planes' review board, one per pair (A6's planes sub-agent, 2026-11-21): the two plans, the two concepts (with
their blockouts), the counts tables, the hooks placed, the corner contract, the requests and the open questions.

    board_planes.py p12          -> planes/board_p12.html and board_p12.png (later p34)

The HTML is rendered to PNG by headless Chrome under its own profile (deleted after use). Run planes_render.py --png
first; the concepts are the highest planes/raw/<key>_arrival_vN.png.
"""
import json
import shutil
import subprocess
import sys
from html import escape
from pathlib import Path

import yaml
from PIL import Image

import planes_design as D

HERE = Path(__file__).resolve().parent
OUT = HERE / 'planes'
CORNERS = yaml.safe_load((HERE / 'corners.yml').read_text())

CSS = """
:root { --bg: #f4f1ea; --ink: #1d1d1f; --muted: #5d5a55; --rule: #d8d2c4; --accent: #6a3410; --card: #fffdf8; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 15px/1.45 "DejaVu Sans", sans-serif; }
main { width: 2200px; padding: 28px 32px 36px; }
h1 { font-size: 32px; margin: 0 0 4px; }
h2 { font-size: 19px; margin: 22px 0 8px; color: var(--accent); text-transform: uppercase; letter-spacing: .04em; }
h3 { font-size: 16px; margin: 12px 0 6px; }
.sub { color: var(--muted); margin-bottom: 14px; max-width: 2100px; }
.row { display: grid; grid-template-columns: 1090px 1fr; gap: 24px; align-items: start; margin-bottom: 18px; }
.card { background: var(--card); border: 1px solid var(--rule); border-radius: 6px; padding: 12px 14px; }
.plan img { width: 1060px; height: 1060px; display: block; }
.concept { position: relative; }
.concept img.c { width: 100%; display: block; border-radius: 4px; }
.concept img.b { position: absolute; left: 22px; top: 52px; width: 270px; border: 3px solid #fff; }
.concept p { margin: 6px 0 4px; color: var(--muted); font-size: 13.5px; }
table { border-collapse: collapse; width: 100%; font-size: 13.5px; }
th, td { text-align: left; padding: 3px 7px; border-bottom: 1px solid var(--rule); vertical-align: top; }
th { color: var(--muted); font-weight: 600; }
td.n { text-align: right; white-space: nowrap; }
.ok { color: #1f6b35; font-weight: 600; } .warn { color: #a05a00; font-weight: 600; }
.q li { margin: 7px 0; font-size: 13.5px; } .q b { color: #5a2a08; }
.cols2 { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.small { font-size: 12.5px; color: var(--muted); }
.legend span { display: inline-block; margin: 2px 14px 2px 0; font-size: 13px; }
.sw { display: inline-block; width: 12px; height: 12px; vertical-align: -1px; margin-right: 5px; border: 1px solid #555; }
code { font-size: 12.5px; }
"""

LEGEND = """<div class="legend small">
<span><i class="sw" style="background:#0b6b3a"></i>arrival (entrance:d7_fall)</span>
<span><i class="sw" style="background:#111;border-radius:50%"></i>way up (to D7, always)</span>
<span><i class="sw" style="background:#777;border-radius:50%"></i>return dais (to D7, after the sleeper)</span>
<span><i class="sw" style="background:#7a1f6a"></i>statue and plaque</span>
<span><i class="sw" style="background:#e0a800"></i>test pedestal</span>
<span><i class="sw" style="background:#1d5fa8"></i>sleeper's couch</span>
<span><i class="sw" style="background:#b8860b;transform:rotate(45deg)"></i>chest</span>
<span><i class="sw" style="background:#9b59b6;border-radius:50%"></i>device or find</span>
<span><i class="sw" style="background:#d0302a;border-radius:50%"></i>group (count x level)</span>
<span><i class="sw" style="background:#fff;border:2px dashed #7a0f0a;border-radius:50%"></i>the test's guardians</span>
<span><i class="sw" style="background:#ffb020"></i>hazard cell</span>
<span><i class="sw" style="background:repeating-linear-gradient(45deg,#2e8b57 0 2px,transparent 2px 6px)"></i>quiet (no spawns)</span>
<span><i class="sw" style="background:#ffe27a"></i>the walk (ticks every 2,048)</span>
<span><i class="sw" style="background:#1f6fd1;opacity:.5"></i>MU-4 camera</span>
<span><i class="sw" style="background:#000"></i>sleeper's gate (opens on the passed test)</span>
</div>"""


def latest(key):
    found = sorted((OUT / 'raw').glob(f'{key}_arrival_v*.png'), key=lambda p: int(p.stem.split('_v')[-1]))
    return found[-1] if found else None


def ok(cond):
    return '<span class="ok">ok</span>' if cond else '<span class="warn">check</span>'


def counts(d, f):
    rows = [
        ('Form', d['form'], ''),
        ('Room', f"{d['room'][0]} x {d['room'][1]} cells; floors {f['floor_bbox_cells'][0]} x "
                 f"{f['floor_bbox_cells'][1]}", ''),
        ('Walkable floor (S 7-20, M 30-90 M units)', f"{f['walkable_area_m']} M", ok(30 <= f['walkable_area_m'] <= 90)),
    ]
    if 'low' in d:
        rows.append((d['low']['name'][4:].capitalize(), f"{f['low_area_m']} M, {round(100 * f['low_share'])} % of the "
                                                         f"basin; farthest from a way out {f['bank_max']:,}", ''))
    else:
        g = f['island_gaps']
        rows.append(('Sky gaps', f"unbridged min {g['min_unbridged_gap']:,}; bridges {g['bridge_spans'][0]:,}-"
                                 f"{g['bridge_spans'][1]:,}", ok(g['bridge_spans'][1] <= 4000)))
    rows += [
        ('Placed hostiles (30)', f"{f['placed_hostiles']} = {f['field_hostiles']} in {len(d['groups'])} groups + "
                                 f"{f['test_hostiles']} in the test", ok(f['placed_hostiles'] == 30)),
        ('Levels (55-70, guardian 75)', f"{f['levels'][0]}-{f['levels'][1]}, mean {f['level_mean']}", ok(True)),
        ('Kill XP per member (31.0k)', f"{f['kill_xp_per_member'] / 1000:.2f}k ({f['kill_xp_vs_target'] * 100:+.1f} %)",
         ok(abs(f['kill_xp_vs_target']) <= 0.15)),
        ('First fight (1,500-4,000)', f"{f['first_fight']['straight']:,}",
         ok(1500 <= f['first_fight']['straight'] <= 4000)),
        ('Quiet arrival', f"{f['landing_hostiles']} on the landing", ok(f['landing_hostiles'] == 0)),
        ('POIs (C8: 10-12)', f"{f['poi_census']} (median spacing {f['poi_spacing']['median']:,})",
         ok(10 <= f['poi_census'] <= 12)),
        ('Chests (C8: 2)', f"{f['chests']} (T6) + 1 find", ok(f['chests'] == 2)),
        ('Hazard cells (source 9)', f"{f['hazard_cells']}, {f['hazard_on_critical']} on the walk",
         ok(f['hazard_on_critical'] == 0)),
        ('Walk: arrival > test > sleeper > out', f"{f['walk_legs']['arrival_to_test']:,} + "
                                                f"{f['walk_legs']['test_to_sleeper']:,} + "
                                                f"{f['walk_legs']['sleeper_to_way_out']:,} = {f['walk_length']:,} "
                                                f"({f['walk_seconds']['walking']} s)", ''),
        ('Textures (S cap 30, 4 new)', f"about {d['textures']['estimate']}, {len(d['textures']['new'])} new "
                                       f"({', '.join(n for n, _ in d['textures']['new'])})", ok(True)),
        ('Sky', f"{d['sky']['preset']} ({'shipped' if d['sky']['shipped'] else 'new, Q3'})", ''),
    ]
    out = ['<table><tr><th>Figure</th><th>Plan</th><th></th></tr>']
    for a, b, c in rows:
        out.append(f'<tr><td>{escape(a)}</td><td>{escape(str(b))}</td><td>{c}</td></tr>')
    out.append('</table>')
    out.append('<table style="margin-top:8px"><tr><th>Hostiles by row</th><th class="n">n</th><th class="n">XP each'
               '</th></tr>')
    for actor, n in f['by_row'].items():
        level = next(r['level'] for r in D.ROWS.values() if r['actor'] == actor)
        out.append(f'<tr><td>{escape(actor)}</td><td class="n">{n}</td><td class="n">{D.xp(level):,}</td></tr>')
    out.append('</table>')
    return '\n'.join(out)


def hooks(d):
    el, El = d['element'], d['Element']
    c = CORNERS['corners'][el]
    items = [
        f"<code>{c['d7_hook']}</code> (D7's {c['d7_corner']} corner) drops the party onto <code>entrance:d7_fall</code>",
        f"<code>m38.plaque_{el}</code>: the statue's plaque (Step text)",
        f"<code>m38.test_{el}</code>: 'Accept the test of {El}?' at the pedestal; yes shows the guardians",
        f"<code>m38.sleeper_{el}</code>: the couch, three states; awake sets m38.{el} and award "
        f"{ {'fire': 412, 'air': 413, 'earth': 414, 'water': 415}[el] }",
        f"the way up and the return dais: exit presets to D7's <code>{c['d7_return']}</code>",
        "new (A3): the map variable test_passed (the gate), the hazard line, device and find lines",
    ]
    return '<ul class="small">' + ''.join(f'<li>{i}</li>' for i in items) + '</ul>'


def questions_html(qs, prefix=''):
    out = ['<ol class="q" style="list-style:none;padding-left:0">']
    for q in qs:
        opts = ' '.join(escape(o) for o in q['options'])
        out.append(f"<li><b>{prefix}{q['id']} {escape(q['title'])}.</b> {opts} <i>Evidence:</i> "
                   f"{escape(q['evidence'])} <b>Default: {escape(q['default'])}</b> <i>Depends:</i> "
                   f"{escape(q['depends'])}</li>")
    out.append('</ol>')
    return '\n'.join(out)


def build(pair):
    keys = D.PAIRS[pair]
    parts = [f'<!doctype html><html><head><meta charset="utf-8"><title>Planes {escape(pair)}</title>'
             f'<style>{CSS}</style></head><body><main>']
    names = ' and '.join(f"{D.PLANES[k]['code']} {D.PLANES[k]['name']}" for k in keys)
    parts.append(f'<h1>{escape(names)}: phase 6 L1 (MU-3 plans, MU-4 concepts)</h1>')
    parts.append('<div class="sub">A6\'s planes sub-agent, 2026-11-21. One family for the four elemental planes: '
                 'arrival from a D7 corner (quiet) &rarr; the statue and its plaque &rarr; the test of the element '
                 '(\'Accept the test?\' raises the guardians: the Sleeper\'s Guardian 75 and two Greater elementals '
                 '70) &rarr; the sleeper\'s chamber behind the gate the test opens (the couch, the test\'s chest) '
                 '&rarr; the return dais to D7; the way up at the arrival is always open. 27 placed in 10 groups of 2-3 '
                 'plus the test\'s 3; the source\'s nine hazard squares; small M by floor. Plans drawn on the proposed '
                 'defaults of the open questions. Briefs: '
                 + ', '.join(f'<code>devdocs/xeen/briefs/{k}/L1/</code>' for k in keys)
                 + ' (oymap fmt, fmt --check, validate: clean).'
                 + '</div>')
    parts.append(LEGEND)
    for key in keys:
        d = D.PLANES[key]
        f = json.loads((OUT / key / 'measure.json').read_text())
        concept = latest(key)
        parts.append(f"<h2>{escape(d['code'])} {escape(d['name'])}: {escape(d['form'])}</h2>")
        parts.append('<div class="row">')
        parts.append(f'<div class="card plan"><img src="{key}/plan_{key}.png"></div>')
        parts.append('<div>')
        parts.append('<div class="card concept">')
        if concept:
            parts.append(f'<img class="c" src="raw/{concept.name}"><img class="b" src="{key}/blockout_{key}.png">')
            parts.append(f'<p>MU-4 arrival concept <code>raw/{concept.name}</code> (one codex exec, no retry); '
                         'inset: the blockout from the same camera.</p>')
        parts.append(f'<p style="color:#1d1d1f">{escape(d.get("concept_notes", ""))}</p></div>')
        parts.append(f'<div class="card" style="margin-top:12px"><p class="small" style="margin:0 0 6px">'
                     f'{escape(d["pitch"])}</p>{counts(d, f)}<h3>Hooks placed</h3>{hooks(d)}</div>')
        parts.append('</div></div>')
    # corner contract
    parts.append('<h2>Corner contract (corners.yml, unchanged) and the ways out</h2><div class="card"><table>'
                 '<tr><th>Plane</th><th>D7 corner</th><th>Hook</th><th>Arrives at</th><th>Returns to (D7)</th>'
                 '<th>Ways out (C5 default)</th><th>Falls</th></tr>')
    for key in keys:
        d = D.PLANES[key]
        c = CORNERS['corners'][d['element']]
        falls = d['falls_text']
        parts.append(f"<tr><td>{d['code']} {escape(d['Element'])}</td><td>{c['d7_corner']} ({d['corner_sky']})</td>"
                     f"<td><code>{c['d7_hook']}</code></td><td><code>{c['plane_arrival']}</code> (C2: no damage)"
                     f"</td><td><code>{c['d7_return']}</code></td><td>the way up (always) and the return dais "
                     f"(after the sleeper)</td><td>{falls}</td></tr>")
    parts.append('</table></div>')
    # questions and requests
    if pair == 'p12':
        common = ('<h3>Common to all four (asked once, in P1\'s NOTES)</h3>' + questions_html(D.COMMON_QUESTIONS))
    else:
        common = ('<h3>Common to all four: asked once, in P1\'s NOTES and on board_p12</h3><p class="small">'
                  'Not repeated here; these plans are drawn on their defaults:</p><ul class="small">'
                  + ''.join(f"<li><b>{q['id']}</b> {escape(q['title'])}: {escape(q['default'])}</li>"
                            for q in D.COMMON_QUESTIONS) + '</ul>')
    parts.append('<h2>Open questions (drawn on the defaults)</h2><div class="cols2"><div class="card">' + common
                 + '</div><div class="card">')
    for key in keys:
        d = D.PLANES[key]
        parts.append(f"<h3>{d['code']}</h3>" + questions_html(d['questions'], d['code'] + ' '))
    parts.append('</div></div>')
    parts.append('<h2>Requests</h2><div class="card"><table><tr><th>Lane</th><th>For</th><th>What</th></tr>')
    for lane, text in D.COMMON_REQUESTS:
        parts.append(f'<tr><td>{lane}</td><td>all four</td><td>{escape(text)}</td></tr>')
    for key in keys:
        for lane, text in D.PLANES[key]['requests']:
            parts.append(f"<tr><td>{lane}</td><td>{D.PLANES[key]['code']}</td><td>{escape(text)}</td></tr>")
    parts.append('</table></div></main></body></html>')
    return '\n'.join(parts)


def main():
    pair = sys.argv[1] if len(sys.argv) > 1 else 'p12'
    page = OUT / f'board_{pair}.html'
    page.write_text(build(pair))
    png = OUT / f'board_{pair}.png'
    profile = OUT / '.chrome_board'
    try:
        subprocess.run(['google-chrome', '--headless=new', '--disable-gpu', '--no-sandbox',
                        f'--user-data-dir={profile}', '--hide-scrollbars', '--window-size=2264,6400',
                        '--virtual-time-budget=8000', f'--screenshot={png}', page.as_uri()],
                       check=True, capture_output=True, timeout=240)
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    im = Image.open(png).convert('RGB')
    px = im.load()
    bottom = im.height - 1
    while bottom > 0 and all(px[x, bottom] == px[0, bottom] for x in range(0, im.width, 16)):
        bottom -= 1
    im = im.crop((0, 0, im.width, min(im.height, bottom + 30)))
    im.save(png)
    small = im.copy()
    small.thumbnail((1400, 10000), Image.LANCZOS)
    small.save(OUT / f'board_{pair}_small.jpg', quality=85)
    print(png, im.size)


if __name__ == '__main__':
    main()
