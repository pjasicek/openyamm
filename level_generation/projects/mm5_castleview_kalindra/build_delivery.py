"""Freeze a reviewed native world, composed registries and exploration save into a portable delivery."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import zipfile

from install_delivery import digest

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
TABLES = ['map_stats.txt', 'map_navigation.txt', 'terrain_tile_data.txt']


def build(output):
    build = json.loads((PROJECT/'review/native/build.json').read_text())
    play = json.loads((PROJECT/'review/playtest/latest.json').read_text())
    native_hash = build['nativeSha256']
    assert play['nativeSha256'] == native_hash, 'Prepare a fresh starting save after the completed native build.'
    assert play['mapPresentation']['nativeSha256'] == native_hash, 'Bake, inspect and stage the current minimap.'
    assert build['actors'] == build['spawns'] == 0
    assert not build['remainingAssemblies']
    runtime = PROJECT/'implementation/runtime/worlds/mm5'
    assert digest(runtime/'maps/mm5_sw.odm') == native_hash
    assert digest(Path(play['binary'])) == play['binarySha256']
    assert digest(Path(play['startSave'])) == play['saveSha256']
    for name, expected in build['sourceObjSha256'].items():
        assert digest(PROJECT/'implementation/source/models'/name) == expected, name
    assert not output.exists(), 'Use a new delivery directory to preserve earlier packages.'
    output.mkdir(parents=True)
    bundle = output/'mm5_castleview'
    shutil.copytree(runtime, bundle/'worlds/mm5')
    (bundle/'bin').mkdir()
    shutil.copy2(play['binary'], bundle/'bin/openyamm')
    shutil.copy2(play['startSave'], bundle/'castleview_start.oysav')
    shutil.copy2(PROJECT/'install_delivery.py', bundle/'install_delivery.py')
    shutil.copy2(PROJECT/'DELIVERY.md', bundle/'README.md')
    (bundle/'registries').mkdir()
    base = ROOT/'assets_dev'
    stage = Path(build['stage'])/'assets_dev'
    dependencies = {}
    registrations = {}
    for name in TABLES:
        relative = Path('engine/data_tables')/name
        with (base/relative).open(newline='') as stream:
            before = list(csv.reader(stream, delimiter='\t'))
        with (stage/relative).open(newline='') as stream:
            after = list(csv.reader(stream, delimiter='\t'))
        assert after[:len(before)] == before, ('Existing registry rows changed', name)
        assert len(after) > len(before), name
        registrations[name] = {'baseRows': len(before), 'appendedRows': after[len(before):]}
        shutil.copy2(stage/relative, bundle/'registries'/name)
    # Pin gameplay registries and inherited scripts used by the tested composed base, plus referenced donor artwork.
    for folder in ['engine/data_tables', 'engine/events']:
        for path in sorted((base/folder).rglob('*')):
            if path.is_file():
                dependencies[str(path.relative_to(base))] = digest(path)
    for world in ['mm7', 'mm8']:
        relative = 'worlds/'+world+'/world.yml'
        dependencies[relative] = digest(base/relative)
    spec = json.loads((PROJECT/'implementation/architecture.json').read_text())
    scenery = json.loads((PROJECT/'implementation/scenery.json').read_text())
    art = [row['path'] for row in spec['materials'].values()]
    art += [row['assetSource'] for row in scenery['records']]
    for name in sorted(set(art)):
        if name.startswith('assets_dev/'):
            relative = name[len('assets_dev/'):]
            dependencies[relative] = digest(base/relative)
    (bundle/'registrations.json').write_text(json.dumps(registrations, indent=2)+'\n')
    manifest = {'project': 'mm5_castleview_kalindra', 'world': 'mm5', 'map': 'mm5_sw.odm',
                'nativeSha256': native_hash, 'binarySha256': play['binarySha256'],
                'startSaveSha256': play['saveSha256'], 'counts': {
                    key: build[key] for key in ['assemblies', 'bmodels', 'props', 'entities', 'nativeEvents',
                                                'actors', 'spawns']},
                'baseDependencies': dependencies,
                'basePolicy': 'Explicit isolated composed engine registry; donor worlds/art remain mounted from base.',
                'platform': 'Reviewed Linux executable; requires the same system runtime libraries as OpenYAMM.',
                'files': {str(path.relative_to(bundle)): digest(path)
                          for path in sorted(bundle.rglob('*')) if path.is_file()}}
    (bundle/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    archive = output/'mm5_castleview_runtime.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as stream:
        for path in sorted(bundle.rglob('*')):
            if path.is_file():
                stream.write(path, path.relative_to(output))
    report = {'status': 'Delivery candidate; isolated installation/runtime review required.',
              'directory': str(bundle), 'archive': str(archive), 'archiveSha256': digest(archive),
              'nativeSha256': native_hash, 'manifestSha256': digest(bundle/'manifest.json'),
              'fileCount': len(manifest['files']), 'baseDependencyCount': len(dependencies)}
    (output/'build.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    build(parser.parse_args().output.resolve())
