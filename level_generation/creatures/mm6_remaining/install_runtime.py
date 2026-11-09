"""Export accepted MM6 actors or an explicitly requested redo playtest.

Original BMPs, gameplay tables, native flags/timing/scales, and custom actor groups stay intact.
Nonlinear palette data is exported as small float32 textures; atlas pages remain shared.
"""
import argparse
import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ENGINE = REPO / 'assets_dev/engine'
SOURCES = REPO / 'assets_source/engine/sprites_new'
STAGE = HERE / 'runtime'
REDO_STAGE = HERE / 'runtime_redo'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def normalize_palette_model(runtime, model):
    """Convert authored inline tables to their explicit runtime lookup schema."""
    variants = [v for v in runtime['variants'].values() if not v.get('exact_base_bypass')]
    if model == 'masked_luminance_rgb_v1' and variants:
        shapes = {np.asarray(v.get('luminance_vector', [])).shape for v in variants}
        if shapes == {(256, 3)}:
            model = 'masked_luminance_lut_v1'
            for variant in variants:
                variant['luminance_lut'] = variant.pop('luminance_vector')
        elif shapes == {(33, 33, 33, 3)}:
            model = 'masked_native_rgb_displacement_lut_v1'
            for variant in variants:
                variant['rgb_displacement_lut'] = variant.pop('luminance_vector')
        else:
            assert shapes == {(3,)}, ('Mixed/invalid inline palette shapes', shapes)
    if model == 'multi_mask_luminance_rgb_v1':
        nonlinear = [v for v in runtime['variants'].values() if not v.get('exact_base_bypass')
                     and len(v.get('region_luminance_vectors', [[]])[0]) == 256]
        if nonlinear:
            assert len(nonlinear) == sum(not v.get('exact_base_bypass') for v in runtime['variants'].values())
            model = 'multi_mask_luminance_lut_v1'
            for variant in nonlinear:
                variant['region_luminance_luts'] = variant.pop('region_luminance_vectors')
    return model


def export_palette_lookups(runtime, target):
    """Write the shader's float lookup textures, preserving authored values."""
    model = runtime['recolor_model']
    files = []
    for palette, variant in runtime['variants'].items():
        if variant.get('exact_base_bypass'):
            continue
        key = {'masked_luminance_lut_v1': 'luminance_lut',
               'multi_mask_luminance_lut_v1': 'region_luminance_luts',
               'masked_native_rgb_displacement_lut_v1': 'rgb_displacement_lut'}.get(model)
        if key is None:
            continue
        values = np.array(variant.pop(key), dtype='<f4')
        shape = {'luminance_lut': (256, 3), 'region_luminance_luts': (4, 256, 3),
                 'rgb_displacement_lut': (33, 33, 33, 3)}[key]
        assert values.shape == shape and np.isfinite(values).all() and np.abs(values).max() <= 64
        size = [1089, 33] if key == 'rgb_displacement_lut' else [256, 4 if key == 'region_luminance_luts' else 1]
        rgba = np.zeros((size[1], size[0], 4), dtype='<f4')
        rgba[:, :, :3] = values.reshape(size[1], size[0], 3)
        relative = f'atlas/palette_{palette}.rgba32f'
        (target / relative).write_bytes(rgba.tobytes())
        variant.update(lookup=relative, lookup_size=size)
        files.append(relative)
    return files


