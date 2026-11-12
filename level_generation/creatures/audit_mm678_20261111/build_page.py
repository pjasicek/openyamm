#!/usr/bin/env python3
"""Build the audit's review page (one self-contained HTML file) from scores.json and frames/*.webp.

    python3 level_generation/creatures/audit_mm678_20261111/build_page.py <out.html>
"""
import base64
import html
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def img(name, alt):
    data = base64.b64encode((HERE / 'frames' / f'{name}.webp').read_bytes()).decode()
    return f'<img src="data:image/webp;base64,{data}" alt="{html.escape(alt)}" loading="lazy">'


def reasons(m):
    out = []
    t = m['tex_detail'] or {}
    if m['texpass_done']:
        out.append('texture pass done')
    elif m['tex'] >= 2:
        out.append(f"texture {'A' if m['tex'] == 3 else 'B'}: atlas {t.get('worst_atlas_pct')} %, "
                   f"fragments {t.get('max_fragment_pct')} %")
    d = m['deform_detail'] or {}
    if m['deform'] >= 1:
        out.append(f"{d.get('clip')}: {d.get('region')} {d.get('excess_pct')} % bad")
    h = m['pen_detail'] or {}
    if m['pen'] >= 1:
        out.append(f"hand inside body in {h.get('clip')} ({h.get('pct')} %)")
    if m['attack_placeholder']:
        out.append(f"attack plays {m['combat']['attack_melee']['clip']}")
    elif m['motion'] >= 1 and m['motion_ratio'] is not None:
        out.append(f"attack at {round(100 * m['motion_ratio'])} % of MM9 energy")
    if m['hands_note']:
        out.append(m['hands_note'])
    return out


def rows(models):
    keep = []
    for m in models:
        t = m['tex_detail'] or {}
        p = m['provenance']
        a = m['combat'].get('attack_melee') or {}
        keep.append({
            'm': m['model'], 'n': m['name'], 'w': m['worlds'], 'b': m['body'], 'p': round(m['priority'], 1),
            'tx': m['tex'], 'at': t.get('worst_atlas_pct'), 'fr': t.get('max_fragment_pct'), 'tp': m['texpass_done'],
            'df': m['deform'], 'dc': (m['deform_detail'] or {}).get('clip'),
            'dr': (m['deform_detail'] or {}).get('region'), 'dx': (m['deform_detail'] or {}).get('excess_pct'),
            'pn': m['pen'], 'pc': (m['pen_detail'] or {}).get('clip'), 'pp': (m['pen_detail'] or {}).get('pct'),
            'mo': m['motion'], 'mr': m['motion_ratio'], 'ac': a.get('clip'),
            'hd': m['hands'], 'hn': m['hands_note'], 'kn': m['known'],
            'tri': m['mesh']['triangles'].get('lod0'),
            'rig': (p.get('rig_route') or '')[:240], 'clips': (p.get('clip_sources') or '')[:400],
            'iss': (p.get('known_open_issues') or '')[:600], 'ver': (p.get('user_verdicts') or '')[:300],
            'why': reasons(m),
        })
    return keep


def top_table(models, count):
    body = []
    for i, m in enumerate(models[:count], 1):
        why = ''.join(f'<li>{html.escape(r)}</li>' for r in reasons(m))
        issue = html.escape((m['provenance'].get('known_open_issues') or '')[:220])
        body.append(f'<tr><td class="num">{i}</td><td><b>{html.escape(m["name"])}</b><br><code>{m["model"]}</code>'
                    f' <span class="world">{m["worlds"]}</span></td><td><ul class="why">{why}</ul></td>'
                    f'<td class="issue">{issue}</td></tr>')
    return '\n'.join(body)


def main():
    data = json.loads((HERE / 'scores.json').read_text())
    models = data['models']
    payload = json.dumps(rows(models), separators=(',', ':')).replace('</', '<\\/')
    page = (HERE / 'page_template.html').read_text()
    page = page.replace('{{TOP}}', top_table(models, 30)).replace('{{DATA}}', payload)
    for name, alt in (('cmp_attacks', 'Attack frames: MM9 Guard and Dwarf against MM6 Guard, MM8 Ogre Mage, MM7 Mage '
                                      'and MM7 Dwarf'),
                      ('v3', 'Deformation checks: PeasantF3 Sprint, Wight Walking, Minotaur Jog, Dwarf Hit, Knight Hit, '
                             'Troglodyte Attack'),
                      ('ttn_lh2', 'Titan Cast, left hand from behind, 0.4 to 2.15 s'),
                      ('pfem_hit', 'PeasantF1 Hit, left hand entering the skirt'),
                      ('v2', 'Hand checks: Dragon Hunter Walking, Ratman Running, Minotaur peasant Attack')):
        page = page.replace('{{IMG:' + name + '}}', img(name, alt))
    Path(sys.argv[1]).write_text(page)
    print(sys.argv[1], len(page) // 1024, 'KB')


if __name__ == '__main__':
    main()
