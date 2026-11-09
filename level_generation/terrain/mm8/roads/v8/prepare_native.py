"""Recover diagonal footprints and shading from native pixels, never restored road donors."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from common import *
from scipy.ndimage import binary_closing, binary_fill_holes, label, gaussian_filter, distance_transform_edt
from PIL import ImageDraw
import json

NAMES = ['drsrne1', 'drsrne2', 'drsrnw1', 'drsrnw2']
records = []
sheet = Image.new('RGB', (1024, 4 * 280), '#182027')
draw = ImageDraw.Draw(sheet)
for row, name in enumerate(NAMES):
    source = P / 'references' / (name + '.png')
    native = read(source)
    candidate = (native[:, :, 1] > .77 * native[:, :, 0]) & (native[:, :, 2] > .58 * native[:, :, 0])
    # One native pixel closes dark mortar gaps; no large contour smoothing or
    # straight-donor endpoint substitution is allowed here.
    mask = binary_closing(np.pad(candidate, 3, mode='edge'), iterations=1)[3:-3, 3:-3]
    components, _ = label(mask)
    sizes = np.bincount(components.ravel()); sizes[0] = 0
    mask = binary_fill_holes(components == sizes.argmax())
    alpha = gaussian_filter(mask.astype(float), .35)
    save(HERE / 'inputs' / (name + '_native_mask.png'), mask * 255)
    save(HERE / 'inputs' / (name + '_native_512.png'), read(source, 512))
    guide = Image.fromarray((mask * 255).astype('uint8')).resize((512, 512), Image.NEAREST)
    guide.save(HERE / 'inputs' / (name + '_guide.png'))
    np.savez_compressed(HERE / 'inputs' / (name + '_native_fields.npz'), rgb=native, alpha=alpha)
    for column, pixels in enumerate([native, mask[:, :, None].repeat(3, 2) * 255,
                                    read(HERE.parent / 'v7/runtime' / (name + '.png'))]):
        im = Image.fromarray(seams.byte(pixels)).resize((256, 256), Image.NEAREST)
        sheet.paste(im, (column * 256, row * 280 + 24))
        draw.text((column * 256 + 4, row * 280 + 4), name + ' ' + ['native', 'native footprint', 'rejected v7'][column], fill='white')
    openings = {side: np.flatnonzero(values).tolist() for side, values in
                [('N', mask[0]), ('S', mask[-1]), ('W', mask[:, 0]), ('E', mask[:, -1])]}
    records.append(dict(name=name, source_sha256=sha(source), native_size=list(native.shape[:2]),
                        mask_sha256=sha(HERE / 'inputs' / (name + '_native_mask.png')), openings=openings))
sheet.save(HERE / 'native_footprints.png')
(HERE / 'native_inventory.json').write_text(json.dumps(records, indent=2) + '\n')
print('Recovered four native diagonal footprints at native resolution')
