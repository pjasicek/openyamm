#!/usr/bin/env python3
"""Two glow colours in one material: like claude_shared/emission.py, but the emissive texture is a COLOUR image (the
ruby red on the gem, green on the eye cores; textures/guardian_emission_rgb.png, sRGB) and the factor is a grey
strength, as CLAUDE_CREATURE_TEXTURES.md "Emission" allows ("a colour texture works too"). Every material whose name
starts with PREFIX gets emissiveTexture = that image (embedded once, the base colour's sampler) and
emissiveFactor = [s, s, s]; creature materials with an emissive texture bloom. Optional gentle pulse.
Usage: emission_rgb.py in.glb out.glb --material PREFIX --image rgb.png --strength S [--pulse a,p]"""
import argparse, io, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
from emission import read_glb, write_glb   # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('input'); ap.add_argument('output')
ap.add_argument('--material', required=True); ap.add_argument('--image', required=True)
ap.add_argument('--strength', type=float, default=1.0); ap.add_argument('--pulse')
a = ap.parse_args()
doc, binary = read_glb(a.input)
targets = [i for i, m in enumerate(doc.get('materials', [])) if m.get('name', '').startswith(a.material)]
if not targets:
    sys.exit(f'no material starts with {a.material}')
png = io.BytesIO(); Image.open(a.image).convert('RGB').save(png, 'PNG', optimize=True)
binary += b'\0' * (-len(binary) % 4)
doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(png.getvalue())})
binary += png.getvalue(); doc['buffers'][0]['byteLength'] = len(binary)
doc['images'].append({'name': Path(a.image).stem, 'mimeType': 'image/png', 'bufferView': len(doc['bufferViews']) - 1})
base = doc['materials'][targets[0]].get('pbrMetallicRoughness', {}).get('baseColorTexture')
tex = {'source': len(doc['images']) - 1}
if base is not None and 'sampler' in doc['textures'][base['index']]:
    tex['sampler'] = doc['textures'][base['index']]['sampler']
doc['textures'].append(tex)
for i in targets:
    m = doc['materials'][i]
    s = round(min(max(a.strength, 0.0), 1.0), 6)
    m['emissiveFactor'] = [s, s, s]; m['emissiveTexture'] = {'index': len(doc['textures']) - 1}
    ex = m.setdefault('extras', {}); ex.pop('openyamm_bloom', None)
    if a.pulse:
        amp, per = (float(v) for v in a.pulse.split(',')); ex['openyamm_pulse'] = [amp, per]
    print(f'EMISSION {m.get("name")} factor={m["emissiveFactor"]} texture {Path(a.image).name}')
write_glb(a.output, doc, binary)
