#!/usr/bin/env python3
"""Generate the enhanced projectile flight effects (assets_dev/engine/effects/authored/projectile_library.yml).

Every projectile is built from the same layers (see PROJECTILE_VFX_ALL_PROPOSAL.md): a bright core on the collision
point, a head, a tongue of shed sprites or a ribbon, smoke or mist, sparks, and sometimes a pulse. The families below
pick and colour those layers. Edit the specs here and rerun; do not edit the generated file by hand.
Bindings from projectile recipes to these effects live in assets_dev/engine/effects/projectiles.yml.
Requires PyYAML.
"""
import argparse
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "assets_dev/engine/effects/authored/projectile_library.yml"
DURATION = 30
SPRITE = "openyamm:effect-sprite/"


def key(time, rgb, transparency):
    return {"time": time, "rgb": list(rgb), "transparency": transparency}


def scales(*values):
    """Evenly spaced scale keys: scales(0.3, 0.1) or explicit (time, value) pairs."""
    if values and isinstance(values[0], tuple):
        return [{"time": time, "value": value} for time, value in values]
    if len(values) == 1:
        return [{"time": 0, "value": values[0]}]
    return [{"time": round(index / (len(values) - 1), 3), "value": value} for index, value in enumerate(values)]


def sprite(texture, scale, rgb, transparency=0, blend="additive", stretch=None, velocity_aligned=False,
           pulse=None):
    """A sprite fixed on the projectile. pulse=(period_seconds, low, high) breathes its scale."""
    component = {"type": "sprite", "sprite_resource": SPRITE + texture, "blend": blend}
    if velocity_aligned:
        component["alignment"] = "velocity"
    if stretch:
        component["stretch_u"] = stretch
    if pulse:
        period, low, high = pulse
        component["repeat_count"] = int(DURATION / period)
        component["scale_keys"] = scales((0, scale * low), (0.5, scale * high), (1, scale * low))
    else:
        component["scale_keys"] = scales(scale)
    component["color_keys"] = [key(0, rgb, transparency)]
    component["motion_keys"] = []
    return component


def shed(texture, scale_keys, color_keys, lifetime, distance=None, interval=None, blend="additive", radius=4,
         velocity=0, shape="sphere", wind=None, per_emission=1, velocity_aligned=False, stretch=None, roll=False,
         spin=0.0, local=False):
    """Sprites shed into the world: by distance travelled (trails) or by time (sparks). roll starts each at a
    random angle and spin turns it (radians per second), so repeated puffs look less alike. local sprites move
    with the effect (a swarm around its head or its target) and must be shed by time. A negative velocity pulls
    sprites in towards the centre."""
    component = {"type": "sprite_system", "sprite_resource": SPRITE + texture,
                 "particle_space": "local" if local else "world", "blend": blend}
    if velocity_aligned:
        component["alignment"] = "velocity"
    if stretch:
        component["stretch_u"] = stretch
    if roll:
        component["random_roll"] = True
    if spin:
        component["spin_speed"] = spin
    component["sprites_per_emission"] = per_emission
    if distance:
        component["emission_distance"] = distance
    else:
        component["emission_interval_seconds"] = interval
    component.update({"particle_lifetime_seconds": lifetime, "emission_shape": shape, "radius": radius,
                      "velocity": velocity})
    if wind:
        direction, amount = wind
        component["wind_direction"] = list(direction)
        component["wind_amount"] = amount
    component["scale_keys"] = scale_keys
    component["color_keys"] = color_keys
    component["motion_keys"] = []
    return component


def ribbon(texture, width, max_length, lifetime, color_keys, width_keys=None, blend="additive", sample=14,
           texture_length=128, scroll=2.0, fill=0.3, erosion=0.5, core=0.0, jitter=0.0, jitter_rate=0.0):
    component = {"type": "ribbon", "sprite_resource": SPRITE + texture, "blend": blend,
                 "lifetime_seconds": lifetime, "max_length": max_length, "width": width, "sample_distance": sample,
                 "texture_length": texture_length, "scroll_speed": scroll, "fill": fill, "erosion": erosion}
    if core:
        component["core"] = core
    if jitter:
        component["jitter"] = jitter
        component["jitter_rate"] = jitter_rate
    component["width_keys"] = width_keys or scales(1.0, 0.3)
    component["color_keys"] = color_keys
    return component


UP = ((0, 0, 1), 1)
DOWN = ((0, 0, -1), 1)


def rising(amount):
    return (UP[0], amount)


def falling(amount):
    return (DOWN[0], amount)


def sparks(rgb_start, rgb_end, interval=0.05, velocity=80, lifetime=0.45, scale=0.045, scale_end=0.01,
           wind=rising(35), texture="spark", per_emission=1, radius=10, stretch=2.2):
    return shed(texture, scales(scale, scale_end), [key(0, rgb_start, 0), key(1, rgb_end, 255)], lifetime,
                interval=interval, radius=radius, velocity=velocity, wind=wind, velocity_aligned=True,
                stretch=stretch, per_emission=per_emission)


def flame_tongue(scale, scale_end, lifetime, distance, colors, radius=4, velocity=30, grow=None):
    keys = scales((0, scale), (0.35, scale * grow), (1, scale_end)) if grow else scales(scale, scale_end)
    return shed("fireball", keys, colors, lifetime, distance=distance, radius=radius, velocity=velocity, roll=True)


def smoke(scale, scale_end, lifetime, distance, colors, texture="smoke", velocity=18, wind=rising(30), radius=6):
    return shed(texture, scales(scale, scale_end), colors, lifetime, distance=distance, blend="alpha",
                radius=radius, velocity=velocity, wind=wind, roll=True, spin=0.8)


def effect(effect_id, name, comment, components, duration=DURATION, kind="projectile"):
    """kind: projectile (flight and settled effects, components run the whole duration) or impact (components
    carry their own start and end)."""
    for index, component in enumerate(components, start=1):
        component["id"] = index
        component.setdefault("start_seconds", 0)
        component.setdefault("end_seconds", duration)
    ordered = []
    for component in components:
        head = {name: component.pop(name) for name in ("id", "type", "start_seconds", "end_seconds")}
        head.update(component)
        ordered.append(head)
    return {"id": f"openyamm:fx/{kind}/{effect_id}", "display_name": name, "comment": comment,
            "duration_seconds": duration, "compatibility_profile": "predictable", "components": ordered}


def scaled(components, factor):
    """The same layers at another size: sprites, spread, ribbon width and trail length scale together, and sheds keep
    their spacing relative to their size, so the look and the particle count stay the same."""
    for component in components:
        for scale_key in component.get("scale_keys", []):
            scale_key["value"] = round(scale_key["value"] * factor, 4)
        for name in ("radius", "velocity", "width", "max_length", "emission_distance"):
            if name in component:
                component[name] = round(component[name] * factor, 3)
        if "emission_distance" in component:
            component["particle_lifetime_seconds"] = round(component["particle_lifetime_seconds"] * factor, 3)
    return components


def impact(effect_id, name, comment, duration, components):
    """Components without a lift of their own sit a little above the impact point, so a hit on the ground does not
    bury half of each sprite."""
    for component in components:
        component.setdefault("offset", [0, 0, 20])
    return effect(effect_id, name, comment, components, duration, "impact")


def flash(texture, start, end, scale_keys, color_keys, blend="additive", lift=0, ground=False):
    """A sprite on the impact point for [start, end]; its scale and colour keys run over that span. ground lays it
    flat (a shockwave ring on the floor)."""
    component = {"type": "sprite", "start_seconds": start, "end_seconds": end, "sprite_resource": SPRITE + texture,
                 "blend": blend}
    if lift:
        component["offset"] = [0, 0, lift]
    if ground:
        component.update({"alignment": "world_plane", "plane_right": [1, 0, 0], "plane_up": [0, 1, 0]})
    component["scale_keys"] = scale_keys
    component["color_keys"] = color_keys
    component["motion_keys"] = []
    return component


def burst(texture, count, lifetime, velocity, scale_keys, color_keys, start=0.0, blend="additive", radius=6,
          wind=None, velocity_aligned=False, stretch=None, roll=False, spin=0.0, lift=0, window=None,
          interval=1.0, local=False):
    """count sprites flung out at once (or, with window, every interval seconds for that long)."""
    component = shed(texture, scale_keys, color_keys, lifetime, interval=interval, blend=blend, radius=radius,
                     velocity=velocity, wind=wind, per_emission=count, velocity_aligned=velocity_aligned,
                     stretch=stretch, roll=roll, spin=spin, local=local)
    component["start_seconds"] = start
    component["end_seconds"] = round(start + (window if window else 0.03), 3)
    if lift:
        component["offset"] = [0, 0, lift]
    return component


def moving(component, start):
    """Moves a component from start (an offset) to its own place over its span: a meteor falling onto the impact
    point. A shed component then trails its sprites along the path."""
    component["motion_keys"] = [{"time": 0, "value": list(start)}, {"time": 1, "value": [0, 0, 0]}]
    return component


def fade(rgb, transparency=0, end_rgb=None, peak=None):
    """Colour keys that hold, then fade out: fade((255, 200, 120)) or with an end colour and a fade start."""
    end_rgb = end_rgb or rgb
    if peak is None:
        return [key(0, rgb, transparency), key(1, end_rgb, 255)]
    return [key(0, rgb, transparency), key(peak, end_rgb, transparency), key(1, end_rgb, 255)]


FIRE_TONGUE = [key(0, (255, 190, 110), 70), key(0.4, (255, 100, 25), 140), key(1, (150, 30, 8), 255)]
FIRE_SMOKE = [key(0, (150, 45, 15), 150), key(0.4, (90, 35, 20), 185), key(1, (45, 40, 40), 255)]
SPAT_TONGUE = [key(0, (255, 165, 85), 80), key(0.4, (235, 85, 20), 150), key(1, (120, 25, 8), 255)]
SPAT_SMOKE = [key(0, (120, 40, 15), 130), key(0.4, (70, 35, 25), 175), key(1, (40, 35, 35), 255)]


def fire_effects():
    return [
        effect("fire_bolt", "Fire bolt (projectile)",
               "Fire Bolt spell: a round flame head shedding a dense tongue of flame over faint smoke (the comet).",
               [sprite("glow", 0.9, (255, 120, 40), 195),
                sprite("fireball", 0.4, (255, 200, 140), 30),
                sprite("glow", 0.2, (255, 245, 215)),
                smoke(0.22, 0.42, 0.3, 28, FIRE_SMOKE),
                flame_tongue(0.34, 0.06, 0.14, 9, FIRE_TONGUE),
                sparks((255, 215, 130), (255, 80, 20), interval=0.04, lifetime=0.5)]),
        effect("monster_fire_bolt", "Monster fire missile (projectile)",
               "Monsters' ordinary fire attack: the fire bolt smaller and rougher, smokier and dirtier (spat flame).",
               scaled([sprite("glow", 0.75, (255, 105, 35), 205),
                       sprite("fireball", 0.32, (255, 175, 110), 45),
                       sprite("glow", 0.15, (255, 225, 170), 30),
                       smoke(0.2, 0.45, 0.4, 18, SPAT_SMOKE, velocity=20, wind=rising(35)),
                       flame_tongue(0.27, 0.05, 0.12, 10, SPAT_TONGUE, radius=5, velocity=40),
                       sparks((255, 200, 120), (240, 70, 20), velocity=90, scale=0.04, radius=8, stretch=2.0,
                              wind=rising(30))], 0.6)),
        effect("fireball", "Fireball (projectile)",
               "Fireball spell: bigger and heavier than the fire bolt, a churning double head and a thick dark "
               "smoke trail that hangs in the air.",
               [sprite("glow", 1.4, (255, 100, 30), 190),
                sprite("fireball", 0.62, (255, 170, 100), 40),
                sprite("fireball", 0.45, (255, 215, 160), 20),
                sprite("glow", 0.28, (255, 240, 205)),
                smoke(0.32, 0.64, 0.65, 20, [key(0, (140, 40, 12), 120), key(0.3, (80, 32, 20), 165),
                                       key(1, (40, 36, 36), 255)], velocity=22, wind=rising(28), radius=10),
                flame_tongue(0.5, 0.09, 0.16, 10, [key(0, (255, 180, 95), 60), key(0.4, (240, 85, 20), 130),
                                             key(1, (130, 25, 8), 255)], radius=7, velocity=40),
                sparks((255, 210, 120), (255, 70, 15), interval=0.025, velocity=110, lifetime=0.6)]),
        effect("flame_gout", "Flame gout (projectile)",
               "Dragon Breath and Flame Blast: a gout of breathed flame that widens as it flies, heavy smoke.",
               [sprite("glow", 1.3, (255, 95, 25), 195),
                sprite("fireball", 0.55, (255, 185, 120), 35),
                sprite("glow", 0.22, (255, 235, 190)),
                smoke(0.3, 0.6, 0.6, 16, FIRE_SMOKE, velocity=30, radius=12),
                flame_tongue(0.32, 0.058, 0.26, 7, [key(0, (255, 200, 120), 60), key(0.35, (255, 110, 30), 120),
                                             key(1, (140, 30, 8), 255)], radius=8, velocity=70, grow=2.0),
                sparks((255, 205, 120), (255, 70, 15), interval=0.03, velocity=120)]),
        effect("incinerate", "Incinerate (projectile)",
               "Incinerate spell: the hottest look, a white core and a narrow white-centred flame lance with "
               "wisps peeling off and almost no smoke.",
               [sprite("glow", 1.2, (255, 170, 80), 170),
                sprite("fireball", 0.42, (255, 235, 200), 0),
                sprite("glow", 0.32, (255, 255, 240)),
                ribbon("trail_noise", 18, 380, 0.3, [key(0, (255, 250, 225), 0), key(0.4, (255, 190, 90), 90),
                                                     key(1, (230, 80, 20), 255)],
                       fill=0.75, erosion=0.35, core=0.9, scroll=3.5, texture_length=110),
                flame_tongue(0.3, 0.054, 0.16, 9, [key(0, (255, 225, 160), 40), key(0.4, (255, 140, 40), 120),
                                            key(1, (200, 50, 10), 255)], radius=8, velocity=60),
                sparks((255, 240, 190), (255, 120, 30), interval=0.03, velocity=120)]),
        effect("meteor", "Meteor (projectile)",
               "Meteor Shower: the native meteor rock stays visible, wrapped in a large flame envelope trailing "
               "upward and a very heavy smoke trail.",
               [sprite("glow", 1.1, (255, 100, 30), 205),
                sprite("fireball", 0.5, (255, 175, 110), 50),
                smoke(0.4, 0.8, 0.8, 14, [key(0, (80, 30, 12), 90), key(0.3, (55, 35, 28), 140),
                                     key(1, (45, 42, 40), 255)], velocity=25, radius=14),
                flame_tongue(0.55, 0.099, 0.22, 10, [key(0, (255, 190, 110), 70), key(0.4, (240, 90, 20), 140),
                                              key(1, (120, 25, 8), 255)], radius=10, velocity=50),
                sparks((255, 210, 120), (255, 70, 15), interval=0.02, velocity=140, lifetime=0.6)]),
        effect("fire_spike", "Fire spike (projectile)",
               "Fire Spike in flight: a small crackling white-yellow star with sparks and a short flame trail.",
               [sprite("glow", 0.7, (255, 140, 50), 190),
                sprite("glint", 0.35, (255, 230, 170), 0),
                flame_tongue(0.18, 0.032, 0.12, 8, FIRE_TONGUE, velocity=40),
                sparks((255, 225, 150), (255, 90, 20), interval=0.02, velocity=150, lifetime=0.3,
                       per_emission=2)]),
        effect("dark_fire_bolt", "Darkfire bolt (projectile)",
               "Darkfire Bolt (MM8 dark elf): fire that eats light, a black-violet smoky body with a magenta and "
               "orange burning rim.",
               [sprite("glow", 0.9, (200, 50, 170), 190),
                sprite("fireball", 0.38, (200, 70, 190), 60),
                sprite("glow", 0.16, (255, 170, 120), 40),
                flame_tongue(0.32, 0.058, 0.15, 9, [key(0, (230, 90, 200), 80), key(0.4, (170, 40, 150), 150),
                                             key(1, (90, 15, 70), 255)], velocity=35),
                smoke(0.26, 0.52, 0.35, 12, [key(0, (30, 8, 40), 90), key(0.4, (25, 10, 35), 150),
                                       key(1, (20, 15, 25), 255)], velocity=15),
                sparks((255, 150, 90), (200, 40, 160), interval=0.05)]),
    ]


