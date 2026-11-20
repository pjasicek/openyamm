"""Inventory insufficient MM6 detail, its native aliases and coherent regeneration scopes. No AI calls."""
import collections
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

from PIL import Image

HERE = Path(__file__).resolve().parent
CREATURES = HERE.parents[1]
REPO = CREATURES.parents[1]
sys.path.insert(0, str(CREATURES))
from mm6_sampling_audit import audit


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(name, aliases):
    seen = set()
    while name in aliases:
        assert name not in seen, 'Alias cycle: ' + name
        seen.add(name)
        name = aliases[name]
    return name


def animation_uses(manifest):
    uses = collections.defaultdict(list)
    def visit(node, path):
        if isinstance(node, dict):
            if isinstance(node.get('frame'), str):
                uses[node['frame']].append(dict(binding=path, **node))
            else:
                for key, value in node.items():
                    visit(value, path + '/' + str(key))
        elif isinstance(node, list):
            for index, value in enumerate(node):
                visit(value, path + '/' + str(index))
    for key in ['animations', 'animations_by_palette']:
        visit(manifest.get(key, {}), key)
    return uses


def main():
    ledger = read(HERE.parent / 'progress.json')
    previous = read(HERE / 'inventory.json') if (HERE / 'inventory.json').exists() else {}
    previous_jobs = {j['id']: j for f in previous.get('families', []) for j in f['jobs']}
    previous_families = {f['project']: f for f in previous.get('families', [])}
    front_groups = read(CREATURES / 'mm6_goblin/direct_front_final/groups.json')
    front_batches = {frame: 'accepted_front/' + key for key, frames in front_groups.items() for frame in frames}
    families, flat, inputs = [], [], {}
    source_owners = collections.defaultdict(set)
    for family in ledger['families']:
        root = REPO / Path(family['package']).parent
        manifest = read(root / 'manifest.json')
        sources = read(root / 'sources.json')
        registration = read(root / 'registration.json')
        batches = read(root / 'batches.json')
        generation = read(root / 'generation.json')
        generation_batches = generation.get('batches', {})
        if isinstance(generation_batches, list):
            generation_batches = {b['batch']: b for b in generation_batches}
        sampling = audit(root)
        assert all(f['status'] != 'unresolved_provenance' for f in sampling['frames']), family['label']
        aliases = sources.get('pixel_aliases', {})
        measured = {r['frame']: r for r in sampling['frames']}
        pixel_groups = collections.defaultdict(list)
        for name in manifest['frames']:
            image = Image.open(REPO / sources['sources'][name]['path'])
            key = hashlib.sha256(str(image.size).encode() + image.tobytes()).hexdigest()
            pixel_groups[key].append(name)
        pixel_canonical = {}
        for names in pixel_groups.values():
            chosen = min(names, key=lambda n: (measured[n]['status'] != 'at_least_2x_sampling',
                                               n in aliases, n))
            pixel_canonical.update({n: chosen for n in names})
        uses = animation_uses(manifest)
        rows, grouped = [], collections.defaultdict(list)
        for row in sampling['frames']:
            name = row['frame']
            source = sources['sources'][name]
            source_path = REPO / source['path']
            assert source_path.is_file() and sha(source_path) == source['sha256'], source_path
            batch = front_batches[name] if row['batch'] == 'accepted_front' else row['batch']
            status = {'below_2x': 'insufficient', 'at_least_2x_sampling': 'retain_sampling_sufficient',
                      'native_endpoint_preserved': 'retain_native_endpoint'}[row['status']]
            record = dict(row, status=status, generation_batch=batch,
                          canonical_frame=pixel_canonical[name], declared_canonical_frame=canonical(name, aliases),
                          source=source,
                          native_bindings=uses[name], required_redo=status == 'insufficient',
                          dependent_atlas_page=manifest['frames'][name]['page'])
            if status == 'insufficient':
                record['repair_method'] = ('reuse_sufficient_native_alias'
                    if measured[record['canonical_frame']]['status'] == 'at_least_2x_sampling'
                    else 'regenerate_canonical_base')
            rows.append(record)
            grouped[batch].append(record)
            if status == 'insufficient':
                flat.append(dict(family=family['label'], project=str(root.relative_to(REPO)), frame=name,
                                 canonical_frame=record['canonical_frame'], batch=batch, status=status,
                                 sampling_x=row['sampling_x'], sampling_y=row['sampling_y'], source=source['path']))
                source_owners[source['sha256']].add(family['label'] + '/' + record['canonical_frame'])
        jobs = []
        for batch, frames in grouped.items():
            failed = [r for r in frames if r['required_redo']]
            if not failed:
                continue
            names = [r['frame'] for r in frames]
            native_bounds = []
            for name in names:
                source = sources['sources'][name]
                box = Image.open(REPO / source['path']).getbbox()
                if box:
                    offset = manifest['frames'][name].get('native_offset', [0, 0])
                    native_bounds.append([box[0] + offset[0], box[1] + offset[1],
                                          box[2] + offset[0], box[3] + offset[1]])
            crop = [math.floor(min(b[0] for b in native_bounds)) - 6,
                    math.floor(min(b[1] for b in native_bounds)) - 6,
                    math.ceil(max(b[2] for b in native_bounds)) + 6,
                    math.ceil(max(b[3] for b in native_bounds)) + 6]
            project = str(root.relative_to(REPO))
            job_id = project + ':' + batch
            provenance = generation_batches.get(batch)
            raw_path = root / 'raw' / (batch + '.png')
            job = dict(id=job_id, status='pending', quality_status='insufficient',
                       batch=batch, failed_frames=[r['frame'] for r in failed],
                       unique_failed_frames=sorted({r['canonical_frame'] for r in failed}),
                       generation_required_frames=sorted({r['canonical_frame'] for r in failed
                           if r['repair_method']=='regenerate_canonical_base'}),
                       reuse_sufficient_aliases={r['frame']: r['canonical_frame'] for r in failed
                           if r['repair_method']=='reuse_sufficient_native_alias'},
                       sequence_context_frames=names,
                       sufficient_context_frames=[r['frame'] for r in frames if not r['required_redo']],
                       native_crop_xyxy_with_6px_padding=crop,
                       native_crop_size=[crop[2] - crop[0], crop[3] - crop[1]],
                       previous_layout=batches.get(batch), previous_generation=provenance,
                       provenance_file=project + '/generation.json',
                       registration_file=project + '/registration.json',
                       minimum_sampling=min(min(r['sampling_x'], r['sampling_y']) for r in failed),
                       output_stage=project + '/redo_2x',
                       note='A repair scope, not a fixed AI request: choose new grid/sub-batches using actual pixel budget.')
            if raw_path.is_file():
                job['raw'] = dict(path=str(raw_path.relative_to(REPO)), sha256=sha(raw_path),
                                  actual_size=list(Image.open(raw_path).size))
            if batch.startswith('accepted_front/'):
                job['retained_front_provenance'] = 'level_generation/creatures/mm6_goblin/direct_front_final/extraction_manifest.json'
            signature = hashlib.sha256(json.dumps([frames, job.get('raw')], sort_keys=True).encode()).hexdigest()
            job['input_signature'] = signature
            old = previous_jobs.get(job_id)
            if old and old.get('input_signature') == signature:
                for key in ['status', 'attempts', 'selected_checkpoint', 'blocker', 'resume_step', 'run']:
                    if key in old:
                        job[key] = old[key]
            jobs.append(job)
        status = 'insufficient' if jobs else 'sampling_sufficient_motion_unverified'
        counts = dict(collections.Counter(r['status'] for r in rows))
        project = str(root.relative_to(REPO))
        family_row = dict(family=family['label'], descriptor_id=family['descriptor_id'], project=project,
                          status=status, installed_package=family['installed_package'], counts=counts,
                          unique_failed_native_frames=len({r['canonical_frame'] for r in rows if r['required_redo']}),
                          unique_poses_to_generate=len({r['canonical_frame'] for r in rows
                              if r.get('repair_method')=='regenerate_canonical_base'}),
                          derived_pixel_aliases={n: c for n, c in pixel_canonical.items() if n != c},
                          palette_variants=list(manifest['variants']),
                          logical_canvas=manifest['logical_canvas'], logical_pivot=manifest['logical_pivot'],
                          jobs=jobs, frames=rows)
        old_family = previous_families.get(project, {})
        for key in ['execution_status', 'selected_checkpoint', 'acceptance']:
            if key in old_family:
                family_row[key] = old_family[key]
        families.append(family_row)
        evidence = {name: sha(root / name) for name in ['manifest.json', 'registration.json', 'sources.json']}
        inputs[project] = evidence
        write(root / 'quality_status.json', dict(status=status, generated_detail_minimum=2,
              insufficient_frames=[r['frame'] for r in rows if r['required_redo']],
              inventory='level_generation/creatures/mm6_remaining/redo_2x/inventory.json',
              evaluated_sources=evidence, installed_art_retained=True,
              animation_landmarks_status='not_exhaustively_validated',
              note='Historical acceptance does not satisfy the new detail/animation quality gates.'))
    summary = dict(families=60, insufficient_families=sum(bool(f['jobs']) for f in families),
                   insufficient_frame_names=len(flat),
                   unique_failed_native_frames_within_families=sum(f['unique_failed_native_frames'] for f in families),
                   distinct_failed_native_file_hashes=len(source_owners),
                   unique_poses_to_generate=sum(f['unique_poses_to_generate'] for f in families),
                   reuse_sufficient_alias_frame_names=sum(r.get('repair_method')=='reuse_sufficient_native_alias'
                       for f in families for r in f['frames']),
                   regeneration_scopes=sum(len(f['jobs']) for f in families),
                   sufficient_frame_names=sum(f['counts'].get('retain_sampling_sufficient', 0) for f in families),
                   preserved_native_endpoints=sum(f['counts'].get('retain_native_endpoint', 0) for f in families))
    inventory = dict(schema_version=1, scope='MM6 native creatures/actors only; all 60 installed families',
                     status=previous.get('status', 'inventoried_no_generation_started'), summary=summary, inputs=inputs,
                     families=families, shared_native_sources={k: sorted(v) for k, v in source_owners.items() if len(v) > 1},
                     policy='Generate canonical base art once; preserve native aliases/mirrors and derive palette variants. '
                            'Only failed frames require replacement; adequate neighbors are context/overlap unless a defect is proven.')
    if 'execution_policy' in previous:
        inventory['execution_policy'] = previous['execution_policy']
    write(HERE / 'inventory.json', inventory)
    with (HERE / 'insufficient_frames.csv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(flat[0]))
        writer.writeheader()
        writer.writerows(flat)
    lines = ['# MM6 assets requiring regeneration', '',
             '**Insufficient means generated below 2x**, regardless of current atlas dimensions or prior acceptance.',
             'This is an inventory, not a generation run. [Workflow](WORKFLOW.md); [machine inventory](inventory.json).', '',
             f"{summary['insufficient_frame_names']} frame names, {summary['insufficient_families']} families, "
             f"{summary['regeneration_scopes']} original batch/action repair scopes (not a fixed imagegen-call count).", '',
             '| Family | Status | Insufficient names | Canonical frames | Repair scopes |',
             '| --- | --- | ---: | ---: | ---: |']
    for f in families:
        lines.append(f"| {f['family']} | {f['status']} | {f['counts'].get('insufficient', 0)} | "
                     f"{f['unique_failed_native_frames']} | {len(f['jobs'])} |")
    (HERE / 'INVENTORY.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