def export_family(row, stage=STAGE):
    source = REPO / row['package']
    root = source.parent
    m = json.loads(source.read_text())
    validation = json.loads((root / 'validation.json').read_text())
    assert row['status'] == 'validated' and not [k for k, v in validation.items() if v is False], root
    family_root = root.parent if root.name == 'redo_2x' else root
    package = 'mm6_gob' if family_root.name == 'direct_complete' else family_root.name
    target = stage / package
    (target / 'atlas').mkdir(parents=True, exist_ok=True)
    model = m.get('recolor_model', m.get('recolor', {}).get('model'))
    if model == 'exact_base_bypass_v1':
        assert all(v.get('exact_base_bypass') for v in m['variants'].values())
        model = 'masked_luminance_rgb_v1'
    supported = {'masked_luminance_rgb_v1', 'masked_regions_luminance_rgb_v1', 'multi_mask_luminance_rgb_v1',
                 'masked_luminance_lut_v1', 'multi_mask_luminance_lut_v1', 'masked_native_rgb_displacement_lut_v1'}
    assert model in supported, (package, model)
    runtime = {k: copy.deepcopy(m[k]) for k in ('creature', 'pixels_per_logical_pixel', 'logical_canvas',
                                               'logical_pivot', 'variants')}
    model = normalize_palette_model(runtime, model)
    runtime.update(schema_version=1, recolor_model=model)
    sources = json.loads((root / 'sources.json').read_text())['sources']
    for source_frame in sources.values():
        if 'fixed_palette' in source_frame:
            palette = str(source_frame['fixed_palette'])
            assert palette not in m['variants']
            runtime['variants'][palette] = dict(exact_base_bypass=True, name='Native fixed-palette shared appearance')
    # Native actor draw paths bottom-anchor even the special Cactus actor's Center-flagged groups.
    # Preserve that current native actor behavior; the offline centered viewer remains unchanged.
    runtime['logical_pivot'][1] = m['logical_canvas'][1]
    runtime['pages'] = [{k: page[k] for k in ('base', 'mask', 'size')} for page in m['pages']]
    runtime['frames'] = {name.lower(): {k: f[k] for k in ('page', 'atlas_xywh', 'crop_origin_px')}
                         for name, f in m['frames'].items()}
    files = []
    for page in runtime['pages']:
        for key in ('base', 'mask'):
            path = page[key]
            assert Path(path).parent == Path('atlas') and path.endswith('.png')
            shutil.copy2(root / path, target / path)
            files.append(path)
    files.extend(export_palette_lookups(runtime, target))
    write(target / 'manifest.json', runtime)
    files.append('manifest.json')
    return package, runtime, dict(family=row['label'], descriptor_id=row['descriptor_id'], source=str(source.relative_to(REPO)),
        source_manifest_sha256=digest(source), package=package, frames=len(runtime['frames']),
        palettes=sorted(map(int, runtime['variants'])), model=model,
        anchor_export='native actor bottom anchor' if m.get('anchor') == 'center' else 'native bottom anchor',
        files={f: dict(sha256=digest(target / f), bytes=(target / f).stat().st_size) for f in files})


def wire(manifests):
    inventory = json.loads((HERE.parent / 'remaining_inventory.json').read_text())
    descriptor_path = ENGINE / 'data_tables/monster_descriptors.txt'
    descriptors = {int(r[0]): r for r in csv.reader(io.StringIO(descriptor_path.read_text(encoding='cp1252')),
                                                  delimiter='\t') if r and r[0].isdigit()}
    groups = {}
    for family in inventory['families']:
        if family['world'] != 'mm6':
            continue
        key = family['descriptors'][0]['id']
        if key not in manifests:
            continue
        package, manifest = manifests[key]
        for descriptor in family['descriptors']:
            for name in descriptors[descriptor['id']][11:19]:
                name = name.lower()
                if name in ('null', '0', ''):
                    continue
                if name in groups and groups[name] != package:
                    # Both native demon families deliberately share the same ash corpse group.
                    assert name == 'm498x' and {groups[name], package} == {'mm6_wdm', 'mm6_dmn'}, name
                    continue
                groups[name] = package
    by_package = {package: m for package, m in manifests.values()}
    edits = []
    found = set()
    bindings = {package: 0 for package in by_package}
    paths = [ENGINE / 'rendering/sprite_frame_data_common.yml']
    paths += sorted((ENGINE / 'rendering/sprite_frames').rglob('*.yml'))
    for path in paths:
        original = path.read_text()
        parsed = yaml.load(original, Loader=yaml.CSafeLoader)
        desired = copy.deepcopy(parsed)
        changes = []
        for group in desired.get('sprites', []):
            name = group['sprite_name'].lower()
            if name not in groups:
                continue
            assert name not in found, 'Duplicate active group: ' + name
            found.add(name)
            package = groups[name]
            m = by_package[package]
            for frame in group['frames']:
                old = frame['texture_name']
                texture = old.lower()
                if texture.startswith('atlas:'):
                    prefix = 'atlas:' + package + '/'
                    assert texture.startswith(prefix), (name, texture)
                    texture = texture[len(prefix):]
                if texture == 'null':
                    continue
                names = [texture] if 'Image1' in frame.get('flags', []) else [texture + str(i) for i in range(5)]
                assert all(n in m['frames'] for n in names), (name, names)
                assert str(frame['palette_id']) in m['variants'], (name, frame.get('palette_id'))
                frame['texture_name'] = 'atlas:' + package + '/' + texture
                changes.append((old, frame['texture_name']))
                bindings[package] += 1
        if not changes:
            continue
        # Replace only the selected frame entries, leaving unrelated groups and exact formatting intact.
        selected = {g['sprite_name'].lower() for g in parsed['sprites'] if g['sprite_name'].lower() in groups}
        current = None
        index = 0
        lines = []
        for line in original.splitlines(keepends=True):
            match = re.search(r'sprite_name:\s*["\']?([^"\'\s]+)', line)
            if match:
                current = match[1].lower()
            match = re.search(r'(texture_name:\s*)(["\']?)([^"\'\s]+)(["\']?)', line)
            if match and current in selected and match[3].lower() != 'null':
                old, new = changes[index]
                assert match[3] == old, (path, match[3], old)
                line = line[:match.start(3)] + new + line[match.end(3):]
                index += 1
            lines.append(line)
        result = ''.join(lines)
        assert index == len(changes)
        assert yaml.load(result, Loader=yaml.CSafeLoader) == desired, 'Non-texture table changes'
        edits.append((path, original, result))
    assert found == set(groups), sorted(set(groups) - found)
    assert all(bindings.values()), bindings
    return edits, bindings, len(found)


