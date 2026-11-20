"""Learn a normal-state colour curve without copying or moving its drawing."""

import numpy as np
from scipy import ndimage


LUMA = np.asarray([.2126, .7152, .0722], dtype=np.float64)


def weighted_quantiles(values, weights, probabilities):
    keep = weights > 0
    values, weights = values[keep], weights[keep]
    order = np.argsort(values, kind="stable")
    values, weights = values[order], weights[order]
    positions = (np.cumsum(weights) - weights * .5) / weights.sum()
    return np.interp(probabilities, positions, values)


def learn_palette(normal, colour, glyph_mask):
    """Return a 256-entry RGB LUT indexed by the canonical image's luminance.

    The source and reference canvases may differ. Only colour distributions are
    measured, so reference placement, contours and internal edges never enter
    the result. Alpha-squared weighting suppresses unreliable transparent fringe
    RGB. Glyphs are excluded from grading statistics and protected at application.
    """
    reference = np.asarray(normal, dtype=np.float64)
    canonical = np.asarray(colour, dtype=np.float64)
    reference_rgb = reference[:, :, :3]
    canonical_rgb = canonical[:, :, :3]
    reference_luma = reference_rgb @ LUMA
    canonical_luma = canonical_rgb @ LUMA

    red, green, blue = [reference_rgb[:, :, index] for index in range(3)]
    reference_glyph = (green > red * 1.08 + 3) & (green > blue * 1.12 + 3) & (green > 30)
    reference_weight = (reference[:, :, 3] / 255) ** 2 * ~reference_glyph
    canonical_weight = (canonical[:, :, 3] / 255) ** 2 * (1 - glyph_mask)
    if reference_weight.sum() < 1 or canonical_weight.sum() < 1:
        raise ValueError("Insufficient foreground pixels for a normal-state colour reference")

    probabilities = np.linspace(.001, .999, 257)
    source_levels = weighted_quantiles(canonical_luma, canonical_weight, probabilities)
    target_levels = weighted_quantiles(reference_luma, reference_weight, probabilities)
    # Retain the darkest target for repeated source levels, particularly black
    # ink. Averaging duplicate black samples would lift the outlines again.
    source_levels, indices = np.unique(source_levels, return_index=True)
    mapped_luma = np.interp(np.arange(256), source_levels, target_levels[indices])

    # Estimate the actual reference colour at each luminance. Smoothing colour
    # offsets (RGB minus luminance) leaves the contrast curve above intact.
    bins = np.rint(reference_luma).astype(np.uint8).ravel()
    weights = reference_weight.ravel()
    counts = np.bincount(bins, weights=weights, minlength=256)
    density = ndimage.gaussian_filter1d(counts, 3, mode="nearest")
    valid = density > density.max() * 1e-7
    grid = np.arange(256)
    palette = np.empty((256, 3), dtype=np.float64)
    for channel in range(3):
        difference = (reference_rgb[:, :, channel] - reference_luma).ravel()
        totals = np.bincount(bins, weights=weights * difference, minlength=256)
        smoothed = ndimage.gaussian_filter1d(totals, 3, mode="nearest")
        offsets = np.interp(grid, grid[valid], smoothed[valid] / density[valid])
        palette[:, channel] = mapped_luma + np.interp(mapped_luma, grid, offsets)
    return np.uint8(np.clip(np.rint(palette), 0, 255))


def apply_palette(colour, palette, glyph_mask):
    pixels = np.asarray(colour).copy()
    rgb = pixels[:, :, :3].astype(np.float64)
    luminance = rgb @ LUMA
    graded = np.stack([np.interp(luminance, np.arange(256), palette[:, channel])
                       for channel in range(3)], axis=2)
    keep = glyph_mask[:, :, None]
    pixels[:, :, :3] = np.uint8(np.clip(np.rint(graded * (1 - keep) + rgb * keep), 0, 255))
    return pixels
