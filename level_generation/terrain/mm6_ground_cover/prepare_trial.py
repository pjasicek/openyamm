"""Create an isolated ground-cover trial over the currently accepted enhanced content."""
import configparser
import hashlib
import json
import shutil
import os
import tempfile
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
STAGE = Path('/tmp/openyamm-sorpigal-ground-cover')


def main():
    source = Path('/tmp/openyamm-sorpigal-peasants-playtest/enhanced')
    assert source.is_dir(), 'Prepare the enhanced peasants trial first'
    STAGE.mkdir(exist_ok=True)
    assets = STAGE / 'assets_dev'
    if not assets.exists():
        shutil.copytree(source / 'assets_dev', assets, symlinks=True)
    decorations = assets / 'worlds/mm6/terrain_decorations'
    assert not decorations.is_symlink()
    shutil.copytree(ROOT / 'assets_dev/worlds/mm6/terrain_decorations', decorations, dirs_exist_ok=True)
    # Atomic replacement also works while the user still has the previous trial running.
    with tempfile.NamedTemporaryFile(dir=STAGE, prefix='.openyamm-', delete=False) as stream:
        binary_temp = Path(stream.name)
    try:
        shutil.copy2(ROOT / 'build/game/openyamm', binary_temp)
        os.replace(binary_temp, STAGE / 'openyamm')
    finally:
        binary_temp.unlink(missing_ok=True)
    settings = configparser.ConfigParser(interpolation=None)
    settings.read(STAGE / 'settings.ini' if (STAGE / 'settings.ini').exists() else source / 'settings.ini')
    settings['assets']['root'] = str(assets)
    settings['video']['terrain_decorations'] = 'true'
    settings['startup']['start_in_main_menu'] = 'true'
    with (STAGE / 'settings.ini').open('w') as stream:
        settings.write(stream, space_around_delimiters=False)
    saves = STAGE / 'saves'
    saves.mkdir(exist_ok=True)
    if not (saves / 'terrain.oysav').exists():
        shutil.copy2(P.parent / 'mm6_new_sorpigal_dirt_fidelity/references/Dirt_View.oysav', saves / 'terrain.oysav')
    metadata = dict(stage=str(STAGE), source=str(source),
                    binary_sha256=hashlib.sha256((STAGE / 'openyamm').read_bytes()).hexdigest())
    (P / 'trial.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(STAGE)


if __name__ == '__main__':
    main()
