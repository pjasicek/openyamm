"""Build Hangar Nine's lander sockets and the unlit light pylon (hard-surface, Blender) into work/hard_surface/.

    blender --background --factory-startup --python scripts/build_lander_sockets.py [-- <name> ...]

The derelict lander in D0 Hangar Nine (design/kreegan_world/zone1/dungeons/D0_HANGAR_NINE.md) has five sockets, like
the memory-crystal alcoves of MM6's Oracle: the cockpit socket (the Pilot's Core), the drive pod's coil housing (the
Ion Coil), the nose's navigation bay (the Nav Matrix), the engine bay (the Energy Core) and the ventral shield ring
(the Re-entry Emitter). Each has three models that the map's script swaps with evt.SetSprite:

  hes_sock_<socket>_dead   empty, the hangar unpowered: dark cavity, dark status lamp, loose cable ends
  hes_sock_<socket>_ready  empty, powered: the status lamp amber
  hes_sock_<socket>_lit    the part fitted, glowing cyan, the lamp green

Wall-type housings have their back on the plane y = 0 (the hull) and face -y; the cockpit socket stands on the flight
deck's console. Built with the shared hard-surface kit (build_hard_surface.py: materials, UV density, export).
hes_light_pylon_off is the bay's light pylon with an unlit diffuser, for its power-on swap.
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_hard_surface as hs  # noqa: E402
from build_hard_surface import cone, cube, cylinder  # noqa: E402

LAMP = {'dead': 'diffuser_off', 'ready': 'lamp', 'lit': 'lamp_green'}


def torus(major, minor, location, key, rotation=(0, 0, 0), segments=20):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=segments,
                                     minor_segments=6, location=location, rotation=rotation)
    return hs.finish(bpy.context.active_object, key)


def housing(width, height, depth, state):
    """A service bay on the hull: a ceramic back plate, a dark cavity, a gold frame standing `depth` proud and a
    status lamp on the frame's top right. Empty bays show two loose cable ends."""
    cube((width, 0.04, height), (0, -0.02, height / 2), 'ceramic')
    cube((width - 0.12, 0.02, height - 0.12), (0, -0.05, height / 2), 'glass')
    for z in (0.025, height - 0.025):
        cube((width, depth, 0.05), (0, -depth / 2, z), 'trim')
    for x in (-(width / 2 - 0.025), width / 2 - 0.025):
        cube((0.05, depth, height - 0.1), (x, -depth / 2, height / 2), 'trim')
    cube((0.16, 0.03, 0.05), (width / 2 - 0.14, -depth - 0.012, height - 0.025), 'ceramic')
    cylinder(0.022, 0.03, (width / 2 - 0.14, -depth - 0.03, height - 0.025), LAMP[state], 10,
             rotation=(math.pi / 2, 0, 0))
    if state != 'lit':
        for x, length in ((-0.07, 0.16), (0.06, 0.11)):
            cylinder(0.014, length, (x, -0.07, height - 0.06 - length / 2), 'girder', 6)
            cube((0.035, 0.035, 0.03), (x, -0.07, height - 0.06 - length), 'trim')


def coil(state):
    housing(0.5, 0.5, 0.18, state)
    if state == 'lit':
        cylinder(0.03, 0.36, (0, -0.1, 0.25), 'energy', 10)
        for k in range(5):
            torus(0.08, 0.016, (0, -0.1, 0.11 + k * 0.07), 'trim')
        for z in (0.07, 0.43):
            cylinder(0.06, 0.03, (0, -0.1, z), 'trim', 12)


def nav(state):
    housing(0.5, 0.44, 0.2, state)
    if state == 'lit':
        for k, y in enumerate((-0.07, -0.11, -0.15)):
            cube((0.3 - 0.04 * k, 0.012, 0.24 - 0.03 * k), (0, y, 0.22), 'cell')
        cube((0.34, 0.12, 0.03), (0, -0.11, 0.36), 'trim')
        cube((0.34, 0.12, 0.03), (0, -0.11, 0.08), 'trim')