ELECTRIC = [key(0, (235, 245, 255), 0), key(0.4, (140, 195, 255), 50), key(1, (60, 100, 230), 255)]


def air_effects():
    return [
        effect("air_bolt", "Air bolt (projectile)",
               "Monsters' air missile: a white-hot core with a velocity streak, a soft glow ribbon and a thin "
               "crackling electric arc.",
               [sprite("glow", 0.85, (110, 170, 255), 150),
                sprite("glow", 0.3, (235, 245, 255), 0, velocity_aligned=True, stretch=1.8),
                ribbon("trail_noise", 20, 340, 0.35, [key(0, (150, 200, 255), 120), key(1, (50, 90, 220), 255)],
                       width_keys=scales(1.0, 0.4), sample=16, texture_length=120, scroll=1.5, fill=0.5,
                       erosion=0.35),
                ribbon("trail_electric", 28, 520, 0.4, ELECTRIC, width_keys=scales(1.0, 0.6), sample=18,
                       texture_length=90, scroll=6, fill=0, erosion=0.4, jitter=7, jitter_rate=24),
                sparks((240, 248, 255), (80, 130, 255), interval=0.05, velocity=120, lifetime=0.18, scale=0.05,
                       wind=None, radius=4, stretch=3)]),
        effect("lightning_bolt", "Lightning bolt (projectile)",
               "Lightning Bolt spell: the air bolt grown into a storm, a flickering electric head, two wide "
               "jittering arcs over a glow ribbon, and sparks; replaces the flat yellow beam.",
               [sprite("glow", 1.3, (120, 160, 255), 185),
                sprite("electric", 0.5, (225, 235, 255), 0, pulse=(0.12, 0.8, 1.15)),
                sprite("glow", 0.36, (245, 250, 255), 0, velocity_aligned=True, stretch=2.0),
                ribbon("trail_noise", 34, 300, 0.4, [key(0, (170, 205, 255), 100), key(1, (60, 90, 230), 255)],
                       width_keys=scales(1.0, 0.5), sample=16, texture_length=140, scroll=1.8, fill=0.45,
                       erosion=0.4),
                ribbon("trail_electric", 44, 700, 0.45, ELECTRIC, width_keys=scales(1.0, 0.7), sample=20,
                       texture_length=100, scroll=7, fill=0, erosion=0.35, jitter=14, jitter_rate=26),
                ribbon("trail_electric", 30, 450, 0.35, [key(0, (255, 255, 255), 0), key(1, (110, 150, 255), 255)],
                       width_keys=scales(1.0, 0.5), sample=24, texture_length=70, scroll=-5, fill=0, erosion=0.5,
                       jitter=10, jitter_rate=30),
                sparks((230, 240, 255), (90, 130, 255), interval=0.025, velocity=180, lifetime=0.25, wind=None,
                       per_emission=2)]),
        effect("starburst", "Starburst star (projectile)",
               "Starburst: each falling star keeps its native sprite, with a golden glint, a sparkling ribbon and "
               "falling glitter.",
               [sprite("glow", 1.0, (255, 210, 120), 190),
                sprite("glint", 0.5, (255, 245, 210), 0, pulse=(0.25, 0.85, 1.1)),
                ribbon("trail_noise", 16, 360, 0.4, [key(0, (255, 240, 190), 40), key(1, (255, 150, 60), 255)],
                       fill=0.55, erosion=0.45, core=0.5, scroll=2.5),
                shed("spark", scales(0.05, 0.01), [key(0, (255, 240, 180), 0), key(1, (255, 160, 60), 255)], 0.5,
                     distance=30, radius=12, velocity=30, wind=falling(60))]),
    ]


def water_effects():
    mist = [key(0, (200, 235, 255), 150), key(1, (160, 200, 240), 255)]
    return [
        effect("monster_water_bolt", "Monster water missile (projectile)",
               "Monsters' water missile: a cyan water orb with a flowing ribbon, falling droplets and spray mist.",
               [sprite("glow", 0.8, (70, 160, 255), 195),
                sprite("glow", 0.26, (210, 245, 255), 20),
                ribbon("trail_noise", 22, 300, 0.35, [key(0, (170, 225, 255), 60), key(0.5, (60, 150, 240), 140),
                                                      key(1, (30, 80, 200), 255)],
                       fill=0.45, erosion=0.5, core=0.3, scroll=2.2),
                shed("glow", scales(0.07, 0.03), [key(0, (190, 235, 255), 40), key(1, (70, 140, 230), 255)], 0.45,
                     distance=26, radius=8, velocity=45, wind=falling(160)),
                smoke(0.16, 0.32, 0.35, 22, mist, texture="wisp_smoke", velocity=20, wind=None)]),
        effect("ice_bolt", "Ice bolt (projectile)",
               "Ice Bolt: the native ice shard stays visible inside a cold halo, trailing frost mist, a thin pale "
               "ribbon and tiny ice glints.",
               [sprite("glow", 0.9, (130, 200, 255), 190),
                sprite("flare", 0.4, (230, 248, 255), 20),
                ribbon("trail_noise", 14, 260, 0.35, [key(0, (225, 245, 255), 60), key(1, (110, 170, 240), 255)],
                       fill=0.55, erosion=0.45, core=0.4, scroll=1.5),
                smoke(0.18, 0.36, 0.45, 14, [key(0, (210, 240, 255), 160), key(1, (170, 210, 245), 255)],
                      texture="wisp_smoke", velocity=12, wind=falling(10)),
                shed("glint", scales(0.07, 0.015), [key(0, (240, 250, 255), 0), key(1, (150, 200, 255), 255)],
                     0.5, distance=34, radius=10, velocity=20, wind=falling(40))]),
        effect("ice_shard", "Ice shard (projectile)",
               "Ice Blast fallout shards: small velocity-stretched frost streaks with glints.",
               [sprite("glow", 0.5, (140, 205, 255), 190),
                sprite("streak", 0.3, (230, 248, 255), 0, velocity_aligned=True, stretch=1.6),
                shed("glint", scales(0.05, 0.01), [key(0, (240, 250, 255), 20), key(1, (150, 200, 255), 255)],
                     0.35, distance=24, radius=4, velocity=15)]),
        effect("poison_spray", "Poison spray (projectile)",
               "Poison Spray: sickly green globs that drip and leave a low green mist.",
               [sprite("glow", 0.7, (110, 220, 60), 190),
                sprite("glow", 0.28, (150, 230, 90), 60, blend="alpha"),
                sprite("glow", 0.12, (220, 255, 170), 40),
                smoke(0.12, 0.22, 0.3, 22, [key(0, (90, 160, 40), 200), key(0.5, (70, 120, 40), 225),
                                            key(1, (50, 80, 40), 255)], texture="wisp_smoke", velocity=14,
                      wind=falling(12)),
                shed("glow", scales(0.06, 0.03), [key(0, (140, 220, 70), 60), key(1, (70, 130, 30), 255)], 0.45,
                     distance=30, radius=6, velocity=30, wind=falling(180), blend="alpha")]),
        effect("acid_burst", "Acid burst (projectile)",
               "Acid Burst: a yellow-green bubbling glob that drips acid and leaves hissing vapour rising.",
               [sprite("glow", 0.85, (190, 230, 50), 185),
                sprite("glow", 0.32, (200, 240, 80), 50, blend="alpha", pulse=(0.2, 0.9, 1.1)),
                sprite("glow", 0.14, (245, 255, 190), 20),
                smoke(0.14, 0.26, 0.4, 22, [key(0, (200, 230, 120), 200), key(1, (150, 170, 110), 255)],
                      texture="wisp_smoke", velocity=12, wind=rising(40)),
                shed("glow", scales(0.07, 0.03), [key(0, (210, 240, 80), 40), key(1, (110, 150, 20), 255)], 0.5,
                     distance=26, radius=8, velocity=35, wind=falling(200), blend="alpha")]),
    ]


DUST = [key(0, (170, 140, 100), 150), key(0.4, (140, 115, 85), 190), key(1, (110, 95, 80), 255)]


def earth_effects():
    pebbles = shed("debris", scales(0.12, 0.08), [key(0, (140, 110, 80), 0), key(1, (110, 90, 70), 255)], 0.6,
                   distance=40, blend="alpha", radius=8, velocity=40, wind=falling(260))
    return [
        effect("monster_earth_bolt", "Monster earth missile (projectile)",
               "Monsters' earth missile: a hurled clump of rock and soil with a faint amber glow, a dust trail and "
               "falling pebbles.",
               [sprite("glow", 0.7, (220, 160, 80), 205),
                sprite("debris", 0.32, (150, 115, 80), 0, blend="alpha"),
                sprite("glow", 0.13, (255, 210, 140), 60),
                smoke(0.2, 0.4, 0.5, 16, DUST, velocity=14, wind=falling(15)),
                dict(pebbles)]),
        effect("rock_blast", "Rock blast (projectile)",
               "Rock Blast: the native rock stays visible, trailing heavy dust and pebbles, with a faint earth glow.",
               [sprite("glow", 0.9, (220, 160, 80), 210),
                smoke(0.3, 0.6, 0.6, 14, DUST, velocity=16, wind=falling(15), radius=10),
                dict(pebbles)]),
        effect("death_blossom", "Death blossom (projectile)",
               "Death Blossom: the native seed with a sickly green-brown glow and a dust trail.",
               [sprite("glow", 0.8, (150, 170, 70), 195),
                sprite("glow", 0.14, (220, 230, 150), 40),
                smoke(0.22, 0.44, 0.5, 16, [key(0, (120, 120, 80), 150), key(1, (80, 80, 60), 255)], velocity=14),
                sparks((210, 230, 140), (90, 110, 40), interval=0.06, velocity=60, wind=falling(60))]),
        effect("blades", "Blades (projectile)",
               "Blades: the native blades stay visible, with a silver velocity streak and a thin sharp wind-cut "
               "ribbon.",
               [sprite("streak", 0.45, (230, 235, 245), 40, velocity_aligned=True, stretch=2.2),
                ribbon("trail_noise", 8, 260, 0.25, [key(0, (240, 245, 255), 40), key(1, (150, 160, 180), 255)],
                       fill=0.9, erosion=0.25, core=0.8, scroll=4),
                shed("glint", scales(0.05, 0.01), [key(0, (255, 255, 255), 0), key(1, (170, 180, 200), 255)], 0.25,
                     interval=0.06, radius=6, velocity=40)]),
    ]


