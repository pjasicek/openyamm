"""Read-only x2 decoration placement audit; writes reports, never source/art/queue state."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import csv
import hashlib
import json
import html
import os
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
QUEUE = ROOT / 'level_generation/sprites/restoration_jobs'
PILOT = ROOT / 'level_generation/decorations/mm6_new_sorpigal'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bounds(alpha, threshold):
    y, x = np.nonzero(alpha >= threshold)
    return [int(x.min()), int(y.min()), int(x.max()+1), int(y.max()+1)] if len(x) else None


def measure(native_path, output_path):
    native = Image.open(native_path).convert('RGBA')
    output = Image.open(output_path).convert('RGBA')
    a, b = np.asarray(native)[:, :, 3], np.asarray(output)[:, :, 3]
    result = {'native_size': list(native.size), 'actual_size': list(output.size),
              'exact_x2': output.size == (native.width*2, native.height*2), 'thresholds': {}}
    for threshold in (1, 17, 128, 240):
        na, nb = bounds(a, threshold), bounds(b, threshold)
        result['thresholds'][str(threshold)] = {'native': na, 'restored': nb,
            'delta_native_pixels': [nb[i]/2-na[i] for i in range(4)] if na and nb else None}
    na, nb = bounds(a, 128), bounds(b, 128)
    if na and nb:
        # Compare the lowest 5% of the original visible height, at the SAME canvas coordinates.
        band = max(3, round((na[3]-na[1])*.05))
        top = max(0, na[3]-band)
        def center(alpha, scale):
            section = alpha[top*scale:na[3]*scale] >= 128
            y, x = np.nonzero(section)
            return float(((x+.5)/scale).mean()) if len(x) else None
        ca, cb = center(a, 1), center(b, 2)
        result.update(bottom_lift_native_pixels=na[3]-nb[3]/2,
                      base_center_shift_native_pixels=cb-ca if cb is not None and ca is not None else None,
                      base_band_native=[top, na[3]], native_base_center=ca, restored_base_center=cb)
    if result['exact_x2']:
        aa, bb = np.repeat(np.repeat(a >= 128, 2, 0), 2, 1), b >= 128
        result['silhouette_iou'] = float((aa & bb).sum()/max(1,(aa | bb).sum()))
    return result


def base_label(row):
    shift = row.get('base_center_shift_native_pixels')
    return 'no opaque base in band' if shift is None else f'base dx {shift:.1f}px'


def main():
    started = datetime.now(timezone.utc).isoformat()
    sources = read(QUEUE/'sources.json')
    states = {f.stem: read(f) for f in sorted((QUEUE/'state').glob('g*.json'))}
    jobs = {key: read(QUEUE/'jobs'/f'{key}.json') for key in states}
    records, status_counts = [], Counter()
    for job_id, state in states.items():
        job = jobs[job_id]
        if job['category'] != 'decorations':
            continue
        status_counts[state['status']] += 1
        if not state.get('output_dir'):
            continue
        for key in job['assets']:
            output = QUEUE/state['output_dir']/f'{key}.png'
            if not output.exists():
                continue
            source = sources[key]
            records.append({'id': key, 'job': job_id, 'label': job['label'], 'profile': job['profile'],
                'alignment': job['alignment'], 'status': state['status'],
                'anchor_kind': state.get('acceptance_review', {}).get('anchor_kind', 'unreviewed'),
                'names': ', '.join(a['name'] for a in source['aliases']),
                'native': str((QUEUE/source['native']).relative_to(ROOT)), 'output': str(output.relative_to(ROOT)),
                'accepted_hash_matches': sha(output) == state.get('accepted_hashes',{}).get(key) if state['status']=='accepted' else None,
                'output_sha256': sha(output), **measure(QUEUE/source['native'], output)})
    manifest = read(PILOT/'manifest.json')
    inventory = read(PILOT/'inventory.json')
    for name, frame in manifest['frames'].items():
        native, output = PILOT/'native'/f'{name}.png', PILOT/frame['file']
        records.append({'id': name, 'job': 'sorpigal_pilot', 'label': name, 'profile': 'pilot', 'alignment': 'bottom',
            'anchor_kind': 'unreviewed',
            'status': 'pilot', 'names': name, 'native': str(native.relative_to(ROOT)), 'output': str(output.relative_to(ROOT)),
            'accepted_hash_matches': sha(output)==frame['sha256'], 'output_sha256':sha(output),
            'native_bmp_hash_matches':sha(ROOT/inventory['sources'][name]['path'])==inventory['sources'][name]['sha256'],
            **measure(native, output)})
    for row in records:
        row['review_flags'] = []
        if not row['exact_x2']: row['review_flags'].append('wrong_dimensions')
        if row['accepted_hash_matches'] is False: row['review_flags'].append('accepted_hash_changed')
        if row.get('restored_base_center') is None: row['review_flags'].append('no_opaque_pixels_in_native_base_band')
        if row.get('bottom_lift_native_pixels',0)>1: row['review_flags'].append('opaque_base_lift_over_1px')
        if abs(row.get('base_center_shift_native_pixels') or 0)>3: row['review_flags'].append('base_center_shift_over_3px')
        if row.get('silhouette_iou',1)<.7: row['review_flags'].append('silhouette_iou_below_0.7')
        low_alpha = row['thresholds']['17']
        row['visible_base_lift_native_pixels'] = (
            low_alpha['native'][3] - low_alpha['restored'][3] / 2
            if low_alpha['native'] and low_alpha['restored'] else None)
        # Requiring both visible and opaque lift avoids calling a softened alpha edge a floating base.
        row['ground_contact_flags'] = []
        if row['status'] == 'accepted' and row['anchor_kind'] == 'grounded':
            if (row['visible_base_lift_native_pixels'] is not None
                    and row['visible_base_lift_native_pixels'] > 1
                    and row.get('bottom_lift_native_pixels', 0) > 1):
                row['ground_contact_flags'].append('base_lift_over_1px_at_visible_and_opaque_thresholds')
            if abs(row.get('base_center_shift_native_pixels') or 0) > 3:
                row['ground_contact_flags'].append('base_center_shift_over_3px')
    summary = {'started_utc': started, 'finished_utc':datetime.now(timezone.utc).isoformat(),
        'queue_decoration_job_status_at_snapshot':dict(status_counts), 'measured_outputs':len(records),
        'output_status_counts':dict(Counter(r['status'] for r in records)),
        'wrong_dimensions':sum(not r['exact_x2'] for r in records),
        'hash_mismatches':sum(r['accepted_hash_matches'] is False for r in records),
        'accepted_outputs_with_review_flags':sum(bool(r['review_flags']) for r in records if r['status']=='accepted'),
        'accepted_outputs_with_lift_over_1px':sum(r.get('bottom_lift_native_pixels',0)>1 for r in records if r['status']=='accepted'),
        'accepted_grounded_outputs':sum(r['status']=='accepted' and r['anchor_kind']=='grounded' for r in records),
        'grounded_outputs_with_contact_flags':sum(bool(r['ground_contact_flags']) for r in records),
        'flags':dict(Counter(flag for r in records for flag in r['review_flags'])),
        'limits':['Snapshot of a live queue; later jobs are excluded.', 'Flags select visual review, not automatic failures.',
                  'Opaque base uses alpha >=128; thresholds 1,17,240 are retained too.',
                  'Bottom support metrics are meaningful for grounded solid props; particles/bobbing need semantic review.',
                  'Base-center changes measure lowest native 5% band, not a manually labelled trunk.',
                  'No new game capture or per-placement terrain/collision validation.']}
    (HERE/'report.json').write_text(json.dumps({'summary':summary,'records':records},indent=2)+'\n')
    columns=['names','job','status','profile','anchor_kind','exact_x2','bottom_lift_native_pixels',
             'visible_base_lift_native_pixels','base_center_shift_native_pixels','silhouette_iou','output']
    with (HERE/'measurements.csv').open('w') as out:
        w=csv.DictWriter(out,fieldnames=columns,extrasaction='ignore');w.writeheader();w.writerows(records)
    with (HERE/'ground_contact_review.csv').open('w') as out:
        w=csv.DictWriter(out,fieldnames=columns+['ground_contact_flags'],extrasaction='ignore')
        w.writeheader()
        for row in sorted((r for r in records if r['ground_contact_flags']),
                          key=lambda r: (max(r.get('bottom_lift_native_pixels') or 0,
                                             abs(r.get('base_center_shift_native_pixels') or 0))), reverse=True):
            w.writerow({**row,'ground_contact_flags':'; '.join(row['ground_contact_flags'])})
    # Diagnostic contact sheet with aligned original/restored bases; source images remain untouched.
    ranked = sorted(records,key=lambda r:(r.get('bottom_lift_native_pixels',0)*4+abs(r.get('base_center_shift_native_pixels') or 0)),reverse=True)
    selected=ranked[:24]
    sheet=Image.new('RGB',(1600,250*6),(35,40,36));draw=ImageDraw.Draw(sheet)
    for i,r in enumerate(selected):
        x,y=(i%4)*400,(i//4)*250
        draw.text((x+5,y+4),r['names'][:48],fill='white')
        draw.text((x+5,y+18),f"lift {r.get('bottom_lift_native_pixels',0):.1f}px; {base_label(r)}",fill='#eed293')
        h=r['native_size'][1];w=r['native_size'][0];crop_h=min(h,max(24,round(h*.22)))
        zoom=min(190/w,190/crop_h)
        for j,(path,s) in enumerate([(r['native'],1),(r['output'],2)]):
            im=Image.open(ROOT/path).convert('RGBA').crop((0,(h-crop_h)*s,w*s,h*s))
            im=im.resize((max(1,round(w*zoom)),max(1,round(crop_h*zoom))),Image.Resampling.NEAREST)
            bx=x+j*200+(200-im.width)//2;by=y+230-im.height
            sheet.paste(im,(bx,by),im)
            draw.line((x+j*200,y+231,x+(j+1)*200-1,y+231),fill='#62c7ed')
        draw.text((x+5,y+234),'Native | restored; blue = canvas bottom',fill='#a6cddd')
    sheet.save(HERE/'base_closeups.png')
    cards=[]
    for row in ranked:
        if not row['review_flags'] and row['job']!='sorpigal_pilot':continue
        paths=[os.path.relpath(ROOT/row[k],HERE) for k in ('native','output')]
        cards.append(f'<article><h2>{html.escape(row["names"])}</h2><p>{html.escape(row["job"])} · {row["status"]} · lift {row.get("bottom_lift_native_pixels",0):.1f}px · {base_label(row)}</p><div class="pair">'+''.join(f'<img loading="lazy" src="{html.escape(path)}" alt="{label}">' for path,label in zip(paths,['Native','Restored']))+'</div></article>')
    (HERE/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Decoration alignment audit</title><style>body{font:15px system-ui;background:#232824;color:#eee;margin:24px}a{color:#a9d5ed}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(600px,1fr));gap:20px}.pair{display:flex;align-items:flex-end;height:330px;border-bottom:2px solid #62c7ed}.pair img{width:50%;height:100%;object-fit:contain;object-position:center bottom}h2{font-size:18px}article{background:#303730;padding:12px}</style><h1>Decoration alignment audit</h1><p>Original left, restored right. Full canvases share the bottom anchor. Review flags are heuristics, not proof of floating. Numeric distances are native logical pixels.</p><p><a href="report.json">Full snapshot</a> · <a href="measurements.csv">All measurements</a> · <a href="base_closeups.png">Largest base differences</a></p><div class="grid">'+''.join(cards)+'</div>')
    print(json.dumps(summary,indent=2))
    for r in ranked[:15]:print(r['names'],r.get('bottom_lift_native_pixels'),round(r.get('base_center_shift_native_pixels') or 0,2),r['status'])

if __name__=='__main__':main()