def engine(state):
    housing(0.8, 0.7, 0.26, state)
    if state == 'lit':
        cylinder(0.15, 0.46, (0, -0.14, 0.35), 'cell', 16)
        for z in (0.1, 0.6):
            cylinder(0.18, 0.05, (0, -0.14, z), 'trim', 16)
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            cube((0.025, 0.025, 0.46), (math.cos(a) * 0.17, -0.14 + math.sin(a) * 0.17, 0.35), 'trim')


def ring(state):
    housing(0.6, 0.44, 0.16, state)
    if state == 'lit':
        torus(0.15, 0.028, (0, -0.1, 0.22), 'trim', rotation=(math.pi / 2, 0, 0), segments=24)
        cylinder(0.125, 0.012, (0, -0.09, 0.22), 'energy', 20, rotation=(math.pi / 2, 0, 0))
        cylinder(0.04, 0.05, (0, -0.12, 0.22), 'trim', 10, rotation=(math.pi / 2, 0, 0))


def cockpit(state):
    """The cockpit socket on the flight deck's console: a gold cradle with four prongs round a well; the Pilot's Core
    stands in it as a glowing cylinder between gold caps. Upright, centred on its origin."""
    cylinder(0.17, 0.04, (0, 0, 0.02), 'trim', 16)
    cylinder(0.12, 0.03, (0, 0, 0.055), 'glass', 16)
    cylinder(0.175, 0.012, (0, 0, 0.046), LAMP[state], 16)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        cube((0.03, 0.03, 0.2), (math.cos(a) * 0.12, math.sin(a) * 0.12, 0.14), 'trim', rotation=(0, 0, a))
    if state == 'lit':
        cylinder(0.065, 0.26, (0, 0, 0.2), 'cell', 12)
        for z in (0.08, 0.33):
            cylinder(0.075, 0.03, (0, 0, z), 'trim', 12)
        cone(0.04, 0.0, 0.05, (0, 0, 0.37), 'trim', 8)


def light_pylon_off():
    """hes_light_pylon (build_hard_surface.light_pylon) with an unlit diffuser."""
    cylinder(0.22, 0.12, (0, 0, 0.06), 'ceramic', 8)
    cylinder(0.24, 0.03, (0, 0, 0.135), 'trim', 8)
    cylinder(0.07, 1.9, (0, 0, 1.1), 'ceramic', 8)
    cylinder(0.12, 0.05, (0, 0, 2.075), 'trim', 8)
    cylinder(0.08, 0.45, (0, 0, 2.325), 'diffuser_off', 6)
    for i in range(4):
        a = i * math.pi / 2 + math.pi / 4
        cube((0.022, 0.022, 0.5), (math.cos(a) * 0.11, math.sin(a) * 0.11, 2.325), 'trim')
    cone(0.13, 0.0, 0.16, (0, 0, 2.63), 'trim', 8)


def scaled(builder, state, factor):
    """Build at the parts' own sizes, then scale the whole socket about its origin (the game shows it from the floor
    of a hangar: at 1:1 a 0.5 m bay reads as a speck on the hull)."""
    def run():
        before = set(bpy.context.scene.objects)
        builder(state)
        for obj in set(bpy.context.scene.objects) - before:
            obj.location *= factor
            obj.scale *= factor
    return run


# Socket: (builder, scale). The engine bay's is smaller, to sit between the main nozzles.
SOCKETS = {'cockpit': (cockpit, 1.6), 'coil': (coil, 1.8), 'nav': (nav, 1.8), 'engine': (engine, 1.25),
           'ring': (ring, 1.7)}
MODELS = {f'hes_sock_{socket}_{state}': scaled(builder, state, factor)
          for socket, (builder, factor) in SOCKETS.items() for state in ('dead', 'ready', 'lit')}
MODELS['hes_light_pylon_off'] = light_pylon_off

if __name__ == '__main__':
    hs.MODELS.update(MODELS)
    names = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else list(MODELS)
    for model in names:
        hs.build(model)