def body_effects():
    return [
        effect("monster_body_bolt", "Monster body missile (projectile)",
               "Monsters' body missile: pulsing green-teal life energy with wisps peeling off a soft ribbon.",
               [sprite("glow", 0.8, (60, 210, 160), 195, pulse=(0.4, 0.85, 1.1)),
                sprite("glow", 0.22, (200, 255, 225), 20),
                ribbon("trail_noise", 20, 280, 0.35, [key(0, (150, 245, 200), 70), key(1, (30, 140, 110), 255)],
                       fill=0.4, erosion=0.5, core=0.3, scroll=1.8),
                shed("wisp", scales(0.16, 0.08), [key(0, (140, 240, 190), 80), key(1, (40, 150, 110), 255)], 0.45,
                     distance=36, radius=8, velocity=30)]),
        effect("harm", "Harm (projectile)",
               "Harm: the native sprite stays visible, with a pulsing blood-red halo and dark red wisps.",
               [sprite("glow", 0.9, (210, 30, 30), 185, pulse=(0.3, 0.8, 1.15)),
                sprite("glow", 0.2, (255, 160, 150), 40),
                shed("wisp", scales(0.18, 0.08), [key(0, (220, 40, 40), 70), key(1, (90, 10, 10), 255)], 0.45,
                     distance=30, radius=6, velocity=25),
                smoke(0.16, 0.32, 0.4, 24, [key(0, (90, 10, 10), 160), key(1, (50, 10, 10), 255)], velocity=10,
                      wind=None)]),
        effect("flying_fist", "Flying fist (projectile)",
               "Flying Fist: the native fist stays visible, driving a red-orange force streak with shock rings.",
               [sprite("glow", 0.8, (255, 90, 50), 190),
                sprite("streak", 0.5, (255, 170, 120), 60, velocity_aligned=True, stretch=3.0),
                shed("ring", scales(0.06, 0.3), [key(0, (255, 140, 90), 80), key(1, (200, 50, 30), 255)], 0.3,
                     distance=70, radius=0, velocity=0)]),
    ]


def mind_effects():
    return [
        effect("monster_mind_bolt", "Monster mind missile (projectile)",
               "Monsters' mind missile: an amber soft star trailing expanding lilac-rimmed psychic ripples.",
               [sprite("glow", 0.75, (230, 190, 90), 200),
                sprite("soft_star", 0.32, (255, 235, 170), 20, pulse=(0.3, 0.85, 1.1)),
                shed("ripple", scales(0.06, 0.32), [key(0, (240, 200, 110), 60), key(0.5, (200, 150, 220), 150),
                                                    key(1, (150, 100, 200), 255)], 0.4, distance=55, radius=0),
                shed("wisp", scales(0.14, 0.06), [key(0, (240, 210, 140), 90), key(1, (170, 120, 210), 255)], 0.4,
                     distance=40, radius=6, velocity=20)]),
        effect("mind_blast", "Mind blast (projectile)",
               "Mind Blast and Psychic Shock: a violet psychic star pulsing hard, trailing bright expanding "
               "ripples and twisting wisps.",
               [sprite("glow", 1.0, (180, 110, 255), 190),
                sprite("soft_star", 0.42, (240, 210, 255), 0, pulse=(0.2, 0.8, 1.2)),
                sprite("glow", 0.16, (255, 245, 255)),
                shed("ripple", scales(0.08, 0.42), [key(0, (230, 190, 255), 40), key(1, (130, 70, 220), 255)],
                     0.4, distance=45, radius=0),
                shed("wisp", scales(0.18, 0.06), [key(0, (220, 170, 255), 70), key(1, (110, 50, 200), 255)], 0.45,
                     distance=28, radius=8, velocity=25)]),
    ]


def spirit_effects():
    return [
        effect("monster_spirit_bolt", "Monster spirit missile (projectile)",
               "Monsters' spirit missile: a pale silver-blue ghostly glint trailing translucent wisps and a "
               "faint ribbon.",
               [sprite("glow", 0.8, (170, 200, 255), 205),
                sprite("flare_cross", 0.42, (235, 245, 255), 20),
                ribbon("trail_noise", 18, 260, 0.4, [key(0, (210, 225, 255), 100), key(1, (120, 140, 220), 255)],
                       fill=0.35, erosion=0.6, scroll=1.2),
                shed("wisp", scales(0.16, 0.1), [key(0, (220, 235, 255), 110), key(1, (130, 150, 230), 255)],
                     0.55, distance=30, radius=8, velocity=20, wind=rising(20))]),
    ]


GOLD = [key(0, (255, 248, 220), 0), key(0.4, (255, 220, 130), 80), key(1, (240, 160, 60), 255)]


def light_effects():
    return [
        effect("monster_light_bolt", "Monster light missile (projectile)",
               "Monsters' light missile: a white-gold glint with a thin golden ribbon and sparkles.",
               [sprite("glow", 0.8, (255, 230, 150), 200),
                sprite("flare_cross", 0.45, (255, 252, 235), 0),
                ribbon("trail_noise", 12, 260, 0.3, GOLD, fill=0.6, erosion=0.4, core=0.6, scroll=2.5),
                shed("spark", scales(0.045, 0.01), [key(0, (255, 250, 220), 0), key(1, (255, 200, 90), 255)], 0.4,
                     distance=34, radius=8, velocity=25)]),
        effect("light_bolt", "Light bolt (projectile)",
               "Light Bolt: a radiant white-gold starburst head, a golden ribbon with a white core and sparkles.",
               [sprite("glow", 1.2, (255, 225, 140), 180),
                sprite("starburst", 0.55, (255, 250, 230), 0, pulse=(0.3, 0.9, 1.1)),
                sprite("glow", 0.26, (255, 255, 245)),
                ribbon("trail_noise", 20, 420, 0.35, GOLD, fill=0.7, erosion=0.35, core=0.8, scroll=3),
                shed("spark", scales(0.06, 0.01), [key(0, (255, 252, 230), 0), key(1, (255, 190, 80), 255)], 0.5,
                     distance=22, radius=12, velocity=40)]),
        effect("sunray", "Sunray (projectile)",
               "Sunray: a blinding golden lance, a wide white-cored ribbon behind a large starburst; replaces the "
               "flat beam.",
               [sprite("glow", 1.6, (255, 220, 120), 170),
                sprite("flare_star", 0.8, (255, 252, 235), 0),
                sprite("glow", 0.35, (255, 255, 250)),
                ribbon("trail_noise", 34, 700, 0.45, [key(0, (255, 252, 235), 0), key(0.4, (255, 225, 140), 60),
                                                      key(1, (240, 170, 60), 255)],
                       width_keys=scales(1.0, 0.6), fill=0.85, erosion=0.25, core=1.0, scroll=3.5,
                       texture_length=160),
                shed("glint", scales(0.08, 0.015), [key(0, (255, 255, 240), 0), key(1, (255, 200, 90), 255)], 0.6,
                     distance=28, radius=16, velocity=35)]),
        effect("destroy_undead", "Destroy undead (projectile)",
               "Destroy Undead: a holy white-gold soft star with drifting sparkles.",
               [sprite("glow", 0.9, (255, 240, 190), 190),
                sprite("soft_star", 0.4, (255, 252, 235), 0, pulse=(0.35, 0.9, 1.1)),
                shed("spark", scales(0.05, 0.01), [key(0, (255, 252, 230), 0), key(1, (255, 210, 120), 255)], 0.6,
                     distance=26, radius=10, velocity=25, wind=rising(30))]),
    ]


def dark_effects():
    return [
        effect("monster_dark_bolt", "Monster dark missile (projectile)",
               "Monsters' dark missile: an alpha-blended black-violet smoke body and dark ribbon around a dim "
               "violet core, so it reads dark against any ground.",
               [sprite("glow", 0.8, (120, 50, 170), 200),
                sprite("glow", 0.3, (25, 10, 35), 60, blend="alpha"),
                sprite("glow", 0.12, (200, 140, 255), 60),
                ribbon("trail_noise", 22, 280, 0.4, [key(0, (30, 10, 40), 80), key(1, (20, 15, 25), 255)],
                       blend="alpha", fill=0.45, erosion=0.55, scroll=1.5),
                smoke(0.2, 0.4, 0.45, 18, [key(0, (35, 15, 50), 110), key(1, (20, 15, 25), 255)],
                      texture="wisp_smoke", velocity=15, wind=None)]),
        effect("toxic_cloud", "Toxic cloud (projectile)",
               "Toxic Cloud: a cloud of green poison breathing round the ghostly skull (its model), rolling out "
               "heavy green-black smoke.",
               [sprite("glow", 0.9, (90, 160, 40), 180),
                sprite("smoke_puff", 0.75, (90, 150, 55), 110, blend="alpha", pulse=(1.3, 0.85, 1.1)),
                sprite("smoke_puff", 0.6, (120, 190, 70), 140, blend="alpha", pulse=(0.9, 1.1, 0.9)),
                smoke(0.3, 0.6, 0.7, 12, [key(0, (70, 120, 35), 90), key(0.5, (45, 70, 28), 150),
                                     key(1, (25, 30, 20), 255)], velocity=18, wind=None, radius=12),
                smoke(0.2, 0.4, 0.5, 16, [key(0, (130, 200, 70), 120), key(1, (60, 100, 30), 255)],
                      texture="wisp_smoke", velocity=20, wind=None)]),
        effect("sharpmetal", "Sharpmetal (projectile)",
               "Sharpmetal: the native shards stay visible, with metallic glints and thin dark streaks.",
               [sprite("glow", 0.6, (200, 200, 220), 205),
                shed("streak", scales(0.12, 0.05), [key(0, (210, 215, 230), 60), key(1, (90, 90, 110), 255)], 0.25,
                     distance=30, radius=4, velocity=10, velocity_aligned=True, stretch=2.0),
                shed("glint", scales(0.05, 0.01), [key(0, (255, 255, 255), 0), key(1, (160, 160, 190), 255)], 0.25,
                     interval=0.05, radius=6, velocity=40)]),
    ]


def tech_effects():
    return [
        effect("blaster", "Blaster bolt (projectile)",
               "Blaster: a red-hot energy bolt, a white-hot core in a red glow trailing a solid red ribbon with a "
               "white core.",
               [sprite("glow", 0.7, (255, 60, 40), 185),
                sprite("glow", 0.3, (255, 120, 100), 60),
                sprite("glow", 0.14, (255, 240, 230), 0),
                ribbon("trail_noise", 10, 260, 0.2, [key(0, (255, 235, 225), 0), key(0.3, (255, 90, 60), 60),
                                                     key(1, (255, 40, 30), 255)],
                       width_keys=scales(1.0, 0.5), fill=1.0, erosion=0.15, core=1.0, scroll=0)]),
    ]


