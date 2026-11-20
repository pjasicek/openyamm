"""Build read-only, table-driven portrait-family review packs. Never approve or install art."""
import collections
import argparse
import hashlib
import html
import json
import math
import os
from pathlib import Path
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy import ndimage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REVIEW = HERE / 'review/second_pass'
OUT = REVIEW / 'portrait_families'
INPUTS = {}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    path = Path(path)
    INPUTS[str(path)] = digest(path)
    return json.loads(path.read_text())


def table(path):
    INPUTS[str(path)] = digest(path)
    return [(n, fields) for n, line in enumerate(path.read_text().splitlines(), 1)
            if (fields := line.split('\t'))[0].isdigit()]


def numeric_frame(name, prefix):
    suffix = name[len(prefix):] if name.startswith(prefix) else ''
    return int(suffix) if suffix.isdigit() else None


def magenta_components(raw, layout):
    """Detect rectangular opaque canvases, not head/alpha bounds. Ambiguity => no mapping."""
    rgb = np.asarray(raw.convert('RGB')).astype(np.int16)
    matte = ((rgb[:, :, 0] > 160) & (rgb[:, :, 2] > 130) & (rgb[:, :, 1] < 130)
             & (rgb[:, :, 0] - rgb[:, :, 1] > 80) & (rgb[:, :, 2] - rgb[:, :, 1] > 60))
    labels, _ = ndimage.label(~matte)
    boxes = []
    for region in ndimage.find_objects(labels):
        if region is None:
            continue
        ys, xs = region
        w, h = xs.stop - xs.start, ys.stop - ys.start
        if w > 60 and h > 90:
            if np.mean(~matte[ys, xs]) < .97:
                return []
            boxes.append([xs.start, ys.start, w, h])
    if len(boxes) != len(layout['cells']):
        return []
    boxes.sort(key=lambda b: b[1])
    ordered = []
    columns = layout['columns']
    for start in range(0, len(boxes), columns):
        row = boxes[start:start + columns]
        if max(b[1] for b in row) - min(b[1] for b in row) > min(b[3] for b in row) * .15:
            return []
        ordered.extend(sorted(row, key=lambda b: b[0]))
    return ordered


def separator_spans(rgb, axis, expected):
    """Measure near-uniform dark full-sheet gutters; never infer equal grid spacing."""
    spread = np.ptp(rgb.astype(np.int16), axis=axis).max(axis=1)
    mean = rgb.mean(axis=axis).mean(axis=1)
    separator = (spread < 30) & (mean < 110)
    runs = []
    start = None
    for i, value in enumerate([*separator, False]):
        if value and start is None:
            start = i
        elif not value and start is not None:
            runs.append((start,i))
            start = None
    spans, previous = [], 0
    for start, end in runs:
        if start > previous:
            spans.append((previous,start))
        previous = end
    if previous < len(separator):
        spans.append((previous,len(separator)))
    return spans if len(spans) == expected else []


def components(raw, layout):
    boxes = magenta_components(raw, layout)
    if boxes:
        return boxes
    rgb = np.asarray(raw.convert('RGB'))
    columns = layout['columns']
    rows = math.ceil(len(layout['cells']) / columns)
    xs = separator_spans(rgb, 0, columns)
    ys = separator_spans(rgb, 1, rows)
    boxes = [[x0,y0,x1-x0,y1-y0] for y0,y1 in ys for x0,x1 in xs]
    if len(boxes) != len(layout['cells']) or any(b[2] < 60 or b[3] < 90 for b in boxes):
        return []
    return boxes


@lru_cache(maxsize=8)
def raw_image(path):
    with Image.open(path) as im:
        return im.convert('RGB')


