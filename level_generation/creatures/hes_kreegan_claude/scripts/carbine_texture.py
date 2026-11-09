"""hkr pulse carbine texture (512), painted from make_carbine.py's UV layout (concept fam_troopers.png: ivory bone,
amber resin, dark joints, orange glow): the body loft takes u = around (0..0.75 -> angle, 0 = the gun's right side,
quarter = top), v = along (the stock's butt 0 -> the muzzle 1); the grip strip x 0.78-0.86 / v 0.30-0.55, the
trigger guard texel (0.90, 0.40), the rear cap (0.80, 0.02), the muzzle's inner lip (0.80, 0.98).
v2 (work/carbine_layout.json from make_carbine.py): zones along the main loft (metres in the rifle frame): a ribbed
bone stock, the amber resin receiver between ivory bone side plates with gold edges, the ivory barrel housing with
gold rib rings and an orange seam, the bone emitter with a gold rim; the fore-grip bar (u 0.88-0.96) dark wrapped,
the struts and the fin ivory.
Writes textures/props/carbine.png and textures/hkr_carbine_{basecolor,normal,metal_rough,material_classes}.png.
Args: none"""
import json, os, math
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAY = json.load(open(os.path.join(HERE, 'work', 'carbine_layout.json')))
Y0, Y1 = LAY['Y0'], LAY['Y1']
N = 512
v, u = np.mgrid[0:N, 0:N]; v = 1 - (v + 0.5) / N; u = (u + 0.5) / N
y = Y0 + v * (Y1 - Y0); th = 2 * math.pi * np.clip(u / 0.75, 0, 1)
rng = np.random.default_rng(3)
noise = gaussian_filter(rng.random((N, N)), 2.0); noise = (noise - noise.mean()) / (noise.std() + 1e-9)
fine = gaussian_filter(rng.random((N, N)), 0.7); fine = (fine - fine.mean()) / (fine.std() + 1e-9)
IV = np.array([222, 208, 176]) / 255; AMB = np.array([176, 96, 30]) / 255; DK = np.array([62, 40, 28]) / 255
GD = np.array([200, 158, 76]) / 255; GL = np.array([255, 140, 40]) / 255
col = np.zeros((N, N, 3)); hgt = np.zeros((N, N)); rough = np.full((N, N), 0.5); cls = np.zeros((N, N), np.uint8)
side = np.abs(np.cos(th)) > 0.70                                         # the receiver's bone side plates
zone = np.select([y < LAY['stock_end'], y < LAY['receiver_end'], y < LAY['muzzle_start']], [0, 1, 3], 4)
ribs = (np.abs(((y - Y0) / 0.024) % 1 - 0.5) < 0.12) & (zone == 0)
col[:] = IV * (0.95 + 0.04 * noise)[..., None]
cls[:] = 5
rec = (zone == 1) & ~side
amber = AMB * (0.85 + 0.12 * noise + 0.06 * fine)[..., None]
veins = np.clip(1 - np.abs(np.sin(y * 90 + th * 2 + noise)) * 4, 0, 1)
col[rec] = (amber * (1 - 0.35 * veins[..., None]))[rec]; rough[rec] = 0.3; cls[rec] = 11
edge = (zone == 1) & (np.abs(np.abs(np.cos(th)) - 0.70) < 0.035)        # gold edges of the side plates
col[edge] = GD; rough[edge] = 0.35; cls[edge] = 9
col[ribs] = col[ribs] * 0.72; hgt[ribs] = -0.6
ring = np.zeros_like(y, bool)
for r in LAY['ribs']:
    ring |= (y > r - 0.003) & (y < r + 0.015)
col[ring & (zone == 3)] = GD; rough[ring & (zone == 3)] = 0.35; cls[ring & (zone == 3)] = 9; hgt[ring & (zone == 3)] = 0.4
muz = zone == 4
rim = muz & (y > Y1 - 0.03)
col[rim] = GD; rough[rim] = 0.35; cls[rim] = 9
seam = (zone == 3) & (np.abs(np.sin(th)) > 0.97) & ~ring                # an orange seam along the barrel's top/bottom
col[seam] = GL; cls[seam] = 11
# strips outside the loft: grip, fore-grip bar, struts, fin, trigger guard, caps
gx = u > 0.76
col[gx] = (IV * (0.93 + 0.05 * noise)[..., None])[gx]; rough[gx] = 0.5; cls[gx] = 5
gr = (u > 0.78) & (u < 0.86) & (v > 0.27) & (v < 0.56)
col[gr] = (np.array([96, 58, 32]) / 255 * (0.9 + 0.1 * noise)[..., None])[gr]; rough[gr] = 0.6; cls[gr] = 11
grip_rib = gr & (np.abs(((v - 0.30) / 0.03) % 1 - 0.5) < 0.15)
col[grip_rib] = col[grip_rib] * 0.7; hgt[grip_rib] = -0.5
fb = (u > 0.87) & (u < 0.97) & (v > 0.02) & (v < 0.28)
stripe = np.abs(((v - 0.05) / 0.02 + (u - 0.88) / 0.08) % 1 - 0.5) < 0.18
col[fb] = (DK * (0.9 + 0.15 * noise)[..., None] * np.where(stripe, 0.75, 1.0)[..., None])[fb]; rough[fb] = 0.75; cls[fb] = 8
tg = (u > 0.88) & (u < 0.92) & (v > 0.38) & (v < 0.42); col[tg] = GD; cls[tg] = 9
cap = (u > 0.78) & (u < 0.82) & (v < 0.04); col[cap] = IV
lip = (u > 0.78) & (u < 0.82) & (v > 0.96); col[lip] = DK
col = np.clip(col, 30 / 255, 243 / 255)
hgt = hgt + 0.15 * fine
gy, gxx = np.gradient(gaussian_filter(hgt, 0.8) * 0.002, 1.0 / (N / 0.8))
nrm = np.dstack([-gxx, gy, np.ones((N, N))]); nrm /= np.linalg.norm(nrm, axis=2, keepdims=True)
T = os.path.join(HERE, 'textures'); os.makedirs(os.path.join(T, 'props'), exist_ok=True)
img = Image.fromarray((col * 255).round().astype(np.uint8))
img.save(os.path.join(T, 'props', 'carbine.png')); img.save(os.path.join(T, 'hkr_carbine_basecolor.png'))
Image.fromarray(((nrm * 0.5 + 0.5) * 255).round().astype(np.uint8)).save(os.path.join(T, 'hkr_carbine_normal.png'))
ao = 1 - 0.3 * (hgt < -0.3)
Image.fromarray((np.dstack([ao, rough, np.zeros_like(ao)]) * 255).round().astype(np.uint8)).save(os.path.join(T, 'hkr_carbine_metal_rough.png'))
Image.fromarray(cls, 'L').save(os.path.join(T, 'hkr_carbine_material_classes.png'))
print('CARBINETEX', N, 'zones', {int(z): int((zone == z).sum()) for z in (0, 1, 3, 4)})