def variant_effects():
    """Per-monster flights for shared monster missiles, and the smaller projectiles (arrows, sparks, armed spike)."""
    return [
        effect("dragon_fire", "Dragon fire (projectile)",
               "Dragons', fire lizards', drakes' and the fire hydra's fire missile: the flame gout at dragon scale, "
               "a bright head and a long tongue of flame over smoke, kept slim so the trail does not balloon.",
               [sprite("glow", 1.15, (255, 95, 25), 190),
                sprite("fireball", 0.5, (255, 185, 120), 30),
                sprite("glow", 0.22, (255, 235, 190)),
                smoke(0.27, 0.55, 0.7, 12, FIRE_SMOKE, texture="smoke_puff", velocity=18, radius=10),
                flame_tongue(0.3, 0.06, 0.3, 6, [key(0, (255, 205, 125), 50), key(0.35, (255, 110, 30), 115),
                                              key(1, (140, 30, 8), 255)], radius=6, velocity=50, grow=2.2),
                sparks((255, 205, 120), (255, 70, 15), interval=0.02, velocity=100, lifetime=0.6, per_emission=2,
                       radius=7)]),
        effect("lava_glob", "Lava glob (projectile)",
               "Gogs' and the fire beast's fire missile: a dark crusted core with glowing cracks, molten drips "
               "falling under gravity and black smoke.",
               [sprite("glow", 0.8, (255, 90, 20), 195),
                sprite("debris", 0.3, (60, 30, 20), 0, blend="alpha"),
                sprite("fireball", 0.24, (255, 120, 40), 90),
                smoke(0.22, 0.5, 0.55, 16, [key(0, (40, 25, 20), 110), key(0.5, (30, 25, 22), 170),
                                       key(1, (25, 22, 22), 255)], texture="smoke_puff", velocity=16),
                shed("glow", scales(0.07, 0.03), [key(0, (255, 170, 60), 20), key(1, (200, 40, 10), 255)], 0.55,
                     distance=24, radius=6, velocity=40, wind=falling(320)),
                sparks((255, 170, 80), (200, 50, 10), interval=0.06, velocity=70, wind=falling(80))]),
        effect("living_flame", "Living flame (projectile)",
               "Fire elementals', efreets' and genies' fire missile: pure bright flickering flame with many "
               "embers and no smoke.",
               [sprite("glow", 1.0, (255, 130, 40), 180),
                sprite("fireball", 0.42, (255, 215, 150), 10, pulse=(0.15, 0.85, 1.1)),
                sprite("glow", 0.22, (255, 250, 220)),
                flame_tongue(0.32, 0.05, 0.18, 7, [key(0, (255, 230, 160), 40), key(0.4, (255, 140, 40), 110),
                                            key(1, (220, 60, 10), 255)], radius=8, velocity=60),
                shed("flame_lick", scales(0.14, 0.04), [key(0, (255, 210, 120), 40), key(1, (230, 70, 10), 255)],
                     0.3, distance=26, radius=8, velocity=50, wind=rising(90), roll=True),
                sparks((255, 230, 150), (255, 90, 20), interval=0.015, velocity=140, lifetime=0.55,
                       per_emission=2)]),
        effect("frost_breath", "Frost breath (projectile)",
               "Water dragons' and wyrms' missile: a gout of freezing mist that widens as it flies, with ice "
               "glints and frost shards.",
               [sprite("glow", 1.4, (120, 200, 255), 185),
                sprite("flare", 0.55, (225, 245, 255), 0),
                smoke(0.3, 0.75, 0.55, 12, [key(0, (220, 245, 255), 120), key(0.5, (170, 215, 250), 170),
                                       key(1, (140, 190, 240), 255)], texture="wisp_smoke", velocity=40,
                      wind=falling(15), radius=14),
                shed("glint", scales(0.08, 0.015), [key(0, (240, 250, 255), 0), key(1, (140, 200, 255), 255)],
                     0.6, distance=20, radius=16, velocity=40, wind=falling(60)),
                shed("streak", scales(0.1, 0.04), [key(0, (230, 248, 255), 40), key(1, (120, 180, 240), 255)],
                     0.35, distance=34, radius=10, velocity=60, velocity_aligned=True, stretch=2.0)]),
        effect("energy_breath", "Energy breath (projectile)",
               "Crystal, gold and mega dragons', energy drakes' and the chaos hydra's energy missile: a "
               "prismatic white-violet lance with a cyan electric arc and shed light motes.",
               [sprite("glow", 1.4, (180, 130, 255), 180),
                sprite("flare_star", 0.6, (245, 235, 255), 0, pulse=(0.2, 0.9, 1.1)),
                sprite("glow", 0.3, (255, 255, 255)),
                ribbon("trail_noise", 26, 460, 0.4, [key(0, (240, 225, 255), 20), key(0.5, (170, 110, 255), 110),
                                                     key(1, (90, 60, 220), 255)],
                       fill=0.65, erosion=0.35, core=0.8, scroll=3),
                ribbon("trail_electric", 30, 520, 0.35, [key(0, (220, 255, 255), 0), key(1, (80, 180, 255), 255)],
                       width_keys=scales(1.0, 0.6), sample=20, texture_length=90, scroll=6, fill=0, erosion=0.4,
                       jitter=9, jitter_rate=24),
                shed("soft_star", scales(0.1, 0.02), [key(0, (240, 220, 255), 20), key(1, (120, 200, 255), 255)],
                     0.5, distance=30, radius=12, velocity=40, roll=True, spin=3)]),
        effect("arcane_bolt", "Arcane bolt (projectile)",
               "Archmages', warlocks' and power liches' energy missile: a violet arcane knot trailing a white-cored "
               "ribbon and twinkling motes.",
               [sprite("glow", 0.9, (170, 90, 255), 185),
                sprite("arcane", 0.34, (225, 190, 255), 20),
                sprite("glow", 0.16, (250, 240, 255)),
                ribbon("trail_noise", 16, 340, 0.35, [key(0, (235, 215, 255), 20), key(1, (110, 40, 220), 255)],
                       fill=0.6, erosion=0.4, core=0.7, scroll=2.5),
                shed("spark", scales(0.05, 0.01), [key(0, (240, 220, 255), 0), key(1, (140, 70, 255), 255)], 0.45,
                     distance=24, radius=10, velocity=35)]),
        effect("necrotic_breath", "Necrotic breath (projectile)",
               "Bone dragons' dark missile: a ghostly gout of green-black grave smoke with pale wisps.",
               [sprite("glow", 1.2, (90, 200, 120), 195),
                sprite("glow", 0.45, (15, 30, 20), 70, blend="alpha"),
                sprite("glow", 0.18, (200, 255, 210), 40),
                smoke(0.26, 0.6, 0.5, 16, [key(0, (45, 80, 55), 150), key(0.5, (35, 55, 42), 195),
                                       key(1, (30, 40, 34), 255)], texture="smoke_puff", velocity=30, wind=None,
                      radius=14),
                shed("wisp", scales(0.2, 0.08), [key(0, (170, 255, 190), 80), key(1, (40, 120, 70), 255)], 0.5,
                     distance=26, radius=12, velocity=30, roll=True, spin=2)]),
        effect("arrow", "Arrow (projectile)",
               "Arrows: the native arrow with a faint, short air streak behind it.",
               [ribbon("trail_noise", 4, 110, 0.12, [key(0, (235, 240, 250), 170), key(1, (200, 210, 230), 255)],
                       width_keys=scales(1.0, 0.4), sample=12, fill=0.8, erosion=0.3, scroll=0)]),
        effect("fire_arrow", "Fire arrow (projectile)",
               "Fire arrows: the native arrow burning, a small flame tongue over a thin smoke line.",
               [sprite("glow", 0.45, (255, 120, 40), 200),
                smoke(0.08, 0.2, 0.35, 16, SPAT_SMOKE, velocity=8, radius=2),
                flame_tongue(0.13, 0.03, 0.12, 8, FIRE_TONGUE, radius=2, velocity=20),
                sparks((255, 210, 130), (255, 80, 20), interval=0.07, velocity=50, lifetime=0.35, scale=0.03)]),
        effect("sparks", "Sparks (projectile)",
               "Sparks: each bouncing spark is a crackling ball of white-blue electricity (two electric cores breathing "
               "out of step and a cross flare, as the native sprite drew it), with a glow and a short crackling arc.",
               [sprite("glow", 0.55, (130, 180, 255), 150),
                sprite("electric", 0.3, (235, 242, 255), 0, pulse=(0.09, 0.7, 1.25)),
                sprite("electric", 0.2, (200, 220, 255), 30, pulse=(0.13, 1.2, 0.75)),
                sprite("flare_cross", 0.16, (255, 255, 255), 20, pulse=(0.07, 0.8, 1.2)),
                ribbon("trail_electric", 10, 140, 0.18, ELECTRIC, width_keys=scales(1.0, 0.5), sample=10,
                       texture_length=60, scroll=6, fill=0, erosion=0.4, jitter=4, jitter_rate=26)]),
        effect("fire_spike_mine", "Armed fire spike (settled)",
               "An armed Fire Spike lying on the ground: a pulsing glow, small flickering flames and sparks rising "
               "slowly, so the player can see where it lies.",
               [sprite("glow", 0.8, (255, 120, 40), 185, pulse=(0.6, 0.7, 1.1)),
                sprite("glint", 0.3, (255, 220, 150), 30, pulse=(0.35, 0.8, 1.15)),
                shed("flame_lick", scales(0.08, 0.02), [key(0, (255, 200, 110), 60), key(1, (220, 60, 10), 255)],
                     0.4, interval=0.08, radius=6, velocity=10, wind=rising(60), roll=True),
                sparks((255, 220, 140), (255, 80, 20), interval=0.12, velocity=25, lifetime=0.9, scale=0.035,
                       wind=rising(45))]),
    ]


WHITE = (255, 255, 255)


def fire_impacts():
    embers = lambda count, speed, life=0.8: burst(  # noqa: E731
        "spark", count, life, speed, scales(0.06, 0.012), [key(0, (255, 225, 140), 0), key(0.5, (255, 120, 30), 40),
                                                           key(1, (150, 30, 5), 255)],
        radius=8, wind=falling(260), velocity_aligned=True, stretch=2.2)
    smoke_rise = lambda count, size, life, start=0.15, rgb=(70, 60, 55): burst(  # noqa: E731
        "smoke_puff", count, life, 40, scales(size, size * 2.2), [key(0, rgb, 120), key(0.4, rgb, 170),
                                                                   key(1, rgb, 255)],
        start=start, blend="alpha", radius=size * 60, wind=rising(45), roll=True, spin=0.6, lift=10)
    return [
        impact("fire_small", "Small fire impact",
               "Fire Bolt and monster fire missiles: a flash, a burst of flame with embers, and a little smoke.",
               1.6,
               [flash("glow", 0, 0.25, scales(0.6, 1.3), fade((255, 230, 180)), lift=24),
                flash("fire_burst", 0, 0.8, scales(0.3, 0.55), fade((255, 235, 215), 0, peak=0.45), blend="alpha",
                      lift=30),
                flash("fireball", 0, 0.35, scales(0.25, 0.55), fade((255, 215, 150), 0, (255, 110, 30)), lift=30),
                embers(10, 170),
                smoke_rise(2, 0.18, 1.2)]),
        impact("fireball", "Fireball explosion",
               "Fireball, Dragon Breath and Flame Blast (damage radius 512): a blinding flash and rays, a big churning "
               "explosion with smaller blasts flung around it, a shockwave racing over the ground to the edge of the "
               "blast, embers to the edge and a lingering smoke cloud.",
               3.0,
               [flash("glow", 0, 0.4, scales(2.5, 6.0), fade((255, 220, 160)), lift=30),
                flash("rays", 0, 0.3, scales(2.0, 5.0), fade((255, 210, 130)), lift=30),
                flash("explosion", 0, 1.1, scales(2.4, 3.8), fade((255, 235, 215), 0, peak=0.45), blend="alpha",
                      lift=60),
                burst("fire_burst", 8, 0.9, 260, scales(0.8, 1.4), fade((255, 235, 215), 0, peak=0.4),
                      blend="alpha", radius=120, wind=falling(320), roll=True, lift=40),
                flash("fireball", 0, 0.5, scales(1.5, 3.5), fade((255, 220, 160), 0, (255, 100, 25)), lift=45),
                flash("glow", 0, 0.9, scales(3.0, 5.0), fade((255, 150, 60), 40, (200, 60, 15)), lift=12,
                      ground=True),
                flash("ripple", 0, 0.6, scales(1.0, 8.0), fade((255, 225, 160), 0, (230, 90, 25)), lift=24,
                      ground=True),
                flash("ring", 0.08, 0.75, scales(0.8, 6.5), fade((255, 170, 80), 60, (200, 60, 15)), lift=24,
                      ground=True),
                embers(50, 620, 1.2),
                burst("smoke_puff", 8, 2.6, 90, scales(0.9, 1.9), fade((70, 60, 55), 120, peak=0.4), start=0.35,
                      blend="alpha", radius=180, wind=rising(50), roll=True, spin=0.4, lift=90)]),
        impact("fire_large", "Large fire impact",
               "Dragons', drakes' and the fire hydra's fire missile (no area damage): a bright flash and rays, a "
               "churning explosion with smaller blasts around it, a shock ring, flung embers and lingering smoke.",
               2.6,
               [flash("glow", 0, 0.35, scales(1.2, 2.8), fade((255, 220, 160)), lift=30),
                flash("rays", 0, 0.25, scales(0.8, 2.0), fade((255, 210, 130)), lift=30),
                flash("explosion", 0, 0.9, scales(0.9, 1.5), fade((255, 235, 215), 0, peak=0.45), blend="alpha",
                      lift=40),
                burst("fire_burst", 4, 0.7, 90, scales(0.4, 0.7), fade((255, 235, 215), 0, peak=0.4), blend="alpha",
                      radius=40, roll=True, lift=30),
                flash("fireball", 0, 0.45, scales(0.6, 1.4), fade((255, 220, 160), 0, (255, 100, 25)), lift=30),
                flash("ring", 0, 0.4, scales(0.3, 2.2), fade((255, 190, 100), 20, (220, 70, 20)), lift=10),
                embers(26, 300, 1.0),
                smoke_rise(5, 0.45, 2.2, start=0.3)]),
        impact("meteor", "Meteor impact",
               "Meteor Shower (damage radius 512 per meteor): a heavy ground burst, flame, a dust shockwave over the "
               "ground, dust thrown up, burning debris arcing out and smoke.",
               2.8,
               [flash("glow", 0, 0.35, scales(1.8, 4.2), fade((255, 220, 160)), lift=30),
                flash("fire_burst", 0, 0.9, scales(1.5, 2.4), fade((255, 235, 215), 0, peak=0.45), blend="alpha",
                      lift=50),
                flash("fireball", 0, 0.4, scales(0.9, 2.2), fade((255, 215, 150), 0, (255, 100, 25)), lift=40),
                flash("glow", 0, 0.8, scales(2.2, 3.6), fade((255, 150, 60), 50, (200, 60, 15)), lift=12,
                      ground=True),
                flash("ripple", 0, 0.6, scales(0.8, 6.0), fade((255, 210, 140), 20, (200, 80, 30)), lift=24,
                      ground=True),
                burst("dust_cloud", 8, 1.6, 240, scales(0.5, 1.3), fade((150, 120, 90), 90, (120, 100, 85)),
                      blend="alpha", radius=80, wind=falling(30), roll=True, spin=0.5, lift=30),
                burst("debris", 18, 1.1, 420, scales(0.16, 0.1), fade((90, 60, 40)), blend="alpha", radius=20,
                      wind=falling(600), roll=True, spin=6),
                embers(32, 480, 1.1),
                burst("smoke_puff", 6, 2.2, 70, scales(0.7, 1.5), fade((70, 60, 55), 120, peak=0.4), start=0.3,
                      blend="alpha", radius=120, wind=rising(45), roll=True, spin=0.5, lift=80)]),
        impact("incinerate", "Incinerate burst",
               "Incinerate: the target is engulfed, a white flash and a column of fire rising from it for about "
               "half a second.",
               1.4,
               [flash("glow", 0, 0.25, scales(0.6, 1.6), fade((255, 250, 225))),
                burst("flame_column", 2, 0.4, 20, scales(0.35, 0.22), [key(0, (255, 230, 170), 40),
                                                                    key(0.5, (255, 140, 40), 90),
                                                                    key(1, (200, 50, 10), 255)],
                      radius=18, wind=rising(140), window=0.6, interval=0.05, lift=-20),
                burst("spark", 3, 0.6, 90, scales(0.05, 0.01), fade((255, 230, 160), 0, (255, 80, 20)), radius=20,
                      wind=rising(160), window=0.6, interval=0.04)]),
        impact("fire_spike", "Fire spike burst",
               "Fire Spike: a sharp radial burst of flame spikes and sparks.",
               1.2,
               [flash("rays_thin", 0, 0.2, scales(0.5, 1.3), fade((255, 220, 140)), lift=12),
                flash("fire_burst", 0, 0.7, scales(0.25, 0.45), fade((255, 235, 215), 0, peak=0.45), blend="alpha",
                      lift=26),
                flash("fireball", 0, 0.3, scales(0.2, 0.45), fade((255, 220, 160), 0, (255, 110, 30)), lift=24),
                embers(18, 320, 0.5)]),
        impact("dark_fire", "Darkfire burst",
               "Darkfire Bolt: a burst of black-violet smoke with a magenta flash and orange burning sparks.",
               1.8,
               [flash("glow", 0, 0.25, scales(0.6, 1.4), fade((220, 80, 200)), lift=10),
                burst("smoke_puff", 4, 1.1, 70, scales(0.25, 0.55), fade((35, 10, 45), 60, (20, 15, 25)),
                      blend="alpha", radius=14, roll=True, spin=1.0, lift=10),
                burst("spark", 12, 0.6, 200, scales(0.05, 0.01), fade((255, 160, 90), 0, (200, 40, 160)),
                      radius=6, wind=falling(150), velocity_aligned=True, stretch=2.0)]),
        impact("fire_arrow", "Fire arrow impact",
               "Fire arrows: a small puff of flame and a few embers.",
               1.0,
               [flash("fire_burst", 0, 0.6, scales(0.15, 0.28), fade((255, 235, 215), 0, peak=0.45), blend="alpha",
                      lift=14),
                flash("fireball", 0, 0.25, scales(0.12, 0.25), fade((255, 215, 150), 0, (255, 110, 30)), lift=14),
                embers(5, 120, 0.5)]),
        impact("lava_splash", "Lava splash",
               "Gogs' lava globs: a splash of molten drops, a small flame burst and black smoke.",
               1.8,
               [flash("glow", 0, 0.25, scales(0.5, 1.1), fade((255, 160, 70)), lift=10),
                flash("fire_burst", 0, 0.7, scales(0.25, 0.45), fade((255, 235, 215), 0, peak=0.45), blend="alpha",
                      lift=26),
                burst("glow", 14, 0.8, 220, scales(0.08, 0.04), fade((255, 160, 60), 20, (180, 40, 10)), radius=8,
                      wind=falling(600)),
                smoke_rise(3, 0.25, 1.4, start=0.1, rgb=(30, 25, 22))]),
    ]


