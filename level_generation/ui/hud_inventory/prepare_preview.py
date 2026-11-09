"""Build a disposable native-plus-reviewed-x2 asset root and a private inventory review save."""
import argparse
import configparser
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from finalize_classification import HERE, ROOT, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', action='store_true', help='Same fixture with restored preference disabled')
    parser.add_argument('--equipment-review', action='store_true',
                        help='Private five-member fixture for restored boots, capes and chainmail')
    parser.add_argument('--amulet-review', action='store_true',
                        help='Grant nine reviewed amulets plus native sun/turquoise fallbacks to the private fixture')
    parser.add_argument('--amulet-batch3-review', action='store_true',
                        help='Grant claw, plaque, Ruby Star, brass, jade and talisman plus two native fallbacks')
    parser.add_argument('--items', type=int, nargs='+', default=[],
                        help='Additional merged item IDs to grant only to the private inventory fixture')
    args = parser.parse_args()
    if args.amulet_review and args.amulet_batch3_review:
        parser.error('Choose one amulet review fixture')
    if any(item <= 0 for item in args.items):
        parser.error('Item IDs must be positive')
    spec = importlib.util.spec_from_file_location('hud_preview_queue', HERE / 'queue.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    queue = module.Queue()
    stage = Path(tempfile.mkdtemp(prefix='openyamm-hud-preview-'))
    assets = stage / 'assets'
    assets.mkdir()
    native = ROOT / 'assets_dev'
    # Only these directories are independent engine mounts. PhysicsFS does not traverse arbitrary
    # symlinks inside a package, so the small metadata trees need real private copies.
    mounted = {'textures', 'terrain', 'sprites', 'icons', 'audio', 'music', 'videos', 'maps', 'events',
               '_legacy', 'terrain_x2', 'terrain_x4'}
    def share_metadata(source, destination):
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)
    packages = [native / 'engine', *sorted((native / 'worlds').iterdir())]
    for child in native.iterdir():
        if child.name not in {'engine', 'worlds'}:
            share_metadata(child, assets / child.name)
    for package in packages:
        destination = assets / package.relative_to(native)
        if not package.is_dir():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(package, destination)
            continue
        destination.mkdir(parents=True, exist_ok=True)
        for child in package.iterdir():
            # Preview only this queue's accepted replacements, with native fallback for every missing target.
            if child.name not in {'icons_x2', 'ui_x2'}:
                if child.is_dir() and child.name in mounted:
                    (destination / child.name).symlink_to(child.resolve(), target_is_directory=True)
                else:
                    share_metadata(child, destination / child.name)
    if queue.layout:
        destination = assets / Path(queue.layout['native_layout']).relative_to('assets_dev')
        shutil.copy2(queue.layout['preview_layout'], destination)
    installed = []
    for target, record in queue.state.get('staged_targets', {}).items():
        assert all(queue.accepted(c) and queue.state['cells'][c]['sha256'] == sha
                   for c, sha in record['cells'].items()), f'Stale accepted cells: {target}'
        source = Path(record['artifact'])
        assert digest(source) == record['sha256'], f'Stale staged output: {target}'
        assert all(Path(p).is_file() and digest(Path(p)) == sha for p, sha in record['evidence_hashes'].items())
        relative = Path(record['runtime_output_path']).relative_to('assets_dev')
        destination = assets / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        installed.append(dict(target=target, path=str(relative), sha256=record['sha256']))
    assert installed, 'No reviewed staged output to preview'
    settings = configparser.ConfigParser(interpolation=None)
    settings.read(ROOT / 'settings.ini')
    for section in ['assets', 'startup', 'video_quality', 'video', 'audio', 'logging']:
        if not settings.has_section(section):
            settings.add_section(section)
    settings['assets']['root'] = str(assets)
    settings['startup'].update(start_in_main_menu='false', save_file='')
    settings['video_quality'].update(prefer_restored_icons='false' if args.original else 'true', icons='x1', ui='x2')
    settings['video'].update(resolution='1600x1200', fullscreen='false', vsync='false')
    settings['audio'].update(sound_volume='0', music_volume='0', voice_volume='0')
    settings['logging'].update(gameplay_trace_file='logs/gameplay_trace.log', combat_trace_file='logs/combat_trace.log')
    fixture = json.loads((ROOT / 'level_generation/projects/brackenford_greywatch/source/baseline_party.json').read_text())
    for member in fixture['members']:
        if 'boots' in member['equipment']:
            member['equipment']['boots'] = 1717
    if args.equipment_review:
        # Character-data row6 is a female cleric (doll type1), row23 a troll (doll type3).
        fixture['members'][1]['portrait_id'] = 5
        fixture['members'][3].update(name='Equipment Troll', portrait_id=22, race_id=4, **{'class': 'Troll'})
        for skill in fixture['members'][3]['skills']:
            if skill['name'] in {'Bow', 'Perception'}:
                skill['mastery'] = 1
        for index, (member, boots, cloak) in enumerate(zip(
                fixture['members'], [1718, 1719, 1720, 1721, 1718], [1707, 1709, 1711, 2030, 2045])):
            member['equipment'].update(boots=boots, cloak=cloak)
            if index < 4:
                member['equipment']['armor'] = 1673
                if not any(skill['name'] == 'Chain' for skill in member['skills']):
                    member['skills'].append(dict(name='Chain', level=4, mastery=2))
    # The fifth fixture member already knows Air Magic; expose the whole page for mixed-icon layout review.
    mage = fixture['members'][4]
    assert any(skill['name'] == 'Air Magic' for skill in mage['skills'])
    mage['spells'] = sorted(set(mage['spells']) | set(range(12, 23)))
    (stage / 'party.json').write_text(json.dumps(fixture, indent=2) + '\n')
    amulet_items = [2034, 2049, 2199, 932, 933, 934, 935, 1341, 1733, 936, 1732] if args.amulet_review else []
    if args.amulet_batch3_review:
        amulet_items = [1734, 1735, 1736, 147, 148, 149, 936, 1732]
    scenario = dict(id='hud_artwork_preview', world='mm6', mode='hybrid', steps=[
        dict(new_game_flow=dict(start_map='oute3.odm', party=fixture)),
        dict(setup_shortcut=dict(kind='grant_item', item_id=1403)),
        *[dict(setup_shortcut=dict(kind='grant_item', item_id=item)) for item in amulet_items],
        *[dict(setup_shortcut=dict(kind='grant_item', item_id=item)) for item in args.items],
        dict(save_game='preview')])
    (stage / 'prepare.yml').write_text(json.dumps(scenario, indent=2) + '\n')
    with (stage / 'settings.ini').open('w') as stream:
        settings.write(stream)
    (stage / 'tmp').mkdir()
    binary = ROOT / 'build/game/openyamm'
    with (stage / 'prepare.log').open('w') as stream:
        subprocess.run([str(binary), '--world', 'mm6', '--headless-run-scenario', str(stage / 'prepare.yml'),
                        '--scenario-no-color'], cwd=stage, env=dict(os.environ, TMPDIR=str(stage / 'tmp')),
                       stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=180)
    save = stage / 'tmp/openyamm_scenario_saves/hud_artwork_preview/preview.oysav'
    assert save.is_file(), f'No private preview save; inspect {stage / "prepare.log"}'
    settings['startup']['save_file'] = str(save)
    with (stage / 'settings.ini').open('w') as stream:
        settings.write(stream)
    metadata = dict(stage=str(stage), assets=str(assets), save=str(save), original=args.original,
        equipment_review=args.equipment_review, amulet_review=args.amulet_review,
        amulet_batch3_review=args.amulet_batch3_review,
        amulet_items=amulet_items, additional_items=args.items, fixture_party=fixture,
        layout_revision=queue.state.get('layout_revision'),
        staged_targets=installed, binary_sha256=digest(binary), source_settings_sha256=digest(ROOT / 'settings.ini'),
        fixture=('Isolated equipment review: four boot styles, five cape identities and chainmail on '
                 'the first four members. ' if args.equipment_review else
                 'Isolated review setup: native party with Old Leather Boots. ') + 'Granted Lich Jar and '
                'all Air spells on the fifth member. '
                'Not a gameplay progression test; only the targets listed in staged_targets are restored.')
    if args.amulet_review:
        metadata['fixture'] += ' Added nine reviewed amulets and two native fallbacks for inventory/picking review.'
    if args.amulet_batch3_review:
        metadata['fixture'] += ' Added six batch3 amulets and native sun/turquoise fallbacks for inventory review.'
    if args.items:
        metadata['fixture'] += ' Additional private inventory item IDs: ' + ', '.join(map(str, args.items)) + '.'
    (stage / 'preview.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
