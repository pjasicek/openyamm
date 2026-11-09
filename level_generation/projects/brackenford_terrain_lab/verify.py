"""Check copied content, terrain export integrity and faithful loads in all three modes."""
import configparser
import hashlib
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile

from PIL import Image

PROJECT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    manifest = json.loads((PROJECT / 'manifest.json').read_text())
    assets = PROJECT / 'playtest/assets_editor_dev'
    package = PROJECT / 'source/brackenford_greywatch_content.zip'
    assert digest(package) == manifest['package_sha256']
    with ZipFile(package) as archive:
        content = json.loads(archive.read('package_manifest.json'))
        for name, expected in content['files'].items():
            assert digest(assets / name) == expected, 'Changed frozen content: ' + name
    for record in manifest['tiles']:
        assert digest(assets / record['source']) == record['source_sha256'], record['name']
        with Image.open(assets / record['source']) as original:
            original_size = original.size
        for variant in ['native', 'smooth2x', 'ai2x']:
            path = PROJECT / 'tiles' / variant / (record['name'] + '.png')
            with Image.open(path) as image:
                assert image.size == (original_size if variant == 'native' else (256, 256)), str(path)
                assert image.mode == 'RGBA', str(path)
                assert not any(r > 240 and b > 240 and g < 10 and a > 0
                               for r, g, b, a in image.getdata()), 'Opaque magenta: ' + str(path)
            if variant != 'native':
                assert digest(path) == record[variant + '_sha256'], str(path)
        if record['name'] != 'grastyl':
            assert record['smooth2x_sha256'] == record['ai2x_sha256'], record['name']
    smooth = Image.open(PROJECT / 'tiles/smooth2x/grastyl.png')
    ai = Image.open(PROJECT / 'tiles/ai2x/grastyl.png')
    assert smooth.tobytes() != ai.tobytes(), 'AI mode must visibly differ from resampling'
    for y in range(256):
        for x in range(256):
            if min(x, y, 255-x, 255-y) <= 4:
                assert smooth.getpixel((x, y)) == ai.getpixel((x, y)), 'Changed grass boundary'
    report = {'frozen_package_files_verified': len(content['files']),
              'terrain_images_per_variant': len(manifest['tiles']), 'image_dimensions_verified': True,
              'opaque_magenta_pixels': 0, 'ai_grass_boundary_matches_control': True,
              'grid_and_content': 'identical native map and scene bytes', 'faithful_loads': {}}
    review = PROJECT / 'review'
    review.mkdir(exist_ok=True)
    for variant in ['native', 'smooth2x', 'ai2x']:
        directory = PROJECT / 'variants' / variant
        settings = configparser.ConfigParser()
        settings.read(directory / 'settings.ini')
        assert settings['video_quality']['terrain'] == ('x1' if variant == 'native' else 'x2')
        assert settings['video_quality']['texture'] == 'x1'
        mounted = Path(settings['assets']['root'])
        assert digest(mounted / 'worlds/mm8/maps/lg01.odm') == manifest['native_map_sha256']
        if variant != 'native':
            assert (mounted / 'worlds/mm8/terrain_x2').resolve() == PROJECT / 'tiles' / variant
        initial_save = directory / 'saves/Brackenford_Level25.oysav'
        reference_save = PROJECT / 'playtest/outdoor/saves/Brackenford_Level25.oysav'
        # Load the frozen initial save even if the user has subsequently played a mode.
        scenario = {'id': 'brackenford_terrain_lab_' + variant, 'world': 'mm8', 'mode': 'faithful',
                    'steps': [{'load_game': {'path': str(reference_save)}}, {'assert': {'map': 'lg01.odm'}}]}
        scenario_path = review / (variant + '_load.json')
        scenario_path.write_text(json.dumps(scenario, indent=2) + '\n')
        log = review / (variant + '_load.log')
        with log.open('w') as stream:
            subprocess.run([str(PROJECT / 'playtest/openyamm'), '--world', 'mm8',
                            '--headless-run-scenario', str(scenario_path), '--scenario-no-color'],
                           cwd=directory, stdout=stream, stderr=subprocess.STDOUT, check=True)
        report['faithful_loads'][variant] = {'passed': True, 'log': str(log.relative_to(PROJECT)),
                                           'initial_save_identical': digest(initial_save) == digest(reference_save)}
    (review / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    verify()
