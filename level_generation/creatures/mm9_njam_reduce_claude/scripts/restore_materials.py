#!/usr/bin/env python3
"""tools/build_actor_lods.py rewrites the material JSON in normalised form (metallicFactor 0 -> 0.0, texCoord 0 added): the
same material, but same_clips.py compares the JSON. Copy the installed materials back verbatim (same names, same order).
Usage: restore_materials.py <installed.glb> <glb, in place>"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
a, _ = read_glb(src); d, b = read_glb(dst)
assert [m['name'] for m in a['materials']] == [m['name'] for m in d['materials']]
d['materials'] = a['materials']; write_glb(dst, d, b); print('MATERIALS restored', len(a['materials']))
