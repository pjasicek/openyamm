#!/usr/bin/env python3
"""Accessory texture set (staff + crown) from the Codex sheet (references_acc/acc_sheet.png, 1254 px, its rows not where the brief
asked: gem/ice 0-27 %, silver 28.5-47 %, wood 49-100 %) into the layout make_staff.py / make_crown.py use (1024 px):
rows 0-255 gem (left) / ice (right), 256-511 silver band, 512-1023 the pole (follow-up: the Codex pole tile). Wood and ice wrap left-right, wood also top-bottom
(cross-faded with a half-shifted copy near the edges). Normal map from luminance; ORM by region (R 1, G roughness, B metal).
Writes textures/yan_acc_{color,normal,orm}.png. Run from the project folder."""
import numpy as np
from PIL import Image
from scipy import ndimage
src = np.asarray(Image.open('references_acc/acc_sheet.png').convert('RGB')).astype(np.float32) / 255
H, W = src.shape[:2]
crop = lambda r0, r1, c0, c1, w, h: np.asarray(Image.fromarray((src[int(r0 * H):int(r1 * H), int(c0 * W):int(c1 * W)] * 255).astype('u1')).resize((w, h), Image.LANCZOS)).astype(np.float32) / 255


def wrap_x(a, band=48):
    """cross-fade with the copy shifted by half the width, near the left and right edges"""
    w = a.shape[1]; s = np.roll(a, w // 2, axis=1)
    x = np.arange(w); t = np.clip(1 - np.minimum(x, w - 1 - x) / band, 0, 1)[None, :, None]
    return a * (1 - t) + s * t


def wrap_y(a, band=48):
    h = a.shape[0]; s = np.roll(a, h // 2, axis=0)
    y = np.arange(h); t = np.clip(1 - np.minimum(y, h - 1 - y) / band, 0, 1)[:, None, None]
    return a * (1 - t) + s * t


gem = crop(0.0, 0.27, 0.0, 0.495, 512, 256)
ice = wrap_x(crop(0.0, 0.27, 0.505, 1.0, 512, 256))
silver = crop(0.285, 0.47, 0.0, 1.0, 1024, 256)
# follow-up r5: the pole is MM9's speckled grey-brown (references_acc/v2/pole_tile.png, Codex), grain along u (make_staff.py maps u
# along the pole in four lengths); its edges were not quite seamless, so both wraps are cross-faded
pole = np.asarray(Image.open('references_acc/v2/pole_tile.png').convert('RGB').resize((1024, 512), Image.LANCZOS)).astype(np.float32) / 255
wood = wrap_y(wrap_x(pole, 64), 48)
col = np.zeros((1024, 1024, 3), np.float32)
col[:256, :512] = gem; col[:256, 512:] = ice; col[256:512] = silver; col[512:] = wood
Image.fromarray((np.clip(col, 0, 1) * 255).astype('u1')).save('textures/yan_acc_color.png')
lum = ndimage.gaussian_filter(col @ np.array([0.3, 0.55, 0.15]), 1.2)
gy, gx = np.gradient(lum)
k = 3.0
n = np.dstack([-gx * k * 10, gy * k * 10, np.ones_like(lum)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
Image.fromarray(((n * 0.5 + 0.5) * 255).astype('u1')).save('textures/yan_acc_normal.png')
orm = np.zeros((1024, 1024, 3), np.uint8); orm[..., 0] = 255
orm[:256, :512, 1] = 40; orm[:256, 512:, 1] = 55               # gem, ice: glossy, not metal
orm[256:512, :, 1] = 90; orm[256:512, :, 2] = 230             # silver
orm[512:, :, 1] = 200                                           # the pole
# the niello in the knotwork grooves is rougher and not metal
dark = (col[256:512] @ np.array([0.3, 0.55, 0.15])) < 0.28
orm[256:512, :, 1][dark] = 170; orm[256:512, :, 2][dark] = 60
Image.fromarray(orm).save('textures/yan_acc_orm.png')
print('ACC', col.shape, 'silver dark share', round(float(dark.mean()), 3))
