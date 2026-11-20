"""Median albedo of the bare arm skin (body set: vertices weighted mostly to the upper arms/forearms) and of the cheeks
(head set: face front between the eyes and the beard). Args: <body_tex glb> [body png] [head png]"""
import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb
from PIL import Image
glb = Glb(Path(sys.argv[1])); doc = glb.json
B = np.asarray(Image.open(sys.argv[2] if len(sys.argv) > 2 else 'textures/sven_tp_basecolor_graded.png').convert('RGB')).astype(float)
H = np.asarray(Image.open(sys.argv[3] if len(sys.argv) > 3 else 'textures/sven_tp_head_basecolor.png').convert('RGB')).astype(float)
names = [n.get('name') for n in doc['nodes']]
skin = doc['skins'][0]; jn = [names[j] for j in skin['joints']]
mesh = next(m for m in doc['meshes'])
for prim in mesh['primitives']:
    mat = doc['materials'][prim['material']]['name']
    a = prim['attributes']
    P = glb.accessor(a['POSITION']); uv = glb.accessor(a['TEXCOORD_0'])
    J = glb.accessor(a['JOINTS_0']).astype(int); W = glb.accessor(a['WEIGHTS_0'])
    dom = np.array([jn[J[v][np.argmax(W[v])]] for v in range(len(P))])
    img = H if mat.endswith('Head') else B
    S = img.shape[0]
    def samp(m):
        return img[((uv[m, 1] % 1) * (S - 1)).astype(int), ((uv[m, 0] % 1) * (S - 1)).astype(int)]
    if not mat.endswith('Head'):
        m = np.isin(dom, ['Bip01 L Forearm', 'Bip01 R Forearm', 'Bip01 L UpperArm', 'Bip01 R UpperArm'])
        c = samp(m); r, g, b = c.T
        sk = (r > g) & (g > b) & (r - b > 30)
        print(mat, 'arm verts', m.sum(), 'skin-hued', sk.sum(), 'median', np.median(c[sk], 0).round(), 'lum p25/50/75', np.percentile(c[sk].mean(1), [25, 50, 75]).round())
    else:
        print(mat, 'bbox', P.min(0).round(3), P.max(0).round(3))
        hand = np.isin(dom, [n for n in jn if any(k in n for k in ('Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))])
        c = samp(hand); print(mat, 'hand verts', hand.sum(), 'median', np.median(c, 0).round())
        # glTF y-up: face front = -z? report by height band
        yz = P[:, 1]; fwd = P[:, 2]
        top = yz.max()
        cheek = (~hand) & (yz < top - 0.13) & (yz > top - 0.19) & (fwd > np.percentile(fwd[~hand & (yz > top - 0.3)], 85))
        c = samp(cheek); print(mat, 'cheek verts', cheek.sum(), 'median', np.median(c, 0).round())
