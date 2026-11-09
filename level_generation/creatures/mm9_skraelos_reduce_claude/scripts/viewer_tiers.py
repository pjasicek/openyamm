#!/usr/bin/env python3
"""Review-viewer GLB (Skraelos copy of ../mm9_skraelos_claude/scripts/viewer_sk.py with the GLB and an output prefix as arguments):
one tier, no ramps; every material gets KHR_materials_specular 0 (the engine's openyamm_specular 0).
Usage: viewer_tiers.py <glb> <prefix> -> work/viewer_<prefix>_sk.glb"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV
doc, binary = RV.read_glb(Path(sys.argv[1]))
for m in doc['materials']:
    m.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.0}
doc['extensionsUsed'] = sorted(set(doc.get('extensionsUsed', [])) | {'KHR_materials_specular'})
RV.write_glb(HERE / 'work' / f'viewer_{sys.argv[2]}_sk.glb', doc, bytes(binary)); print('viewer', sys.argv[2])
