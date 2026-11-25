#!/usr/bin/env python3
"""Xeen's sky presets (WORLD_DESIGN §4, PRODUCTION E8) as data in the engine's sky schema
(level_generation/lighting/SKY_RENDERING.md, "Preset schema").

Writes assets_dev/worlds/xeen/rendering/sky/sky.yml: presets, aliases, themes and map assignments for the world.
The engine reads only engine/rendering/sky/sky.yml today, so these entries reach the game once A1 merges a world's
sky file (requested) or copies them in; the file is written in the same schema so either works unchanged.

Darkside keeps day and night. Its days are amber: each daytime key of the engine's `base` preset is recoloured by the
ratio of a noon target to base's noon value, so dawn, noon and dusk keep base's shape; nights stay base's nights.
Three stages chosen by main-quest qbits through Lua (`evt.SetOutdoorSky` with the alias names below):
day (M7 to M17), fading (M17 to M27), failing (M27 to M33), then back to day.
"""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
ENGINE_SKY = ROOT / 'assets_dev/engine/rendering/sky/sky.yml'
OUT = ROOT / 'assets_dev/worlds/xeen/rendering/sky/sky.yml'

COLOURS = ['zenith', 'horizon', 'sun_glow', 'fog', 'sun_disc', 'cloud_lit', 'cloud_shadow', 'ambient_tint',
           'water_sun', 'water_sky']
# Weight of the recolour per base key: full by day, half in the dawn and dusk keys, none at night.
DAYLIGHT = {'02:00': 0.0, '04:40': 0.15, '05:20': 0.6, '06:15': 1.0, '12:00': 1.0, '17:30': 1.0, '19:50': 0.85,
            '20:35': 0.6, '21:10': 0.15, '22:00': 0.0}

# Noon targets (linear RGB) and scalar changes per stage.
STAGES = {
    'xeen_darkside_day': {
        'comment': 'Darkside by day: a low amber-gold band at the horizon, a muted warm zenith, a pale small sun.',
        'noon': {'zenith': [0.22, 0.19, 0.21], 'horizon': [0.86, 0.56, 0.26], 'fog': [0.56, 0.43, 0.29],
                 'sun_glow': [1.0, 0.80, 0.52], 'sun_disc': [1.0, 0.96, 0.84], 'cloud_lit': [0.96, 0.72, 0.44],
                 'cloud_shadow': [0.36, 0.27, 0.24], 'ambient_tint': [1.0, 0.92, 0.80],
                 'water_sun': [1.0, 0.84, 0.58], 'water_sky': [0.40, 0.33, 0.26]},
        'sun_glow_strength': 0.35, 'sun_disc_visibility': 1.0, 'day_stars': 0.0,
        'sun_disc_degrees': 1.0,
        'clouds': [{'texture': 'clouds_stratus', 'scale': 0.090, 'speed': 0.0010, 'direction_deg': 30,
                    'coverage': 0.55, 'softness': 0.55, 'opacity': 0.85, 'curvature': 0.16},
                   {'texture': 'clouds_cumulus', 'scale': 0.120, 'speed': 0.0018, 'direction_deg': 40,
                    'coverage': 0.30, 'softness': 0.35, 'opacity': 0.9, 'curvature': 0.13}],
    },
    'xeen_darkside_fading': {
        # D-169: amber-red, halfway from the day's amber to the failing stage's ember red
        'comment': 'Acts III-IV after M17: the sun weakens; the band reddens to amber-red, the day is dimmer.',
        'noon': {'zenith': [0.15, 0.085, 0.055], 'horizon': [0.72, 0.25, 0.08], 'fog': [0.48, 0.24, 0.11],
                 'sun_glow': [1.0, 0.50, 0.24], 'sun_disc': [1.0, 0.78, 0.52], 'cloud_lit': [0.78, 0.35, 0.17],
                 'cloud_shadow': [0.26, 0.13, 0.08], 'ambient_tint': [0.96, 0.80, 0.66],
                 'water_sun': [0.92, 0.56, 0.32], 'water_sky': [0.30, 0.17, 0.12]},
        'sun_glow_strength': 0.3, 'sun_disc_visibility': 0.85, 'day_stars': 0.05,
        'sun_disc_degrees': 0.85,
        'clouds': [{'texture': 'clouds_stratus', 'scale': 0.090, 'speed': 0.0012, 'direction_deg': 30,
                    'coverage': 0.62, 'softness': 0.55, 'opacity': 0.9, 'curvature': 0.16},
                   {'texture': 'clouds_cumulus', 'scale': 0.120, 'speed': 0.0018, 'direction_deg': 40,
                    'coverage': 0.28, 'softness': 0.35, 'opacity': 0.85, 'curvature': 0.13}],
    },
    'xeen_darkside_failing': {
        'comment': 'Act V after M27 until Sheltem falls (M33): a failing ember of a sun, an ember-red dusk all day, the '
                   'brightest stars showing through; lamps and windows burn all day (map events).',
        # D-169: ember red-orange
        'noon': {'zenith': [0.09, 0.033, 0.02], 'horizon': [0.52, 0.12, 0.03], 'fog': [0.32, 0.11, 0.04],
                 'sun_glow': [1.0, 0.36, 0.14], 'sun_disc': [1.0, 0.48, 0.24], 'cloud_lit': [0.56, 0.17, 0.06],
                 'cloud_shadow': [0.15, 0.055, 0.035], 'ambient_tint': [0.92, 0.66, 0.50],
                 'water_sun': [0.86, 0.36, 0.18], 'water_sky': [0.20, 0.08, 0.05]},
        'sun_glow_strength': 0.25, 'sun_disc_visibility': 0.65, 'day_stars': 0.18,
        'sun_disc_degrees': 0.7,
        'clouds': [{'texture': 'clouds_stratus', 'scale': 0.090, 'speed': 0.0014, 'direction_deg': 30,
                    'coverage': 0.68, 'softness': 0.55, 'opacity': 0.9, 'curvature': 0.16},
                   {'texture': 'clouds_cirrus', 'scale': 0.070, 'speed': 0.0010, 'direction_deg': 25,
                    'coverage': 0.30, 'softness': 0.45, 'opacity': 0.5, 'curvature': 0.10}],
    },
}

