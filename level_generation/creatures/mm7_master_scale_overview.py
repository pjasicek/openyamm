"""Report measured generated master sampling, independently of the fixed 2x export."""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent


def run():
    progress = json.loads((HERE / 'mm7_progress.json').read_text())
    rows = []
    details = {}
    for key, family in progress['families'].items():
        project = HERE / family['project']
        path = project / 'registration.json'
        registration = json.loads(path.read_text()) if path.exists() else {}
        sampling = {name: 2 / frame['scale'] for name, frame in registration.items()}
        values = list(sampling.values())
        notes = []
        generation_path = project / 'generation.json'
        unregistered = []
        if generation_path.exists():
            generation = json.loads(generation_path.read_text())
            registered_batches = {frame['batch'] for frame in registration.values()}
            active_path = project / 'batches.json'
            active = json.loads(active_path.read_text()) if active_path.exists() else {}
            for batch, entry in generation.get('batches', {}).items():
                if entry.get('selected') and batch in active and batch not in registered_batches:
                    unregistered.append(batch)
        if unregistered:
            notes.append(f'{len(unregistered)} selected replacement sheets await registration; '
                         'reported scales describe the existing processed frames.')
        if key == 'mm7_m210':
            notes.append('Five provisional standing frames only; identity correction remains blocked.')
        if family['status'] == 'blocked':
            notes.append('Coverage/visual blocker remains; sampling alone does not establish completion.')
        rows.append(dict(project=key, family=family['label'], status=family['status'],
                         measured_frames=len(values), expected_frames=family['expected_all_native_frames'],
                         minimum=min(values) if values else None,
                         median=median(values) if values else None,
                         maximum=max(values) if values else None,
                         below_2x=sum(value < 2 - 1e-6 for value in values), notes=' '.join(notes)))
        details[key] = dict(registration_sha256=hashlib.sha256(path.read_bytes()).hexdigest()
                           if path.exists() else None, frame_sampling=sampling,
                           selected_unregistered_batches=unregistered)
    timestamp = datetime.now(timezone.utc).isoformat()
    report = dict(updated_utc=timestamp, summary=progress['summary'],
                  measurement='Raw generated pixels per native pixel = 2 / raw-to-2x registration scale. '
                              'Linear resolution, not area, artistic quality or gameplay descriptor scale. '
                              'Ranges include all registered unique frames, including unused native poses. '
                              'Aligned/exported masters are fixed 2x. Missing frames receive no scale.',
                  families=rows, details=details)
    (HERE / 'mm7_master_scale_overview.json').write_text(json.dumps(report, indent=2) + '\n')
    with (HERE / 'mm7_master_scale_overview.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    counts = progress['summary']
    summary = ', '.join(f'{counts.get(status, 0)} {status}'
                        for status in ['validated', 'partial', 'blocked', 'pending'])
    lines = ['# MM7 generated master scale overview', '', f'Measured {timestamp}.', '',
             f'{summary}: {len(rows)} families, {len(rows) - counts.get("validated", 0)} remaining.', '',
             report['measurement'], '',
             'Minimum is the conservative whole-family figure. Median is weighted by unique frame count; '
             'neither palette multiplicity nor repeated playback entries add weight. '
             'Pending families have no measurable restored master.', '',
             '| Family | Project | Status | Measured/native frames | Minimum | Median | Maximum | Below 2× |',
             '|---|---|---|---:|---:|---:|---:|---:|']
    for row in rows:
        scales = ['—' if row[key] is None else f'{row[key]:.3f}×'
                  for key in ['minimum', 'median', 'maximum']]
        lines.append(f"| {row['family']} | {row['project']} | {row['status']} | "
                     f"{row['measured_frames']}/{row['expected_frames']} | "
                     + ' | '.join(scales) + f" | {row['below_2x'] if row['measured_frames'] else '—'} |")
    lines += ['', 'Current exceptions:', '']
    lines += [f"- {row['project']}: {row['notes']}" for row in rows if row['notes']]
    lines += ['', 'Rebuild this snapshot after refreshing inventory and progress:', '',
              '```sh', 'python3 level_generation/creatures/mm7_master_scale_overview.py', '```', '']
    (HERE / 'MM7_MASTER_SCALE_OVERVIEW.md').write_text('\n'.join(lines))
    print(json.dumps(dict(summary=progress['summary'], families=len(rows),
                          measured=sum(bool(row['measured_frames']) for row in rows)), indent=2))


if __name__ == '__main__':
    run()
