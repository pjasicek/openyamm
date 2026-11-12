"""Review-page images for the other maps: concept A, now and result per concept view (1600 x 900 JPEGs), plus the
gallery entries as JSON for the page script.

  python3 source/page_maps.py <run> <map>...      writes page/img/m_<map>_<shot>_{concept,now,result}.jpg
"""
import json
import sys
from pathlib import Path

from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'source'))
import maps  # noqa: E402

PAGE = PROJECT.parents[1] / 'geometry_study_20261111/page/img'


def main():
    run, stems = sys.argv[1], sys.argv[2:]
    entries = {}
    for stem in stems:
        entries[stem] = []
        for concept in sorted(maps.concepts(stem).glob('*_A.png')):
            shot = concept.name[:-6]
            result = maps.run(stem, run) / f'{shot}.png'
            if not result.exists():
                continue
            for path, kind in ((concept, 'concept'), (maps.original(stem) / f'{shot}.png', 'now'), (result, 'result')):
                Image.open(path).convert('RGB').resize((1600, 900), Image.LANCZOS).save(
                    PAGE / f'm_{stem}_{shot}_{kind}.jpg', quality=84)
            entries[stem].append(shot)
    print(json.dumps(entries))


if __name__ == '__main__':
    main()
