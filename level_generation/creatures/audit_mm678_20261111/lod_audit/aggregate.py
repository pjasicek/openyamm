#!/usr/bin/env python3
"""Join the audit outputs (scores_*.tsv, fine_*.tsv, static_*.jsonl, shadow_*.jsonl, models.tsv) into table.json and
table.tsv, with each model's gate results. Gates: lod_repair repair.py (LOD2 outline <= 6 %, colour <= 16 or LOD1's
+ 3; LOD3 outline <= 13 %, colour <= 19.5); far maps (own maps at LOD2/3, RGBA mask on four-ramp models, no variant
copy on the default's far map); shadow (shadow level s against colour levels c <= s: share > 1 world unit outside
<= 2 %, the worst pair). Usage: aggregate.py (in this folder)"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def tsv(name):
    with open(HERE / name) as f:
        return list(csv.DictReader(f, delimiter='\t'))


def jsonl(name):
    return {r['stem']: r for r in map(json.loads, open(HERE / name))}


models = [line.rstrip('\n').split('\t') for line in open(HERE / 'models.tsv')]
scores = {side: {(r['model'], int(r['lod'])): r for r in tsv(f'scores_{side}.tsv')} for side in ('after', 'before')}
fine = {side: {(r['model'], int(r['lod'])): r for r in tsv(f'fine_{side}.tsv')} for side in ('after', 'before')}
static = {side: jsonl(f'static_{side}.jsonl') for side in ('after', 'before')}
shadow = {side: jsonl(f'shadow_{side}.jsonl') for side in ('after', 'before')}

rows = []
for stem, world, streams, *_ in models:
    row = {'stem': stem, 'world': world, 'streams': streams}
    for side in ('after', 'before'):
        s = {}
        for level in (1, 2, 3):
            r = scores[side].get((stem, level))
            if r:
                s[f'l{level}_out'] = float(r['outline_pct'])
                s[f'l{level}_col'] = float(r['colour_diff'])
            f = fine[side].get((stem, level))
            if f:
                s[f'l{level}_hf'] = float(f['hf_corr'])
                s[f'l{level}_hfr'] = float(f['hf_ratio'])
        st = static[side].get(stem, {})
        s['ratios'] = st.get('ratios')
        s['tris'] = st.get('tris')
        levels = st.get('levels', {})
        far = [p for L in ('2', '3') for p in levels.get(L, {}).get('prims', []) if 'size' in p]
        s['far_own'] = all(p['own_maps'] for p in far) if far else None
        s['far_sizes'] = {L: [p['size'][0] for p in levels.get(L, {}).get('prims', []) if 'size' in p]
                          for L in ('2', '3')}
        s['far_uv'] = {L: [p['uv_share'] for p in levels.get(L, {}).get('prims', []) if 'uv_share' in p]
                       for L in ('2', '3')}
        s['ramps'] = st.get('ramps')
        s['masks'] = sorted({p.get('mask_mode') for p in far if p.get('mask_mode')})
        s['variant_issues'] = [i for p in far for i in p.get('variant_issues', [])]
        s['ramps_mismatch'] = any(p.get('ramps_match') is False for p in far)
        s['smear'] = max([p.get('smear_share', 0) or 0 for L in ('1', '2', '3')
                          for p in levels.get(L, {}).get('prims', [])] or [0])
        own = [p for p in far if p['own_maps'] and 'vertex_colour_median' in p]
        s['vc_median'] = max([p['vertex_colour_median'] for p in own] or [None]) if own else None
        sh = shadow[side].get(stem, {}).get('pairs', {})
        worst = max(sh.items(), key=lambda kv: kv[1]['out1u'], default=(None, None))
        s['shadow_worst'] = worst[0]
        s['shadow_out1u'] = worst[1]['out1u'] if worst[1] else None
        s['shadow_p99u'] = worst[1]['p99u'] if worst[1] else None
        s['shadow_pairs'] = sh
        row[side] = s
    a = row['after']
    reasons = []
    lod1_col = a.get('l1_col', 0)
    if a.get('l2_out', 0) > 6.0:
        reasons.append(f"LOD2 outline {a['l2_out']}")
    if a.get('l2_col', 0) > max(16.0, lod1_col + 3):
        reasons.append(f"LOD2 colour {a['l2_col']}")
    if a.get('l3_out', 0) > 13.0:
        reasons.append(f"LOD3 outline {a['l3_out']}")
    if a.get('l3_col', 0) > 19.5:
        reasons.append(f"LOD3 colour {a['l3_col']}")
    row['score_pass'] = not reasons
    far_reasons = []
    if a['far_own'] is False:
        far_reasons.append('far levels sample the LOD0 atlas (no own far maps)')
    if a['ramps'] and max(a['ramps']) == 4 and 'RGB' in a['masks']:
        far_reasons.append('RGB far mask on a four-ramp model')
    if a['variant_issues']:
        far_reasons.append('variant far maps: ' + ', '.join(a['variant_issues']))
    if a['ramps_mismatch']:
        far_reasons.append('far ramps differ from LOD0')
    if a['ratios'] and a['ratios'][-1] < 0.08:
        far_reasons.append(f"LOD3 {a['ratios'][-1] * 100:.0f} % of LOD0 (build_actor_lods defaults)")
    if a['smear'] > 0.05:
        far_reasons.append(f"{a['smear'] * 100:.0f} % of a level's surface smeared over the atlas")
    row['far_pass'] = not far_reasons
    shadow_reasons = []
    if a['shadow_out1u'] is not None and a['shadow_out1u'] > 0.02:
        shadow_reasons.append(f"shadow {a['shadow_worst']} {a['shadow_out1u'] * 100:.1f} % > 1 unit outside "
                              f"(p99 {a['shadow_p99u']})")
    row['shadow_pass'] = not shadow_reasons
    row['reasons'] = reasons + far_reasons + shadow_reasons
    rows.append(row)

(HERE / 'table.json').write_text(json.dumps(rows, indent=1) + '\n')
with open(HERE / 'table.tsv', 'w') as out:
    columns = ['stem', 'streams', 'tris', 'ratios', 'l1_out', 'l1_col', 'l2_out', 'l2_col', 'l3_out', 'l3_col',
               'l2_hf', 'l3_hf', 'far_own', 'shadow_worst', 'shadow_out1u', 'score_pass', 'far_pass', 'shadow_pass',
               'reasons']
    out.write('\t'.join(columns) + '\n')
    for row in rows:
        a = row['after']
        values = [row['stem'], row['streams'], a['tris'], a['ratios']] + [a.get(k) for k in columns[4:13]] + \
            [a['shadow_worst'], a['shadow_out1u'], row['score_pass'], row['far_pass'], row['shadow_pass'],
             '; '.join(row['reasons'])]
        out.write('\t'.join(str(v) for v in values) + '\n')
print('models', len(rows), 'score pass', sum(r['score_pass'] for r in rows), 'far pass', sum(r['far_pass'] for r in rows),
      'shadow pass', sum(r['shadow_pass'] for r in rows))
