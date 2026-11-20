"""Screen current MM6 generation rows for relative size drift; never modify artwork or acceptance."""

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
from itertools import combinations
import json
from pathlib import Path
from statistics import median

from PIL import Image


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def packages():
    progress = read(HERE.parent / 'redo_2x/progress.json')['families']
    names = {item['family'] for item in progress}
    result = [(item['family'], REPO / item['project'] / 'redo_2x') for item in progress]
    result.extend((item['family'], (REPO / item['package']).parent)
                  for item in read(HERE / 'audit.json')['families'] if item['family'] not in names)
    return result


def alpha_metrics(path, scale):
    with Image.open(path) as image:
        alpha = image.getchannel('A').point(lambda value: 255 if value >= 128 else 0)
        bounds = alpha.getbbox()
        if bounds is None:
            return None
        return {'height': (bounds[3] - bounds[1]) / scale,
                'width': (bounds[2] - bounds[0]) / scale,
                'area': alpha.histogram()[255] / scale ** 2}


def landmark_pair(records):
    """Use the same longest vertical pair across every pose; exclude known diagnostic points."""
    usable = []
    for record in records:
        points = record.get('review_landmarks', {})
        excluded = record.get('diagnostic_landmarks', [])
        usable.append({key for key, point in points.items() if key not in excluded
                       and 'native' in point and 'restored_before_translation' in point})
    common = set.intersection(*usable)
    choices = []
    for first, second in combinations(sorted(common), 2):
        spans = []
        for record in records:
            points = record['review_landmarks']
            spans.append(abs(points[first]['native'][1] - points[second]['native'][1]))
        if min(spans) >= 20:
            choices.append((median(spans), first, second))
    return max(choices)[1:] if choices else None


def summarize_rows(frames, field):
    cells = defaultdict(list)
    for frame in frames:
        if frame.get(field) is not None:
            cells[(frame['row'], tuple(frame['raw_rect']))].append(frame[field])
    grouped = defaultdict(list)
    for (row, _), values in cells.items():
        # Pixel aliases of one generated cell are not independent samples.
        grouped[row].append(median(values))
    return [{'row': row, 'count': len(values), 'median': median(values),
             'min': min(values), 'max': max(values),
             'mad': median(abs(value - median(values)) for value in values)}
            for row, values in sorted(grouped.items())]


def compare_rows(rows):
    if len(rows) < 2:
        return []
    first = rows[0]
    return [{'rows': [first['row'], other['row']],
             'relative_percent': 100 * (other['median'] / first['median'] - 1),
             'replicated': min(first['count'], other['count']) >= 2,
             'nonoverlapping_ranges': other['max'] < first['min'] or other['min'] > first['max']}
            for other in rows[1:] if first['median'] > 0]


def audit_family(label, root):
    manifest = read(root / 'manifest.json')
    registration = read(root / 'registration.json')
    generation = read(root / 'generation.json')
    palette = next(key for key, variant in manifest['variants'].items() if variant.get('exact_base_bypass'))
    sheets = defaultdict(list)
    ungrouped = []
    for name in manifest['frames']:
        record = registration[name]
        if 'raw_rect' not in record or 'scale' not in record:
            ungrouped.append({'frame': name, 'batch': record.get('batch'),
                              'reason': 'No recorded source-sheet rectangle/scale'})
            continue
        raw_path = record.get('raw_path')
        if not raw_path:
            raw_path = str((root / generation['batches'][record['batch']]['raw']['path']).relative_to(REPO))
        raw_path = str((REPO / raw_path).relative_to(REPO))
        sheets[raw_path].append((name, record))
    results = []
    for raw_path, entries in sheets.items():
        row_tops = sorted({record['raw_rect'][1] for _, record in entries})
        # The recorded extraction rectangles establish row identity; animation ordering does not.
        pair = landmark_pair([record for _, record in entries])
        frames = []
        for name, record in entries:
            native = alpha_metrics(root / 'native_variants' / f'{name}_{palette}.png', 1)
            restored = alpha_metrics(root / 'aligned_2x' / f'{name}.png', manifest['pixels_per_logical_pixel'])
            frame = {'frame': name, 'row': row_tops.index(record['raw_rect'][1]),
                     'raw_rect': record['raw_rect'], 'export_scale': record['scale'],
                     'height_ratio': None, 'width_ratio': None, 'area_scale_ratio': None,
                     'landmark_ratio': None}
            if native and restored:
                frame.update(height_ratio=restored['height'] / native['height'],
                             width_ratio=restored['width'] / native['width'],
                             area_scale_ratio=(restored['area'] / native['area']) ** 0.5)
            if pair:
                points = record['review_landmarks']
                first, second = (points[key] for key in pair)
                native_span = abs(first['native'][1] - second['native'][1])
                restored_span = abs(first['restored_before_translation'][1]
                                    - second['restored_before_translation'][1]) / 2
                frame.update(landmark_ratio=restored_span / native_span,
                             native_landmark_span=native_span, restored_landmark_span=restored_span)
            frames.append(frame)
        metrics = {field: summarize_rows(frames, field) for field in
                   ['height_ratio', 'width_ratio', 'area_scale_ratio', 'landmark_ratio', 'export_scale']}
        comparisons = {field: compare_rows(rows) for field, rows in metrics.items()}
        preferred = 'landmark_ratio' if pair else 'height_ratio'
        candidates = [item for item in comparisons[preferred]
                      if item['replicated'] and abs(item['relative_percent']) >= 2]
        results.append({'raw_path': raw_path, 'raw_sha256': digest(REPO / raw_path),
                        'batches': sorted({record['batch'] for _, record in entries}),
                        'rows': len(row_tops), 'landmark_pair': pair, 'frames': frames,
                        'metrics': metrics, 'comparisons': comparisons,
                        'screening_method': preferred, 'candidate': bool(candidates),
                        'largest_row_difference_percent': max(
                            (abs(item['relative_percent']) for item in comparisons[preferred]
                             if item['replicated']), default=0)})
    return {'family': label, 'root': str(root.relative_to(REPO)), 'creature': manifest['creature'],
            'manifest_sha256': digest(root / 'manifest.json'),
            'registration_sha256': digest(root / 'registration.json'), 'ungrouped_frames': ungrouped,
            'frame_count': len(manifest['frames']), 'sheets': results}


