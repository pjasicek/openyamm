"""Trace the guard's halberd head from the native broadside frame guawinc0 (MM6 gua hit c).

Iron pixels (low saturation, dark) are split by the shaft line into the crescent axe blade and the opposite star
spike. Outlines are expressed in a shaft frame: u along the shaft from the gem cap downwards, v across it (axe side
negative), both in units of the native body height, so make_halberd.py can scale them to the model.
Writes work/halberd_outline.json and review/halberd_trace.png."""
import json
import os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMES = os.path.join(HERE, '..', 'new_sorpigal_3d_stage1_20261006', 'gua', 'source', 'frames')
BODY_PX = 252.0                     # native standing height, helmet top to sole (guastaa0), px


def load(name):
    return np.array(Image.open(os.path.join(FRAMES, name + '.png')).convert('RGBA')).astype(float)


def trace(mask):
    """Moore-neighbour outer boundary of the largest component, as (row, col) points."""
    lab, n = ndimage.label(mask)
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    m = lab == (1 + int(np.argmax(sizes)))
    m = np.pad(m, 1)
    r0, c0 = np.argwhere(m)[0]
    nb = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
    pts = [(r0, c0)]
    cur, back = (r0, c0), 6
    for _ in range(100000):
        for k in range(8):
            d = (back + 1 + k) % 8
            q = (cur[0] + nb[d][0], cur[1] + nb[d][1])
            if m[q]:
                back = (d + 4) % 8
                cur = q
                break
        if cur == (r0, c0):
            break
        pts.append(cur)
    return np.array(pts, float) - 1


def simplify(p, eps):
    """Douglas-Peucker on a closed polygon."""
    def dp(a):
        if len(a) < 3:
            return a
        s, e = a[0], a[-1]
        d = e - s
        nrm = np.hypot(*d) or 1.0
        dist = np.abs(d[0] * (a[:, 1] - s[1]) - d[1] * (a[:, 0] - s[0])) / nrm
        i = int(np.argmax(dist))
        if dist[i] > eps:
            return np.vstack([dp(a[:i + 1])[:-1], dp(a[i:])])
        return np.vstack([s, e])
    k = int(np.argmax(np.hypot(*(p - p.mean(0)).T)))
    p = np.roll(p, -k, 0)
    j = int(np.argmax(np.hypot(*(p - p[0]).T)))          # split the ring at its two most distant points
    return np.vstack([dp(p[:j + 1])[:-1], dp(np.vstack([p[j:], p[:1]]))[:-1]])


def main():
    a = load('guawinc0')
    rgb, al = a[..., :3], a[..., 3] > 0
    mx, mn = rgb.max(-1), rgb.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1)
    iron = al & (sat < 0.28) & (mx < 200)
    gem = al & (rgb[..., 2] > rgb[..., 0] + 40) & (rgb[..., 2] > 120)
    brown = al & (rgb[..., 0] > rgb[..., 2] + 25) & (mx < 150) & (sat > 0.35)
    head = np.zeros_like(iron)
    head[60:140, 66:134] = True                             # the halberd head (canvas px, frame top-left)
    head[60:100, 134:150] = True                            # spike point, above the shoulder mail
    iron &= head
    gy, gx = np.argwhere(gem).mean(0)
    # shaft axis: brown pixels below the head, fitted x = f(y)
    sh = np.argwhere(brown[165:240, 95:135]) + (165, 95)
    k, b = np.polyfit(sh[:, 0], sh[:, 1], 1)
    ax = np.array([1.0, k]) / np.hypot(1.0, k)               # (row, col) direction down the shaft
    top = np.array([gy, gx])
    shaft_px = None
    out = {'body_px': BODY_PX, 'gem': [0.0, 0.0]}
    rows, cols = np.nonzero(brown)
    for side, sel in (('axe', -1), ('spike', 1)):
        m = iron.copy()
        rr, cc = np.indices(m.shape)
        across = (cc - (k * rr + b)) * ax[0]               # signed perpendicular distance in px
        m &= (across * sel > 1.0)
        m = ndimage.binary_closing(m, iterations=1)
        m = ndimage.binary_fill_holes(m)
        big = ndimage.zoom(m.astype(float), 4, order=1) > 0.5
        p = trace(big) / 4.0
        p = simplify(p, 0.75)
        rel = p - top
        u = rel @ ax
        v = rel @ np.array([-ax[1], ax[0]])                # +v toward image right (spike side)
        out[side] = (np.stack([u, v], 1) / BODY_PX).tolist()
    # shaft: gem to butt in the hit frame is foreshortened; length taken from the genuine side view below
    out['shaft_axis_px'] = [float(k), float(b)]
    out['top_px'] = [float(top[0]), float(top[1])]           # gem centre (row, col), native px
    out['axis_px'] = [float(ax[0]), float(ax[1])]            # unit (row, col) down the shaft
    with open(os.path.join(HERE, 'work', 'halberd_outline.json'), 'w') as f:
        json.dump(out, f, indent=1)
    img = Image.fromarray(a.astype(np.uint8)).crop((60, 60, 140, 180)).resize((640, 960), Image.NEAREST)
    d = ImageDraw.Draw(img)
    for side, col in (('axe', (255, 0, 0)), ('spike', (0, 255, 0))):
        uv = np.array(out[side]) * BODY_PX
        pts = [tuple(((top + uu * ax + vv * np.array([ax[1], -ax[0]]) * -1)[::-1] - (60, 60)) * 8) for uu, vv in uv]
        d.line(pts + pts[:1], fill=col, width=2)
    img.save(os.path.join(HERE, 'review', 'halberd_trace.png'))
    for side in ('axe', 'spike'):
        uv = np.array(out[side])
        print(side, len(uv), 'u', uv[:, 0].min().round(3), uv[:, 0].max().round(3), 'v', uv[:, 1].min().round(3),
              uv[:, 1].max().round(3))


main()
