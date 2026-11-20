"""Tangent-space normal-map texels that make a surface shade with a chosen world normal (round 3).

The engine builds each pixel's tangent frame from position and UV derivatives (fs_model.sc; the same frame as
lod_repair_claude/scripts/transfer_textures.py `frame`) around the interpolated vertex normal. Geometry whose own
normals disagree with its neighbours can then shade like them without any vertex change:
- the eyeball's lid-coloured part (sphere normals, lit lighter above and darker below than the lids around it);
- skin shards in front of the eyeball;
- the inward-facing triangles between the lips (lit in stair steps).

The cook multiplies a creature's normalTexture.scale so the map's 90th-percentile tilt reaches 0.25 (at most x3,
tools/cook/model_textures.yml normal_relief). The written tilt is divided by that factor, so the game shows about the
intended normal; tilts above MAX_TILT_DEG are capped.
"""
import sys
import types
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
sys.modules.setdefault('pymeshlab', types.ModuleType('pymeshlab'))
sys.path.insert(0, str(HERE.parent / 'lod_repair_claude' / 'scripts'))
import transfer_textures as TT  # noqa: E402

MAX_TILT_DEG = 35.0


def cook_relief_scale(normal_rgb):
    """The cook's normalTexture.scale multiplier for this map (tools/cook_models.py normal_relief, target 0.25, max 3)."""
    xy = normal_rgb[..., :2].astype(np.float64) / 127.5 - 1
    tilt = np.linalg.norm(xy, axis=-1)
    relief = tilt[(tilt > 0.01) & (tilt < 0.9)]
    p90 = float(np.percentile(relief, 90)) if relief.size else 0.0
    return min(3.0, max(1.0, 0.25 / p90)) if p90 > 0 else 1.0


def encode(target, corner_pos, corner_uv, corner_nrm, bary, scale):
    """target (N,3) world normals; per texel its triangle's corner positions, UVs and vertex normals (N,3,3/2) and its
    barycentrics (N,3) -> (N,3) normal-map RGB."""
    normal = TT.normalize((bary[:, :, None] * corner_nrm).sum(1))
    e1, e2 = corner_pos[:, 1] - corner_pos[:, 0], corner_pos[:, 2] - corner_pos[:, 0]
    t1, b1 = TT.frame(e1, e2, corner_uv[:, 1] - corner_uv[:, 0], corner_uv[:, 2] - corner_uv[:, 0], normal)
    basis = np.stack([t1, -b1, normal], -1)
    target = TT.normalize(target)
    # cap the tilt from the shading normal
    cosang = np.clip((target * normal).sum(-1), -1, 1)
    over = cosang < np.cos(np.radians(MAX_TILT_DEG))
    if over.any():
        perp = TT.normalize(target[over] - normal[over] * cosang[over, None])
        a = np.radians(MAX_TILT_DEG)
        target[over] = normal[over] * np.cos(a) + perp * np.sin(a)
    coef = np.linalg.solve(basis + np.eye(3) * 1e-9, target[:, :, None])[:, :, 0]
    coef = TT.normalize(coef)
    xy = coef[:, :2] / scale
    # the engine's frame is not orthonormal on skewed UV triangles: cap the stored tilt as well (in game x scale)
    mag = np.linalg.norm(xy, axis=1, keepdims=True)
    xy *= np.minimum(1.0, np.sin(np.radians(MAX_TILT_DEG)) / scale / np.maximum(mag, 1e-9))
    z = np.sqrt(np.clip(1 - (xy ** 2).sum(-1), 0.0025, 1))
    out = np.concatenate([xy, z[:, None]], 1)
    return np.clip(out * 127.5 + 127.5, 0, 255)
