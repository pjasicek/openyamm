"""Make the Crown's sky textures (THE_CROWN.md section 9, zone4/KITS.md "Sky layers") into
design/kreegan_world/art/sky/hes_out4/runtime/, where the Hesper stage cooks them (stage.py, the zones' sky layers):

  hesper_crown_horizon.png   4096 x 512 horizon band from hesper_crown_horizon_src.png (Codex, approved R3), through
                             tools/sky/prepare_sky_art.py's horizon ring step (wrap blend, two repeats), as Starport
                             Reach's.
  hesper_lattice_night.png   Starport Reach's night sky (art/sky/hesper_night.png) with the Lattice's aurora
                             (hesper_aurora_src.png, approved R3) composited over its northern half: the sky renderer
                             has no aurora layer, so the curtains turn with the stars and fade with them by day.

    python3 level_generation/projects/hesper_out4/make_sky_out4.py
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
SKY = ROOT / 'design/kreegan_world/art/sky'
SOURCES = SKY / 'hes_out4'
OUT = SOURCES / 'runtime'
sys.path.insert(0, str(ROOT / 'tools/sky'))
import prepare_sky_art  # noqa: E402

OUT.mkdir(exist_ok=True)
ring = prepare_sky_art.horizon_ring(SOURCES / 'hesper_crown_horizon_src.png')
Image.fromarray(np.clip(ring + 0.5, 0, 255).astype(np.uint8), 'RGBA').save(OUT / 'hesper_crown_horizon.png')

# The night sky is an equirectangular panorama of the celestial sphere (2:1, its pole at the top). The aurora band
# (4:1, its curtains' hems near its foot) covers declinations from about +80 down to +25 degrees, round the pole the
# preset raises 55 degrees over the horizon, so the curtains stand over the northern sky through the night.
night = np.asarray(Image.open(SKY / 'hesper_night.png').convert('RGB'), dtype=np.float32) / 255.0
height, width = night.shape[:2]
top, bottom = int(height * (90 - 80) / 180), int(height * (90 - 25) / 180)
aurora = Image.open(SOURCES / 'hesper_aurora_src.png').convert('RGB').resize((width, bottom - top), Image.LANCZOS)
aurora = np.asarray(aurora, dtype=np.float32) / 255.0
# Soften the band's own top and bottom edges so it has no seam against the stars, and keep the curtains a little
# below full strength (the stars and the debris ring stay readable through them).
rows = np.linspace(0.0, 1.0, bottom - top)[:, None, None]
fade = np.clip(rows / 0.25, 0, 1) * np.clip((1.0 - rows) / 0.08, 0, 1)
band = night[top:bottom]
night[top:bottom] = 1.0 - (1.0 - band) * (1.0 - aurora * fade * 0.85)          # screen blend
Image.fromarray(np.clip(night * 255.0 + 0.5, 0, 255).astype(np.uint8), 'RGB').save(OUT / 'hesper_lattice_night.png')
print('wrote', sorted(p.name for p in OUT.glob('*.png')))
