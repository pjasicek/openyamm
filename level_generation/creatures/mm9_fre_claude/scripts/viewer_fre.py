#!/usr/bin/env python3
"""Review-viewer GLB for Fre (one skin, no tiers): a copy of export/mm9_fre.glb with KHR_materials_specular 0 on every material (three.js
has no openyamm_specular). Writes work/viewer_fre_a.glb."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV
doc, binary = RV.read_glb(HERE / 'export' / 'mm9_fre.glb')
for m in doc['materials']: m.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.0}
doc['extensionsUsed'] = sorted(set(doc.get('extensionsUsed', [])) | {'KHR_materials_specular'})
RV.write_glb(HERE / 'work' / 'viewer_fre_a.glb', doc, binary); print('viewer fre_a')
