"""Torn edge and holes as a grid (numpy only): a signed distance in texels of a (S rows, T columns) mask, s=rows 0 root..1 rim. Worn along the rim, long vertical tears, a few slits above it."""
import numpy as np
from scipy import ndimage


def tear_field(S, T, seed, depth=0.1, periodic=True, holes=9, vertical=True):
    rng = np.random.default_rng(seed)
    mode = 'wrap' if periodic else 'nearest'
    n1 = ndimage.gaussian_filter1d(rng.normal(size=T), T / 14, mode=mode); n1 /= n1.std()
    n2 = ndimage.gaussian_filter1d(rng.normal(size=T), T / 60, mode=mode); n2 /= n2.std()
    n3 = ndimage.gaussian_filter1d(rng.normal(size=T), T / 170, mode=mode); n3 /= n3.std()
    h = depth * (1.0 + 0.45 * n1 + 0.42 * n2 + 0.3 * np.abs(n3) ** 1.5 * np.sign(n3))
    h = np.clip(h, 0.012, depth * 2.6)
    rows = (np.arange(S) + 0.5) / S
    mask = rows[:, None] < 1 - h[None, :]
    # slits: thin vertical holes just above the rim
    yy, xx = np.mgrid[0:S, 0:T]
    for k in range(holes):
        c = rng.integers(0, T); r = rng.uniform(1 - depth * 3.2, 1 - depth * 1.2) * S
        ax = rng.uniform(0.012, 0.03) * S; ay = rng.uniform(0.002, 0.006) * T
        dx = xx - c
        if periodic:
            dx = (dx + T // 2) % T - T // 2
        mask &= ((yy - r) / ax) ** 2 + (dx / ay) ** 2 > 1
    sdf = ndimage.distance_transform_edt(mask) - ndimage.distance_transform_edt(~mask)
    # jitter: long fibres
    j1 = ndimage.gaussian_filter(rng.normal(size=(S, T)), (S / 40, T / 700), mode=('nearest', mode)); j1 /= j1.std()
    j2 = ndimage.gaussian_filter(rng.normal(size=(S, T)), (S / 140, T / 1400), mode=('nearest', mode)); j2 /= j2.std()
    return sdf + 7 * j1 + 3 * j2
