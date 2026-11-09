#!/usr/bin/env python3
"""Review-viewer GLB. The Treant has no tier ramps (descriptors 451-453 share palette 530 and one material), so the
viewer model is the exported LOD0 itself: export/mm7_m479_lod0.glb -> review/viewer/mm7_m479.glb."""
import shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
shutil.copyfile(ROOT / 'export' / 'mm7_m479_lod0.glb', ROOT / 'review' / 'viewer' / 'mm7_m479.glb')
print('VIEWER mm7_m479.glb')
