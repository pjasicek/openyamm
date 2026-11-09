#!/usr/bin/env python3
"""Check the complete input -> picture -> movie -> staged clip chain (hold stage.lock shared)."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess

import yaml

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]
INPUTS = ROOT / 'level_generation/projects/hesper_stage'
STAGE = ROOT / 'output/hesper_stage/assets_editor_dev'
backdrops = json.loads((PROJECT / 'backdrops.json').read_text())
manifest = json.loads((PROJECT / 'generation_runs_house_backdrops.json').read_text())


def rows(path):
    with path.open(encoding='cp1252', newline='') as stream:
        data = [row for row in csv.reader(stream, delimiter='\t') if row and row[0].isdigit()]
    assert len({row[0] for row in data}) == len(data), path
    return {int(row[0]): row for row in data}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


tables = STAGE / 'engine/data_tables'
houses = rows(tables / 'house_data.txt')
movies = rows(tables / 'house_movies.txt')
animations = rows(tables / 'house_animations.txt')
vendors = rows(STAGE / 'worlds/hesper/data_tables/vendors.txt')
venues = {}
for path in [INPUTS / 'skills.yml', *sorted(INPUTS.glob('npcs*.yml'))]:
    data = yaml.safe_load(path.read_text())
    for kind in ('houses', 'vendors'):
        for venue in data.get(kind, []):
            assert venue['id'] not in venues
            venues[venue['id']] = venue
            if kind == 'houses':
                assert int(houses[venue['id']][4]) == venue['picture']
            else:
                assert vendors[venue['id']][22] == 'HouseVideo'
                assert vendors[venue['id']][-2:] == ['Disabled', 'Enabled']
assert len(venues) == 41
assert set(venues) == {house for backdrop in backdrops for house in backdrop['houses']}
assert {backdrop['picture'] for backdrop in backdrops} == set(range(9800, 9814))
assert len(manifest['jobs']) == 28
for name in ('house_movies.txt', 'house_animations.txt'):
    native = (ROOT / 'assets_dev/engine/data_tables' / name).read_bytes()
    assert (tables / name).read_bytes().startswith(native), name
for backdrop in backdrops:
    picture = backdrop['picture']
    source = ROOT / backdrop['source']
    staged = STAGE / 'worlds/hesper/videos/Houses' / source.name
    assert staged.is_file() and not staged.is_symlink()
    assert sha256(source) == sha256(staged)
    assert movies[picture][1] == source.stem
    for house in backdrop['houses']:
        assert venues[house]['picture'] == picture
        assert int(animations[house][1]) == picture
        assert animations[house][2] == venues[house]['name']
        assert animations[house][3:9] == ['', '', '', '0', '0', '0']
    candidates = [job for job in manifest['jobs'] if job['key'] == backdrop['key']]
    assert {job['candidate'] for job in candidates} == {1, 2}
    assert sum(job['selected'] for job in candidates) == 1
    for job in candidates:
        assert job['status'] == 'generated' and sha256(PROJECT / job['file']) == job['sha256']
        for filename, digest in job.get('exports', {}).items():
            assert sha256(PROJECT / filename) == digest
    streams = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams',
                                                 '-of', 'json', str(staged)]))['streams']
    assert len(streams) == 1 and streams[0]['codec_name'] == 'theora'
    assert (streams[0]['width'], streams[0]['height']) == (460, 344)
    subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(staged), '-f', 'null', '-'], check=True)
print('PASS: all 41 venues -> 14 pictures -> 14 world clips; native table rows preserved')
print('PASS: 28 retained candidates, 14 selected exports; hashes, 460x344 Theora and full silent decode')
