#!/usr/bin/env python3
"""Replace the base colour atlas of a built GLB (shared by every variant material) with a PNG of the same size.
Usage: swap_basecolor.py <in.glb> <png> <out.glb>"""
import io, sys
from pathlib import Path
from PIL import Image
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'claude_shared')); import region_variants as R  # noqa: E402
src, png, dst = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
doc, binary = R.read_glb(src); binary = bytearray(binary)
texs = {m['pbrMetallicRoughness']['baseColorTexture']['index'] for m in doc['materials']}
images = {doc['textures'][t]['source'] for t in texs}; assert len(images) == 1, images
image = doc['images'][images.pop()]
new = Image.open(png).convert('RGB'); data = io.BytesIO(); new.save(data, 'PNG', optimize=True); data = data.getvalue()
binary.extend(b'\0' * (-len(binary) % 4))
doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(data)}); binary.extend(data)
image['bufferView'] = len(doc['bufferViews']) - 1
doc, binary = R._compact(doc, binary)
R.write_glb(dst, doc, binary); print('WROTE', dst, image.get('name'), dst.stat().st_size)
