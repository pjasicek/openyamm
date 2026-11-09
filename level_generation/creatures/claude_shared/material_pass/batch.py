#!/usr/bin/env python3
"""Material pass over every installed MM6 creature and attachment (material_classes_to_orm.py), batch phase.

For each assets_source/worlds/mm6/models/*.glb:
1. Back it up to backup_pre_material_pass/ (an existing backup is kept: the pilots are already installed, so their
   backups are the pre-pass originals). The pre-pass GLB (the backup) is the input.
2. Find the project that produced it (same bytes among level_generation/creatures/**/*.glb outside meshy/), and the
   class maps (textures/**/*material_classes*.png, outside work/ and review/) in it, in the other projects of the
   same creature code (mm6_<code>_*) and in projects whose maps are named <code>_*.
3. Per metallic-roughness image, the role from its material names (head, wings, cloak, or the attachment word for an
   attachment model, else body) picks the candidate maps; every body x head combination is fitted against the GLB's
   UVs (dry run) and the best one is kept. An image whose best fit leaves over 5 % of the island texels without a
   class (more than 2 texels from one) skips the model; no --force.
4. Deliberate choices: an image whose material has the specular mask on and gives skin, fur or cloth an old effective
   specular between 0.05 and 0.95 keeps those classes' old specular and roughness (--keep-classes).
5. The three pilots (bar1, gob2, kni) are the coordinator's decided pilot outputs, copied from pilot/.
Writes batch/<name>.glb, batch/<name>.json, batch/batch_results.json and batch/SUMMARY.md. Installs nothing.
Usage: batch.py [name ...]   (default: every model)"""
import hashlib
import itertools
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import material_classes_to_orm as M  # noqa: E402

ROOT = HERE.parents[3]
MODELS = ROOT / 'assets_source' / 'worlds' / 'mm6' / 'models'
CREATURES = ROOT / 'level_generation' / 'creatures'
BACKUP = HERE / 'backup_pre_material_pass'
OUT = HERE / 'batch'
PILOTS = {'mm6_bar1': 'skin', 'mm6_gob2': '', 'mm6_kni': ''}
ATTACHMENTS = ('sword', 'bow', 'arrow', 'axe', 'staff', 'knife', 'shield', 'buckler', 'spear', 'mace', 'halberd',
               'trident', 'club', 'blade', 'remains')
KEEP_CANDIDATES = (1, 2, 8)   # skin, fur, cloth
DELIBERATE = (0.05, 0.95)
NOTES = [
    '- Pilots keep the coordinator\'s decisions (bar1: keep skin; gob2 and kni: table values). The batch rule alone',
    '  would also keep the knight\'s hair (old mask 0.25) and the barbarian\'s fur and leather (0.1-0.35).',
    '- The barbarian\'s head class map was derived (`bar1_head_classes.py`,',
    '  `../pilot/bar1_head_material_classes.png`).',
    '- The output is compacted: mm6_mep and mm6_mep_staff lose LOD materials and images no primitive referenced.',
    '- "No class map" covers models whose producing project and related projects have none; a skipped fit means the',
    '  map was made for another UV layout (an earlier mesh, a re-UV after reduction or an unusual atlas packing).',
    '- Models found by bytes in no project (mm6_pmn2_staff, mm6_rob1, mm6_ske_sword) are skipped, as instructed.',
]


def md5(path):
    return hashlib.md5(path.read_bytes()).hexdigest()


def producing_projects(model):
    size, digest = model.stat().st_size, md5(model)
    found = []
    for path in CREATURES.rglob('*.glb'):
        parts = path.relative_to(CREATURES).parts
        if 'meshy' in parts or parts[0] == 'claude_shared' or path.stat().st_size != size:
            continue
        if md5(path) == digest:
            found.append(path)
    return found


def class_maps(code, projects):
    dirs = set(projects) | {p for p in CREATURES.glob(f'mm6_{code}_*') if p.is_dir()}
    for path in CREATURES.glob(f'mm6_*/textures/**/{code}_*material_classes*.png'):
        dirs.add(CREATURES / path.relative_to(CREATURES).parts[0])
    maps = []
    for d in sorted(dirs):
        for path in sorted(d.glob('textures/**/*material_classes*.png')):
            if not {'work', 'review'} & set(path.relative_to(d).parts):
                maps.append(path)
    return maps


def map_role(path):
    name, folder = path.name.lower(), path.parent.name.lower()
    for word in ATTACHMENTS:
        if word in folder or word in name:
            return word
    for word in ('head', 'wings', 'cloak'):
        if word in name:
            return word
    return 'body'


def image_role(materials, attachment):
    names = ' '.join(m.get('name', '') for m in materials).lower()
    if attachment:
        return attachment
    for word in ('wings', 'cloak'):
        if word in names:
            return word
    if all('head' in m.get('name', '').lower() for m in materials):
        return 'head'
    return 'body'


