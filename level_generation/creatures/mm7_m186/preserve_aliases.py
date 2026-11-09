"""Reuse accepted art for the pixel-identical native death-frame alias."""
import json
import shutil
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def run():
    source, alias = 'm186df0', 'm186dg0'
    native = [Image.open(REPO / f'assets_dev/engine/sprites/{name}.bmp') for name in [source, alias]]
    assert native[0].size == native[1].size and native[0].tobytes() == native[1].tobytes()
    for folder in ['cleaned', 'aligned_2x', 'masks_2x']:
        shutil.copyfile(HERE / folder / f'{source}.png', HERE / folder / f'{alias}.png')
    registration = json.loads((HERE / 'registration.json').read_text())
    registration[alias] = dict(registration[source], native_pixel_alias_of=source)
    (HERE / 'registration.json').write_text(json.dumps(registration, indent=2) + '\n')
    audit = json.loads((HERE / 'review/cleaned_edge_audit.json').read_text())
    audit[alias] = audit[source]
    (HERE / 'review/cleaned_edge_audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    settings = json.loads((HERE / 'processing_settings.json').read_text())
    settings['native_pixel_aliases'] = {alias: source}
    (HERE / 'processing_settings.json').write_text(json.dumps(settings, indent=2) + '\n')
    print('Preserved native pixel alias:', alias, '->', source)


if __name__ == '__main__':
    run()
