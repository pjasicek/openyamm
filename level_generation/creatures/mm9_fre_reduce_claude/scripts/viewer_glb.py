#!/usr/bin/env python3
"""Review-viewer GLB for a runtime Fre GLB (installed or reduced; copy of ../mm9_fre_claude/scripts/viewer_fre.py with arguments): the
GLB with KHR_materials_specular 0 on every material (three.js has no openyamm_specular). Usage: viewer_glb.py <glb> <out glb>"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV
doc, binary = RV.read_glb(Path(sys.argv[1]))
for m in doc['materials']: m.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.0}
doc['extensionsUsed'] = sorted(set(doc.get('extensionsUsed', [])) | {'KHR_materials_specular'})
RV.write_glb(Path(sys.argv[2]), doc, binary); print('viewer', sys.argv[2])
