#!/usr/bin/env python3
"""Build one way-up column decoration (the elemental planes' exits back to the Skyroads, D-58 C5/C7) straight to GLB:
open shells round a vertical axis (a circle, or an ellipse for P1's heat curtain), every one additive, faded at its
foot, its sides (ellipses only) and its top through COLOR_0, its texture scrolling up with openyamm_uv_scroll.

Reuses the water fall's GlbWriter and noise textures (level_generation/decorations/xeen_waterfall_claude/scripts/
build_fall.py, imported, not copied). Distances in map units (81.7 per metre); the GLB is in metres, y up. Origin: the
column's foot centre on the floor; for the ellipse, +z (the model's front) is the side away from the wall.

Writes work/<preset>/<output>, work/<preset>/textures/*.png and work/<preset>/report.json.
Usage: build_column.py <preset>"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'xeen_waterfall_claude/scripts'))
from build_fall import GlbWriter, make_texture, periodic_noise, smoothstep, grid_indices, UNITS_PER_METRE  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from column_presets import PRESETS  # noqa: E402


def specks(spec, rng):
    """Sparse soft motes (dust grains, embers) on a transparent field, periodic."""
    width, height = spec['size']
    field = periodic_noise(rng, spec['size'], spec['blur'], spec['blur'] * spec.get('stretch', 1.0))
    keep = np.clip((field - spec['threshold']) / spec['softness'], 0.0, 1.0)
    alpha = spec['alpha'] * keep
    rgb = np.tile(np.array(spec['rgb'])[None, None, :], (height, width, 1))
    image = np.dstack([rgb, alpha[:, :, None]])
    return (np.clip(image, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)


def build_shell(shell):
    """One open shell: rows up the height, segments round it; radius r(t) = r0 + (r1 - r0) t^p, x scaled by `wide`
    and z by `deep` (ellipse). An ellipse may be cut to its front half (`front_only`): it stands against a wall."""
    rows, segments = shell['rows'], shell['segments']
    heights = shell['height'] * (np.arange(rows + 1) / rows)
    if shell.get('front_only'):
        angles = np.linspace(-0.5 * np.pi, 0.5 * np.pi, segments + 1)
    else:
        angles = np.linspace(0.0, 2.0 * np.pi, segments + 1)
    positions, uvs, colours = [], [], []
    for h in heights:
        t = h / shell['height']
        r = shell['r0'] + (shell['r1'] - shell['r0']) * t ** shell.get('power', 1.0)
        sway = shell.get('sway', 0.0) * np.sin(2.0 * np.pi * t * shell.get('sway_turns', 1.0))
        x = np.sin(angles) * r * shell.get('wide', 1.0) + sway
        z = np.cos(angles) * r * shell.get('deep', 1.0) + shell.get('shift', 0.0)
        positions.append(np.stack([x, np.full(len(angles), shell.get('lift', 0.0) + h), z], axis=1))
        span = (angles - angles[0]) / (2.0 * np.pi)
        uvs.append(np.stack([span * shell['u_tiles'], np.full(len(angles), h / shell['period'])], axis=1))
        fade = smoothstep(0.0, shell['fade_in'], t) * (1.0 - smoothstep(shell['full_until'], 1.0, t)) ** 1.4
        side = np.ones(len(angles))
        if shell.get('front_only'):
            side = smoothstep(0.0, 0.35, np.cos(angles))
        colours.append(np.stack([fade * side, fade * side, fade * side, np.ones(len(angles))], axis=1))
    return (np.concatenate(positions), np.concatenate(uvs), np.concatenate(colours),
            grid_indices(len(heights), len(angles)))


def main():
    name = sys.argv[1]
    preset = PRESETS[name]
    rng = np.random.default_rng(preset['seed'])
    out_dir = HERE / 'work' / name
    (out_dir / 'textures').mkdir(parents=True, exist_ok=True)
    writer = GlbWriter()
    writer.doc['asset']['generator'] = 'xeen_wayup_claude build_column.py'
    textures = {}
    for key, spec in preset['textures'].items():
        image = specks(spec, rng) if spec.get('kind') == 'specks' else make_texture(spec, rng)
        if spec.get('u_fade'):
            # The game's static shader does not apply COLOR_0, so a shell's side fade lives in its texture: across u
            # (the shell's span; such a shell keeps u_tiles 1 and no drift) RGB and alpha fall to 0 at both ends.
            u = (np.arange(image.shape[1]) + 0.5) / image.shape[1]
            edge = spec['u_fade']
            fade = smoothstep(0.0, edge, u) * smoothstep(0.0, edge, 1.0 - u)
            image = (image.astype(np.float64) * fade[None, :, None] + 0.5).astype(np.uint8)
        Image.fromarray(image, 'RGBA').save(out_dir / 'textures' / f'{key}.png')
        textures[key] = writer.texture(image, 10497)
    primitives, report = [], {'preset': name, 'layers': []}
    everything = []
    for index, shell in enumerate(preset['shells']):
        positions, uvs, colours, indices = build_shell(shell)
        extras = {'openyamm_additive': True, 'openyamm_uv_scroll': [shell.get('drift', 0.0), -shell['scroll']],
                  'openyamm_specular': 0.0, 'openyamm_translucency': shell.get('translucency', 0.4)}
        material = writer.material(f'Shell{index + 1}', textures[shell['texture']], shell['colour'], extras,
                                   shell.get('emissive'))
        primitives.append(writer.primitive(positions / UNITS_PER_METRE, (0.0, 1.0, 0.0), uvs, colours, indices,
                                           material))
        everything.append(positions)
        report['layers'].append({'name': f'Shell{index + 1}', 'texture': shell['texture'],
                                 'triangles': int(len(indices))})
    output = out_dir / preset['output']
    writer.write(output, Path(preset['output']).stem, primitives)
    points = np.concatenate(everything)
    lo, hi = points.min(axis=0), points.max(axis=0)
    report.update({'output': str(output), 'triangles': int(sum(l['triangles'] for l in report['layers'])),
                   'bounds_units': {'x': [float(lo[0]), float(hi[0])], 'up': [float(lo[1]), float(hi[1])],
                                    'z': [float(lo[2]), float(hi[2])]},
                   'height_units': float(hi[1] - lo[1])})
    (out_dir / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
