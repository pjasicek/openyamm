"""Loot satchel v2 (concept E): one shared sack, six retextures. Final in-game widths (m), drawn 1:1 by the engine;
specular per material family; tiers 5-6 have an emissive clasp gem."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(ROOT, '..', '..', '..', '..'))
LOD0_TRIANGLES = 900
TIERS = {
    1: {'width': 0.50, 'material': 'burlap', 'specular': 0.3},
    2: {'width': 0.58, 'material': 'green wool', 'specular': 0.3},
    3: {'width': 0.66, 'material': 'rust leather', 'specular': 0.3},
    4: {'width': 0.76, 'material': 'blue leather', 'specular': 0.3},
    5: {'width': 1.01, 'material': 'purple velvet', 'specular': 0.2, 'gem_emissive': (0.18, 0.08, 0.30)},
    6: {'width': 1.25, 'material': 'crimson velvet', 'specular': 0.2, 'gem_emissive': (0.40, 0.30, 0.12)},
}
# Clasp gem on the shared 1 m mesh: a separate 20-face island (the clasp ball at the cord knot); finish.py takes the
# whole island containing the face nearest to this point.
CLASP = {'centre': (-0.023, -0.235, 0.793)}
