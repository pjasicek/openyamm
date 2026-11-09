"""Restage the accepted MM5 map against the current development build, preserving private saves/settings."""
import configparser
import csv
from datetime import datetime
import json
from pathlib import Path
import shlex
import shutil
import tempfile

from install_delivery import compose_base, digest

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]


def stage(project=PROJECT, root=ROOT):
    bundle = project/'delivery/release_v2/mm5_castleview'
    base = root/'assets_dev'
    binary = root/'build/game/openyamm'
    installation = project/'local_playtest'
    assert binary.is_file(), 'Build the development executable: cmake --build build --target openyamm -j25'
    manifest = json.loads((bundle/'manifest.json').read_text())
    assert manifest['project'] == 'mm5_castleview_kalindra'
    for name, expected in manifest['files'].items():
        assert digest(bundle/name) == expected, ('Delivery file changed', name)
    if installation.exists():
        assert json.loads((installation/'installation.json').read_text())['project'] == manifest['project']
    registrations = json.loads((bundle/'registrations.json').read_text())
    with tempfile.TemporaryDirectory(prefix='.mm5-stage-', dir=project) as temporary:
        candidate = Path(temporary)/'installation'
        assets = candidate/'assets_dev'
        compose_base(base, assets)
        for name, registration in registrations.items():
            path = assets/'engine/data_tables'/name
            with path.open(newline='') as source:
                rows = list(csv.reader(source, delimiter='\t'))
            additions = registration['appendedRows']
            keys = {row[0] for row in rows[1:] if row}
            assert not keys.intersection(row[0] for row in additions), ('MM5 registry ID collision', name)
            if name == 'terrain_tile_data.txt':
                assert len(rows) == registration['baseRows'], 'Terrain indices changed; rebuild the native MM5 map'
            with path.open('w', newline='') as output:
                csv.writer(output, delimiter='\t', lineterminator='\n').writerows(rows + additions)
        shutil.copytree(bundle/'worlds/mm5', assets/'worlds/mm5')
        # This MM5 corner is absent from the merged native terrain registry. Import its current donor explicitly.
        corner = base/'worlds/mm8/textures_x2/rcsw.png'
        shutil.copy2(corner, assets/'worlds/mm5/textures/rcsw.png')
        (candidate/'bin').mkdir()
        (candidate/'bin/openyamm').symlink_to(binary.resolve())
        work = candidate/'playtest'
        settings = configparser.ConfigParser(interpolation=None)
        if installation.exists():
            shutil.copytree(installation/'playtest', work)
            settings.read(work/'settings.ini')
        else:
            (work/'saves').mkdir(parents=True)
            shutil.copy2(bundle/'castleview_start.oysav', work/'saves/castleview_start.oysav')
            settings.read(root/'settings.ini')
            for section in ['startup', 'debug']:
                if not settings.has_section(section):
                    settings.add_section(section)
            settings['startup'].update(start_in_main_menu='true', save_file='')
            settings['debug'].update(start_world='mm5', start_map_file='mm5_sw.odm')
        if not settings.has_section('assets'):
            settings.add_section('assets')
        settings['assets']['root'] = str(installation/'assets_dev')
        with (work/'settings.ini').open('w') as output:
            settings.write(output, space_around_delimiters=False)
        launcher = candidate/'play-mm5.sh'
        launcher.write_text('#!/bin/sh\nset -eu\ncd '+shlex.quote(str(installation/'playtest'))+'\nexec '+
                            shlex.quote(str(installation/'bin/openyamm'))+' --world mm5 "$@"\n')
        launcher.chmod(0o755)
        report = {'project': manifest['project'], 'bundle': str(bundle), 'base': str(base),
                  'nativeSha256': manifest['nativeSha256'], 'binary': str(binary), 'binarySha256': digest(binary),
                  'manifestSha256': digest(bundle/'manifest.json'), 'launcher': str(installation/'play-mm5.sh'),
                  'terrainImport': {'source': str(corner), 'destination': 'worlds/mm5/textures/rcsw.png',
                                    'sha256': digest(corner)},
                  'baseModified': False, 'world': 'mm5', 'map': 'mm5_sw.odm', 'mode': 'current development build'}
        if installation.exists():
            backup = project/('local_playtest_previous_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
            report['previousInstallation'] = str(backup)
        (candidate/'installation.json').write_text(json.dumps(report, indent=2)+'\n')
        if installation.exists():
            installation.rename(backup)
        candidate.rename(installation)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    stage()
