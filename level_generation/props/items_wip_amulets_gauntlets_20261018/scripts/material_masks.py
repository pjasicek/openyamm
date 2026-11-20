"""Discrete painted material classes; never infer metal from an albedo's brightness."""
import numpy as np

NAMES = ('metal', 'leather', 'cloth', 'horn', 'gem')
PALETTE = np.array([(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (0, 0, 0)], dtype=np.float32)
ROUGHNESS = np.array([0.35, 0.6, 0.85, 0.55, 0.18], dtype=np.float32)


def classify(rgb):
    distances = np.sum((np.asarray(rgb)[..., None, :] - PALETTE) ** 2, axis=-1)
    # An antialiased boundary halfway between two primary class colours has squared distance 0.5.
    if not np.isfinite(distances).all() or np.any(np.min(distances, axis=-1) > 0.500001):
        raise ValueError('Material masks must use flat red/green/blue/yellow/black classes, without shading')
    return np.argmin(distances, axis=-1)


def pbr(votes, unseen):
    classes = np.argmax(votes, axis=-1)
    classes[np.sum(votes, axis=-1) == 0] = NAMES.index(unseen)
    roughness = ROUGHNESS[classes]
    return np.stack([np.ones_like(roughness), roughness, (classes == 0).astype(np.float32)], axis=-1)


def interior_albedo(colours, votes, unseen):
    samples = np.asarray(colours)[np.argmax(votes, axis=-1) == NAMES.index(unseen)]
    if not len(samples):
        raise ValueError(f'No painted {unseen} samples define the unseen surface albedo')
    return np.median(samples, axis=0)


if __name__ == '__main__':
    np.testing.assert_array_equal(classify(PALETTE), np.arange(5))
    assert classify([[1, 0.5, 0]])[0] in (0, 3)
    assert classify([[0.5, 0, 0.5]])[0] in (0, 2)
    votes = np.eye(5, dtype=np.float32)
    maps = pbr(votes, 'leather')
    np.testing.assert_array_equal(maps[:, 2], [1, 0, 0, 0, 0])
    np.testing.assert_array_equal(maps[:, 1], ROUGHNESS)
    np.testing.assert_array_equal(pbr(np.zeros((1, 5)), 'cloth')[0], [1, ROUGHNESS[2], 0])
    votes[1, 0] = 0.9
    assert pbr(votes, 'leather')[1, 2] == 0
    colours = np.array([[0.8, 0.8, 0.8], [0.2, 0.1, 0.04], [0.4, 0.2, 0.08]])
    classes = np.eye(5)[[0, 1, 1]]
    np.testing.assert_allclose(interior_albedo(colours, classes, 'leather'), [0.3, 0.15, 0.06])
    try:
        interior_albedo(colours, classes, 'cloth')
    except ValueError:
        pass
    else:
        raise AssertionError('An unpainted material silently supplied an interior colour')
    for invalid in (np.full((1, 3), 0.5), np.full((1, 3), np.nan)):
        try:
            classify(invalid)
        except ValueError:
            continue
        raise AssertionError('Invalid material palette accepted')
    print('Material mask self-check passed: all five classes, mixed votes, unseen cloth and invalid inputs.')