def energy_impacts():
    return [
        impact("air_small", "Small electric impact",
               "Monsters' air missiles and Sparks: an electric flash, a cross glint, a quick spray of sparks "
               "and a ring.",
               0.8,
               [flash("electric", 0, 0.15, scales(0.3, 0.6), fade((230, 240, 255))),
                flash("flare_cross", 0, 0.2, scales(0.5, 0.9), fade((170, 210, 255))),
                flash("ring", 0, 0.3, scales(0.15, 0.9), fade((150, 200, 255), 40)),
                burst("spark", 12, 0.3, 300, scales(0.05, 0.01), fade((240, 248, 255), 0, (90, 140, 255)),
                      velocity_aligned=True, stretch=3)]),
        impact("lightning", "Lightning strike",
               "Lightning Bolt and storm breath: a blinding blue-white flash, flickering electric blobs, a wide "
               "flare, a spray of sparks and a ring.",
               1.0,
               [flash("glow", 0, 0.25, scales(0.8, 2.0), fade((210, 230, 255))),
                flash("flare_wide", 0, 0.25, scales(1.0, 1.8), fade((190, 215, 255))),
                burst("electric", 3, 0.12, 30, scales(0.3, 0.5), fade((235, 245, 255)), radius=24, roll=True,
                      window=0.35, interval=0.06),
                flash("ring", 0, 0.35, scales(0.2, 1.6), fade((160, 200, 255), 30)),
                burst("spark", 26, 0.4, 380, scales(0.06, 0.01), fade((240, 248, 255), 0, (90, 130, 255)),
                      velocity_aligned=True, stretch=3)]),
        impact("starburst", "Starburst impact",
               "Starburst stars: a golden star flash with rays, a ring and falling glitter.",
               1.4,
               [flash("flare_star", 0, 0.35, scales(0.5, 1.3), fade((255, 240, 190))),
                flash("rays", 0, 0.25, scales(0.5, 1.2), fade((255, 210, 120))),
                flash("ring", 0, 0.35, scales(0.2, 1.2), fade((255, 220, 140), 40)),
                burst("spark", 18, 0.9, 200, scales(0.05, 0.01), fade((255, 245, 200), 0, (255, 160, 60)),
                      wind=falling(200))]),
        impact("energy_burst", "Energy burst",
               "Energy breath: a prismatic white-violet star flash, rays, a cyan ring and violet and cyan sparks.",
               1.2,
               [flash("glow", 0, 0.3, scales(0.8, 1.8), fade((220, 190, 255))),
                flash("flare_star", 0, 0.35, scales(0.6, 1.4), fade((245, 235, 255))),
                flash("rays", 0, 0.25, scales(0.5, 1.3), fade((190, 150, 255))),
                flash("ring", 0, 0.4, scales(0.2, 1.5), fade((140, 220, 255), 30)),
                burst("spark", 20, 0.6, 280, scales(0.06, 0.01), fade((235, 215, 255), 0, (100, 200, 255)),
                      velocity_aligned=True, stretch=2.5)]),
        impact("arcane_burst", "Arcane burst",
               "Arcane bolts: a violet arcane flash, a spinning swirl and motes.",
               1.0,
               [flash("glow", 0, 0.25, scales(0.5, 1.2), fade((200, 140, 255))),
                burst("swirl", 1, 0.5, 0, scales(0.25, 0.7), fade((210, 160, 255), 30), radius=0, spin=7),
                burst("spark", 12, 0.5, 160, scales(0.05, 0.01), fade((240, 220, 255), 0, (130, 60, 255)))]),
        impact("blaster", "Blaster hit",
               "Blaster: a red-hot wide flash, a spray of red sparks and a wisp of smoke.",
               0.9,
               [flash("flare_wide", 0, 0.2, scales(0.6, 1.1), fade((255, 120, 100))),
                flash("glow", 0, 0.2, scales(0.4, 0.9), fade((255, 200, 190))),
                burst("spark", 14, 0.35, 280, scales(0.05, 0.01), fade((255, 220, 200), 0, (255, 40, 30)),
                      velocity_aligned=True, stretch=2.5),
                burst("smoke_puff", 1, 0.8, 20, scales(0.12, 0.25), fade((70, 65, 65), 140), start=0.05,
                      blend="alpha", wind=rising(40), roll=True)]),
    ]


def water_earth_impacts():
    def droplets(rgb, end_rgb, count=16, blend="additive", transparency=20):
        return burst("glow", count, 0.7, 200, scales(0.06, 0.03), fade(rgb, transparency, end_rgb), blend=blend,
                     radius=6, wind=falling(520))

    def mist(rgb, count=2, size=0.3, life=0.9, transparency=110, wind=None):
        return burst("dust_cloud", count, life, 60, scales(size * 0.5, size), fade(rgb, transparency),
                     blend="alpha", radius=12, wind=wind, roll=True, spin=0.4, lift=6)

    dust = (160, 130, 95)
    return [
        impact("water_small", "Water splash",
               "Monsters' water missiles: a splash of droplets, spray mist and a ripple ring.",
               1.2,
               [flash("glow", 0, 0.2, scales(0.4, 0.9), fade((190, 235, 255))),
                flash("ring", 0, 0.4, scales(0.15, 1.0), fade((140, 210, 255), 50)),
                droplets((190, 235, 255), (60, 140, 230)),
                mist((210, 235, 250))]),
        impact("ice", "Ice burst",
               "Ice Bolt and frost breath: a cold flare, ice glints, frost shards flung out and frost mist.",
               1.4,
               [flash("flare", 0, 0.3, scales(0.5, 1.2), fade((225, 245, 255))),
                burst("glint", 14, 0.7, 150, scales(0.08, 0.015), fade((240, 250, 255), 0, (140, 200, 255)),
                      radius=10, wind=falling(120)),
                burst("streak", 10, 0.45, 240, scales(0.12, 0.05), fade((230, 248, 255), 30, (120, 180, 240)),
                      velocity_aligned=True, stretch=2.0, wind=falling(300)),
                mist((220, 240, 255), count=3, size=0.4, life=1.2)]),
        impact("ice_shard", "Ice shard hit",
               "Ice Blast shards: a few glints and a puff of frost.",
               0.8,
               [flash("flare_cross", 0, 0.2, scales(0.3, 0.6), fade((225, 245, 255))),
                burst("glint", 6, 0.4, 120, scales(0.05, 0.01), fade((240, 250, 255), 0, (140, 200, 255))),
                mist((220, 240, 255), count=1, size=0.2, life=0.6)]),
        impact("poison", "Poison splash",
               "Poison Spray: green droplets splashing and a low green mist.",
               1.3,
               [droplets((140, 220, 70), (70, 130, 30), count=14, blend="alpha", transparency=40),
                mist((100, 160, 50), count=2, size=0.3, transparency=150, wind=falling(10))]),
        impact("acid", "Acid splash",
               "Acid Burst: yellow-green acid splashing, a bubbling glow and hissing vapour rising.",
               1.5,
               [flash("glow", 0, 0.4, scales(0.5, 0.9), fade((200, 240, 80), 60)),
                droplets((210, 240, 80), (110, 150, 20), count=16, blend="alpha", transparency=30),
                burst("smoke_puff", 3, 1.2, 30, scales(0.15, 0.35), fade((200, 230, 120), 150), start=0.1,
                      blend="alpha", radius=14, wind=rising(60), roll=True, spin=0.6)]),
        impact("earth_small", "Earth impact",
               "Monsters' earth missiles: a thump of dust, pebbles flung out and a faint amber flash.",
               1.4,
               [flash("glow", 0, 0.2, scales(0.3, 0.7), fade((240, 190, 120), 60)),
                mist(dust, count=3, size=0.35, life=1.1, transparency=80, wind=falling(20)),
                burst("debris", 10, 0.8, 200, scales(0.1, 0.07), fade((120, 95, 70)), blend="alpha", radius=6,
                      wind=falling(520), roll=True, spin=6)]),
        impact("rock", "Rock blast impact",
               "Rock Blast: a heavier burst of dust and stones with a dust ring.",
               1.8,
               [flash("glow", 0, 0.25, scales(0.5, 1.0), fade((240, 190, 120), 60)),
                flash("ring", 0, 0.45, scales(0.2, 1.4), fade((170, 140, 100), 120), blend="alpha"),
                mist(dust, count=5, size=0.5, life=1.4, transparency=70, wind=falling(20)),
                burst("debris", 16, 1.0, 260, scales(0.14, 0.09), fade((110, 85, 60)), blend="alpha", radius=10,
                      wind=falling(520), roll=True, spin=6)]),
        impact("death_blossom", "Death blossom burst",
               "Death Blossom: a sickly green-brown burst of dust and seeds.",
               1.6,
               [flash("glow", 0, 0.3, scales(0.6, 1.3), fade((180, 210, 90), 40)),
                mist((120, 120, 80), count=4, size=0.45, life=1.3, transparency=90),
                burst("spark", 14, 0.8, 200, scales(0.05, 0.01), fade((210, 230, 140), 0, (90, 110, 40)),
                      wind=falling(220)),
                burst("debris", 8, 0.8, 200, scales(0.08, 0.05), fade((70, 60, 40)), blend="alpha",
                      wind=falling(480), roll=True, spin=5)]),
        impact("blades", "Blades hit",
               "Blades and Sharpmetal: a silver slash, a cross glint and flying metallic glints.",
               0.8,
               [flash("slash", 0, 0.18, scales(0.3, 0.6), fade((235, 240, 250))),
                flash("flare_cross", 0, 0.2, scales(0.3, 0.7), fade((230, 235, 250))),
                burst("glint", 10, 0.35, 220, scales(0.05, 0.01), fade(WHITE, 0, (160, 170, 200))),
                burst("streak", 6, 0.3, 200, scales(0.1, 0.04), fade((200, 205, 220), 60, (90, 90, 110)),
                      blend="alpha", velocity_aligned=True, stretch=2.0)]),
    ]


