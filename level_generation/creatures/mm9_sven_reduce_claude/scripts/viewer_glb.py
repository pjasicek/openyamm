#!/usr/bin/env python3
"""Review-viewer copy of a one-skin runtime GLB (no tiers, so viewer_tiers.py is not needed): every material gets
KHR_materials_specular 0 (the engine's openyamm_specular 0; three.js would otherwise add a specular sheen), nothing else changes.
Usage: viewer_glb.py <glb> <out glb>"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
doc, binary = read_glb(Path(sys.argv[1]))
for m in doc['materials']:
    m.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.0}
doc['extensionsUsed'] = sorted(set(doc.get('extensionsUsed', [])) | {'KHR_materials_specular'})
write_glb(Path(sys.argv[2]), doc, binary); print('VIEWER GLB', sys.argv[2])
