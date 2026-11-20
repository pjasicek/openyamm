"""Runtime maps from the Meshy retexture (meshy/retexture_v1) into textures/: base colour 2048 (+ baked AO and skin
detail), normal 1024 and metal/roughness 1024 (R = colour-variant mask, G = rough, B = metal), with the staff packed in
(one material, one draw per creature): the body atlas is squeezed horizontally to u * BODY_U (an axis scale keeps the
tangent directions, so the normal map stays valid) and the staff's wood (textures/staff_basecolor.png, staff u range
[0, STAFF_U_SPAN) wrapped) fills the strip [STRIP_U0, STRIP_U1] on the right, edge-extended into the margins; flat
normal, roughness 0.8, no metal, no tint mask. export_runtime.py remaps the UVs from textures/atlas_pack.json. The mask covers the cloth that the native
palettes 801/802/803 recolour (mantle, pouches, trousers: every green texel, so the ochre pouch strings stay and
green painted onto neighbouring regions is recoloured too). textures/tints.json gets each tier's linear tint so that the masked mean colour
becomes the native palette ramp's mean (shader: colour = luminance * tint inside the mask)."""
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures'); M = os.path.join(HERE, 'meshy', 'retexture_v1')
PAL = os.path.join(HERE, '..', 'new_sorpigal_3d_stage1_20261006', 'pmn2', 'source', 'palettes')
base = Image.open(os.path.join(M, 'texture_urls_0_base_color.png')).convert('RGB')
# Meshy paints skin as near-flat albedo (no creases, no depth): bake AO in (wide 15 cm + tight 3 cm, work/ao_*.png
# from bake_ao.py), warmer and stronger on skin, plus low-frequency tone mottling and fine pore noise on skin texels.
from scipy import ndimage
c = np.asarray(base, np.float32) / 255.0
hsv = np.asarray(base.convert('HSV'), np.float32)
h, sat, val = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255
skin = ((h > 8) & (h < 40) & (sat > 0.2) & (sat < 0.7) & (val > 0.45)).astype(np.float32)
skin = ndimage.gaussian_filter(skin, 1.5)
wide = np.asarray(Image.open(os.path.join(HERE, 'work', 'ao_wide.png')).convert('L'), np.float32) / 255.0
tight = np.asarray(Image.open(os.path.join(HERE, 'work', 'ao_tight.png')).convert('L'), np.float32) / 255.0
occ = np.clip(wide, 0, 1) ** 0.9 * np.clip(tight, 0, 1) ** 0.7
k = 0.45 + 0.2 * skin                                        # AO strength: skin 0.65, rest 0.45
shade = 1 - k * (1 - occ)
warm = np.stack([shade ** 0.75, shade, shade ** 1.15], -1)    # skin shadows go warm/red instead of grey
c = c * (shade[..., None] * (1 - skin[..., None]) + warm * skin[..., None])
rng = np.random.default_rng(7)
mottle = ndimage.gaussian_filter(rng.normal(0, 1, c.shape[:2]), 18); mottle /= mottle.std()
pores = ndimage.gaussian_filter(rng.normal(0, 1, c.shape[:2]), 0.8); pores /= pores.std()
tone = 1 + skin * (0.05 * mottle + 0.025 * pores)
c = c * tone[..., None]
c[..., 0] *= 1 + 0.035 * skin * np.clip(mottle, 0, None)    # redder blotches
base = Image.fromarray((np.clip(c, 0, 1) * 255).astype(np.uint8))
normal = np.array(Image.open(os.path.join(M, 'texture_urls_0_normal.png')).convert('RGB').resize((1024, 1024), Image.LANCZOS))
rough = np.array(Image.open(os.path.join(M, 'texture_urls_0_roughness.png')).convert('L').resize((1024, 1024), Image.LANCZOS))
metal = np.array(Image.open(os.path.join(M, 'texture_urls_0_metallic.png')).convert('L').resize((1024, 1024), Image.LANCZOS))

R = 1024
layout = json.load(open(os.path.join(HERE, 'work', 'uv_layout.json')))
cloth = {layout['regions'].index(n) for n in ('Mantle', 'PouchLeft', 'PouchRight', 'LegL', 'LegR')}
region = Image.new('L', (R, R), 0); draw = ImageDraw.Draw(region)
for r, pts in layout['faces']:
    if r in cloth:
        draw.polygon([(u * R, (1 - v) * R) for u, v in pts], fill=255, outline=255)
