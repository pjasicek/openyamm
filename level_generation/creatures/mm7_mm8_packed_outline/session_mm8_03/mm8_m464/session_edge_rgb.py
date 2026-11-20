"""Local faint-fringe RGB repair; preserves every supplied alpha and opaque material pixel."""
import numpy as np
from PIL import Image
from scipy import ndimage


def correct(image):
    pixels = np.array(image)
    alpha = pixels[:, :, 3]
    stable = alpha >= 128
    if not stable.any():
        return image.copy()
    distance, nearest = ndimage.distance_transform_edt(~stable, return_indices=True)
    rgb = pixels[:, :, :3].astype(float)
    reference = rgb[nearest[0], nearest[1]]
    chroma = rgb - rgb.mean(axis=2, keepdims=True)
    target_chroma = reference - reference.mean(axis=2, keepdims=True)
    affected = ((alpha > 0) & (alpha <= 96) & (distance <= 4)
                & (np.max(np.abs(chroma - target_chroma), axis=2) > 70)
                & (rgb.max(axis=2) - rgb.min(axis=2) >= 80))
    pixels[:, :, :3][affected] = np.round(reference[affected]).astype(np.uint8)
    result = Image.fromarray(pixels)
    assert np.array_equal(np.asarray(result)[:, :, 3], alpha)
    return result
