"""A top-down hillshade of a built Crown height field (north up), tinted by height with 256-unit contours, for the
relief review (2026-10-24).

    python3 level_generation/projects/hesper_out4/make_hillshade.py <map.odm | heights.npy> <out.png> [title]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'util'))

source, out = Path(sys.argv[1]), Path(sys.argv[2])
title = sys.argv[3] if len(sys.argv) > 3 else source.name
if source.suffix == '.npy':
    heights = np.load(source).astype(np.float64)
else:
    from map_export import parse_odm_file
    heights = np.array(parse_odm_file(source)['payload']['height_map'], np.float64).reshape(128, 128) * 32.0
SCALE = 8
big = ndimage.zoom(heights, SCALE, order=3)                  # 64 world units a pixel
step = 512.0 / SCALE
gy, gx = np.gradient(big, step)                              # rows run south
azimuth, elevation = np.radians(315.0), np.radians(40.0)
# Light from the north-west: x east, y north (rows run south, so the north component is -gy).
lx, ly, lz = np.cos(elevation) * np.sin(azimuth), np.cos(elevation) * np.cos(azimuth), np.sin(elevation)
nx, ny, nz = -gx * 2.0, gy * 2.0, np.ones_like(gx)          # exaggerated x2
shade = np.clip((nx * lx + ny * ly + nz * lz) / np.sqrt(nx * nx + ny * ny + nz * nz), 0, 1)
stops = np.array([0, 600, 1100, 1700, 2600, 5600], float)          # the floor's detail apart, the rim compressed
ramp = np.array([[30, 50, 130], [40, 120, 150], [70, 130, 80], [170, 160, 80], [180, 110, 70], [215, 205, 215]],
                float)
colour = np.stack([np.interp(big, stops, ramp[:, c]) for c in range(3)], -1)
rgb = colour * (0.35 + 0.75 * shade[..., None])
contour = np.floor(big / 256.0)
edge = (np.abs(np.diff(contour, axis=0, prepend=contour[:1])) + np.abs(np.diff(contour, axis=1, prepend=contour[:, :1]))) > 0
rgb[edge] *= 0.55
# The playable square (+-23 040) outlined.
lo, hi = int((32768 - 23040) / 64), int((32768 + 23040) / 64)
image = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB')
draw = ImageDraw.Draw(image)
draw.rectangle((lo, lo, hi, hi), outline=(255, 220, 120))
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
draw.rectangle((0, 0, 1024, 30), fill=(0, 0, 0))
draw.text((8, 5), f'{title}: {heights.min():.0f}-{heights.max():.0f}, contours every 256', font=font,
          fill=(255, 230, 120))
image.save(out)
print(out, heights.min(), heights.max())
