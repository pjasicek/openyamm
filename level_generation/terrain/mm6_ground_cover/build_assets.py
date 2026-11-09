"""Export the generated tuft and accepted directional material masks for runtime scattering."""
from pathlib import Path
from PIL import Image
import yaml

from audit_edges import audit

P = Path(__file__).resolve().parent
ROOT = P.parents[2]
OUT = ROOT / 'assets_dev/worlds/mm6/terrain_decorations'
MASKS = P.parent / 'mm6_new_sorpigal_dirt_fidelity/transitions/masks/connected_v4'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'masks').mkdir(exist_ok=True)
    atlas = Image.new('RGBA', (512, 384))
    sources = ['grass_tuft', 'grass_fine', 'grass_wispy', 'grass_dry']
    for index, source in enumerate(sources):
        image = Image.open(P / 'generated' / (source + '.png')).convert('RGBA')
        assert image.getchannel('A').getextrema() == (0, 255), source + ' requires real transparency'
        image = image.crop(image.getchannel('A').getbbox())
        # Preserve alpha and aspect ratio; roots sit at a common two-pixel bottom gutter.
        image = image.convert('RGBa')
        image.thumbnail((252, 188), Image.Resampling.LANCZOS)
        image = image.convert('RGBA')
        cell = Image.new('RGBA', (256, 192))
        cell.paste(image, ((256-image.width)//2, 192-image.height-2))
        atlas.paste(cell, ((index % 2) * 256, (index // 2) * 192))
    audit(atlas)
    atlas.save(OUT / 'grass_variants.png')
    rules = []
    for name, kind in [('6grastyl', 'grass'), ('6dirttyl', 'stone')]:
        rules.append(rule(name, kind))
    for path in sorted(MASKS.glob('6grdrt*.png')):
        Image.open(path).convert('L').resize((64, 64), Image.Resampling.BOX).save(OUT / 'masks' / path.name)
        for kind in ['grass', 'stone']:
            item = rule(path.stem, kind)
            item['mask'] = 'masks/' + path.name
            if kind == 'stone':
                item['invert_mask'] = True
            rules.append(item)
    config = dict(version=1, seed=6127, near_distance=3072, minimum_normal_z=0.88,
                  density_variation=0.8, patch_size=768, tall_grass_chance=0.08, tall_grass_scale=1.8,
                  tuft_texture='grass_variants.png', tuft_atlas_grid=[2, 2],
                  tuft_variants=[dict(weight=45, width_scale=1.0, height_scale=1.0),
                                 dict(weight=35, width_scale=1.0, height_scale=0.9),
                                 dict(weight=15, width_scale=1.0, height_scale=1.35),
                                 dict(weight=5, width_scale=0.85, height_scale=0.85)], rules=rules)
    (OUT / 'oute3.yml').write_text(yaml.safe_dump(config, sort_keys=False))
    print(OUT)


def rule(texture, kind):
    grass = kind == 'grass'
    return dict(texture=texture, kind=kind, candidates=50 if grass else 10,
                width=40 if grass else 12, height=30 if grass else 4,
                tint=[0.82, 0.98, 0.78] if grass else [0.65, 0.43, 0.29])


if __name__ == '__main__':
    main()
