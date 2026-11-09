"""MM9 skin UV islands labelled by body region (dominant joint + height), drawn over each skin. Args: <true glb> <out png>"""
import sys, numpy as np
from pygltflib import GLTF2
from PIL import Image, ImageDraw
g = GLTF2().load(sys.argv[1]); blob = g.binary_blob()
def acc(i):
    a = g.accessors[i]; bv = g.bufferViews[a.bufferView]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a.type]; ct = {5126: 'f4', 5123: 'u2', 5125: 'u4', 5121: 'u1'}[a.componentType]
    return np.frombuffer(blob, ct, a.count * n, (bv.byteOffset or 0) + (a.byteOffset or 0)).reshape(a.count, n)
mesh = [m for m in g.meshes if m.name.startswith('MP')][0]; pr = mesh.primitives[0]
P = acc(pr.attributes.POSITION); UV = acc(pr.attributes.TEXCOORD_0); T = acc(pr.indices).reshape(-1, 3)
J = acc(pr.attributes.JOINTS_0); Wt = acc(pr.attributes.WEIGHTS_0)
skin = g.skins[0]; names = [g.nodes[j].name for j in skin.joints]
dom = np.array([names[J[i][np.argmax(Wt[i])]] for i in range(len(P))])
S = 1024
for k in 'cd':
    im = Image.open(f'source/true/skins/pm2d_{k}.png').convert('RGB').resize((S, S)); d = ImageDraw.Draw(im)
    cols = {}
    for t in T:
        b = dom[t[0]]
        key = 'arm' if any(s in b for s in ('UpperArm', 'Forearm', 'Clavicle')) else 'hand' if ('Hand' in b or 'Finger' in b) else 'leg' if any(s in b for s in ('Thigh', 'Calf')) else 'foot' if ('Foot' in b or 'Toe' in b) else 'head' if ('Head' in b or 'Neck' in b or 'Pony' in b) else 'skirt' if b.startswith('Bone') else 'torso'
        c = {'arm': (255, 0, 0), 'hand': (255, 255, 0), 'leg': (0, 0, 255), 'foot': (0, 255, 255), 'head': (255, 0, 255), 'skirt': (0, 255, 0), 'torso': (255, 128, 0)}[key]
        d.polygon([(UV[i][0] * S, UV[i][1] * S) for i in t], outline=c)
    im.save(sys.argv[2].replace('.png', f'_{k}.png'))
print('ok')