def groups_of(path):
    doc, _ = M.RV.read_glb(path)
    groups = {}
    for material in doc['materials']:
        texture = material.get('pbrMetallicRoughness', {}).get('metallicRoughnessTexture')
        if texture is not None:
            source = doc['textures'][texture['index']]['source']
            groups.setdefault(source, (doc['images'][source], []))[1].append(material)
    return list(groups.values())


def score(report):
    entry = report['textures'][0]
    return max(p['uv_covered_without_class_far'] for p in entry['parts'].values())


def plan(name, source, maps):
    """Per image: (matcher, body, head, fit report) of the best-fitting combination, or a skip reason."""
    attachment = next((w for w in ATTACHMENTS if name.endswith('_' + w) or f'_{w}' in name[4:]), None)
    by_role = {}
    for path in maps:
        by_role.setdefault(map_role(path), []).append(path)
    chosen = []
    for image, materials in groups_of(source):
        role = image_role(materials, attachment)
        matcher = '=' + materials[0]['name']
        if role == 'head':
            combos = [(None, h) for h in by_role.get('head', [])]
        elif role == 'body':
            combos = list(itertools.product(by_role.get('body', []), by_role.get('head', []) + [None]))
        else:
            combos = [(b, None) for b in by_role.get(role, [])]
        best = None
        for body, head in combos:
            try:
                report = M.convert(source, None, [(matcher, body, head)], dry_run=True)
            except ValueError as error:
                last_error = str(error)
                continue
            if best is None or score(report) < best[3]:
                best = (body, head, report, score(report))
        if not combos:
            chosen.append({'image': image.get('name'), 'role': role, 'matcher': matcher, 'skip': 'no class map'})
        elif best is None:
            chosen.append({'image': image.get('name'), 'role': role, 'matcher': matcher, 'skip': last_error})
        else:
            body, head, report, fit = best
            reason = f'class map does not fit the UVs ({fit:.1%} of island texels far from a class)'
            chosen.append({'image': image.get('name'), 'role': role, 'matcher': matcher, 'body': body, 'head': head,
                           'fit': fit, 'report': report['textures'][0],
                           'skip': None if fit <= M.MAX_UNLABELLED else reason})
    return chosen


def keep_for(entry):
    if not entry['old_factors']['openyamm_specular_mask']:
        return []
    old = entry['old_specular_mean_by_class']
    return [M.NAMES[k] for k in KEEP_CANDIDATES
            if M.NAMES[k] in old and DELIBERATE[0] < old[M.NAMES[k]] < DELIBERATE[1]]


def run(name):
    model = MODELS / f'{name}.glb'
    backup = BACKUP / f'{name}.glb'
    if not backup.exists():
        shutil.copy2(model, backup)
    result = {'name': name, 'backup': str(backup.relative_to(ROOT))}
    if name in PILOTS:
        shutil.copy2(HERE / 'pilot' / f'{name}.glb', OUT / f'{name}.glb')
        shutil.copy2(HERE / 'pilot' / f'{name}.json', OUT / f'{name}.json')
        report = json.loads((OUT / f'{name}.json').read_text())
        result.update(status='processed (pilot)', keep={'*': PILOTS[name].split(',') if PILOTS[name] else []},
                      flags=metal_flags(report), report=report)
        return result
    projects = sorted({CREATURES / p.relative_to(CREATURES).parts[0] for p in producing_projects(backup)})
    result['projects'] = [str(p.relative_to(ROOT)) for p in projects]
    groups = groups_of(backup)
    if not groups:
        result.update(status='skipped', reason='no metallic-roughness texture (unlit/effect or factor-only materials)')
        return result
    if not projects:
        result.update(status='skipped', reason='no project GLB with the same bytes')
        return result
    code = name[4:].split('_')[0]
    maps = class_maps(code, projects)
    result['class_maps_found'] = [str(p.relative_to(ROOT)) for p in maps]
    if not maps:
        result.update(status='skipped', reason='no class map in the producing or related projects')
        return result
    chosen = plan(name, backup, maps)
    result['images'] = [{k: (str(v.relative_to(ROOT)) if isinstance(v, Path) else v) for k, v in c.items()
                         if k != 'report'} for c in chosen]
    bad = [c for c in chosen if c['skip'] and c['skip'] != 'no class map']
    usable = [c for c in chosen if not c['skip']]
    if bad or not usable:
        result.update(status='skipped', reason='; '.join(f"{c['image']}: {c['skip']}" for c in (bad or chosen)))
        return result
    assignments, keep = [], {}
    for c in usable:
        k = keep_for(c['report'])
        keep[c['image']] = k
        assignments.append((c['matcher'], c['body'], c['head'], M.parse_classes(','.join(k))))
    report = M.convert(backup, OUT / f'{name}.glb', assignments)
    (OUT / f'{name}.json').write_text(json.dumps(report, indent=1) + '\n')
    partial = [c['image'] for c in chosen if c['skip'] == 'no class map']
    result.update(status='processed' + (' (partly: no class map for ' + ', '.join(partial) + ')' if partial else ''),
                  keep=keep, flags=metal_flags(report), report=report)
    return result


