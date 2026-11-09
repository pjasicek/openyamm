"""Compare each prepared canonical mesh's clay guides with its inventory icon."""
import json
from pathlib import Path

from PIL import Image, ImageDraw

project = Path(__file__).resolve().parents[1]
designs = json.loads((project / 'designs.json').read_text())
owned = {entry['icon'] for entry in json.loads((project / 'ownership.json').read_text())}
assert all(entry['master_icon'] in owned for entry in designs.values())
for family in ['boots', 'cloaks', 'gauntlets', 'helms']:
    names = [name for name, entry in designs.items() if entry['family'] == family
             and entry['geometry_design'] == name
             and (project / 'codex_tex' / name / 'guide_top.png').exists()]
    for start in range(0, len(names), 6):
        sheet = Image.new('RGBA', (1040, 1320), (32, 36, 44, 255))
        draw = ImageDraw.Draw(sheet)
        for row, name in enumerate(names[start:start + 6]):
            draw.text((5, row * 220 + 5), name, fill='white')
            paths = [project / 'references/icons' / (designs[name]['master_icon'] + '.png')]
            paths += [project / 'codex_tex' / name / f'guide_{view}.png' for view in ['front', 'left', 'top']]
            for column, path in enumerate(paths):
                image = Image.open(path).convert('RGBA')
                image.thumbnail((250, 190))
                sheet.alpha_composite(image, (column * 260 + (260 - image.width) // 2,
                                             row * 220 + 25 + (190 - image.height) // 2))
        output = project / 'review' / f'geometry_{family}_{start // 6 + 1}.png'
        sheet.convert('RGB').save(output)
        print(output)