region = np.array(region.filter(ImageFilter.MaxFilter(5))) > 0          # cover the island bleed margin
small = np.array(base.resize((R, R), Image.LANCZOS)).astype(float)
# green cloth anywhere: Meshy also painted mantle/trouser green onto neighbouring regions (collar, hips under the tunic
# hem), which stayed green on the red/blue tiers. Green is unique to the recoloured cloth on this character.
mx = small.max(2); mn = small.min(2)
green = (small[..., 1] >= small[..., 0] * 1.02) & (small[..., 1] >= small[..., 2]) & (mx - mn > 0.07 * 255) & (mx > 25)
green = ndimage.binary_closing(green, iterations=2)
mask = Image.fromarray((green * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
mask = np.array(mask)
BODY_U, STRIP_U0, STRIP_U1, STAFF_U_SPAN = 1968 / 2048, 1976 / 2048, 2040 / 2048, 1.4
staff = np.asarray(Image.open(os.path.join(T, 'staff_basecolor.png')).convert('RGB'))


def pack(body, staff_texel):
    """body: H x N x C map in the original UVs; staff_texel(rows, cols) -> staff colours at those staff-image texels."""
    n = body.shape[1]; w = int(round(n * BODY_U))
    out = np.empty_like(body)
    out[:, :w] = np.asarray(Image.fromarray(body).resize((w, body.shape[0]), Image.LANCZOS)).reshape(body.shape[0], w, -1)
    u = ((np.arange(w, n) + 0.5) / n - STRIP_U0) / (STRIP_U1 - STRIP_U0) * STAFF_U_SPAN
    u = np.clip(u, 0, STAFF_U_SPAN) % 1.0
    rows = np.minimum(((np.arange(body.shape[0]) + 0.5) / body.shape[0] * staff.shape[0]).astype(int), staff.shape[0] - 1)
    cols = np.minimum((u * staff.shape[1]).astype(int), staff.shape[1] - 1)
    out[:, w:] = staff_texel(rows[:, None], cols[None, :])
    return out


# image row 0 = v 1 for both the body maps and staff_basecolor.png, so rows map straight across
big = np.asarray(Image.fromarray(staff).resize((staff.shape[1], 2048), Image.LANCZOS))
Image.fromarray(pack(np.asarray(base), lambda r, c: big[r, c])).save(os.path.join(T, 'pmn2_a_basecolor.png'))
Image.fromarray(pack(normal, lambda r, c: np.broadcast_to(np.array([128, 128, 255], np.uint8), r.shape[:1] + c.shape[1:] + (3,)))).save(
    os.path.join(T, 'pmn2_normal_1k.png'))
Image.fromarray(pack(np.stack([mask, rough, metal], 2), lambda r, c: np.broadcast_to(np.array([0, 204, 0], np.uint8), r.shape[:1] + c.shape[1:] + (3,)))).save(
    os.path.join(T, 'pmn2_metal_rough_1k.png'))
json.dump({'body_u': BODY_U, 'strip_u0': STRIP_U0, 'strip_u1': STRIP_U1, 'staff_u_span': STAFF_U_SPAN},
          open(os.path.join(T, 'atlas_pack.json'), 'w'), indent=1)

lin = lambda c: np.where(c / 255 <= 0.04045, c / 255 / 12.92, ((c / 255 + 0.055) / 1.055) ** 2.4)
luma = np.array([0.2126, 0.7152, 0.0722])
src = lin(small[(mask > 128) & region]).mean(0)                # cloth islands only, not green padding
pal = {k: np.frombuffer(open(os.path.join(PAL, f'pal{k}.act'), 'rb').read()[:768], np.uint8).reshape(256, 3).astype(int)
       for k in (801, 802, 803)}
ramp = np.where((pal[801] != pal[802]).any(1) | (pal[802] != pal[803]).any(1))[0]
tints = {tier: (lin(pal[k][ramp]).mean(0) / float(src @ luma)).round(4).tolist() for tier, k in (('a', 801), ('b', 802), ('c', 803))}
json.dump({'mask_texels': int((mask > 128).sum()), 'source_linear_mean': src.round(4).tolist(), 'tints': tints},
          open(os.path.join(T, 'tints.json'), 'w'), indent=1)
print('MAPS mask texels', int((mask > 128).sum()), 'source mean', src.round(4).tolist(), 'tints', tints)
