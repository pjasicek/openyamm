#!/usr/bin/env python3
"""Kreegan skin colours per caste and tier (user decision 2026-10-24, design/kreegan_world/MONSTERS.md "Kreegan skin
colours"), as region ramps for region_variants.py.

Every caste once shared one violet / plum / rose skin. Each caste's tier ramp scripts now take their skin colour from
SKIN / BOSS here and recolour their own skin ramp with recolour():
  - the ramp keeps its luminance range and its stops' light-to-dark spread (scales and folds still read);
  - the colour at 70 % of the ramp is the table's mid-tone (as research/tier_colours/proposal_swatches.png measures);
  - shadows are a little more saturated, highlights a little paler;
  - dark tiers (Lancer C, Harrower C, the Forgemaster, Trooper C) lift their highlights instead of sinking to black.
Armour, plate, cloth and glow ramps are not touched here.

CLI: kreegan_skin.py ramps.json [...]  prints each material's ramps measured at 70 % (sRGB hex).
"""
import json
import sys

import numpy as np

LUMA = np.array([0.2126, 0.7152, 0.0722])
SKIN = {
    'drudge': {'a': '#8b6b55', 'b': '#7a7672', 'c': '#93412c'},     # clay, ash grey, rust
    'trooper': {'a': '#9d5f9a', 'b': '#4f6488', 'c': '#5a2430'},    # violet, slate blue, black crimson
    'lancer': {'a': '#7d7240', 'b': '#3f7a78', 'c': '#3a3433'},     # bronze olive, teal, charcoal
    'harrower': {'a': '#7b4556', 'b': '#a69c88', 'c': '#262024'},   # dusk red, bone ash, black
    'overseer': {'a': '#4a55a0', 'b': '#4b8579', 'c': '#a33a2a'},   # indigo, verdigris, ember
}
BOSS = {'krav': '#8c8781', 'ghulkat': '#8a6a3a', 'forgemaster': '#2e2a28', 'vreth': '#cfc6b0', 'thrix': '#a88c8c'}
MEASURE_AT = 0.7
HIGHLIGHT_FLOOR = 0.07   # linear luminance the top stop reaches at least (dark tiers keep their form in dim rooms)
MAX_LIFT = 4.0


def linear(srgb):
    srgb = np.asarray(srgb, dtype=np.float64)
    return np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)


def encode(value):
    value = np.clip(np.asarray(value, dtype=np.float64), 0, 1)
    return np.where(value <= 0.0031308, value * 12.92, 1.055 * value ** (1 / 2.4) - 0.055)


def hex_linear(code):
    code = code.lstrip('#')
    return linear(np.array([int(code[i:i + 2], 16) for i in (0, 2, 4)]) / 255.0)


def hex_of(value_linear):
    return '#' + ''.join('%02x' % int(round(float(c) * 255)) for c in encode(value_linear))


def sample(colors, t):
    """Linear colour of a 16-stop ramp at t, interpolated as the shader samples the ramp row."""
    colors = np.asarray(colors, dtype=np.float64)
    x = t * (len(colors) - 1)
    i = min(int(np.floor(x)), len(colors) - 2)
    f = x - i
    return colors[i] * (1 - f) + colors[i + 1] * f


def measure(ramp):
    return hex_of(sample(ramp['colors'], MEASURE_AT))


def _chroma(c, amount):
    """Scale a luminance-normalised colour's distance from grey (1, 1, 1)."""
    return np.maximum(1 + (c - 1) * amount, 0.02)


def recolour(ramp, target, reference=None):
    """New ramp in the target colour. reference: the caste's main skin ramp when this ramp belongs to a second skin
    material of the same body (a head atlas with its own luminance range); its brightness scale and highlight lift
    apply, so the head keeps its relation to the body."""
    reference = reference or ramp
    goal = hex_linear(target) if isinstance(target, str) else np.asarray(target, dtype=np.float64)
    goal_y = float(goal @ LUMA)
    old = np.asarray(ramp['colors'], dtype=np.float64) @ LUMA
    ref = np.asarray(reference['colors'], dtype=np.float64) @ LUMA
    scale = goal_y / max(float(sample(ref, MEASURE_AT)), 1e-6)
    lift = float(np.clip(HIGHLIGHT_FLOOR / max(ref[-1] * scale, 1e-6), 1.0, MAX_LIFT))
    t = np.linspace(0, 1, len(old))
    above = np.clip((t - MEASURE_AT) / (1 - MEASURE_AT), 0, 1)
    lum = old * scale * (1 + (lift - 1) * above ** 1.5)
    mid = goal / max(goal_y, 1e-6)
    pale = 0.75 if lift < 1.05 else 0.55   # a lifted highlight reads as sheen, not as a brighter dye
    shadow, light = _chroma(mid, 1.2), _chroma(mid, pale)
    below = np.clip(t / MEASURE_AT, 0, 1)[:, None]
    chroma = np.where(t[:, None] <= MEASURE_AT, shadow * (1 - below) + mid * below,
                      mid * (1 - above[:, None]) + light * above[:, None])
    chroma /= (chroma @ LUMA)[:, None]
    colors = np.clip(chroma * lum[:, None], 0, 1)
    if reference is ramp:
        for _ in range(4):   # stops 10 and 11 straddle 70 %: pull their blend onto the goal
            colors = np.clip(colors * (goal / np.maximum(sample(colors, MEASURE_AT), 1e-6)) ** 0.5, 0, 1)
    return {'range': list(ramp['range']), 'colors': np.round(colors, 6).tolist()}


if __name__ == '__main__':
    for path in sys.argv[1:]:
        config = json.load(open(path))
        for material in config['materials']:
            for variant, ramps in material['ramps'].items():
                print(path, material['base'], variant, [measure(r) for r in ramps])
