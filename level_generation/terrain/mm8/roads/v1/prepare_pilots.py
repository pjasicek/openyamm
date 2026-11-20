"""Native straight-road guides: close joints, keep broad stone irregularity and original width."""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import binary_closing, binary_fill_holes, gaussian_filter1d, label, median_filter

P = Path(__file__).resolve().parent
PROJECT = P.parents[1]
for name in ('drsrew', 'drsrns'):
    source = Image.open(PROJECT / 'references' / (name + '.png')).convert('RGB')
    source.resize((512, 512), Image.Resampling.NEAREST).save(P / 'inputs' / (name + '_native_512.png'))
    rgb = np.asarray(source.resize((512, 512), Image.Resampling.BICUBIC), float)
    coverage = (rgb[:, :, 1] / np.maximum(rgb[:, :, 0], 1) > .77) & (rgb[:, :, 2] / np.maximum(rgb[:, :, 0], 1) > .58)
    coverage = binary_closing(np.pad(coverage, 10, mode='edge'), iterations=3)[10:-10, 10:-10]
    components, _ = label(coverage)
    counts = np.bincount(components.ravel())
    counts[0] = 0
    coverage = binary_fill_holes(components == counts.argmax())
    Image.fromarray((coverage * 255).astype('uint8')).save(P / 'inputs' / (name + '_native_mask.png'))
    if name.endswith('ns'):
        coverage = coverage.T
    lower = np.argmax(coverage, axis=0).astype(float)
    upper = 511 - np.argmax(coverage[::-1], axis=0).astype(float)
    lower, upper = [gaussian_filter1d(median_filter(edge, size=21, mode='nearest'), 3)
                    for edge in (lower, upper)]
    coverage = (np.arange(512)[:, None] >= lower) & (np.arange(512)[:, None] <= upper)
    if name.endswith('ns'):
        coverage = coverage.T
    Image.fromarray((coverage * 255).astype('uint8')).save(P / 'inputs' / (name + '_solid_guide.png'))
