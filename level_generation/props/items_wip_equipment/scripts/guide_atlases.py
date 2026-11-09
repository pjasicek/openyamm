"""Arrange exact guides into a 3x2 painting template; generated atlas pixels stay unmodified."""
import json
from pathlib import Path

from PIL import Image

project = Path(__file__).resolve().parents[1]
views = ['front', 'back', 'left', 'right', 'top']
assert len(set(views)) == 5
for frame_path in (project / 'codex_tex').glob('equipment_*/views.json'):
    folder = frame_path.parent
    frame = json.loads(frame_path.read_text())
    if not all((folder / f'guide_{view}.png').exists() for view in views):
        continue
    output = folder / 'guide_atlas.png'
    if (output.exists() and frame.get('paint_layout') == 'atlas_3x2'
            and output.stat().st_mtime >= max((folder / f'guide_{view}.png').stat().st_mtime for view in views)):
        continue
    atlas = Image.new('RGBA', (1536, 1024))
    for index, view in enumerate(views):
        guide = Image.open(folder / f'guide_{view}.png').convert('RGBA')
        assert guide.width == guide.height
        atlas.alpha_composite(guide.resize((512, 512)), ((index % 3) * 512, (index // 3) * 512))
    atlas.save(output)
    frame['paint_layout'] = 'atlas_3x2'
    frame['atlas_views'] = views + [None]
    frame_path.write_text(json.dumps(frame, indent=2) + '\n')
    print(folder.name)
