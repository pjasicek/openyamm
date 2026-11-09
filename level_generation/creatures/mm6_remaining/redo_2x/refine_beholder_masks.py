"""Refine enhanced eye ownership; native pixels only bound a coarse search region."""
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage

from prepare_run import REPO

ROOT = REPO/'level_generation/creatures/mm6_bh'
OUT = ROOT/'redo_2x'


def main():
    sources = json.loads((ROOT/'sources.json').read_text())['sources']
    registration = json.loads((OUT/'registration.json').read_text())
    palette = np.fromfile(REPO/'assets_dev/worlds/mm6/textures/pal670.act', np.uint8)[:768].reshape(256, 3)
    palette = palette.astype(int)
    iris_ids = np.minimum(palette[:, 0], palette[:, 2]) > palette[:, 1]+8
    records = {}
    for name, source in sources.items():
        path = OUT/'aligned_2x'/(name+'.png')
        image = Image.open(path).convert('RGBA')
        pixels = np.array(image)
        colors = pixels[:, :, :3].astype(float)
        weights = np.array(Image.open(OUT/'masks_2x'/(name+'.png'))).astype(float)/255
        native = np.array(Image.open(REPO/source['path']))
        yy, xx = np.where(iris_ids[native])
        roi = np.zeros(pixels.shape[:2], bool)
        if len(xx):
            offset = np.array(source['native_offset'][:2])*2-registration[name]['canvas_origin_px']
            lo = np.maximum([0, 0], np.array([xx.min(), yy.min()])*2+offset-24)
            hi = np.minimum(image.size, np.array([xx.max(), yy.max()])*2+offset+26)
            roi[lo[1]:hi[1], lo[0]:hi[0]] = True
        if name.startswith('bhwlk') and name[-1] == '2':
            ya, xa = np.where(pixels[:, :, 3] > 128)
            roi[:] = False
            roi[int(ya.min()+.23*np.ptp(ya)):int(ya.min()+.51*np.ptp(ya)),
                int(xa.min()+.76*np.ptp(xa)):xa.max()+1] = True
        if name.startswith('bhwlk') and name[-1] in '34':
            roi[:] = False
        r, g, b = colors.transpose(2, 0, 1)
        # Select actual enhanced iris chroma inside that ROI, including blue casting/death phases.
        seed = roi & (np.minimum(r, b) > g+6) & (pixels[:, :, 3] > 128)
        if seed.sum() < 8:
            seed = roi & (b > g+5) & (pixels[:, :, 3] > 128)
        labels, _ = ndimage.label(seed)
        sizes = np.bincount(labels.ravel())
        eye = np.zeros(roi.shape, np.uint8)
        if len(sizes) > 1:
            landmarks = registration[name]['placement_landmarks']
            if landmarks['names'].startswith(('eye center', 'eye remnant center')):
                center = np.array(landmarks['native'][0])*2-registration[name]['canvas_origin_px']
                valid = sizes >= 8
                valid[0] = False
                sy, sx = np.where(valid[labels])
                if not len(sx):
                    sy, sx = np.where(seed)
                closest = np.argmin((sx-center[0])**2+(sy-center[1])**2)
                component = labels[sy[closest], sx[closest]]
            else:
                component = 1+np.argmax(sizes[1:])
            selected = labels == component
            blue_labels, _ = ndimage.label(roi & (b > g+5) & (pixels[:, :, 3] > 128))
            connected = np.unique(blue_labels[selected])
            connected = connected[connected != 0]
            selected |= np.isin(blue_labels, connected)
            points = np.column_stack(np.where(selected)[::-1]).astype(np.int32)
            if len(points) >= 3:
                cv2.fillConvexPoly(eye, cv2.convexHull(points), 1)
        eye = ndimage.binary_dilation(eye, iterations=2) & roi
        iris = eye*np.clip((b-g-3)/12, 0, 1)
        # Purple-blue skull highlights are skin, never an iris region above the brow.
        outside_iris = weights[:, :, 2]*(~eye)
        weights[:, :, 0] += outside_iris
        weights[:, :, 2] -= outside_iris
        # Replace ownership only inside the eye hull. Keep pre-grade horn/skin segmentation elsewhere.
        weights[:, :, :3] *= 1-eye[:, :, None]
        weights[:, :, 2] += iris
        protected = eye*np.clip((colors.min(axis=2)-100)/35, 0, 1)
        if name in ['bhatkc0', 'bhatkd0', 'bhdthc0']:
            # Bright cyan is the pale native flare, not brown skull in a palette variant.
            flare = eye*np.clip((np.minimum(g, b)-r-10)/20, 0, 1)
            colors = colors*(1-.85*flare[:, :, None])+colors.max(axis=2, keepdims=True)*.85*flare[:, :, None]
            protected = np.maximum(protected, flare)
        weights *= 1-protected[:, :, None]
        weights /= np.maximum(1, weights.sum(axis=2, keepdims=True))
        mask = np.floor(np.clip(weights, 0, 1)*255).astype(np.uint8)
        mask[pixels[:, :, 3] == 0] = 0
        Image.fromarray(mask, 'RGBA').save(OUT/'masks_2x'/(name+'.png'))
        pixels[:, :, :3] = np.round(np.clip(colors, 0, 255)).astype(np.uint8)
        Image.fromarray(pixels, 'RGBA').save(path)
        records[name] = dict(enhanced_eye_hull_pixels=int(eye.sum()), protected_flare_pixels=int((protected>.5).sum()))
    (OUT/'review/eye_masks.json').write_text(json.dumps(records, indent=2)+'\n')
    print('Refined enhanced iris ownership for', len(records), 'poses; review required.')


if __name__ == '__main__':
    main()