def spirit_impacts():
    def wisps(rgb, end_rgb, count=8, life=0.6, wind=None, transparency=60):
        return burst("wisp", count, life, 90, scales(0.18, 0.08), fade(rgb, transparency, end_rgb), radius=10,
                     wind=wind, roll=True, spin=3)

    def sparkles(rgb, end_rgb, count=12, wind=None, speed=150, life=0.7):
        return burst("spark", count, life, speed, scales(0.05, 0.01), fade(rgb, 0, end_rgb), radius=8, wind=wind)

    return [
        impact("body", "Body energy burst",
               "Monsters' body missiles: a pulse of green-teal life energy breaking into wisps.",
               1.0,
               [flash("glow", 0, 0.3, scales(0.5, 1.1), fade((120, 240, 190), 30)),
                wisps((150, 245, 200), (40, 150, 110))]),
        impact("harm", "Harm",
               "Harm: a blood-red pulse on the target, dark red wisps and a stain of red smoke.",
               1.3,
               [flash("glow", 0, 0.35, scales(0.5, 1.2), fade((230, 40, 40), 30)),
                wisps((230, 50, 50), (90, 10, 10), count=10),
                burst("smoke_puff", 2, 1.0, 30, scales(0.15, 0.35), fade((90, 10, 10), 140), blend="alpha",
                      radius=10, roll=True, spin=0.8)]),
        impact("flying_fist", "Flying fist impact",
               "Flying Fist: two shock rings, an orange flash and force streaks.",
               0.9,
               [flash("glow", 0, 0.2, scales(0.5, 1.0), fade((255, 150, 100))),
                flash("ring", 0, 0.3, scales(0.2, 1.2), fade((255, 140, 90), 40)),
                flash("ring", 0.1, 0.45, scales(0.2, 1.6), fade((230, 90, 60), 80)),
                burst("streak", 8, 0.25, 260, scales(0.12, 0.05), fade((255, 170, 120), 40, (200, 60, 30)),
                      velocity_aligned=True, stretch=2.5)]),
        impact("mind", "Mind impact",
               "Monsters' mind missiles: an amber star flash and two expanding lilac ripples.",
               1.0,
               [flash("soft_star", 0, 0.3, scales(0.3, 0.7), fade((255, 230, 160))),
                flash("ripple", 0, 0.45, scales(0.1, 0.9), fade((230, 190, 240), 60)),
                flash("ripple", 0.12, 0.6, scales(0.1, 1.2), fade((180, 130, 230), 100)),
                wisps((240, 210, 150), (170, 120, 210), count=6)]),
        impact("mind_blast", "Mind blast",
               "Mind Blast and Psychic Shock: a violet flash, a spinning psychic swirl, bright ripples and wisps.",
               1.2,
               [flash("glow", 0, 0.3, scales(0.6, 1.4), fade((200, 140, 255))),
                burst("swirl", 1, 0.6, 0, scales(0.25, 0.9), fade((220, 180, 255), 20), radius=0, spin=8),
                flash("ripple", 0, 0.45, scales(0.15, 1.2), fade((230, 190, 255), 40)),
                flash("ripple", 0.15, 0.6, scales(0.15, 1.6), fade((150, 90, 230), 90)),
                wisps((220, 170, 255), (110, 50, 200), count=10)]),
        impact("spirit", "Spirit impact",
               "Monsters' spirit missiles: a silver glint and ghostly wisps rising.",
               1.2,
               [flash("flare_cross", 0, 0.3, scales(0.4, 0.8), fade((230, 240, 255))),
                wisps((220, 235, 255), (130, 150, 230), count=8, life=0.9, wind=rising(80), transparency=90)]),
        impact("light_small", "Light impact",
               "Monsters' light missiles: a golden flare and sparkles.",
               1.0,
               [flash("flare", 0, 0.3, scales(0.4, 0.9), fade((255, 240, 190))),
                sparkles((255, 250, 220), (255, 200, 90), count=10)]),
        impact("light_bolt", "Light bolt impact",
               "Light Bolt: a radiant star flash with rays, a golden ring and a spray of sparkles.",
               1.2,
               [flash("glow", 0, 0.3, scales(0.6, 1.5), fade((255, 235, 170))),
                flash("flare_star", 0, 0.35, scales(0.5, 1.2), fade((255, 250, 230))),
                flash("rays", 0, 0.25, scales(0.5, 1.2), fade((255, 220, 130))),
                flash("ring", 0, 0.35, scales(0.2, 1.3), fade((255, 220, 140), 40)),
                sparkles((255, 252, 230), (255, 190, 80), count=20, speed=220)]),
        impact("sunray", "Sunray impact",
               "Sunray: a blinding golden flash, wide rays, a big ring and a shower of sparkles.",
               1.5,
               [flash("glow", 0, 0.4, scales(1.0, 2.4), fade((255, 240, 190))),
                flash("flare_star", 0, 0.45, scales(0.8, 1.8), fade((255, 252, 235))),
                flash("rays", 0, 0.35, scales(0.8, 2.0), fade((255, 220, 120))),
                flash("ring", 0, 0.45, scales(0.3, 2.0), fade((255, 220, 130), 30)),
                sparkles((255, 255, 240), (255, 200, 90), count=30, speed=300, life=0.9)]),
        impact("destroy_undead", "Destroy undead",
               "Destroy Undead: a holy star flash on the target with rays and sparkles rising.",
               1.4,
               [flash("soft_star", 0, 0.4, scales(0.4, 1.0), fade((255, 252, 235))),
                flash("flare_star", 0, 0.35, scales(0.4, 1.0), fade((255, 245, 210))),
                flash("rays_thin", 0, 0.3, scales(0.4, 1.0), fade((255, 230, 160))),
                sparkles((255, 252, 230), (255, 210, 120), count=16, wind=rising(120), speed=80, life=1.0)]),
        impact("dark_small", "Dark impact",
               "Monsters' dark missiles: a dim violet flash, a slow dark swirl and black-violet smoke.",
               1.3,
               [flash("glow", 0, 0.3, scales(0.4, 0.9), fade((140, 70, 190), 60)),
                burst("swirl", 1, 0.6, 0, scales(0.2, 0.6), fade((150, 90, 210), 60), radius=0, spin=-5),
                burst("smoke_puff", 3, 1.0, 50, scales(0.18, 0.4), fade((30, 12, 40), 80, (20, 15, 25)),
                      blend="alpha", radius=10, roll=True, spin=0.8)]),
        impact("necrotic", "Necrotic burst",
               "Bone dragons' necrotic breath: a burst of green-black grave smoke and pale wisps rising.",
               1.8,
               [flash("glow", 0, 0.3, scales(0.6, 1.4), fade((110, 220, 140), 50)),
                burst("smoke_puff", 5, 1.4, 70, scales(0.25, 0.6), fade((25, 45, 30), 80, (15, 20, 18)),
                      blend="alpha", radius=16, roll=True, spin=0.6),
                wisps((170, 255, 190), (40, 120, 70), count=10, life=0.9, wind=rising(90), transparency=80)]),
        impact("toxic_cloud", "Toxic cloud burst",
               "Toxic Cloud: a lingering cloud of green-black poison smoke.",
               2.8,
               [flash("glow", 0, 0.5, scales(0.6, 1.3), fade((110, 190, 50), 80)),
                burst("smoke_puff", 6, 2.2, 60, scales(0.3, 0.75), fade((50, 80, 30), 90, (25, 30, 20)),
                      blend="alpha", radius=24, roll=True, spin=0.4, lift=10),
                burst("dust_cloud", 3, 1.6, 40, scales(0.25, 0.55), fade((120, 190, 70), 160), blend="alpha",
                      radius=20, roll=True, spin=0.3, lift=10)]),
    ]


INSECT = [key(0, (22, 18, 10), 0), key(0.7, (40, 32, 18), 30), key(1, (40, 32, 18), 255)]
FIRE_LICK = [key(0, (255, 230, 170), 40), key(0.5, (255, 140, 40), 90), key(1, (200, 50, 10), 255)]
RAINBOW = [(255, 80, 80), (255, 170, 60), (255, 240, 90), (110, 240, 110), (100, 170, 255), (190, 110, 255)]


def spell_flights():
    """Spells that had kept their native sprites or drew nothing: flights, a visual-only debuff bolt and the drain
    wisps that fly back to the party."""
    return [
        effect("deadly_swarm", "Deadly swarm (projectile)",
               "Deadly Swarm: a buzzing cloud of insects around a faint dark haze, amber wing glints and stragglers "
               "dropping behind; replaces the native swarm sprite.",
               [sprite("glow", 0.6, (40, 34, 20), 130, blend="alpha"),
                shed("spark", scales(0.11, 0.08), INSECT, 0.3, interval=0.008, per_emission=3, blend="alpha",
                     radius=34, velocity=90, velocity_aligned=True, stretch=1.6, local=True),
                shed("glint", scales(0.03, 0.008), fade((255, 210, 120), 40, (200, 140, 60)), 0.18, interval=0.04,
                     radius=24, velocity=40, local=True),
                shed("spark", scales(0.04, 0.03), INSECT, 0.5, distance=14, blend="alpha", radius=18, velocity=60,
                     velocity_aligned=True, stretch=1.5, wind=falling(20))]),
        effect("mass_distortion", "Mass distortion (projectile)",
               "Monsters' Mass Distortion: a small dark gravity well pulling violet rings into itself, leaving "
               "a wake of dark violet motes.",
               [sprite("glow", 0.6, (150, 110, 230), 200),
                sprite("glow", 0.25, (30, 15, 45), 60, blend="alpha"),
                shed("ring", scales(0.3, 0.04), fade((200, 170, 255), 60, (120, 80, 220)), 0.3, interval=0.08,
                     radius=0, local=True),
                smoke(0.12, 0.25, 0.4, 20, [key(0, (40, 20, 60), 120), key(1, (25, 15, 35), 255)],
                      texture="wisp_smoke", velocity=12, wind=None)]),
        effect("shrinking_ray", "Shrinking ray (bolt)",
               "Shrinking Ray: a visual-only violet beam from the party to its target, shedding rings that shrink "
               "as they fade.",
               [sprite("glow", 0.6, (220, 90, 255), 170),
                sprite("glow", 0.14, (255, 225, 255)),
                ribbon("trail_noise", 12, 900, 0.35, [key(0, (255, 230, 255), 0), key(0.4, (200, 80, 255), 80),
                                                      key(1, (120, 40, 220), 255)],
                       fill=0.8, erosion=0.3, core=0.9, scroll=3),
                shed("ring", scales(0.22, 0.02), fade((230, 150, 255), 40, (140, 60, 230)), 0.35, distance=60,
                     radius=0)]),
        effect("soul_drain", "Soul drain (return flight)",
               "Souldrinker: a pale soul torn from each victim swoops back to the party, trailing a ghostly ribbon "
               "that darkens to violet.",
               [sprite("glow", 0.7, (120, 220, 200), 190),
                sprite("glow", 0.18, (230, 255, 250)),
                ribbon("trail_noise", 7, 150, 0.3, [key(0, (210, 255, 245), 120), key(1, (90, 40, 160), 255)],
                       fill=0.3, erosion=0.6, scroll=1.5),
                shed("wisp", scales(0.14, 0.06), fade((200, 250, 240), 90, (100, 50, 170)), 0.4, distance=26,
                     radius=6, velocity=15)]),
        effect("life_drain", "Life drain (return flight)",
               "Lifedrain: a globule of the victim's blood swoops back to the party, trailing a red ribbon and "
               "dripping.",
               [sprite("glow", 0.6, (200, 20, 30), 180),
                sprite("glow", 0.16, (255, 150, 140)),
                ribbon("trail_noise", 7, 150, 0.3, [key(0, (255, 120, 110), 90), key(1, (110, 10, 15), 255)],
                       fill=0.5, erosion=0.5, scroll=1.5),
                shed("glow", scales(0.06, 0.03), fade((210, 30, 30), 40, (100, 10, 10)), 0.5, distance=22,
                     blend="alpha", radius=4, velocity=20, wind=falling(300))]),
    ]


