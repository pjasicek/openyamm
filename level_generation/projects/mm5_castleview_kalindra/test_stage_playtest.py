"""Run with python3 test_stage_playtest.py; verify registry rebasing and preservation during refresh."""
import configparser
import csv
import json
from pathlib import Path
import tempfile

from install_delivery import digest
from stage_playtest import stage


with tempfile.TemporaryDirectory(prefix='mm5-restage-test-') as temporary:
    root = Path(temporary)
    project = root/'project'
    bundle = project/'delivery/release_v2/mm5_castleview'
    (bundle/'worlds/mm5/maps').mkdir(parents=True)
    (bundle/'worlds/mm5/textures').mkdir()
    (bundle/'worlds/mm5/maps/mm5_sw.odm').write_bytes(b'accepted map')
    (bundle/'castleview_start.oysav').write_bytes(b'starting save')
    tables = root/'assets_dev/engine/data_tables'
    tables.mkdir(parents=True)
    table = tables/'terrain_tile_data.txt'
    table.write_text('ID\tName\n0\tbase\n')
    (root/'assets_dev/engine/icons_x2').mkdir()
    corner = root/'assets_dev/worlds/mm8/textures_x2/rcsw.png'
    corner.parent.mkdir(parents=True)
    corner.write_bytes(b'current donor corner')
    effect = root/'assets_dev/engine/effects/authored/sprites/arcane.yml'
    effect.parent.mkdir(parents=True)
    effect.write_text('effect descriptor')
    (root/'build/game').mkdir(parents=True)
    (root/'build/game/openyamm').write_bytes(b'current executable')
    (root/'settings.ini').write_text('[audio]\nmusic_volume=2\n')
    registrations = {'terrain_tile_data.txt': {'baseRows': 2, 'appendedRows': [['1', 'mm5']]}}
    (bundle/'registrations.json').write_text(json.dumps(registrations))
    files = {str(f.relative_to(bundle)): digest(f) for f in bundle.rglob('*') if f.is_file()}
    (bundle/'manifest.json').write_text(json.dumps({'project': 'mm5_castleview_kalindra',
                                                  'nativeSha256': digest(bundle/'worlds/mm5/maps/mm5_sw.odm'),
                                                  'files': files}))
    stage(project, root)
    installation = project/'local_playtest'
    saved = installation/'playtest/saves/personal.oysav'
    saved.write_bytes(b'personal progress')
    settings = installation/'playtest/settings.ini'
    settings.write_text(settings.read_text().replace('music_volume=2', 'music_volume=7'))
    table.write_text('ID\tName\n0\tupdated base\n')
    stage(project, root)
    assert saved.read_bytes() == b'personal progress'
    assert 'music_volume=7' in settings.read_text()
    assert table.read_text() == 'ID\tName\n0\tupdated base\n'
    with (installation/'assets_dev/engine/data_tables/terrain_tile_data.txt').open() as source:
        assert list(csv.reader(source, delimiter='\t')) == [['ID', 'Name'], ['0', 'updated base'], ['1', 'mm5']]
    assert (installation/'assets_dev/engine/icons_x2').is_dir()
    assert not (installation/'assets_dev/engine/icons_x2').is_symlink()
    staged_effect = installation/'assets_dev/engine/effects/authored/sprites/arcane.yml'
    assert staged_effect.read_text() == 'effect descriptor'
    assert not staged_effect.parent.is_symlink()
    assert (installation/'assets_dev/worlds/mm5/textures/rcsw.png').read_bytes() == corner.read_bytes()
    assert (installation/'bin/openyamm').resolve() == root/'build/game/openyamm'
    preferences = configparser.ConfigParser()
    preferences.read(settings)
    assert preferences['assets']['root'] == str(installation/'assets_dev')
    table.write_text('ID\tName\n0\tbase\n1\tcollision\n')
    try:
        stage(project, root)
    except AssertionError as error:
        assert 'collision' in str(error)
    else:
        raise AssertionError('An occupied terrain ID must reject restaging')
    assert saved.read_bytes() == b'personal progress'
print('MM5 restaging checks passed.')
