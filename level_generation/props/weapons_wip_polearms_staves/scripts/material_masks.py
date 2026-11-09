"""Physical material regions for the sculptural staff ornaments, independent of painted illumination."""
import numpy as np


def metal_mask(design, base, pixels, positions):
    red, green, blue = np.moveaxis(base, -1, 0)
    gold = (red > blue * 1.4) & (green > blue * 1.2) & (red > green * 1.05) & (red < green * 1.6)
    result = np.zeros(base.shape[:2], np.float32)
    kind = design.get('head_material')
    if kind in ('ram_bone', 'green_crystal', 'tentacle'):
        height = positions[:, 2]
        normalized = (height - height.min()) / max(float(np.ptp(height)), 1e-6)
        colours = gold[pixels[:, 1], pixels[:, 0]]
        values = colours & (normalized < .26) if kind == 'ram_bone' else colours & (normalized < .24)
        if kind == 'tentacle':
            silver = ((base.max(axis=-1) - base.min(axis=-1)) < .13) & (blue > .45)
            values = (silver[pixels[:, 1], pixels[:, 0]] & (normalized > .4)) | (colours & (normalized < .12))
        result[pixels[:, 1], pixels[:, 0]] = values
    elif kind == 'gold_silver':
        enamel = (blue > red * 1.1) | ((red > green * 1.7) & (red > blue * 1.5))
        result[:] = ~enamel
    elif kind == 'serpent':
        # Yellow ventral scales belong to the snake; gold is the narrow central rod inside its coils.
        xy = positions[:, :2]
        centre = (xy.min(axis=0) + xy.max(axis=0)) / 2
        radius = np.linalg.norm(xy - centre, axis=1)
        z = positions[:, 2]
        rod = (radius < np.ptp(xy[:, 0]) * .19) & (z < z.min() + np.ptp(z) * .8)
        result[pixels[:, 1], pixels[:, 0]] = gold[pixels[:, 1], pixels[:, 0]] & rod
    elif kind in ('swamp', 'gold_bone'):
        result[:] = gold
    elif kind == 'spirit':
        silver = ((base.max(axis=-1) - base.min(axis=-1)) < .16) & (base.mean(axis=-1) > .35)
        z = positions[:, 2]
        region = z > z.min() + float(np.ptp(z)) * .14
        values = (gold | silver)[pixels[:, 1], pixels[:, 0]] & region
        result[pixels[:, 1], pixels[:, 0]] = values
    else:
        result[:] = design.get('metallic', 0)
    return result


if __name__ == '__main__':
    rgb = np.array([[[.7, .5, .2], [.7, .5, .2], [.1, .3, .7]]])
    pix = np.array([[0, 0], [1, 0], [2, 0]])
    pos = np.array([[0, 0, 0], [0, 0, 1], [0, 0, .1]])
    assert metal_mask({'head_material': 'ram_bone'}, rgb, pix, pos).tolist() == [[1, 0, 0]]
