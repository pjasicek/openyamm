"""Concept against result: for every tour pose that has a concept edit, a sheet of concept A | original | result.

  python3 source/concept_compare.py <original review dir> <result review dir>

Writes review/concept_<result>/<pose>.jpg. The concept edits are Codex image edits of engine captures at the same
pose (level_generation/geometry_study_20261111/concepts/<view>_A_target.png); see PLAYBOOK.md, step 6.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[1]
CONCEPTS = PROJECT.parents[1] / 'geometry_study_20261111/concepts'
# Tour shot name -> concept view.
POSES = {'armory_v03': 'v03', 'tavern_v01': 'v01', 'bridge_v08': 'v08', 'goblinwatch_v07': 'v07'}


def main():
    original, result = Path(sys.argv[1]), Path(sys.argv[2])
    out = PROJECT / 'review' / f'concept_{result.name}'
    out.mkdir(parents=True, exist_ok=True)
    for shot, view in POSES.items():
        concept = CONCEPTS / f'{view}_A_target.png'
        before = next(original.glob(f'*-{shot}.png'), None)
        after = next(result.glob(f'*-{shot}.png'), None)
        if not concept.exists() or before is None or after is None:
            continue
        images = [Image.open(path).convert('RGB') for path in (concept, before, after)]
        size = images[1].size
        images = [image.resize(size) for image in images]
        sheet = Image.new('RGB', (size[0], size[1] * 3 + 16), (0, 0, 0))
        draw = ImageDraw.Draw(sheet)
        for row, (image, label) in enumerate(zip(images, ('concept A', 'original', 'result'))):
            sheet.paste(image, (0, row * (size[1] + 8)))
            draw.rectangle([0, row * (size[1] + 8) + 60, 230, row * (size[1] + 8) + 104], fill=(0, 0, 0))
            draw.text((8, row * (size[1] + 8) + 66), label, fill=(255, 255, 0), font_size=30)
        sheet.resize((size[0] // 2, sheet.size[1] // 2)).save(out / f'{shot}.jpg', quality=88)
        print(out / f'{shot}.jpg')


if __name__ == '__main__':
    main()