def spell_impacts():
    """Impacts for the spells above and for the instant spells that kept the classic burst or drew nothing."""
    def ring(start, end, grow, rgb, transparency, end_rgb):
        return flash("ring", start, end, scales(*grow), fade(rgb, transparency, end_rgb))

    def pulled_in(texture, rgb, end_rgb, radius, window, speed=220, start=0.0):
        return burst(texture, 4, 0.4, -speed, scales(0.12, 0.05), fade(rgb, 0, end_rgb), start=start, radius=radius,
                     velocity_aligned=True, stretch=2.5, window=window, interval=0.025)

    rainbow_rings = [ring(index * 0.06, 0.6 + index * 0.06, (0.3, 1.2 + index * 0.2), rgb, 0, rgb)
                     for index, rgb in enumerate(RAINBOW)]
    rainbow_sparks = [burst("spark", 6, 0.8, 240, scales(0.08, 0.02), fade(rgb), radius=8, start=index * 0.05,
                            velocity_aligned=True, stretch=2.0)
                      for index, rgb in enumerate(RAINBOW)]
    meteor_trail = shed("fireball", scales(0.35, 0.1), FIRE_TONGUE, 0.35, interval=0.015, radius=10, velocity=30,
                        roll=True)
    meteor_trail.update({"start_seconds": 0, "end_seconds": 0.5})
    meteor_smoke = shed("smoke_puff", scales(0.3, 0.7), fade((60, 50, 45), 130, peak=0.4), 0.9, interval=0.03,
                        blend="alpha", radius=16, velocity=20, roll=True, spin=0.6)
    meteor_smoke.update({"start_seconds": 0, "end_seconds": 0.5})
    return [
        impact("deadly_swarm", "Deadly swarm",
               "Deadly Swarm: the insects engulf the target and crawl over it in a dark haze, then scatter.",
               2.1,
               [flash("glow", 0, 1.6, scales(0.8, 1.1), fade((40, 34, 20), 110, peak=0.7), blend="alpha"),
                burst("spark", 5, 0.35, 130, scales(0.12, 0.08), INSECT, blend="alpha", radius=65,
                      velocity_aligned=True, stretch=1.6, window=1.4, interval=0.008, local=True),
                burst("glint", 1, 0.2, 50, scales(0.03, 0.008), fade((255, 210, 120), 40, (200, 140, 60)), radius=50,
                      window=1.4, interval=0.05, local=True),
                burst("spark", 50, 0.8, 300, scales(0.11, 0.08), INSECT, start=1.35, blend="alpha", radius=30,
                      velocity_aligned=True, stretch=1.6)]),
        impact("mass_distortion", "Mass distortion",
               "Mass Distortion: violet rings and motes collapse into the target under a dark swirl, then the "
               "crush throws out a flash and stone chips.",
               1.4,
               [ring(0, 0.6, (1.5, 0.15), (170, 110, 255), 0, (110, 60, 220)),
                ring(0.15, 0.75, (1.3, 0.1), (200, 150, 255), 20, (110, 60, 220)),
                pulled_in("spark", (210, 170, 255), (120, 70, 220), 120, 0.6),
                burst("swirl", 1, 0.8, 0, scales(1.0, 0.2), fade((35, 15, 60), 40), blend="alpha", radius=0,
                      spin=-9),
                flash("glow", 0.5, 0.8, scales(0.4, 1.0), fade((220, 190, 255))),
                burst("debris", 8, 0.6, 180, scales(0.07, 0.05), fade((100, 80, 70)), start=0.5, blend="alpha",
                      wind=falling(400), roll=True, spin=6)]),
        impact("spirit_lash", "Spirit lash",
               "Spirit Lash: a spectral whip cracks across the target in two silver-blue slashes, with a glint, "
               "force streaks and ghostly wisps rising.",
               1.0,
               [flash("glow", 0, 0.35, scales(0.5, 1.0), fade((60, 90, 200), 60), blend="alpha"),
                flash("slash", 0, 0.3, scales(0.6, 1.1), fade((200, 225, 255))),
                flash("slash", 0.1, 0.4, scales(0.5, 1.0), fade((130, 180, 255))),
                flash("flare_cross", 0, 0.3, scales(0.5, 1.0), fade((220, 235, 255))),
                burst("streak", 8, 0.25, 260, scales(0.12, 0.04), fade((230, 240, 255), 30, (120, 150, 240)),
                      velocity_aligned=True, stretch=2.5),
                burst("wisp", 10, 0.7, 120, scales(0.18, 0.08), fade((210, 230, 255), 70, (120, 140, 230)),
                      radius=10, wind=rising(80), roll=True, spin=3)]),
        impact("prismatic_light", "Prismatic light",
               "Prismatic Light, on every creature in view: a white star flash and rays inside six staggered "
               "rainbow rings, with sparkles of each colour.",
               1.3,
               [flash("glow", 0, 0.5, scales(0.9, 2.0), fade(WHITE)),
                flash("flare_star", 0, 0.5, scales(0.7, 1.6), fade((255, 250, 240))),
                flash("rays", 0, 0.4, scales(0.6, 1.5), fade((255, 220, 255)))] + rainbow_rings + rainbow_sparks),
        impact("souldrinker", "Souldrinker",
               "Souldrinker, on every creature in view: a dark violet pulse and swirl tear pale soul wisps out of "
               "the victim; one soul then flies back to the party.",
               1.3,
               [flash("glow", 0, 0.35, scales(0.5, 1.1), fade((150, 60, 200), 30)),
                burst("swirl", 1, 0.6, 0, scales(0.3, 0.7), fade((40, 15, 60), 70), blend="alpha", radius=0,
                      spin=-6),
                burst("wisp", 8, 0.8, 70, scales(0.16, 0.08), fade((200, 240, 230), 60, (90, 40, 160)), radius=10,
                      wind=rising(120), roll=True, spin=3),
                burst("smoke_puff", 2, 1.0, 30, scales(0.15, 0.35), fade((30, 12, 40), 110), blend="alpha",
                      radius=10, roll=True, spin=0.8)]),
        impact("lifedrain", "Lifedrain",
               "Lifedrain: a blood-red pulse on the victim, drops of blood torn upwards and dark red wisps; the "
               "blood then flies back to the party.",
               1.2,
               [flash("glow", 0, 0.3, scales(0.5, 1.1), fade((220, 30, 40), 30)),
                burst("glow", 10, 0.5, 120, scales(0.06, 0.03), fade((220, 40, 40), 30, (110, 10, 10)),
                      blend="alpha", radius=10, wind=rising(160)),
                burst("wisp", 6, 0.6, 80, scales(0.16, 0.08), fade((220, 50, 50), 70, (90, 10, 10)), radius=10,
                      roll=True, spin=3)]),
        impact("shrinking_ray", "Shrinking ray",
               "Shrinking Ray: two violet rings and a stream of motes close in on the target, which shrinks "
               "under a final flash.",
               1.0,
               [ring(0, 0.45, (1.4, 0.1), (230, 150, 255), 30, (150, 60, 230)),
                ring(0.12, 0.55, (1.2, 0.1), (255, 200, 255), 50, (150, 60, 230)),
                pulled_in("spark", (255, 210, 255), (160, 70, 240), 90, 0.45, speed=200),
                flash("glow", 0.4, 0.7, scales(0.3, 0.8), fade((240, 190, 255)))]),
        impact("implosion", "Implosion",
               "Implosion: the air rushes into the target in contracting rings and streaks, then bursts back out "
               "in a blue-white flash and sparks.",
               1.3,
               [burst("swirl", 1, 0.55, 0, scales(1.3, 0.2), fade((20, 40, 110), 50), blend="alpha", radius=0,
                      spin=10),
                flash("glow", 0, 0.55, scales(1.6, 0.3), fade((90, 150, 255), 40, (220, 235, 255))),
                ring(0, 0.5, (1.7, 0.1), (110, 170, 255), 0, (170, 210, 255)),
                ring(0.12, 0.55, (1.4, 0.1), (170, 210, 255), 20, (170, 210, 255)),
                pulled_in("streak", (200, 225, 255), (80, 140, 255), 150, 0.5, speed=320),
                flash("glow", 0.52, 0.85, scales(0.6, 1.8), fade((235, 245, 255))),
                flash("flare_wide", 0.52, 0.8, scales(0.7, 1.6), fade((170, 210, 255))),
                ring(0.52, 0.9, (0.2, 1.6), (150, 200, 255), 0, (80, 130, 255)),
                burst("spark", 24, 0.4, 360, scales(0.07, 0.015), fade((240, 248, 255), 0, (90, 140, 255)),
                      start=0.52, velocity_aligned=True, stretch=3)]),
        impact("inferno", "Inferno",
               "Inferno, on every creature in view: the target is engulfed in rising columns of flame with a "
               "flash, embers and a little smoke.",
               1.6,
               [flash("glow", 0, 0.3, scales(0.6, 1.4), fade((255, 200, 120))),
                flash("fire_burst", 0, 0.8, scales(0.35, 0.6), fade((255, 235, 215), 0, peak=0.45), blend="alpha"),
                burst("flame_column", 2, 0.45, 20, scales(0.4, 0.25), FIRE_LICK, radius=22, wind=rising(160),
                      window=0.8, interval=0.06, lift=-40),
                burst("spark", 3, 0.7, 120, scales(0.05, 0.01), fade((255, 230, 160), 0, (255, 80, 20)), radius=24,
                      wind=rising(140), window=0.8, interval=0.05),
                burst("smoke_puff", 2, 1.0, 30, scales(0.2, 0.45), fade((60, 50, 45), 130), start=0.4,
                      blend="alpha", radius=16, wind=rising(60), roll=True, spin=0.6, lift=30)]),
        impact("immolation", "Immolation",
               "Immolation, on each creature near the party at every tick: a small lick of flame and a few "
               "embers.",
               0.9,
               [flash("fire_burst", 0, 0.6, scales(0.18, 0.3), fade((255, 235, 215), 0, peak=0.45), blend="alpha"),
                burst("flame_lick", 3, 0.4, 60, scales(0.14, 0.05), FIRE_LICK, radius=20, wind=rising(120),
                      roll=True),
                burst("spark", 5, 0.5, 120, scales(0.04, 0.01), fade((255, 220, 140), 0, (255, 80, 20)), radius=12,
                      wind=rising(100))]),
        impact("armageddon", "Armageddon strike",
               "Armageddon: a burning meteor falls for half a second (the engine times the strikes on that) and "
               "explodes in a flash, a fire burst, a ground shock ring, flung debris, embers and smoke.",
               2.6,
               [moving(flash("glow", 0, 0.5, scales(0.9), [key(0, (255, 150, 60), 60)]), (-350, 250, 1600)),
                moving(flash("fireball", 0, 0.5, scales(0.45), [key(0, (255, 220, 160), 0)]), (-350, 250, 1600)),
                moving(meteor_trail, (-350, 250, 1600)),
                moving(meteor_smoke, (-350, 250, 1600)),
                flash("glow", 0.5, 0.85, scales(1.4, 3.2), fade((255, 220, 160)), lift=30),
                flash("fire_burst", 0.5, 1.4, scales(1.0, 1.7), fade((255, 235, 215), 0, peak=0.45), blend="alpha",
                      lift=40),
                flash("fireball", 0.5, 0.9, scales(0.7, 1.6), fade((255, 215, 150), 0, (255, 100, 25)), lift=30),
                flash("ripple", 0.5, 1.1, scales(0.6, 4.5), fade((255, 210, 140), 20, (200, 80, 30)), lift=4,
                      ground=True),
                burst("debris", 12, 1.0, 380, scales(0.14, 0.09), fade((90, 60, 40)), start=0.5, blend="alpha",
                      radius=20, wind=falling(600), roll=True, spin=6),
                burst("spark", 24, 1.0, 420, scales(0.06, 0.012), FIRE_TONGUE, start=0.5, radius=8,
                      wind=falling(260), velocity_aligned=True, stretch=2.2),
                burst("smoke_puff", 4, 1.8, 60, scales(0.6, 1.3), fade((70, 60, 55), 120, peak=0.4), start=0.7,
                      blend="alpha", radius=80, wind=rising(45), roll=True, spin=0.5, lift=60)]),
    ]


def aura(effect_id, name, comment, duration, components):
    """A buff, heal or debuff aura (openyamm:fx/aura/...). Creature auras are centred on a creature 150 units tall
    (feet at -75, head near +60) and scaled to the real one; they follow it, so lingering parts are local."""
    return effect(effect_id, name, comment, components, duration, "aura")


