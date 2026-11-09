"""Cross sections of the right fist across the knuckle line. Args: out.png gx,gy,gz r [scale x y z about wrist]"""
import json, sys, numpy as np
from PIL import Image, ImageDraw
J = json.load(open('work/hands_v1.json'))['joints']['R']; Z = np.load('work/faces.npz'); T = Z['bc']
W = np.array(J['wrist']); T = T[np.linalg.norm(T.mean(1) - (W + [-.05, -.1, -.15]), axis=1) < .26]
I, Pk = np.array(J['finger2-1']), np.array(J['finger5-1']); kn = (I - Pk) / np.linalg.norm(I - Pk); mid = (I + Pk) / 2
e1 = np.cross(kn, np.array(J['finger3-1']) - W); e1 /= np.linalg.norm(e1); e2 = np.cross(kn, e1)
G = np.array([float(x) for x in sys.argv[2].split(',')]); R = float(sys.argv[3])
S = 2200; c0 = (G - mid) @ np.array([e1, e2]).T if False else np.array([(G - mid) @ e1, (G - mid) @ e2])
im = Image.new('RGB', (1500, 500), (20, 20, 24)); d = ImageDraw.Draw(im)
for k, a in enumerate((-.045, 0, .045)):
    ox = 250 + 500 * k; oy = 250; Ap = (G - mid) @ kn + a
    def P(p): q = p - mid; return (ox + ((q @ e1) - c0[0]) * S, oy + ((q @ e2) - c0[1]) * S)
    for t in T:
        s = (t - mid) @ kn - Ap; pts = []
        for i in range(3):
            j = (i + 1) % 3
            if s[i] * s[j] < 0: pts.append(t[i] + (t[j] - t[i]) * s[i] / (s[i] - s[j]))
        if len(pts) == 2: d.line([P(pts[0]), P(pts[1])], fill=(240, 200, 120), width=2)
    d.ellipse([ox - R * S, oy - R * S, ox + R * S, oy + R * S], outline=(90, 220, 255))
    w = np.array(J['finger3-1']); d.ellipse([*(np.array(P(W)) - 5), *(np.array(P(W)) + 5)], fill=(255, 60, 60))
    d.text((ox - 200, 10), f'axial {a:+.3f}; red = wrist', fill=(255, 255, 255))
im.save(sys.argv[1])
