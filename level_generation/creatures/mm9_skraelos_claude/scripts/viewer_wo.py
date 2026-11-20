#!/usr/bin/env python3
"""Review-viewer GLB: one tier, no ramps; every material gets KHR_materials_specular 0 (the engine's openyamm_specular 0). Writes work/viewer_wo.glb."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV
doc, binary = RV.read_glb(HERE / 'export' / 'mm9_wyrdold.glb')
for m in doc['materials']: m.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.0}
doc['extensionsUsed'] = sorted(set(doc.get('extensionsUsed', [])) | {'KHR_materials_specular'})
RV.write_glb(HERE / 'work' / 'viewer_wo.glb', doc, bytes(binary)); print('viewer wo')