def metal_flags(report):
    flags = []
    for entry in report['textures']:
        for material, metal in entry['metal_base_colour'].items():
            if metal:
                lum = metal['luminance_srgb_p10_p50_p90'][1]
                if lum < M.DARK_METAL or lum > M.BRIGHT_METAL:
                    flags.append(f"{material}: metal median luminance {lum} "
                                 f"({'very dark' if lum < M.DARK_METAL else 'very bright'})")
    return flags


def summary(results):
    lines = ['# Material pass, MM6 batch', '',
             'Converted GLBs for review; **nothing is installed**. Inputs are the pre-pass sources in',
             '`../backup_pre_material_pass/` (the three pilots are already installed and copied from `../pilot/`).',
             'Install after review with `tools/install_model.py material_pass/batch/<name>.glb --world mm6`; revert',
             'with `../revert.sh [name ...]`. Contact sheets: `contact_sheet_*.png` (old / new, front, neutral key and',
             'dim indoor light).', '']
    done = [r for r in results if r['status'].startswith('processed')]
    skipped = [r for r in results if r['status'] == 'skipped']
    lines += [f'Processed {len(done)}, skipped {len(skipped)} of {len(results)}.', '', '## Processed', '',
              '| Model | Class maps | Keep classes | Metal (median sRGB luminance per material) | Flags |',
              '|---|---|---|---|---|']
    for r in done:
        maps, lums = [], []
        for entry in r['report']['textures']:
            for part in entry['parts'].values():
                maps.append(Path(part['class_map']).relative_to(CREATURES).as_posix()
                            if part['class_map'].startswith(str(CREATURES)) else part['class_map'])
            metals = [m['luminance_srgb_p10_p50_p90'][1] for m in entry['metal_base_colour'].values() if m]
            if metals:
                lums.append(f"{entry['image']}: {min(metals)}-{max(metals)}" if min(metals) != max(metals)
                            else f"{entry['image']}: {metals[0]}")
        keep = '; '.join(f"{k}: {', '.join(v)}" for k, v in r['keep'].items() if v) or '-'
        note = ' (pilot)' if 'pilot' in r['status'] else (' (partly)' if 'partly' in r['status'] else '')
        lines.append(f"| {r['name']}{note} | {'<br>'.join(sorted(set(maps)))} | {keep} | "
                     f"{'<br>'.join(lums) or 'no metal'} | {'<br>'.join(r['flags']) or '-'} |")
    partly = [r for r in done if 'partly' in r['status']]
    if partly:
        lines += ['', 'Partly processed (images without a class map left unchanged):', '']
        lines += [f"- {r['name']}: {r['status'].split('(partly: ')[1].rstrip(')')}" for r in partly]
    lines += ['', '## Skipped', '', '| Model | Reason |', '|---|---|']
    lines += [f"| {r['name']} | {r['reason']} |" for r in skipped]
    flagged = [r for r in done if r['flags']]
    lines += ['', '## Flags (metal median luminance below 40 or above 230)', '']
    lines += [f"- {r['name']}: {'; '.join(r['flags'])}" for r in flagged] or ['- none']
    lines += ['', '## Notes', '', *NOTES]
    (OUT / 'SUMMARY.md').write_text('\n'.join(lines) + '\n')


def main():
    OUT.mkdir(exist_ok=True)
    BACKUP.mkdir(exist_ok=True)
    names = sys.argv[1:] or sorted(p.stem for p in MODELS.glob('*.glb'))
    results_path = OUT / 'batch_results.json'
    results = {r['name']: r for r in json.loads(results_path.read_text())} if results_path.exists() else {}
    for name in names:
        try:
            result = run(name)
        except Exception as error:  # noqa: BLE001 - one model's failure is recorded, the batch goes on
            result = {'name': name, 'status': 'skipped', 'reason': f'error: {error}'}
        print(name, result['status'], result.get('reason', ''), result.get('keep', ''), result.get('flags', ''),
              flush=True)
        results[name] = result
    ordered = [results[k] for k in sorted(results)]
    results_path.write_text(json.dumps([{k: v for k, v in r.items() if k != 'report'} for r in ordered], indent=1))
    for r in ordered:
        if r['status'].startswith('processed') and 'report' not in r:
            r['report'] = json.loads((OUT / f"{r['name']}.json").read_text())
    summary(ordered)


if __name__ == '__main__':
    main()