def summary_counts(families):
    sheets = [sheet for family in families for sheet in family['sheets']]
    multi = [sheet for sheet in sheets if sheet['rows'] > 1]
    candidates = [sheet for sheet in multi if sheet['candidate']]
    return {'families': len(families), 'frames': sum(family['frame_count'] for family in families),
              'frames_grouped': sum(len(sheet['frames']) for sheet in sheets),
              'frames_without_sheet_mapping': sum(len(family['ungrouped_frames']) for family in families),
              'source_sheets': len(sheets), 'multiple_row_sheets': len(multi),
              'multiple_row_families': sum(any(sheet['rows'] > 1 for sheet in family['sheets'])
                                           for family in families),
              'multiple_row_with_landmarks': sum(bool(sheet['landmark_pair']) for sheet in multi),
              'sheets_with_two_or_more_frames_in_compared_rows': sum(
                  any(item['replicated'] for item in sheet['comparisons']['height_ratio']) for sheet in multi),
              'landmark_sheets_with_two_or_more_frames_in_compared_rows': sum(
                  any(item['replicated'] for item in sheet['comparisons']['landmark_ratio']) for sheet in multi),
              'candidate_sheets': len(candidates),
              'candidate_families': sum(any(sheet['candidate'] for sheet in family['sheets'])
                                        for family in families),
              'landmark_candidate_sheets': sum(bool(sheet['landmark_pair']) for sheet in candidates),
              'landmark_candidate_families': sum(
                  any(sheet['candidate'] and sheet['landmark_pair'] for sheet in family['sheets'])
                  for family in families),
              'landmark_candidates_with_one_export_scale': sum(
                  bool(sheet['landmark_pair']) and
                  max(frame['export_scale'] for frame in sheet['frames']) -
                  min(frame['export_scale'] for frame in sheet['frames']) < 1e-8 for sheet in candidates),
              'nonoverlapping_landmark_candidate_sheets': sum(
                  any(item['replicated'] and abs(item['relative_percent']) >= 2
                      and item['nonoverlapping_ranges'] for item in sheet['comparisons']['landmark_ratio'])
                  for sheet in candidates)}


def run(output):
    families = []
    for label, root in packages():
        families.append(audit_family(label, root))
        print(label, flush=True)
    counts = summary_counts(families)
    report = {'created_utc': datetime.now(timezone.utc).isoformat(), 'counts': counts,
              'method': 'Per-pose restored/native size ratios; compare medians by recorded raw-sheet row. '
                        'Prefer the longest common named vertical landmark pair, excluding diagnostic points; '
                        'otherwise use alpha>=128 silhouette height. Flag >=2% relative row difference '
                        'with at least two distinct generated cells per row; pixel aliases count once. '
                        'Width and sqrt(area) are supporting screens.',
              'limitations': ['Candidates require visual review; weapons, effects and changed anatomy can fool bounds.',
                              'Saved landmarks are prior annotations, not fresh measurements of every current pixel.',
                              'Rows can correlate with views or phases; this does not establish row layout as the cause.',
                              'Measurements describe current selected masters; historical superseded sheets are excluded.',
                              'No automatic fix, artwork change, acceptance change or saved viewer offset is applied.'],
              'families': families}
    write_report(report, output)
    print(json.dumps(counts, indent=2))


def write_report(report, output):
    families = report['families']
    counts = report['counts']
    output.mkdir(parents=True, exist_ok=True)
    (output / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    lines = ['# MM6 source-sheet row scale screening', '', report['method'], '',
             'These are review candidates, not confirmed uniform-scale defects.', '',
             '```json', json.dumps(counts, indent=2), '```', '']
    if report.get('visual_review'):
        lines += ['## Inspected examples', '', report['visual_review']['method'], '',
                  '| Family / sheet | Finding | Contact |', '| --- | --- | --- |']
        for check in report['visual_review']['checks']:
            lines.append(f"| {check['family']} / {check['batch']} | {check['finding']} | "
                         f"[image]({check['contact']}) |")
        lines += ['', report['visual_review']['conclusion'], '']
    lines += ['## All screening candidates', '',
             '| Family | Sheet | Rows | Basis | Row difference |', '| --- | --- | ---: | --- | ---: |']
    ranked = sorted(((sheet['largest_row_difference_percent'], family, sheet)
                     for family in families for sheet in family['sheets'] if sheet['candidate']),
                    key=lambda item: item[0], reverse=True)
    for _, family, sheet in ranked:
        comparisons = sheet['comparisons'][sheet['screening_method']]
        differences = ', '.join(f"{item['rows'][0] + 1}→{item['rows'][1] + 1}: "
                                f"{item['relative_percent']:+.2f}%" for item in comparisons)
        basis = ' / '.join(sheet['landmark_pair']) if sheet['landmark_pair'] else 'silhouette only'
        lines.append(f"| {family['family']} | {', '.join(sheet['batches'])} | {sheet['rows']} | {basis} | {differences} |")
    lines += ['', '## Limits', ''] + ['- ' + item for item in report['limitations']]
    (output / 'SUMMARY.md').write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=HERE / 'row_scale_audit')
    run(parser.parse_args().output)
