#!/usr/bin/env python3
"""Severity per audit dimension and an overall priority per MM6-MM8 model (audit 2026-11-11).

    python3 level_generation/creatures/audit_mm678_20261111/score.py

Reads table.json (aggregate.py). Writes scores.json and scores.csv, prints the top of the ranking. Severities 0-3:

- texture: 3 = group A of texpass_mm678/HANDOFF.md (atlas < 25 %, fragments >= 30 %, equivalent < 600 px or stretch
  p90 >= 4, worst body set), 2 = group B (atlas < 35 % or fragments >= 20 %), 1 = atlas < 45 % or fragments >= 10 %;
- deform: largest bad-surface share of a region in a bound live clip beyond the same region in Standing
  (motion_audit.py): 3 >= 40 %, 2 >= 25 %, 1 >= 12 %;
- penetration: hand vertices inside the body in a bound attack, cast, hit, idle, walk or run clip: 3 >= 20 %,
  2 >= 8 %, 1 >= 3 %;
- motion: melee attack against the MM9 median of the same body type (mean of the ratios of p90 reach, moving share
  and peak speed): 3 < 0.45 or the attack slot plays Standing/Walking, 2 < 0.6, 1 < 0.75;
- hands: 2 = a person with rigid hands (no finger bones) or a hand the user rejected / that reads badly at rest,
  1 = fists that crumple at rest;
- known: the provenance survey records an open problem (1) or a placeholder / failed-gate / rejected status (2).
"""
import csv
import json
import sys
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
# `score.py after` scores after/table.json into after/scores.json and after/scores.csv.
OUT = HERE / sys.argv[1] if len(sys.argv) > 1 else HERE
TEXPASS_DONE = {'mm8_m616', 'mm8_m500', 'mm7_m210', 'mm8_m480', 'mm7_m461', 'mm7_m274', 'mm7_m322', 'mm7_m342',
                'mm7_m362', 'mm7_m372'}
# MM9 bodies whose joint names read as bipeds but are not (worms, pods): left out of the biped reference.
NOT_BIPED_MM9 = {'mm9_icky', 'mm9_lobberpod'}
# Effect bodies and the hive-bound queen: surface-weighted motion does not describe them (motion not scored).
EFFECT_BODIES = {'mm6_qfi', 'mm6_fie1', 'mm6_aie1', 'mm6_rea', 'mm8_m496', 'mm8_m508', 'mm8_m528', 'mm8_m636',
                 'mm6_ooz', 'mm8_m588'}
# Bipeds whose hands carry no finger bones (rigid open hands or fists), people only.
RIGID_HANDS = {'mm6_gua', 'mm6_ttn', 'mm6_thf', 'mm6_wwf', 'mm6_cle', 'mm6_fmp'}
# Hands that read badly as geometry at rest (handsheet.py, 2026-11-11) or that the user rejected.
WEAK_HANDS = {'mm6_pfem': 'user: "hands are terrible, especially in standing" (2026-10-30)',
              'mm6_pmn2': 'right hand a fingerless lump', 'mm6_thf': 'mitten hands',
              'mm6_gob2': 'blobby four-finger hands, webs stretch', 'mm8_lizardman_peasant': 'spiky low-poly hands',
              'mm7_m475': 'blade-like hands', 'mm6_ttn': 'rigid open hands; OY-27 "hands look messy in the attack"',
              'mm6_lzd': 'bow hand turned outward, crumpled grip', 'mm6_min1': 'thigh weights pull the hand region'}


def tex_severity(t):
    if not t:
        return 0
    atlas, frag = t['worst_atlas_pct'], t['max_fragment_pct']
    if atlas < 25 or frag >= 30 or t['equivalent_px'] < 600 or t['max_stretch_p90'] >= 4:
        return 3
    if atlas < 35 or frag >= 20:
        return 2
    if atlas < 45 or frag >= 10:
        return 1
    return 0


def band(value, steps):
    for level, limit in steps:
        if value >= limit:
            return level
    return 0


