"""Lathe profiles of the goblet and vase (map units, measured on the x2 sprites with small_measure.py), shared by
small_lathe.py (Blender) and small_lathe_compose.py (textures). Each point: (radius, z, last LOD that keeps it).
v of a point is its arc-length fraction along the full LOD0 profile, so every LOD samples the same texture rows."""
import math

PROFILES = {
    '7dec46': [(0, 0, 2), (10.0, 0, 2), (10.2, 1.0, 1), (9.8, 2.2, 2), (7.0, 3.6, 0), (4.0, 5.6, 2),
               (2.6, 7.2, 0), (3.1, 8.4, 1), (2.2, 9.6, 0), (1.8, 12.0, 2), (2.0, 14.2, 0), (2.7, 15.4, 2),
               (4.3, 16.6, 0), (6.4, 18.0, 1), (8.0, 19.8, 0), (8.9, 21.8, 2), (9.2, 24.0, 0),
               (9.6, 26.4, 1), (9.6, 27.6, 1), (9.25, 28.4, 0), (9.2, 40.0, 0), (9.0, 45.4, 2),
               (8.9, 46.0, 0), (8.4, 46.0, 2), (8.4, 45.0, 0), (8.5, 40.0, 0), (8.6, 28.0, 1),
               (8.4, 23.0, 0), (7.4, 20.6, 1), (5.0, 19.0, 0), (0, 18.4, 2)],
    'dec97': [(0, 0, 2), (7.6, 0, 2), (8.1, 0.8, 0), (8.3, 2.4, 1), (8.4, 4.5, 0), (9.0, 8.0, 0),
              (10.0, 11.5, 1), (11.4, 14.8, 0), (13.4, 18.0, 1), (15.0, 21.4, 0), (16.3, 24.8, 1),
              (17.4, 28.0, 0), (18.2, 31.3, 1), (18.6, 34.6, 2), (18.4, 38.0, 1), (17.3, 41.0, 0),
              (14.4, 44.6, 1), (11.0, 47.6, 0), (8.5, 50.5, 1), (7.7, 53.0, 2), (8.4, 55.0, 0),
              (10.5, 56.8, 1), (13.5, 58.5, 0), (15.2, 60.5, 1), (15.6, 62.5, 0), (15.4, 64.5, 1),
              (15.0, 66.0, 2), (14.2, 66.0, 0), (13.9, 64.6, 1), (12.6, 61.0, 0), (9.6, 58.0, 1),
              (7.0, 55.2, 0), (6.4, 52.0, 2), (0, 49.0, 2)],
}


def arc_v(profile):
    """Arc-length fraction of every point of the full profile."""
    lengths = [0.0]
    for (r0, z0, _), (r1, z1, _) in zip(profile, profile[1:]):
        lengths.append(lengths[-1] + math.hypot(r1 - r0, z1 - z0))
    return [l / lengths[-1] for l in lengths], lengths[-1]


def rim_index(profile):
    """Index of the lip's outer top point: the first point at the profile's greatest height."""
    top = max(z for _, z, _ in profile)
    return next(i for i, (_, z, _) in enumerate(profile) if z == top)
