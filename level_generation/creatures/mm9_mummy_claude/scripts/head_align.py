"""Per tier and view: scale and offset that lay the head mesh's silhouette on the bust master's alpha (crown to chin). Writes work/head_align.json + review/head_align.png"""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parents[1]
D = np.load(HERE / 'work/joined.npz'); co, tri, head = D['co'], D['tri'], D['head']
T = tri[head == 1]
VIEWS = {'01_front': (1, 0, 0), '02_back': (-1, 0, 0), '03_left': (0, -1, 0), '04_right': (0, 1, 0)}
Z0 = 1.625   # below this the mask is ignored: necks differ
K = 4
def mask(px, py, W):
    im = Image.new('L', (W, W), 0); dr = ImageDraw.Draw(im)
    for t in T: dr.polygon([(px[i], py[i]) for i in t], fill=255)
    return np.asarray(im) > 0
res = {}
sheet = Image.new('RGB', (4 * 400, 3 * 400))
for ti, t in enumerate('ABC'):
    res[t] = {}
    for vi, (v, rx) in enumerate(VIEWS.items()):
        rx = np.array(rx, float)
        im = Image.open(HERE / f'references_head/tier{t}/{v}.png').convert('RGBA'); W = im.width // K
        al = np.asarray(im.resize((W, W), Image.BILINEAR))[..., 3] > 128
        ys = np.where(al.any(1))[0]; top = ys.min()
        best = (0, None)
        ux = co[:, 0] * rx[0] + co[:, 1] * rx[1]; zz = co[:, 2]
        hv = np.unique(T)
        for s in np.arange(1500, 3300, 30) / K:
            # crown on the master's crown
            oy = top + s * zz[hv].max()
            chin_row = int(oy - s * Z0)
            xs = ux[hv]
            for dy in range(-10, 11, 3):
                # horizontal centre by alpha centre over the head rows
                rows = al[max(top, 0):chin_row]
                if len(rows) == 0: continue
                cols = np.where(rows.any(0))[0]; cx = (cols.min() + cols.max()) / 2
                for dx in range(-14, 15, 3):
                    ox = cx + dx - s * (xs.min() + xs.max()) / 2
                    px = ox + s * ux; py = oy + dy - s * zz
                    m = mask(px, py, W)
                    r0, r1 = max(top - 4, 0), min(chin_row + dy, W)
                    a = al[r0:r1]; b = m[r0:r1]
                    iou = (a & b).sum() / max((a | b).sum(), 1)
                    if iou > best[0]: best = (iou, (s, ox, oy + dy))
        s, ox, oy = best[1]
        res[t][v] = [s * K, ox * K, oy * K]
        print(t, v, round(best[0], 3), [round(x, 1) for x in res[t][v]])
        px = ox + s * ux; py = oy - s * zz
        rgb = Image.new('RGB', (W, W), (70, 70, 70)); s_ = im.resize((W, W)); rgb.paste(s_, (0, 0), s_)
        d = ImageDraw.Draw(rgb)
        for tr in T[::3]:
            d.line([(px[i], py[i]) for i in (*tr, tr[0])], fill=(0, 255, 0))
        sheet.paste(rgb.resize((400, 400)), (vi * 400, ti * 400))
json.dump(res, open(HERE / 'work/head_align.json', 'w'), indent=1)
sheet.save(HERE / 'review/head_align.png')