def main():
    data = json.loads((OUT / 'table.json').read_text())
    models = data['models']
    ref = {}
    for body in ('biped', 'other'):
        rows = [r for r in models.values() if r['mm9'] and r['body'] == body and r['model'] not in NOT_BIPED_MM9
                and 'attack_melee' in r['combat'] and r['combat']['attack_melee']['clip'].lower() not in
                ('standing', 'fidget', 'walking')]
        ref[body] = {k: sorted(r['combat']['attack_melee'][k] for r in rows)[len(rows) // 2]
                     for k in ('amp_p90', 'body_share', 'peak_speed')}
        ref[body]['n'] = len(rows)
    out = []
    for r in models.values():
        if r['mm9']:
            continue
        s = {'model': r['model'], 'worlds': '+'.join(r['worlds']), 'name': re.sub(r'\s+[A-Ca-c]$', '',
                                                                                  r['descriptors'][0]),
             'descriptors': r['descriptors'], 'body': r['body']}
        t = r['texture']
        s['tex'] = 0 if r['model'] in TEXPASS_DONE else tex_severity(t)
        s['texpass_done'] = r['model'] in TEXPASS_DONE
        s['tex_detail'] = t
        d = r['deform_worst'] or {}
        s['deform'] = band(d.get('excess_pct', 0), [(3, 40), (2, 25), (1, 12)])
        s['deform_detail'] = d
        h = r['hand_worst'] or {}
        s['pen'] = band(h.get('pct', 0), [(3, 20), (2, 8), (1, 3)])
        s['pen_detail'] = h
        attack = r['combat'].get('attack_melee')
        rb = ref[r['body']]
        if attack and r['model'] in EFFECT_BODIES:
            s['motion'], s['motion_ratio'], s['attack_placeholder'] = 0, None, False
        elif attack:
            ratio = (attack['amp_p90'] / rb['amp_p90'] + attack['body_share'] / rb['body_share']
                     + attack['peak_speed'] / rb['peak_speed']) / 3
            placeholder = attack['clip'].lower() in ('standing', 'walking', 'walk', 'fidget')
            s['motion'] = 2 if placeholder else 3 if ratio < 0.45 else 2 if ratio < 0.6 else 1 if ratio < 0.75 else 0
            s['motion_ratio'] = round(ratio, 2)
            s['attack_placeholder'] = placeholder
        else:
            s['motion'], s['motion_ratio'], s['attack_placeholder'] = 0, None, False
        s['combat'] = r['combat']
        s['combat_clip_names'] = r['combat_clip_names']
        s['loop_pops'] = r['loop_pops']
        s['near_duplicates'] = r['near_duplicates']
        s['mesh'] = r['mesh']
        p = r.get('provenance', {})
        issues = (p.get('known_open_issues') or '').strip()
        verdicts = (p.get('user_verdicts') or '').strip()
        blob = (issues + ' ' + verdicts).lower()
        s['known'] = 0 if not issues or issues.lower().startswith('none') else 1
        if re.search(r'placeholder|qa hold|not ready|fail|terrible|rejected|plain bad|awaiting user review', blob):
            s['known'] = 2
        s['provenance'] = p
        s['hands'] = 2 if r['model'] in RIGID_HANDS or r['model'] in WEAK_HANDS else 0
        s['hands_note'] = WEAK_HANDS.get(r['model'], 'no finger bones' if r['model'] in RIGID_HANDS else '')
        s['priority'] = s['tex'] + s['deform'] + s['pen'] + s['motion'] + s['hands'] + s['known'] * 0.8
        out.append(s)
    out.sort(key=lambda s: -s['priority'])
    (OUT / 'scores.json').write_text(json.dumps({'mm9_attack_reference': ref, 'models': out}, indent=1))
    with (OUT / 'scores.csv').open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['model', 'worlds', 'name', 'body', 'priority', 'tex', 'deform', 'pen', 'motion', 'hands', 'known',
                    'atlas_pct', 'fragment_pct', 'deform_clip', 'deform_region', 'deform_excess', 'hand_clip',
                    'hand_pct', 'attack_clip', 'motion_ratio', 'known_open_issues'])
        for s in out:
            t, d, h = s['tex_detail'] or {}, s['deform_detail'], s['pen_detail']
            w.writerow([s['model'], s['worlds'], s['name'], s['body'], round(s['priority'], 1), s['tex'], s['deform'],
                        s['pen'], s['motion'], s['hands'], s['known'], t.get('worst_atlas_pct'), t.get('max_fragment_pct'),
                        d.get('clip'), d.get('region'), d.get('excess_pct'), h.get('clip'), h.get('pct'),
                        (s['combat'].get('attack_melee') or {}).get('clip'), s['motion_ratio'],
                        s['provenance'].get('known_open_issues', '')[:300]])
    print('MM9 attack reference', ref)
    for s in out[:40]:
        d, h = s['deform_detail'], s['pen_detail']
        print(f"{s['priority']:4.1f} {s['model']:22s} {s['name'][:22]:22s} tex{s['tex']} def{s['deform']} pen{s['pen']} "
              f"mot{s['motion']} hd{s['hands']} kn{s['known']}  {d.get('clip')}/{d.get('region')} {d.get('excess_pct')}  "
              f"hand {h.get('clip')} {h.get('pct')}  ratio {s['motion_ratio']}")


if __name__ == '__main__':
    main()
