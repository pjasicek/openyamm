"""Local magenta matting for reviewed opaque cutouts, including intentional purple interiors.

Uses the creature workflow's foreground/background estimation and RGB unmixing. Spatial core selection avoids
the goblin extractor's no-purple-material assumption. These thresholds must be reviewed on each batch; this
is not an automatic solution for magenta translucent effects or foreground indistinguishable from the matte.
"""
import numpy as np
from PIL import Image
from scipy import ndimage


def extract(image, background_distance=.03, foreground_distance=.16, core_radius=3, fringe_radius=8,
            preserve_thin_lines=False):
    c = np.array(image.convert('RGB'), dtype=float) / 255
    key = np.array([1.0, 0.0, 1.0])
    distance = np.sqrt(((c - key) ** 2).sum(axis=2))
    background = distance <= background_distance
    foreground = distance >= foreground_distance
    core = ndimage.binary_erosion(foreground, iterations=core_radius)
    # Thin strings/tips cannot survive erosion. Add foreground seeds whose color
    # has no excess magenta, avoiding the purple mixed edge as an opaque seed.
    # Intentional purple interiors still use the ordinary spatially eroded core.
    chroma = np.minimum(c[:, :, 0], c[:, :, 2]) - c[:, :, 1]
    thin_lines = foreground & (chroma <= .04) if preserve_thin_lines else np.zeros_like(core)
    core |= thin_lines
    assert core.any() and background.any(), 'Need actual foreground and magenta samples; inspect raw image'
    to_core, indices = ndimage.distance_transform_edt(~core, return_indices=True)
    _, bg_indices = ndimage.distance_transform_edt(~background, return_indices=True)
    f, b = c[indices[0], indices[1]], c[bg_indices[0], bg_indices[1]]
    vector = f - b
    alpha = np.clip(((c - b) * vector).sum(axis=2) / np.maximum((vector * vector).sum(axis=2), 1e-8), 0, 1)
    alpha[core] = 1
    alpha[background | (to_core > fringe_radius)] = 0
    recovered = (c - (1 - alpha[:, :, None]) * b) / np.maximum(alpha[:, :, None], 1 / 255)
    # Compare uncertain colors with their local foreground, not a universal ban on purple chroma.
    expected_chroma = np.minimum(f[:, :, 0], f[:, :, 2]) - f[:, :, 1]
    excess = np.maximum(0, np.minimum(recovered[:, :, 0], recovered[:, :, 2]) - recovered[:, :, 1]
                        - expected_chroma - 2 / 255)
    recovered[:, :, 0] -= excess
    recovered[:, :, 2] -= excess
    recovered[core] = c[core]
    recovered[alpha == 0] = 0
    result = Image.fromarray(np.round(np.clip(np.dstack([recovered, alpha]), 0, 1) * 255).astype('uint8'))
    return result, dict(background_distance=background_distance, foreground_distance=foreground_distance,
        core_radius=core_radius, fringe_radius=fringe_radius, core_pixels=int(core.sum()),
        preserve_thin_lines=preserve_thin_lines, thin_line_seed_pixels=int(thin_lines.sum()),
        protected_core_rgb_unchanged=bool(np.array_equal(np.array(result)[:, :, :3][core],
                                                       np.array(image.convert('RGB'))[core])),
        limitation='Spatial seeds require visual review; bright magenta translucent material needs its own matte.')