def spell_auras():
    """Bound to spells in assets_dev/engine/effects/spell_auras.yml; they replace the procedural aura particles."""
    def feet_ring(start, end, grow, rgb, transparency=0, end_rgb=None):
        return flash("ring", start, end, scales(*grow), fade(rgb, transparency, end_rgb), lift=-72, ground=True)

    def rising_motes(texture, count, rgb, end_rgb, window=0.9, speed=40, wind=90, size=(0.07, 0.02), radius=45,
                     life=0.9, lift=-50, blend="additive"):
        return burst(texture, count, life, speed, scales(*size), fade(rgb, 0, end_rgb), radius=radius,
                     wind=rising(wind), window=window, interval=0.05, lift=lift, blend=blend, local=True)

    def body_glow(rgb, end, transparency=60, size=(0.9, 1.3), blend="additive", start=0.0):
        return flash("glow", start, end, scales(*size), fade(rgb, transparency, peak=0.5), blend=blend)

    gold = (255, 215, 110)
    heal_green = (120, 255, 150)
    return [
        # Creature debuffs: the moment a party spell's debuff lands.
        aura("debuff", "Debuff",
             "Any debuff without its own aura: a violet swirl tightening on the creature with wisps drawn in.",
             1.6,
             [burst("swirl", 1, 1.0, 0, scales(1.1, 0.5), fade((50, 20, 80), 60), blend="alpha", radius=0, spin=6),
              body_glow((170, 100, 255), 0.8),
              burst("wisp", 2, 0.6, -90, scales(0.18, 0.08), fade((210, 160, 255), 30, (120, 60, 220)), radius=70,
                    window=0.8, interval=0.06, roll=True, spin=3, local=True)]),
        aura("stun", "Stun",
             "Stun: a white flash, a golden halo over the head and stars twinkling around it.",
             1.8,
             [flash("flare_star", 0, 0.35, scales(0.7, 1.4), fade((255, 250, 220))),
              flash("glow", 0, 1.6, scales(0.6, 0.7), fade((255, 200, 80), 40, peak=0.7), lift=70),
              flash("ring", 0, 1.6, scales(0.6, 0.7), fade((255, 220, 110), 0, peak=0.7), lift=70, ground=True),
              burst("flare_cross", 2, 0.5, 25, scales(0.24, 0.08), fade((255, 235, 140)), radius=40,
                    window=1.4, interval=0.08, lift=72, local=True),
              burst("soft_star", 1, 0.6, 30, scales(0.14, 0.05), fade((255, 240, 160)), radius=36, window=1.4,
                    interval=0.1, lift=70, local=True)]),
        aura("slow", "Slow",
             "Slow: a heavy blue-grey haze settling over the creature, motes sinking and a ring closing slowly at "
             "its feet.",
             2.0,
             [burst("dust_cloud", 1, 1.4, 15, scales(0.5, 0.8), fade((90, 110, 160), 90, peak=0.4), blend="alpha",
                    radius=30, wind=falling(25), window=0.6, interval=0.15, roll=True, spin=0.3, lift=30),
              feet_ring(0, 1.6, (1.2, 0.5), (120, 160, 255), 20, (60, 90, 200)),
              burst("spark", 2, 1.2, 10, scales(0.07, 0.03), fade((170, 200, 255), 0, (70, 100, 200)), radius=50,
                    wind=falling(60), window=1.2, interval=0.06, lift=60, local=True)]),
        aura("paralyze", "Paralyze",
             "Paralyze: pale golden light locks the creature in place, crackling over it with thin rays.",
             1.8,
             [body_glow((255, 230, 150), 1.2, 80, (1.0, 1.2)),
              flash("rays_thin", 0, 0.4, scales(0.6, 1.3), fade((255, 240, 180))),
              burst("electric", 1, 0.12, 0, scales(0.35, 0.5), fade((255, 245, 200)), radius=45, roll=True,
                    window=1.3, interval=0.09, local=True),
              burst("glint", 2, 0.4, 20, scales(0.08, 0.02), fade((255, 250, 220)), radius=50, window=1.3,
                    interval=0.08, local=True)]),
        aura("turn_undead", "Turn undead",
             "Turn Undead: holy white-gold rays burst from the undead with sparks rising off it.",
             1.6,
             [flash("flare_star", 0, 0.4, scales(0.6, 1.4), fade((255, 250, 225))),
              flash("rays", 0, 0.5, scales(0.7, 1.6), fade((255, 225, 140))),
              rising_motes("spark", 3, (255, 245, 200), (255, 190, 80), window=0.8, wind=140)]),
        aura("charm", "Charm",
             "Charm and Vampire Charm: a rose glow and soft rose stars spiralling up around the creature.",
             1.8,
             [body_glow((255, 120, 190), 1.0, 70),
              rising_motes("soft_star", 2, (255, 170, 220), (220, 80, 170), window=1.1, size=(0.12, 0.04)),
              burst("wisp", 2, 0.8, 40, scales(0.16, 0.06), fade((255, 150, 210), 40, (200, 60, 150)), radius=45,
                    wind=rising(70), window=1.0, interval=0.08, roll=True, spin=2, lift=-30, local=True)]),
        aura("berserk", "Berserk",
             "Berserk: the creature flares blood red three times, throwing red sparks and dark smoke.",
             1.6,
             [flash("glow", 0, 1.2, scales((0, 0.7), (0.15, 1.3), (0.33, 0.8), (0.5, 1.3), (0.66, 0.8), (0.83, 1.3),
                                         (1, 0.7)), fade((255, 40, 30), 40), blend="additive"),
              burst("spark", 6, 0.5, 220, scales(0.08, 0.02), fade((255, 140, 90), 0, (200, 20, 10)), radius=20,
                    window=1.0, interval=0.2, velocity_aligned=True, stretch=2.5),
              burst("smoke_puff", 1, 1.0, 30, scales(0.3, 0.6), fade((60, 10, 10), 110), blend="alpha", radius=30,
                    wind=rising(50), window=0.8, interval=0.2, roll=True, spin=0.6)]),
        aura("enslave", "Enslave",
             "Enslave and Control Undead: violet rings close round the creature's head under a dark swirl, with "
             "wisps drawn into it.",
             1.8,
             [burst("swirl", 1, 1.2, 0, scales(1.2, 0.6), fade((40, 15, 70), 50), blend="alpha", radius=0, spin=-5),
              flash("ring", 0, 0.7, scales(1.0, 0.3), fade((190, 120, 255), 0, (110, 50, 220)), lift=60),
              flash("ring", 0.3, 1.0, scales(1.0, 0.3), fade((210, 160, 255), 20, (110, 50, 220)), lift=60),
              burst("wisp", 2, 0.6, -100, scales(0.18, 0.08), fade((200, 150, 255), 30, (100, 40, 200)), radius=80,
                    window=1.0, interval=0.06, roll=True, spin=3, local=True)]),
        aura("fear", "Fear",
             "Fear and Mass Fear: dark grey-violet smoke and pale ghostly wisps flee upwards off the creature.",
             1.8,
             [burst("smoke_puff", 2, 1.1, 60, scales(0.3, 0.7), fade((35, 25, 45), 70), blend="alpha", radius=35,
                    wind=rising(160), window=0.8, interval=0.12, roll=True, spin=0.8),
              burst("wisp", 2, 0.8, 80, scales(0.2, 0.1), fade((220, 215, 240), 60, (110, 90, 160)), radius=40,
                    wind=rising(200), window=1.0, interval=0.08, roll=True, spin=3)]),
        aura("blind", "Blind",
             "Blind: a band of black smoke wraps the creature's head and lingers.",
             2.2,
             [burst("smoke_puff", 2, 1.4, 25, scales(0.35, 0.5), fade((10, 8, 14), 40, peak=0.5), blend="alpha",
                    radius=25, window=1.0, interval=0.1, roll=True, spin=0.6, lift=60, local=True),
              flash("glow", 0, 1.6, scales(0.5, 0.6), fade((10, 5, 20), 60, peak=0.6), blend="alpha", lift=60),
              flash("ring", 0, 1.6, scales(0.5, 0.6), fade((60, 30, 90), 60, peak=0.6), blend="alpha", lift=62,
                    ground=True)]),
        aura("dark_grasp", "Dark grasp",
             "Dark Grasp: black tendrils of smoke rise from a dark ring at the creature's feet and coil round it.",
             2.0,
             [flash("glow", 0, 1.6, scales(1.0, 1.4), fade((20, 5, 30), 40, peak=0.6), blend="alpha", lift=-60,
                    ground=True),
              burst("wisp_smoke", 4, 1.0, 30, scales(0.4, 0.6), fade((15, 5, 20), 0), blend="alpha", radius=40,
                    wind=rising(120), window=1.2, interval=0.06, roll=True, spin=1.5, lift=-65, local=True),
              burst("wisp", 1, 0.7, 30, scales(0.14, 0.06), fade((150, 90, 220), 60, (60, 20, 120)), radius=40,
                    wind=rising(90), window=1.2, interval=0.1, roll=True, spin=2, lift=-50, local=True)]),
        aura("dispel", "Dispel magic",
             "Dispel Magic: the creature's magic shatters, a silver-blue ring bursting outwards and glints flying "
             "off.",
             1.2,
             [flash("flare_cross", 0, 0.3, scales(0.6, 1.2), fade((230, 240, 255))),
              flash("ring", 0, 0.5, scales(0.3, 1.8), fade((180, 210, 255), 0, (90, 130, 255))),
              burst("glint", 18, 0.6, 260, scales(0.09, 0.02), fade((240, 248, 255), 0, (120, 160, 255)),
                    radius=30, wind=falling(150))]),
        # Creature buffs: a monster's buff or heal on itself.
        aura("blessing", "Blessing",
             "A creature's Bless, Heroism, Fate, Day of Protection or Hour of Power: a golden light column with "
             "rising sparkles and a ring at its feet.",
             1.8,
             [body_glow(gold, 1.0, 60, (0.8, 1.4)),
              feet_ring(0, 0.9, (0.4, 1.4), gold, 0, (240, 160, 60)),
              rising_motes("spark", 3, (255, 245, 200), (255, 180, 60), window=1.0, wind=150)]),
        aura("haste", "Haste",
             "A creature's Haste: orange-red speed streaks racing up around it and a fiery ring at its feet.",
             1.4,
             [feet_ring(0, 0.6, (0.4, 1.6), (255, 120, 50), 0, (220, 50, 20)),
              body_glow((255, 120, 40), 0.8, 40, (0.9, 1.2)),
              burst("streak", 4, 0.35, 280, scales(0.24, 0.1), fade((255, 200, 130), 0, (230, 60, 20)), radius=45,
                    wind=rising(400), window=0.9, interval=0.04, velocity_aligned=True, stretch=3.0, lift=-60,
                    local=True)]),
        aura("shield", "Shield",
             "A creature's Shield: a pale blue dome ripples round it with glints sliding over the surface.",
             1.6,
             [flash("ripple", 0, 0.9, scales(0.8, 1.5), fade((150, 200, 255), 20)),
              flash("glow", 0, 1.0, scales(1.2, 1.4), fade((110, 170, 255), 120, peak=0.5)),
              burst("glint", 2, 0.4, 30, scales(0.08, 0.02), fade((230, 245, 255)), radius=70, window=1.0,
                    interval=0.06, local=True)]),
        aura("stoneskin", "Stone skin",
             "A creature's Stone Skin: ochre dust and stone chips swirl up round it as an earthen ring spreads at "
             "its feet.",
             1.8,
             [feet_ring(0, 0.9, (0.4, 1.5), (200, 160, 100), 40, (140, 110, 70)),
              body_glow((220, 170, 90), 0.8, 60, (0.9, 1.2)),
              burst("dust_cloud", 2, 1.2, 30, scales(0.45, 0.8), fade((150, 125, 90), 40), blend="alpha", radius=40,
                    wind=rising(60), window=0.6, interval=0.1, roll=True, spin=0.6, lift=-40),
              burst("debris", 3, 0.9, 40, scales(0.12, 0.08), fade((120, 95, 70)), blend="alpha", radius=45,
                    wind=rising(120), window=0.9, interval=0.06, roll=True, spin=5, lift=-60, local=True)]),
        aura("hammerhands", "Hammerhands",
             "A creature's Hammerhands: a red-orange force pulse and shock rings round its fists.",
             1.2,
             [flash("glow", 0, 0.5, scales(0.6, 1.2), fade((255, 110, 60), 30)),
              flash("ring", 0, 0.4, scales(0.2, 1.2), fade((255, 140, 90), 20, (200, 50, 30)), lift=10),
              flash("ring", 0.15, 0.55, scales(0.2, 1.4), fade((230, 90, 60), 40, (200, 50, 30)), lift=10),
              burst("spark", 10, 0.4, 200, scales(0.07, 0.02), fade((255, 180, 120), 0, (220, 60, 30)), radius=15,
                    velocity_aligned=True, stretch=2.5)]),
        aura("pain_reflection", "Pain reflection",
             "A creature's Pain Reflection: a dark red-violet swirl with thorny red streaks lashing outwards.",
             1.4,
             [burst("swirl", 1, 1.0, 0, scales(1.0, 1.4), fade((70, 10, 40), 20), blend="alpha", radius=0, spin=4),
              body_glow((255, 50, 100), 0.8, 20),
              burst("streak", 5, 0.3, 260, scales(0.22, 0.08), fade((255, 100, 130), 0, (140, 20, 60)), radius=20,
                    window=0.8, interval=0.1, velocity_aligned=True, stretch=2.5)]),
        aura("creature_heal", "Creature heal",
             "A creature's Heal or Power Cure: a green-gold glow, soft stars and wisps rising through it.",
             1.6,
             [body_glow(heal_green, 1.0, 60, (0.8, 1.3)),
              rising_motes("soft_star", 2, (220, 255, 200), (120, 220, 90), window=1.0, size=(0.1, 0.03)),
              burst("wisp", 1, 0.8, 30, scales(0.16, 0.06), fade((170, 255, 190), 60, (60, 180, 90)), radius=40,
                    wind=rising(100), window=1.0, interval=0.08, roll=True, spin=2, lift=-40, local=True)]),
        # The party's own buffs and heals, played just in front of and below its eyes (rising into the view).
        aura("party_buff", "Party buff",
             "The party's own buffs without a family of their own: a golden ring spreading on the ground ahead and "
             "golden sparkles rising past the view.",
             1.4,
             [flash("glow", 0, 0.7, scales(0.8, 1.6), fade((255, 200, 90), 90, peak=0.4)),
              flash("ring", 0, 0.8, scales(0.4, 2.0), fade(gold, 0, (240, 160, 60)), lift=-60, ground=True),
              burst("soft_star", 2, 1.0, 40, scales(0.09, 0.03), fade((255, 245, 200), 0, (255, 180, 60)),
                    radius=110, wind=rising(160), window=0.7, interval=0.05, lift=-50),
              burst("spark", 4, 1.0, 50, scales(0.08, 0.02), fade((255, 245, 200), 0, (255, 180, 60)), radius=110,
                    wind=rising(170), window=0.7, interval=0.04, lift=-50)]),
        aura("party_ward", "Party ward",
             "The party's resistances and protections: a cyan-blue ring spreading ahead, a soft ripple and glints "
             "rising.",
             1.4,
             [flash("ring", 0, 0.8, scales(0.4, 2.0), fade((120, 210, 255), 0, (60, 120, 230)), lift=-60,
                    ground=True),
              flash("ripple", 0, 0.6, scales(0.6, 1.6), fade((150, 210, 255), 60)),
              burst("glint", 3, 0.9, 40, scales(0.07, 0.015), fade((230, 245, 255), 0, (100, 160, 255)), radius=110,
                    wind=rising(150), window=0.7, interval=0.05, lift=-50)]),
        aura("party_utility", "Party utility",
             "The party's utility spells (light, sight, flight, walking): a few pale silver motes drifting up.",
             1.2,
             [burst("glint", 2, 0.9, 30, scales(0.06, 0.015), fade((240, 245, 255), 0, (170, 190, 230)), radius=100,
                    wind=rising(120), window=0.6, interval=0.05, lift=-40)]),
        aura("party_weapon", "Party weapon",
             "The party's weapon enchantments (Fire Aura, Vampiric Weapon): embers and a red-orange flare ahead.",
             1.2,
             [flash("flare_wide", 0, 0.3, scales(0.5, 1.0), fade((255, 140, 70))),
              burst("spark", 4, 0.8, 60, scales(0.06, 0.015), FIRE_TONGUE, radius=80, wind=rising(160), window=0.6,
                    interval=0.04, lift=-40)]),
        aura("heal", "Heal",
             "The party's heals and cures: a green-gold glow ahead, soft stars and wisps rising past the view.",
             1.6,
             [flash("glow", 0, 0.8, scales(0.8, 1.6), fade((150, 255, 170), 100, peak=0.4)),
              flash("ring", 0, 0.9, scales(0.4, 1.8), fade((170, 255, 160), 0, (80, 200, 90)), lift=-60,
                    ground=True),
              burst("soft_star", 3, 1.1, 40, scales(0.09, 0.03), fade((230, 255, 210), 0, (120, 220, 90)),
                    radius=100, wind=rising(150), window=0.8, interval=0.05, lift=-50),
              burst("wisp", 1, 1.0, 30, scales(0.18, 0.08), fade((180, 255, 200), 60, (70, 190, 100)), radius=90,
                    wind=rising(130), window=0.8, interval=0.08, roll=True, spin=2, lift=-50)]),
    ]


def build():
    effects = (fire_effects() + air_effects() + water_effects() + earth_effects() + body_effects() +
               mind_effects() + spirit_effects() + light_effects() + dark_effects() + tech_effects() +
               variant_effects() + spell_flights() + fire_impacts() + energy_impacts() + water_earth_impacts() +
               spirit_impacts() + spell_impacts() + spell_auras())
    return effects


class Dumper(yaml.SafeDumper):
    pass


def represent_dict(dumper, data):
    flow = "time" in data and len(data) <= 3
    return dumper.represent_mapping("tag:yaml.org,2002:map", data.items(), flow_style=flow)


def represent_list(dumper, data):
    flow = all(isinstance(item, (int, float)) for item in data)
    return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=flow)


Dumper.add_representer(dict, represent_dict)
Dumper.add_representer(list, represent_list)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    effects = build()
    lines = ["# Generated by tools/fx/generate_projectile_effects.py; edit the generator and rerun, not this file.",
             "schema: openyamm.effectLibrary.v1", "effects:"]
    for item in effects:
        comment = item.pop("comment")
        body = yaml.dump([item], Dumper=Dumper, sort_keys=False, width=118, allow_unicode=True)
        lines.append("# " + comment if len(comment) < 116 else "# " + comment[:comment.rfind(" ", 0, 114)])
        if len(comment) >= 116:
            rest = comment[comment.rfind(" ", 0, 114) + 1:]
            lines.append("#   " + rest)
        lines.extend(body.rstrip("\n").split("\n"))
    args.output.write_text("\n".join(lines) + "\n")
    args.output.chmod(0o644)
    shown = args.output.relative_to(ROOT) if args.output.is_relative_to(ROOT) else args.output
    print(f"wrote {len(effects)} effects to {shown}")


if __name__ == "__main__":
    main()
