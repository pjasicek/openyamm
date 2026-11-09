"""Stage the combined terrain over the current enhanced content for isolated native review."""
import configparser
import json
import shutil
from pathlib import Path

from build import P, WATER, sha


def main():
    enhanced = Path('/tmp/openyamm-sorpigal-peasants-playtest/enhanced')
    stage = Path('/tmp/openyamm-new-dirt-shore-review')
    stage.mkdir(exist_ok=True)
    shutil.copy2(enhanced.parent / 'openyamm', stage / 'openyamm')
    for name in ('map', 'flat'):
        target = stage / name
        if not target.exists():
            shutil.copytree(enhanced, target, symlinks=True)
        terrain = target / 'assets_dev/worlds/mm6/terrain_x2'
        assert not terrain.is_symlink()
        for f in (P / 'runtime_x2/worlds/mm6/terrain_x2').glob('*.png'):
            shutil.copy2(f, terrain / f.name)
        maps = target / 'assets_dev/worlds/mm6/maps'
        assert not maps.is_symlink()
        if name == 'flat':
            # The empty fixture has no actors; preserve the real map's actor overrides
            # outside the fixture asset mount rather than applying them to unrelated indices.
            excluded = target / 'fixture_excluded_overlays'
            excluded.mkdir(exist_ok=True)
            for overlay in maps.glob('oute3.scene.*.yml'):
                shutil.move(str(overlay), excluded / overlay.name)
            shutil.copy2(WATER / 'fixture/oute3.odm', maps / 'oute3.odm')
            shutil.copy2(WATER / 'fixture/oute3.scene.yml', maps / 'oute3.scene.yml')
        settings = configparser.ConfigParser(interpolation=None)
        settings.read(target / 'settings.ini')
        settings['assets']['root'] = str(target / 'assets_dev')
        settings['video_quality']['terrain'] = 'x2'
        with (target / 'settings.ini').open('w') as f:
            settings.write(f)
    (P / 'captures').mkdir(exist_ok=True)
    report = {'stage': str(stage), 'binary_sha256': sha(stage / 'openyamm'),
              'files': json.loads((P / 'report.json').read_text())['files'],
              'map_sha256': sha(stage / 'map/assets_dev/worlds/mm6/maps/oute3.odm'),
              'flat_sha256': sha(stage / 'flat/assets_dev/worlds/mm6/maps/oute3.odm')}
    (P / 'review_stage.json').write_text(json.dumps(report, indent=2) + '\n')
    print(stage)


if __name__ == '__main__': main()
