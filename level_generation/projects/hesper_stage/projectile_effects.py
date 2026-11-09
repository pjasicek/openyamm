#!/usr/bin/env python3
"""Hesper's projectile flight and impact effects (design/kreegan_world/PROJECTILES.md), built with the layer helpers of
the engine's effect generator (tools/fx/generate_projectile_effects.py; MM's effects are not touched).

    python3 level_generation/projects/hesper_stage/projectile_effects.py --output <file>

stage.py writes them into the stage as worlds/hesper/effects/projectile_library.yml. Each missile of projectiles.yml
has a flight effect hesper:fx/projectile/<object name> and an impact hesper:fx/impact/<object name>. The palette:
Ancient blue-white (hes_*), Kreegan orange-red plasma (kr_*), the Ashrunners' unsteady yellow and cyan, the crawlers'
green acid, the great ion cannon's violet (crown_ion, fired by the Crown's map script with evt.FireMissile). Size,
brightness and the impact grow with the weapon.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/fx'))
import generate_projectile_effects as fx  # noqa: E402
from generate_projectile_effects import (burst, effect, fade, falling, flash, impact, key, ribbon, rising,  # noqa: E402
                                         scales, shed, smoke, sparks, sprite)

# White core, cyan, deep blue: the Ancients' bolts.
ANCIENT_RIBBON = [key(0, (235, 245, 255), 0), key(0.3, (110, 180, 255), 60), key(1, (40, 90, 255), 255)]
ANCIENT_ARC = [key(0, (225, 240, 255), 0), key(0.4, (130, 190, 255), 60), key(1, (50, 100, 240), 255)]
# Hot white, orange, dark red: Kreegan plasma.
PLASMA_RIBBON = [key(0, (255, 215, 160), 0), key(0.35, (255, 110, 30), 70), key(1, (170, 30, 10), 255)]
HOT_RIBBON = [key(0, (255, 250, 230), 0), key(0.3, (255, 190, 90), 60), key(1, (230, 80, 20), 255)]
# White, violet, deep violet: the great ion cannon's pulse (COMBAT "Ion cannons").
ION_VIOLET = (170, 110, 255)
ION_WHITE = (235, 220, 255)
ION_RIBBON = [key(0, (255, 255, 255), 0), key(0.25, ION_WHITE, 40), key(0.6, ION_VIOLET, 120),
              key(1, (90, 40, 200), 255)]


def flights():
    return [
        effect('hes_bolt', 'Ancient bolt (projectile)',
               'Hesperian turrets: an Ancient blue-white bolt, a white core in a blue glow trailing a solid blue '
               'ribbon with a white core (the blaster bolt in the Ancients\' colour).',
               [sprite('glow', 0.75, (70, 150, 255), 185),
                sprite('glow', 0.32, (140, 200, 255), 60),
                sprite('glow', 0.15, (235, 248, 255), 0),
                ribbon('trail_noise', 11, 280, 0.2, ANCIENT_RIBBON, width_keys=scales(1.0, 0.5), fill=1.0,
                       erosion=0.15, core=1.0, scroll=0)]),
        effect('hes_heavy_bolt', 'Ancient heavy bolt (projectile)',
               'The Gate Bastion\'s twin heavy bolt: twice the head in a pulsing halo, a white-hot inner ribbon inside '
               'a crackling outer strand, and blue sparks.',
               [sprite('glow', 1.45, (60, 140, 255), 180, pulse=(0.25, 0.9, 1.1)),
                sprite('flare', 0.62, (170, 215, 255), 30),
                sprite('glow', 0.32, (240, 250, 255), 0),
                ribbon('trail_noise', 22, 420, 0.28, ANCIENT_RIBBON, width_keys=scales(1.0, 0.45), fill=1.0,
                       erosion=0.2, core=1.0, scroll=0),
                ribbon('trail_electric', 34, 380, 0.25, ANCIENT_ARC, width_keys=scales(1.0, 0.6), sample=16,
                       texture_length=90, scroll=6, fill=0, erosion=0.4, jitter=7, jitter_rate=20),
                sparks((220, 240, 255), (70, 130, 255), interval=0.03, velocity=90, lifetime=0.4, radius=12)]),
        effect('hes_rifle_bolt', 'Ancient rifle bolt (projectile)',
               'The Landfall guards\' rifles: a slim blue bolt, a small bright head and a long thin ribbon.',
               [sprite('glow', 0.5, (80, 160, 255), 190),
                sprite('streak', 0.2, (190, 225, 255), 40, velocity_aligned=True, stretch=2.5),
                sprite('glow', 0.12, (240, 250, 255), 0),
                ribbon('trail_noise', 6, 360, 0.18, ANCIENT_RIBBON, width_keys=scales(1.0, 0.4), fill=1.0,
                       erosion=0.1, core=1.0, scroll=0)]),
        effect('kr_dart', 'Kreegan dart (projectile)',
               'Kreegan drones: a small orange dart, a stretched streak and a short ribbon.',
               [sprite('glow', 0.45, (255, 110, 30), 190),
                sprite('streak', 0.22, (255, 200, 140), 20, velocity_aligned=True, stretch=3.0),
                sprite('glow', 0.1, (255, 235, 200), 0),
                ribbon('trail_noise', 5, 150, 0.14, PLASMA_RIBBON, width_keys=scales(1.0, 0.3), fill=1.0,
                       erosion=0.2, core=0.8, scroll=0)]),
        effect('kr_plasma', 'Kreegan plasma (projectile)',
               'Kreegan carbines and pistols: a pulsing orange plasma blob in an orange glow, an orange ribbon cooling '
               'to red, a few sparks.',
               [sprite('glow', 0.9, (255, 90, 25), 180),
                sprite('electric', 0.32, (255, 170, 90), 20, pulse=(0.12, 0.8, 1.15)),
                sprite('glow', 0.16, (255, 230, 190), 0),
                ribbon('trail_noise', 14, 300, 0.25, PLASMA_RIBBON, width_keys=scales(1.0, 0.4), fill=0.8,
                       erosion=0.35, core=0.7, scroll=2.5),
                sparks((255, 190, 110), (220, 60, 15), interval=0.05, velocity=70, lifetime=0.35, scale=0.035)]),
        effect('kr_hot_plasma', 'Kreegan hot plasma (projectile)',
               'The hot ranks (Spire Guards, Reavers, Nobles, the heavy Sentinels): the plasma bigger and white-orange, '
               'with a cross flare and a yellow-white ribbon.',
               [sprite('glow', 1.1, (255, 150, 60), 180),
                sprite('electric', 0.38, (255, 225, 170), 10, pulse=(0.1, 0.85, 1.15)),
                sprite('flare_cross', 0.3, (255, 245, 220), 20),
                sprite('glow', 0.2, (255, 252, 240), 0),
                ribbon('trail_noise', 16, 340, 0.25, HOT_RIBBON, width_keys=scales(1.0, 0.4), fill=0.9,
                       erosion=0.25, core=0.9, scroll=2.5),
                sparks((255, 235, 180), (255, 110, 30), interval=0.035, velocity=90, lifetime=0.4, scale=0.04)]),
        effect('kr_lance', 'Kreegan lance shot (projectile)',
               'The Lancers\' charged shot: a long thick white-hot beam in an orange sheath with a crackling arc.',
               [sprite('glow', 1.5, (255, 110, 40), 175),
                sprite('flare_wide', 0.7, (255, 220, 170), 20),
                sprite('glow', 0.32, (255, 250, 240), 0),
                ribbon('trail_noise', 26, 700, 0.35, HOT_RIBBON, width_keys=scales(1.0, 0.6), fill=1.0, erosion=0.15,
                       core=1.0, scroll=0),
                ribbon('trail_electric', 30, 560, 0.3, [key(0, (255, 230, 190), 0), key(1, (255, 120, 40), 255)],
                       width_keys=scales(1.0, 0.5), sample=18, texture_length=90, scroll=6, fill=0, erosion=0.4,
                       jitter=8, jitter_rate=22),
                sparks((255, 230, 170), (255, 90, 20), interval=0.025, velocity=110, lifetime=0.45, scale=0.045)]),
        effect('ash_blaster', 'Ashrunner salvage blaster (projectile)',
               'The Ashrunners\' patched blasters: a flickering yellow core and a jittering cyan arc over a ragged '
               'yellow ribbon.',
               [sprite('glow', 0.75, (230, 220, 80), 185, pulse=(0.07, 0.75, 1.2)),
                sprite('glow', 0.16, (255, 255, 215), 0, pulse=(0.11, 0.8, 1.25)),
                ribbon('trail_noise', 9, 240, 0.2, [key(0, (255, 250, 190), 0), key(0.35, (235, 210, 70), 80),
                                                    key(1, (160, 130, 30), 255)],
                       width_keys=scales(1.0, 0.4), fill=0.7, erosion=0.45, core=0.6, scroll=3),
                ribbon('trail_electric', 14, 220, 0.18, [key(0, (200, 255, 255), 0), key(1, (60, 200, 255), 255)],
                       width_keys=scales(1.0, 0.5), sample=10, texture_length=60, scroll=6, fill=0, erosion=0.45,
                       jitter=6, jitter_rate=30),
                sparks((210, 255, 255), (60, 180, 255), interval=0.06, velocity=90, lifetime=0.3, scale=0.035)]),
        effect('crown_ion', 'Great ion cannon pulse (projectile)',
               'The great cannon\'s release: a thick white core in a violet halo crossing in about 0.15 s, leaving a '
               'long bright violet trail with arcs crawling along it.',
               [sprite('glow', 6.0, ION_VIOLET, 150, pulse=(0.06, 0.85, 1.15)),
                sprite('flare_star', 3.0, ION_WHITE, 20),
                sprite('glow', 1.6, (255, 255, 255), 0),
                ribbon('trail_noise', 180, 9000, 0.45, ION_RIBBON, width_keys=scales(1.0, 0.35), fill=1.0,
                       erosion=0.1, core=1.0, scroll=0),
                ribbon('trail_electric', 260, 7000, 0.4, [key(0, ION_WHITE, 0), key(1, ION_VIOLET, 255)],
                       width_keys=scales(1.0, 0.5), sample=60, texture_length=400, scroll=8, fill=0, erosion=0.4,
                       jitter=40, jitter_rate=20)]),
        effect('crawler_acid', 'Crawler acid (projectile)',
               'Acid crawlers\' spit: a bubbling yellow-green glob dripping acid, with a thin hissing vapour.',
               [sprite('glow', 0.7, (150, 230, 40), 185),
                sprite('glow', 0.28, (170, 235, 60), 40, blend='alpha', pulse=(0.18, 0.85, 1.15)),
                sprite('glow', 0.12, (235, 255, 170), 20),
                shed('glow', scales(0.06, 0.025), [key(0, (180, 235, 60), 40), key(1, (90, 140, 20), 255)], 0.5,
                     distance=22, radius=6, velocity=30, wind=falling(260), blend='alpha'),
                smoke(0.1, 0.22, 0.35, 26, [key(0, (190, 225, 110), 205), key(1, (140, 165, 100), 255)],
                      texture='wisp_smoke', velocity=10, wind=rising(35))]),
    ]


def puff(count=1, size=(0.12, 0.25), start=0.05):
    return burst('smoke_puff', count, 0.8, 20, scales(*size), fade((70, 65, 65), 140), start=start, blend='alpha',
                 wind=rising(40), roll=True)


def impacts():
    return [
        impact('hes_bolt', 'Ancient bolt hit',
               'Hesperian turrets: a blue-white wide flash, a spray of blue sparks and a wisp of smoke.', 0.9,
               [flash('flare_wide', 0, 0.2, scales(0.6, 1.1), fade((120, 190, 255))),
                flash('glow', 0, 0.2, scales(0.4, 0.9), fade((210, 235, 255))),
                burst('spark', 14, 0.35, 280, scales(0.05, 0.01), fade((225, 240, 255), 0, (50, 110, 255)),
                      velocity_aligned=True, stretch=2.5),
                puff()]),
        impact('hes_heavy_bolt', 'Ancient heavy bolt hit',
               'The Gate Bastion: a big blue-white flash with rays, a shock ring on the ground, crackling electric '
               'blobs, a wide spray of sparks and smoke.', 1.3,
               [flash('glow', 0, 0.3, scales(0.9, 2.1), fade((170, 210, 255))),
                flash('flare_wide', 0, 0.28, scales(1.1, 2.0), fade((140, 195, 255))),
                flash('rays', 0, 0.25, scales(0.6, 1.4), fade((200, 230, 255))),
                flash('ring', 0, 0.45, scales(0.3, 2.4), fade((120, 180, 255), 40), lift=6, ground=True),
                burst('electric', 2, 0.14, 30, scales(0.35, 0.6), fade((225, 240, 255)), radius=26, roll=True,
                      window=0.3, interval=0.08),
                burst('spark', 28, 0.5, 380, scales(0.06, 0.012), fade((230, 245, 255), 0, (60, 110, 255)),
                      velocity_aligned=True, stretch=3),
                puff(2, (0.2, 0.45))]),
        impact('hes_rifle_bolt', 'Ancient rifle bolt hit',
               'Guard rifles: a small blue flash and a few sparks.', 0.6,
               [flash('glow', 0, 0.15, scales(0.3, 0.6), fade((190, 225, 255))),
                flash('flare_cross', 0, 0.15, scales(0.35, 0.6), fade((150, 200, 255))),
                burst('spark', 8, 0.3, 240, scales(0.04, 0.01), fade((225, 240, 255), 0, (60, 120, 255)),
                      velocity_aligned=True, stretch=2.5)]),
        impact('kr_dart', 'Kreegan dart hit',
               'Drones: a small orange flash and a fizz of sparks.', 0.6,
               [flash('glow', 0, 0.15, scales(0.3, 0.55), fade((255, 170, 90))),
                burst('spark', 8, 0.3, 240, scales(0.04, 0.01), fade((255, 210, 150), 0, (230, 60, 15)),
                      velocity_aligned=True, stretch=2.5)]),
        impact('kr_plasma', 'Kreegan plasma hit',
               'Kreegan carbines: an orange flash, embers falling and a wisp of smoke.', 1.0,
               [flash('flare_wide', 0, 0.2, scales(0.6, 1.1), fade((255, 140, 60))),
                flash('glow', 0, 0.22, scales(0.45, 1.0), fade((255, 200, 140))),
                burst('spark', 14, 0.55, 250, scales(0.05, 0.012), fade((255, 200, 120), 0, (200, 40, 10)),
                      wind=falling(240)),
                puff()]),
        impact('kr_hot_plasma', 'Kreegan hot plasma hit',
               'The hot ranks: a white-orange star flash with rays, sparks and smoke.', 1.1,
               [flash('glow', 0, 0.25, scales(0.6, 1.4), fade((255, 220, 170))),
                flash('flare_star', 0, 0.28, scales(0.55, 1.2), fade((255, 240, 210))),
                flash('rays', 0, 0.2, scales(0.45, 1.0), fade((255, 180, 90))),
                burst('spark', 18, 0.5, 300, scales(0.05, 0.012), fade((255, 235, 180), 0, (240, 80, 20)),
                      velocity_aligned=True, stretch=2.5),
                puff(1, (0.15, 0.3))]),
        impact('kr_lance', 'Kreegan lance blast',
               'The Lancers\' charged shot: a blinding white-orange flash, rays, a ground ring, a burst of flame, '
               'sparks and smoke.', 1.4,
               [flash('glow', 0, 0.32, scales(1.0, 2.3), fade((255, 210, 160))),
                flash('flare_wide', 0, 0.3, scales(1.2, 2.2), fade((255, 170, 90))),
                flash('rays', 0, 0.28, scales(0.7, 1.6), fade((255, 230, 190))),
                flash('ring', 0, 0.45, scales(0.3, 2.4), fade((255, 150, 70), 40), lift=6, ground=True),
                burst('fireball', 3, 0.45, 90, scales(0.3, 0.6), fade((255, 170, 80), 60, (180, 40, 10)), radius=18,
                      roll=True, spin=2),
                burst('spark', 28, 0.55, 400, scales(0.06, 0.012), fade((255, 230, 170), 0, (230, 70, 15)),
                      velocity_aligned=True, stretch=3),
                puff(2, (0.2, 0.45))]),
        impact('ash_blaster', 'Ashrunner blaster hit',
               'Salvage blasters: an uneven yellow flash and a spit of cyan and yellow sparks.', 0.8,
               [flash('glow', 0, 0.18, scales(0.35, 0.8), fade((240, 230, 120))),
                flash('electric', 0, 0.15, scales(0.3, 0.6), fade((170, 240, 255))),
                burst('spark', 8, 0.35, 260, scales(0.045, 0.01), fade((200, 255, 255), 0, (40, 160, 255)),
                      velocity_aligned=True, stretch=2.5),
                burst('spark', 8, 0.4, 220, scales(0.045, 0.01), fade((255, 245, 160), 0, (200, 150, 30)),
                      velocity_aligned=True, stretch=2.5, wind=falling(200)),
                puff()]),
        impact('crown_ion', 'Ion plasma blast',
               'The great cannon\'s impact: a violet-white sphere about 800 across swelling and collapsing, a shock '
               'ring along the ground, arcs crackling on the ground for 1.5 s, debris and smoke.', 2.0,
               [flash('glow', 0, 0.9, scales(10.0, 28.0, 22.0, 6.0), fade(ION_WHITE, 0, ION_VIOLET)),
                flash('flare_star', 0, 0.35, scales(12.0, 24.0), fade((255, 255, 255))),
                flash('rays', 0, 0.5, scales(10.0, 22.0), fade(ION_VIOLET)),
                flash('ring', 0, 0.7, scales(3.0, 40.0), fade(ION_WHITE, 40), lift=8, ground=True),
                flash('ring', 0.15, 0.9, scales(2.0, 30.0), fade(ION_VIOLET, 80), lift=6, ground=True),
                burst('electric', 6, 0.3, 160, scales(4.0, 2.0), fade(ION_WHITE, 30), radius=420, lift=40,
                      window=1.5, interval=0.2),
                burst('spark', 40, 0.9, 900, scales(0.35, 0.08), fade((240, 225, 255), 0, (120, 60, 255)),
                      velocity_aligned=True, stretch=3, wind=falling(300)),
                burst('smoke_puff', 4, 1.6, 120, scales(2.4, 6.0), fade((70, 55, 90), 120), start=0.2,
                      blend='alpha', radius=200, wind=rising(60), roll=True, spin=0.5)]),
        impact('crawler_acid', 'Crawler acid splash',
               'Acid crawlers\' spit: yellow-green droplets splashing, a bubbling glow and hissing vapour.', 1.3,
               [flash('glow', 0, 0.35, scales(0.4, 0.75), fade((170, 235, 60), 60)),
                burst('glow', 12, 0.6, 220, scales(0.06, 0.03), fade((190, 240, 70), 30, (100, 150, 20)),
                      blend='alpha', wind=falling(500)),
                burst('smoke_puff', 2, 1.0, 30, scales(0.12, 0.3), fade((190, 225, 110), 150), start=0.1,
                      blend='alpha', radius=12, wind=rising(60), roll=True, spin=0.6)]),
    ]


def build():
    """The effects with Hesper ids (hesper:fx/...); the helpers name them openyamm:fx/..."""
    effects = flights() + impacts()
    for item in effects:
        item['id'] = item['id'].replace('openyamm:fx/', 'hesper:fx/', 1)
    return effects


def write(path):
    effects = build()
    lines = ['# Generated by level_generation/projects/hesper_stage/projectile_effects.py; edit it and re-stage.',
             'schema: openyamm.effectLibrary.v1', 'effects:']
    for item in effects:
        item = dict(item)
        lines.append('# ' + item.pop('comment')[:114])
        body = fx.yaml.dump([item], Dumper=fx.Dumper, sort_keys=False, width=118, allow_unicode=True)
        lines.extend(body.rstrip('\n').split('\n'))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(lines) + '\n')
    return [item['id'] for item in effects]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    print(f'wrote {len(write(arguments.output))} effects to {arguments.output}')
