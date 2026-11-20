#!/usr/bin/env python3
"""The LOD tool's writer normalises material JSON (metallicFactor 0 -> 0.0, texCoord 0 added on PeasantDM1Head_pdm1_b): put the
installed materials array back exactly (same names, same order, same texture indices). Usage: restore_materials.py <installed> <glb> (in place)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glbio  # noqa: E402
a, _ = glbio.read_glb(Path(sys.argv[1])); b, bb = glbio.read_glb(Path(sys.argv[2]))
assert [m['name'] for m in a['materials']] == [m['name'] for m in b['materials']]
assert len(a['textures']) == len(b['textures'])
b['materials'] = a['materials']; glbio.write_glb(Path(sys.argv[2]), b, bb); print('MATERIALS restored')