# D-36: the bright face's glow over the Darkside's east rim (theme field `rim_glow`, SKY_RENDERING.md); below_deg 1.5
# since merge point 20 (the glow lights the horizon cloud banks); 10 since the void (U-12, rim decider Q6: the bright
# face lies beyond the edge, so its glow rises from below the rim over the void).
RIM_GLOW = {'direction_deg': 90, 'width_deg': 75, 'height_deg': 12, 'below_deg': 10,
            'color': [1.0, 0.88, 0.62], 'day': 0.3, 'night': 0.6}


# U-12 (WORLD_RIM_VOID_20261123.md section 4, Q1): empty space below the horizon over a map's void (terrain.void),
# by day and night: near-black, stars, a thin limb where the horizon's haze turns into space. Written on the Darkside
# stage presets; Cloudside maps on the shipped presets get the engine's defaults (the same values).
VOID = {'color': [0.004, 0.006, 0.016], 'stars': 0.9, 'limb_deg': 3}


def flow(seq):
    return yaml.dump(seq, default_flow_style=True, width=1000).strip()


def number(value):
    return float(f'{value:.3f}')


def stage_keys(base_keys, stage):
    noon = next(k for k in base_keys if k['time'] == '12:00')
    keys = []
    for key in base_keys:
        weight = DAYLIGHT[key['time']]
        out = {'time': key['time']}
        for name in COLOURS:
            ratio = [t / max(b, 1e-4) for t, b in zip(stage['noon'][name], noon[name])]
            out[name] = [number(min(max(1.0, v), v * (1 - weight + weight * r))) for v, r in zip(key[name], ratio)]
        if weight > 0:
            out['sun_glow_strength'] = number(key['sun_glow_strength'] * (1 - weight + weight * stage['sun_glow_strength']
                                                                         / max(noon['sun_glow_strength'], 1e-4)))
            out['sun_disc_visibility'] = number(key['sun_disc_visibility'] * (1 - weight + weight
                                                                             * stage['sun_disc_visibility']))
            out['stars'] = number(max(key['stars'], weight * stage['day_stars']))
        else:
            out['sun_glow_strength'] = key['sun_glow_strength']
            out['sun_disc_visibility'] = key['sun_disc_visibility']
            out['stars'] = key['stars']
        keys.append(out)
    return keys