def fitted_preview(image, size):
    # Preserve raw aspect ratio; never stretch to hide a distorted returned canvas or upscale low sampling.
    if image.width > size[0] or image.height > size[1]:
        image = ImageOps.contain(image, size, Image.Resampling.LANCZOS)
    canvas = Image.new('RGB', size, '#582e58')
    canvas.paste(image.convert('RGB'), ((size[0] - image.width) // 2, (size[1] - image.height) // 2))
    return canvas


def display_candidate(image):
    # Portraits are opaque scenes; expose unexpected transparency instead of showing hidden RGB.
    rgba = image.convert('RGBA')
    backing = Image.new('RGBA', rgba.size, '#582e58')
    return Image.alpha_composite(backing, rgba).convert('RGB')


def main():
    state_path = HERE / 'checkpoint/state.json'
    state_hash = digest(state_path)
    inventory = read(REVIEW / 'inventory.json')
    usage = read(REVIEW / 'usage_scope.json')
    snapshot = Path(read(REVIEW / 'current.json')['snapshot'])
    masters = read(snapshot / 'masters.json')
    families = collections.defaultdict(list)
    tables = ROOT / 'assets_dev/engine/data_tables'
    for line, f in table(tables / 'character_data.txt'):
        prefix = f[19].strip().lower() or f'pc{int(f[0]):02d}-'
        families[prefix].append(dict(character_id=int(f[0]), table_line=line, notes=f[24] if len(f)>24 else ''))
    frame_rows = table(tables / 'portrait_frame_data.txt')
    frame_ids = sorted({int(f[1]) for _, f in frame_rows})
    rows = {r['cell_id']: r for r in inventory['cells']}
    sources = collections.defaultdict(list)
    for r in usage['files']:
        sources[Path(r['source_path']).stem.lower()].append(r)
    candidates = collections.defaultdict(list)
    raw_cache = {}
    relevant = {r['cell_id'] for r in rows.values() if r['restoration_active']
                and any(numeric_frame(Path(r['source_path']).stem.lower(), p) is not None for p in families)}

    def add(cell, path=None, raw=None, rect=None, evidence=None, priority=20, note=''):
        if cell not in relevant or not ((path and Path(path).is_file()) or (raw and rect)):
            return
        candidate = dict(path=str(path) if path else None, raw=raw, raw_rect=rect,
                         evidence=str(evidence) if evidence else None, priority=priority, note=note,
                         mapping_verified=False, accepted=False)
        if path:
            candidate['sha256'] = digest(path)
        candidates[cell].append(candidate)

    for cell in sorted(relevant):
        row = rows[cell]
        if row.get('second_pass', {}).get('candidate'):
            d = row['second_pass']
            add(cell, d['candidate'], d['raw'], d.get('raw_rect'), d.get('registration_record'), 0,
                'Existing individually reviewed diagnostic; retain its unresolved checks.')
        for h in row['historical']:
            r = h['record']
            path = r.get('candidate') or r.get('artifact') or r.get('extraction_path')
            if path and Path(path).suffix.lower() == '.png':
                add(cell, path, r.get('raw') or r.get('raw_path'), evidence=h['inventory'], priority=10,
                    note='Retained historical diagnostic, not verified replacement.')

    # Existing extraction ledgers preserve failed/anisotropic rectangles too; do not discard that evidence.
    ledgers = set()
    for cell in relevant:
        row = rows[cell]
        ext = row['canonical_record'].get('external_return')
        if ext and Path(ext).is_file():
            ledgers.add(Path(ext))
        assignment = row.get('external_assignment') or {}
        if assignment.get('manifest'):
            outputs = Path(assignment['manifest']).parent / 'outputs'
            ledgers.update(outputs.glob('local_review*/S*/review.json'))
    for path in sorted(ledgers):
        doc = read(path)
        attempt = masters.get(doc.get('attempt'), {})
        raw = attempt.get('raw')
        for r in doc.get('cells', []):
            if isinstance(r, dict):
                add(r.get('id') or r.get('cell_id'), r.get('artifact'), raw, r.get('raw_rect'), path,
                    15 if 'edges_v2' in str(path) else 25,
                    'Recorded extraction diagnostic; ' + r.get('reason', r.get('status', 'unverified')))

    master_ids = sorted({a for c in relevant for a in rows[c]['attempts'] if a in masters})
    raw_index = {}
    for aid in master_ids:
        m = masters[aid]
        raw = m.get('raw')
        if not raw or not Path(raw).is_file():
            continue
        assert digest(raw) == m['raw_sha256'], f'Raw changed: {raw}'
        raw_index[aid] = m
        if raw in raw_cache:
            continue
        raw_cache[raw] = True
        if m.get('layout') and Path(m['layout']).is_file():
            layout = read(m['layout'])
            with Image.open(raw) as image:
                boxes = components(image, layout)
            for cell, box in zip(layout['cells'], boxes):
                add(cell['id'], raw=raw, rect=box, evidence=m['layout'], priority=40,
                    note='PROVISIONAL measured opaque-canvas components/dark gutters + submitted row/slot order. '
                         'Slot identity and full-canvas boundaries NOT visually verified; aspect preserved.')
        if m.get('kind') == 'experiment':
            path = Path(raw).parent / 'measurements.json'
            if path.exists():
                for r in read(path)['cells']:
                    add(r['id'], raw=raw, rect=r['raw_xywh'], evidence=path, priority=50,
                        note='Experimental measured rectangle; slot/canvas unverified; no production approval.')

    OUT.mkdir(parents=True, exist_ok=True)
    summaries = []
    packs = []
    for prefix, characters in sorted(families.items()):
        folder = OUT / prefix.rstrip('-')
        folder.mkdir(exist_ok=True)
        frames = []
        # Include table frame indices plus any extra existing numeric family frames, never body/hand suffixes.
        indices = sorted(set(frame_ids) | {n for name in sources if (n := numeric_frame(name, prefix)) is not None})
        for frame in indices:
            name = f'{prefix}{frame:02d}'
            matches = sources.get(name, [])
            active = [r for r in matches if r['restoration_active']]
            source = next(iter(sorted(active, key=lambda r: ('/engine/' not in r['source_path'], r['source_path']))), None)
            row = next((rows[c] for c in relevant if source and rows[c]['source_path'] == source['source_path']), None)
            record = dict(frame=frame, name=name, table_requested=frame in frame_ids, source=source,
                          aliases=[r['source_path'] for r in matches], cell=row['cell_id'] if row else None,
                          status='missing_native' if not matches else 'excluded_by_usage_scope' if not source else 'raw_only',
                          alternatives=[], selected=None, review_status=row['second_pass_status'] if row else None,
                          attempts=row['attempts'] if row else [], disposition=row['disposition'] if row else None)
            if source:
                assert digest(ROOT / source['source_path']) == source['source_sha256']
            if row:
                unique = {}
                for c in sorted(candidates[row['cell_id']], key=lambda c: (c['priority'], str(c['path']), str(c['raw']))):
                    key = c.get('sha256') or (c['raw'], tuple(c['raw_rect'] or []))
                    unique.setdefault(key, c)
                record['alternatives'] = list(unique.values())
                for c in record['alternatives']:
                    if c['raw_rect']:
                        _, _, rw, rh = c['raw_rect']
                        c['sampling_xy'] = [rw/59,rh/79]
                        c['aspect_error'] = (rw/rh)/(59/79)-1
                        c['below_x2'] = rw < 118 or rh < 158
                    if c['path']:
                        with Image.open(c['path']) as im:
                            c['size'] = list(im.size)
                            c['alpha_range'] = list(im.convert('RGBA').getextrema()[3])
                        if c['size'] != row['x2_size']:
                            c['not_selected_reason'] = 'Existing export is not exact x2; retained as alternate.'
                            continue
                    record['selected'] = c
                    record['status'] = 'existing_x2_diagnostic' if c['path'] else 'provisional_raw_preview'
                    break
            frames.append(record)
        cw, ch, columns = 134, 190, 8
        size = (columns*cw, math.ceil(len(frames)/columns)*ch)
        native_sheet = Image.new('RGB', size, '#222222')
        candidate_sheet = Image.new('RGB', size, '#222222')
        for index, record in enumerate(frames):
            x, y = (index % columns)*cw+8, (index//columns)*ch+24
            record['sheet_rect'] = [x, y, 118, 158]
            native = None
            if record['source']:
                with Image.open(ROOT / record['source']['source_path']) as im:
                    assert im.size == (59, 79), 'New native size requires explicit sheet-layout support'
                    native = im.convert('RGB').resize((118,158), Image.Resampling.NEAREST)
                native_sheet.paste(native, (x,y))
            selected = record['selected']
            if selected:
                if selected['path']:
                    with Image.open(selected['path']) as im:
                        preview = display_candidate(im)
                else:
                    bx, by, w, h = selected['raw_rect']
                    im = raw_image(selected['raw'])
                    assert bx >= 0 and by >= 0 and bx+w <= im.width and by+h <= im.height
                    preview = fitted_preview(im.crop((bx,by,bx+w,by+h)), (118,158))
                    selected['sampling_xy'] = [w/59,h/79]
                    selected['aspect_error'] = (w/h)/(59/79)-1
                    selected['below_x2'] = w < 118 or h < 158
                candidate_sheet.paste(preview, (x,y))
            for sheet in (native_sheet,candidate_sheet):
                draw = ImageDraw.Draw(sheet)
                draw.text((x,y-20),f'{record["frame"]:02d} {record["status"][:16]}',fill='#ffffff')
            if not selected:
                ImageDraw.Draw(candidate_sheet).text((x,y+60),'NO MAPPED ART',fill='#ffad66')
        native_sheet.save(folder/'native_x2.png')
        candidate_sheet.save(folder/'candidate_x2.png')
        summary = dict(prefix=prefix, characters=characters, slots=len(frames),
                       statuses=dict(collections.Counter(r['status'] for r in frames)),
                       review_status='prepared_not_reviewed', approved=False)
        pack = dict(summary=summary, frames=frames,
                    display_policy='Existing exact-x2 diagnostics pasted unchanged. Raw rectangles downsampled '
                    'uniformly with purple padding, never stretched/upscaled; provisional slot identity. '
                    'Missing art is labelled, never replaced with enlarged native. Numeric slideshow is NOT game timing.')
        (folder/'manifest.json').write_text(json.dumps(pack,indent=2)+'\n')
        render_page(folder, pack, raw_index)
        summaries.append(dict(summary, path=folder.name))
        packs.append(pack)
        print(prefix, summary['statuses'], flush=True)
    summary = dict(character_rows=sum(map(len,families.values())), families=len(families),
                   slots=sum(s['slots'] for s in summaries),
                   statuses=dict(collections.Counter(r['status'] for p in packs for r in p['frames'])),
                   raw_master_records=len(raw_index), raw_unique_hashes=len({m['raw_sha256'] for m in raw_index.values()}),
                   canonical_state_unchanged=digest(state_path)==state_hash, approved=0)
    assert summary['canonical_state_unchanged']
    (OUT/'manifest.json').write_text(json.dumps(dict(summary=summary,families=summaries,
        input_hashes=INPUTS,canonical_state_sha256=state_hash,raw_masters=raw_index),indent=2)+'\n')
    cards = ''.join(f'<li><a href="{html.escape(s["path"])}/index.html">{html.escape(s["prefix"])}</a> '
                    f'{html.escape(str(s["statuses"]))}</li>' for s in summaries)
    (OUT/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Player portrait families</title>'
        '<h1>Table-driven player portrait review</h1><p>Preparation only; no artwork approval. '
        'Open a family for paired full-resolution sheets, a frame viewer and all raw alternatives.</p>'
        '<p>Raw previews preserve aspect; purple padding and missing slots are intentional diagnostic warnings. '
        'No NPC-only portraits, body parts or usage-excluded families included.</p><pre>'
        +html.escape(json.dumps(summary,indent=2))+'</pre><ul>'+cards+'</ul>')
    print(json.dumps(summary,indent=2))


def render_page(folder, pack, masters):
    frames = pack['frames']
    raw_ids = sorted({aid for r in frames for aid in r['attempts'] if aid in masters})
    links = ''.join(f'<li><a href="{html.escape(os.path.relpath(masters[a]["raw"],folder))}">'
                    f'{html.escape(a)}</a></li>' for a in raw_ids)
    unique_raw = {}
    for aid in raw_ids:
        unique_raw.setdefault(masters[aid]['raw_sha256'], masters[aid])
    raw_gallery = ''.join('<details><summary>'+html.escape(m['id'])+'</summary>'
                          '<p>Original retained master, unmodified. Not a registered x2 export.</p>'
                          '<img loading="lazy" src="'+html.escape(os.path.relpath(m['raw'],folder))+'"></details>'
                          for m in unique_raw.values())
    rects = json.dumps([r['sheet_rect'] for r in frames])
    labels = json.dumps([f'{r["name"]}: {r["status"]}' for r in frames])
    evidence = []
    for r in frames:
        links_for_frame = []
        for number, c in enumerate(r['alternatives'], 1):
            path = c['path'] or c['raw']
            label = f'Alternative {number}: {c["note"]}'
            if c.get('sampling_xy'):
                label += f' Sampling {c["sampling_xy"]}; aspect error {c["aspect_error"]:.3%}.'
            links_for_frame.append(f'<li><a href="{html.escape(os.path.relpath(path,folder))}">'
                                   f'{html.escape(label)}</a></li>')
        evidence.append(f'<details><summary>{html.escape(r["name"])} — {r["status"]}; '
                        f'{len(r["alternatives"])} alternatives; prior review: {r["review_status"]}</summary>'
                        '<ul>'+''.join(links_for_frame)+'</ul></details>')
    (folder/'index.html').write_text('''<!doctype html><meta charset="utf-8">
<style>body{background:#202020;color:#eee;font:16px sans-serif}a{color:#9cf}
canvas{border:1px solid #777} .sheets{display:flex;gap:12px}img{max-width:none}</style>
<a href="../index.html">All characters</a> · <a href="manifest.json">Frame evidence and alternatives</a>
<h1>'''+html.escape(pack['summary']['prefix'])+''' — prepared, NOT approved</h1>
<p>Native left; selected diagnostic right. Family may mix attempts. Use raw links and manifest for provenance.
Purple padding preserves raw aspect, not runtime placement. Slot mappings remain unverified.</p>
<canvas id="viewer" width="244" height="158"></canvas><br>
<input id="frame" type="range" min="0" max="'''+str(len(frames)-1)+'''" value="0">
<button id="play">Play / stop diagnostic sequence</button><span id="label"></span>
<p>Numeric frame order, 250 ms/frame — NOT actual game animation/timing.</p>
<div class="sheets"><div>Native x2<br><img id="native" src="native_x2.png"></div>
<div>Candidate diagnostics x2<br><img id="candidate" src="candidate_x2.png"></div></div>
<h2>Frame provenance and alternatives</h2>'''+''.join(evidence)+'''
<h2>All retained source sheets (including alternatives)</h2><ul>'''+links+'''</ul>'''+raw_gallery+'''
<script>const rects='''+rects+''', labels='''+labels+''';
const slider=document.getElementById('frame'), n=document.getElementById('native'),
c=document.getElementById('candidate'), ctx=document.getElementById('viewer').getContext('2d');
function show(){const i=+slider.value,r=rects[i];ctx.clearRect(0,0,244,158);
if(n.complete&&c.complete){ctx.drawImage(n,...r,0,0,118,158);ctx.drawImage(c,...r,126,0,118,158);}
document.getElementById('label').textContent=labels[i];}slider.oninput=show;n.onload=show;c.onload=show;
let timer;document.getElementById('play').onclick=()=>{if(timer){clearInterval(timer);timer=null;}
else timer=setInterval(()=>{slider.value=(+slider.value+1)%rects.length;show();},250);};show();</script>''')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html-only', action='store_true', help='Refresh viewers from existing pack manifests')
    args = parser.parse_args()
    if args.html_only:
        document = json.loads((OUT / 'manifest.json').read_text())
        for family in document['families']:
            folder = OUT / family['path']
            render_page(folder, json.loads((folder / 'manifest.json').read_text()), document['raw_masters'])
    else:
        main()
