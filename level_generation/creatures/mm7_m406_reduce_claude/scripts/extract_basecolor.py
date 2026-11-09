"""Base-colour image of the first material of a GLB -> work/basecolor.png (for face_classes / texture_drift).
Usage: extract_basecolor.py <glb>"""
import io, json, struct, sys
from PIL import Image
raw = open(sys.argv[1], 'rb').read(); n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n]); binary = raw[28 + n:]
tex = doc['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index']
img = doc['images'][doc['textures'][tex]['source']]; bv = doc['bufferViews'][img['bufferView']]
data = binary[bv.get('byteOffset', 0):bv.get('byteOffset', 0) + bv['byteLength']]
im = Image.open(io.BytesIO(data)); im.save('work/basecolor.png'); print('BASECOLOR', doc['materials'][0]['name'], im.size, im.mode)