def main():
    engine = yaml.safe_load(ENGINE_SKY.read_text())
    base_keys = engine['presets']['base']['keys']
    lines = [
        '# Xeen sky presets (written by level_generation/xeen_art/sky/make_sky.py; do not edit by hand).',
        '# Schema: level_generation/lighting/SKY_RENDERING.md. The engine reads engine/rendering/sky/sky.yml only;',
        '# these entries take effect when A1 merges a world sky file (or copies them into the engine file).',
        '# Colours are linear RGB; times are game-clock HH:MM.',
        'version: 1',
        '',
        '# Sky texture names an ODM or `evt.SetOutdoorSky` gives, resolved to presets. Darkside maps start on',
        '# xeendark1; xeen_common.lua switches to xeendark2 at M17 and xeendark3 at M27, and back to xeendark1 at M33.',
        'aliases:',
        '  xeendark1: xeen_darkside_day',
        '  xeendark2: xeen_darkside_fading',
        '  xeendark3: xeen_darkside_failing',
        '  xeencloud: xeen_cloud_sea',
        '  xeenroads: xeen_skyroads',
        '',
        'presets:',
    ]
    for name, stage in STAGES.items():
        lines.append(f'  # {stage["comment"]}')
        lines.append(f'  {name}:')
        lines.append('    inherits: base')
        lines.append('    keys:')
        for key in stage_keys(base_keys, stage):
            lines.append(f'      - {flow(key)}')
        lines.append(f'    sun_disc_degrees: {stage["sun_disc_degrees"]}')
        lines.append(f'    void: {flow(VOID)}')
        lines.append('    clouds:')
        for layer in stage['clouds']:
            lines.append(f'      - {flow(layer)}')
        lines.append('')
    lines += [
        '  # Cloudside sky maps (X8 Cloudreach, X9 Clouds of Xeen): bright, high sun, the cloud sea below the islands.',
        '  xeen_cloud_sea:',
        '    inherits: above_clouds',
        '    keys:',
        '      - {time: "12:00", zenith: [0.070, 0.210, 0.640], horizon: [0.640, 0.760, 0.920], sun_glow_strength: 0.35,'
        ' aerial_haze: 0.9}',
        '    clouds:',
        '      - {texture: clouds_cirrus, scale: 0.070, speed: 0.0012, direction_deg: 25, coverage: 0.25, softness: 0.45,'
        ' opacity: 0.5, curvature: 0.10}',
        '      - {texture: clouds_cumulus, scale: 0.110, speed: 0.0024, direction_deg: 30, coverage: 0.62, softness: 0.30,'
        ' opacity: 1.0, curvature: 0.13}',
        '',
        '  # D7 The Skyroads: Darkside\'s amber day seen from the clouds, the cloud sea below.',
        '  xeen_skyroads:',
        '    inherits: xeen_darkside_day',
        '    below_horizon: sky',
        '',
        '  # P3 Plane of Earth of Xeen (P1 and P2 use the engine\'s plane_fire and plane_air, P4 xeen_plane_water): a',
        '  # cavern-brown sky of',
        '  # dust, no sun, no stars, dim crystal light.',
        '  xeen_plane_earth:',
        '    inherits: base',
        '    keys:',
        '      - {time: "12:00", zenith: [0.050, 0.038, 0.030], horizon: [0.300, 0.220, 0.150], horizon_exponent: 2.6,',
        '         sun_glow: [0.60, 0.50, 0.40], sun_glow_strength: 0.0, fog: [0.22, 0.17, 0.12], sun_disc_visibility: 0.0,',
        '         stars: 0.0, moon_visibility: 0.0, cloud_lit: [0.40, 0.32, 0.24], cloud_shadow: [0.08, 0.06, 0.05],',
        '         ambient_tint: [1.0, 0.92, 0.82], water_sun: [0.6, 0.5, 0.4], water_sky: [0.20, 0.16, 0.12]}',
        '    horizon_ring: {opacity: 0.0}',
        '    clouds:',
        '      - {texture: clouds_storm, scale: 0.096, speed: 0.0008, direction_deg: 60, coverage: 0.70, softness: 0.50,'
        ' opacity: 0.8, curvature: 0.12}',
        '',
        '  # P4 Plane of Water of Xeen (D-58 P4 Q3; replaces WORLD_DESIGN 4\'s `underwater`, which draws no sky): the party',
        '  # swims at a surface under a sea-green zenith and an aquamarine horizon, no sun disc, bright diffuse light, slow',
        '  # cloud; the sky continues below the horizon (no world beneath).',
        '  xeen_plane_water:',
        '    inherits: base',
        '    below_horizon: sky',
        '    keys:',
        '      - {time: "12:00", zenith: [0.030, 0.300, 0.260], horizon: [0.300, 0.780, 0.700], horizon_exponent: 2.4,',
        '         sun_glow: [0.80, 1.00, 0.92], sun_glow_strength: 0.12, sun_glow_exponent: 2.0, fog: [0.24, 0.58, 0.54],',
        '         sun_disc_visibility: 0.0, stars: 0.0, moon_visibility: 0.0, cloud_lit: [0.86, 1.00, 0.96],',
        '         cloud_shadow: [0.36, 0.60, 0.58], ambient_tint: [0.90, 1.00, 0.97], water_sun: [0.80, 1.00, 0.92],',
        '         water_sky: [0.16, 0.48, 0.44]}',
        '    horizon_ring: {opacity: 0.0}',
        '    clouds:',
        '      - {texture: clouds_stratus, scale: 0.100, speed: 0.0008, direction_deg: 15, coverage: 0.40, softness: 0.60,'
        ' opacity: 0.6, curvature: 0.14}',
        '',
        '# Map themes: Cloudside maps use the shipped themes; Darkside maps keep the stage preset and add their own air.',
        'themes:',
        '  # D5 Desert of Doom: dust in the amber air.',
        '  xeen_doom: {sky_tint: [1.06, 0.98, 0.86], cloud_tint: [1.02, 0.96, 0.86], saturation: 0.8, haze: 0.22}',
        '  # D6 The Forbidden Zone: ash fall over the amber day.',
        '  xeen_ash: {sky_tint: [0.92, 0.84, 0.80], sun_tint: [1.05, 0.85, 0.72], cloud_tint: [0.82, 0.76, 0.74],'
        ' saturation: 0.55, haze: 0.28, stars: 0.6}',
        '  # D2 Sprite Forest: a faint green cast in the forest air.',
        '  xeen_sprite: {sky_tint: [0.94, 1.0, 0.94], cloud_tint: [0.95, 1.0, 0.95], saturation: 0.85, haze: 0.14}',
        '  # D3 and D4 (D-36): the bright face\'s light over the east rim, pale white-gold, fixed in the east, brighter at',
        '  # night; the stage preset is untouched.',
        f'  xeen_bright_rim: {{rim_glow: {flow(RIM_GLOW)}}}',
        '',
        'maps:',
        '  xeen_x3.odm: swamp',
        '  xeen_x4.odm: arid',
        '  xeen_x5.odm: frozen',
        '  xeen_x6.odm: arid',
        '  xeen_x7.odm: ashen',
        '  xeen_d2.odm: xeen_sprite',
        '  xeen_d3.odm: xeen_bright_rim',
        '  xeen_d4.odm: xeen_bright_rim',
        '  xeen_d5.odm: xeen_doom',
        '  xeen_d6.odm: xeen_ash',
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # assets_dev files share inodes with the output/ mirrors: write a temp file and rename it over the old one.
    temp = OUT.with_name(OUT.name + '.tmp')
    temp.write_text('\n'.join(lines) + '\n')
    yaml.safe_load(temp.read_text())
    temp.replace(OUT)
    print(OUT)


if __name__ == '__main__':
    main()
