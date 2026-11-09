"""Prepare focused art repairs where straight donor footprints meet diagonal roads."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import json
from scipy.ndimage import binary_closing, binary_fill_holes, distance_transform_edt, gaussian_filter
from common import *

F = Path(__file__).resolve().parent / 'outline_repairs'
for sub in ('inputs', 'prompts', 'raw'): (F / sub).mkdir(parents=True, exist_ok=True)
yy, xx = np.mgrid[:512, :512]
border = np.minimum.reduce([xx, yy, 511 - xx, 511 - yy])
cy, cx = np.mgrid[-18:19, -18:19]; disk = cx * cx + cy * cy <= 18 * 18
records = []
for name in ('drsrne1', 'drsrne2', 'drsrnw1', 'drsrnw2'):
    source = F.parent / 'authoring' / (name + '.png')
    image = read(source)
    alpha = read(F.parent / 'masks' / (name + '.png'))[:, :, 0] > 127
    closed = binary_closing(np.pad(alpha, 32, mode='edge'), structure=disk)[32:-32, 32:-32]
    closed = binary_fill_holes(closed)
    sdf = distance_transform_edt(closed) - distance_transform_edt(~closed)
    smooth = gaussian_filter(sdf, 4) > 0
    # The native interior and exact shared-opening pixels remain locked.
    repaired = np.where((border > 8) & (border < 128), smooth, alpha)
    save(F / 'inputs' / (name + '_target.png'), image)
    save(F / 'inputs' / (name + '_coverage.png'), repaired * 255)
    prompt = f'''Use case: precise-object-edit
Asset type: local outline correction of a restored MM8 diagonal cobble-road tile.
Image 1 is the target colour tile. Its road is already restored but some stones are visibly chopped or form unnatural triangular notches near the canvas edges, where straight road openings connect to its diagonal interior. Image 2 defines the required continuous solid road silhouette, white for cobbles and black for earth.
Repair these outline connections within the outer quarter of the tile, using the silhouette in image 2. Redraw only malformed border stones as complete ordinary cobbles, keeping the existing stone size, dark grey-brown palette, mineral grain and original diagonal-road character. Fill the artificial notches inside the white silhouette with complete stone shapes and packed joints, and remove chopped projections outside that silhouette. The road should have a naturally irregular but coherent edge with soft contact shading into the brown earth. Keep every road opening at the canvas edge exactly where it is in image 1. Preserve the central half of the tile and the earth away from the road. The goal is painted MM8 art with more definition, not photorealism, no new lighting, no wet gloss, no thin serrated outlines, no scattered fragments or dirt holes. Return the colour tile only, one square full-bleed image at the same framing; no mask, labels, grid or repeated preview.'''
    (F / 'prompts' / (name + '.txt')).write_text(prompt)
    records.append(dict(name=name, source_sha256=sha(source), target_sha256=sha(F / 'inputs' / (name + '_target.png')),
                        mask_sha256=sha(F / 'inputs' / (name + '_coverage.png'))))
(F / 'inputs.json').write_text(json.dumps(records, indent=2) + '\n')