def verify_files(root, files):
    return all((root / name).is_file() and digest(root / name) == info['sha256']
               for name, info in files.items())


def install_accepted_redos(packages, prepare_only, playtest=False):
    redo_ledger = json.loads((HERE / 'redo_2x/progress.json').read_text())
    original_ledger = json.loads((HERE / 'progress.json').read_text())
    installation = json.loads((HERE / 'installation.json').read_text())
    original_by_label = {row['label']: row for row in original_ledger['families']}
    installed_by_package = {row['package']: row for row in installation['packages']}
    installed_by_descriptor = {row['descriptor_id']: row for row in installation['packages']}
    selected = {}
    manifests = {}
    records = {}
    for redo in redo_ledger['families']:
        project = REPO / redo['project']
        original = original_by_label[redo['family']]
        package = installed_by_descriptor[original['descriptor_id']]['package']
        if package not in packages:
            continue
        assert package not in selected, package
        source = project / 'redo_2x'
        acceptance_path = source / 'review/acceptance.json'
        acceptance = json.loads(acceptance_path.read_text())
        validation = json.loads((source / 'validation.json').read_text())
        assert acceptance['status'] == 'accepted' and validation['visual_review_complete'] is True, package
        if playtest:
            assert acceptance['generated_minimum'] >= 2 and not redo['retained_detail_exception_names'], package
            if acceptance['generated_minimum'] == 2:
                retained = validation.get('retained_adequate_frames', [])
                registration = json.loads((source / 'registration.json').read_text())
                assert retained, package
                for name in retained:
                    checkpoint = registration[name].get('source_checkpoint')
                    assert checkpoint and digest(REPO / checkpoint['path']) == checkpoint['sha256'], (package, name)
                assert all(min(frame['effective_sampling_xy']) > 2 for frame in registration.values()
                           if frame.get('effective_sampling_xy') and not frame.get('retained_from')), package
        else:
            assert acceptance['generated_minimum'] > 2 and not redo['retained_detail_exception_names'], package
        assert all((source / name).is_file() and digest(source / name) == expected
                   for name, expected in acceptance['artifact_hashes'].items()), package + ': acceptance changed'
        row = dict(original, package=str((source / 'manifest.json').relative_to(REPO)), status='validated')
        exported, manifest, record = export_family(row, REDO_STAGE)
        assert exported == package
        assert package in installed_by_package
        record['acceptance_sha256'] = digest(acceptance_path)
        if playtest:
            record['installation_mode'] = 'user_playtest_pending_animation_review'
        selected[package] = record
        records[package] = (installed_by_package[package], record)
        manifests[row['descriptor_id']] = package, manifest
    assert set(selected) == set(packages), sorted(set(packages) - set(selected))
    edits, bindings, groups = wire(manifests)
    assert all(before == after for _, before, after in edits), 'Redo installation must preserve active frame tables'
    for table in installation['tables']:
        assert digest(REPO / table['path']) == table['after_sha256'], table['path']
    for package, (previous, replacement) in records.items():
        target = SOURCES / package
        assert not target.is_symlink(), package
        assert verify_files(target, previous['files']) or verify_files(target, replacement['files']), (
            package + ': installed package differs from both the recorded and accepted version')
        assert verify_files(REDO_STAGE / package, replacement['files']), package
    summary = dict(families=len(selected), groups=groups, frame_bindings=bindings,
                   installation_mode='playtest' if playtest else 'accepted',
                   packages=sorted(selected), shipping_bytes=sum(sum(info['bytes'] for info in row['files'].values())
                   for row in selected.values()))
    if prepare_only:
        print(json.dumps(dict(summary, installed=False)))
        return
    backup_root = HERE / 'installation_backups/redo_2x_before_install'
    for package, (previous, replacement) in records.items():
        target = SOURCES / package
        if verify_files(target, replacement['files']):
            continue
        pending = target.parent / f'.{package}.redo_pending'
        assert not pending.exists(), 'Existing pending package needs review: ' + str(pending)
        pending.mkdir(parents=True)
        for relative, info in replacement['files'].items():
            dest = pending / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REDO_STAGE / package / relative, dest)
            assert digest(dest) == info['sha256'], dest
        backup = backup_root / package
        version = 2
        while backup.exists():
            backup = backup_root / f'{package}_v{version}'
            version += 1
        backup.parent.mkdir(parents=True, exist_ok=True)
        target.rename(backup)
        try:
            pending.rename(target)
        except OSError:
            backup.rename(target)
            raise
    subprocess.run([sys.executable, str(REPO / 'tools/cook_sprite_atlases.py'),
                    '--profile', 'desktop'], cwd=REPO, check=True)
    updated = {row['package']: row for row in installation['packages']}
    updated.update(selected)
    installation['packages'] = [updated[row['package']] for row in installation['packages']]
    installation['shipping_bytes'] = sum(info['bytes'] for row in installation['packages']
                                         for info in row['files'].values())
    installation['frames'] = sum(row['frames'] for row in installation['packages'])
    write(HERE / 'installation.json', installation)
    print(json.dumps(dict(summary, installed=True)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--redo-family', action='append', default=[], help='Install one accepted MM6 redo project')
    parser.add_argument('--playtest-redo-family', action='append', default=[],
                        help='Install a reviewed MM6 redo for in-game testing, including retained adequate 2x frames')
    args = parser.parse_args()
    assert not (args.redo_family and args.playtest_redo_family), 'Choose accepted or playtest redo installation'
    if args.redo_family or args.playtest_redo_family:
        install_accepted_redos(args.redo_family or args.playtest_redo_family, args.prepare_only,
                               playtest=bool(args.playtest_redo_family))
        return
    ledger = json.loads((HERE / 'progress.json').read_text())
    assert len(ledger['families']) == 60
    manifests = {}
    packages = []
    for row in ledger['families']:
        package, manifest, record = export_family(row)
        manifests[row['descriptor_id']] = package, manifest
        packages.append(record)
    edits, bindings, group_count = wire(manifests)
    report = dict(families=len(packages), frames=sum(p['frames'] for p in packages),
                  groups=group_count, frame_bindings=bindings, packages=packages, installed=False,
                  shipping_bytes=sum(f['bytes'] for p in packages for f in p['files'].values()),
                  tables=[dict(path=str(p.relative_to(REPO)), before_sha256=hashlib.sha256(old.encode()).hexdigest(),
                               after_sha256=hashlib.sha256(new.encode()).hexdigest()) for p, old, new in edits])
    write(HERE / 'runtime_prepared.json', report)
    if args.prepare_only:
        print(json.dumps({k: report[k] for k in ('families', 'frames', 'groups', 'shipping_bytes', 'installed')}))
        return
    # Installation was requested. Copy validated packages before publishing any native table binding.
    for record in packages:
        target = SOURCES / record['package']
        assert not target.is_symlink()
        for relative, info in record['files'].items():
            dest = target / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(STAGE / record['package'] / relative, dest)
            assert digest(dest) == info['sha256']
    subprocess.run([sys.executable, str(REPO / 'tools/cook_sprite_atlases.py'),
                    '--profile', 'desktop'], cwd=REPO, check=True)
    for path, original, result in edits:
        assert path.read_text() == original, 'Table changed during export: ' + str(path)
        backup = HERE / 'installation_backups' / path.relative_to(ENGINE)
        if not backup.exists():
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_text(original)
        pending = path.with_suffix(path.suffix + '.mm6_pending')
        pending.write_text(result)
        pending.replace(path)
    report['installed'] = True
    write(HERE / 'installation.json', report)
    print(json.dumps({k: report[k] for k in ('families', 'frames', 'groups', 'shipping_bytes', 'installed')}))


if __name__ == '__main__':
    main()
