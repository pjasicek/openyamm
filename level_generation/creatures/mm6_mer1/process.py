"""Extract merchant sheets and apply the reviewed fixed family tonal correction."""
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'mm6_peasants'))
import process_family


def main():
    process_family.run('mer1')
    for folder in ['cleaned', 'aligned_2x']:
        for path in (ROOT / folder).glob('*.png'):
            a = np.array(Image.open(path))
            a[:, :, :3] = np.round(a[:, :, :3].astype(float) * .90).astype(np.uint8)
            Image.fromarray(a).save(path)
    (ROOT / 'tone.json').write_text(json.dumps(dict(rgb_gain=.90,
        reason='Reduce brighter generated skin, trim and boots toward native tonal weight; fixed across frames',
        alpha='unchanged', comparisons='Extraction comparison sheets precede this fixed grade; packaged reviews use it'),
        indent=2) + '\n')


if __name__ == '__main__':
    main()
