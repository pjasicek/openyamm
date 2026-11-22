#!/usr/bin/env python3
"""XD-11's tours: tour.py <name> writes shots/<name>.yml (the same poses for a fresh map and for the save after the
playtest): every room, every interactive thing, the top of every lift."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math, sys, yaml
P = math.pi
X = _REPO_ROOT + '/output/studio_cal/xd11'
E = 160
S = [
    ('01-arrival-door-room', [-1408, -1700, E], P / 2, 0.0),
    ('02-enchanted-door', [-1408, -1500, E], -P / 2, -0.05),
    ('03-foyer', [-1700, -900, E], 0.9, -0.05),
    ('04-foyer-door-athanor', [-1088, 300, E], P / 2, 0.0),
    ('05-athanor', [-1500, 1250, E], 0.25, -0.05),
    ('06-athanor-fire-brew', [400, 1300, E], 0.6, -0.25),
    ('07-coils', [640, 900, E], -P / 2, -0.05),
    ('08-coils-electric-brew', [500, 500, E], P + 0.5, -0.3),
    ('09-core0-from-coils-door', [640, -300, E], -P / 2, 0.6),
    ('10-core0-up-the-shaft', [448, -576, E], -P / 2, 1.3),
    ('11-east-stair-foot', [1500, 700, E], -P / 2 + 0.3, 0.15),
    ('12-east-stair-gallery', [1600, -1800, 640 + E], P / 2, -0.25),
    ('13-landing1-gate1-lever', [760, -1500, 640 + E], P / 2, 0.0),
    ('14-lift-a-top-core1', [448, -576, 640 + E], -P / 2, -0.4),
    ('15-core1-shaft', [640, -800, 640 + E], P / 2, 0.3),
    ('16-still', [0, -1600, 640 + E], P - 0.4, -0.1),
    ('17-still-cold-brew', [-100, -1650, 640 + E], -P / 2 - 0.2, -0.35),
    ('18-reagents-valve-box', [-1600, -1750, 640 + E], P / 2 + 0.3, -0.1),
    ('19-poison-garden', [-100, -350, 640 + E], P / 2 + 0.6, -0.1),
    ('20-frozen-door', [-900, -320, 640 + E], P, -0.05),
    ('21-poison-brew', [-800, 900, 640 + E], P - 0.4, -0.25),
    ('22-west-stair-foot', [-1600, -700, 640 + E], P / 2, 0.15),
    ('23-west-stair-gallery', [-1728, 1750, 1280 + E], -P / 2, -0.3),
    ('24-landing2', [-1500, 1728, 1280 + E], 0.0, -0.05),
    ('25-energy-lab', [-768, 1150, 1280 + E], -P / 2 - 0.3, -0.1),
    ('26-energy-brew', [-850, 300, 1280 + E], P + 0.6, -0.3),
    ('27-magic-lab', [700, 900, 1280 + E], 0.5, -0.05),
    ('28-magic-brew-dais', [1344, 1250, 1280 + E], P / 2, -0.2),
    ('29-quarters', [700, 300, 1280 + E], 0.0, -0.1),
    ('30-quarters-gate2-librarian-door', [1200, 300, 1280 + E], -P / 2, -0.05),
    ('31-lift-b-top-core2', [832, -576, 1280 + E], P / 2, -0.4),
    ('32-lift-c-foot-core2', [640, -500, 1280 + E], P, -0.6),
    ('33-high-stair', [1792, -300, 1280 + E], -P / 2, 0.15),
    ('34-landing3-gate3', [760, -1500, 1920 + E], P / 2, 0.0),
    ('35-lift-c-top-core3', [448, -576, 1920 + E], -P / 2, -0.4),
    ('36-library', [0, -1700, 1920 + E], P / 2 + 0.3, -0.05),
    ('37-library-art-of-magic', [-300, -1150, 1920 + E], -P / 2 - 0.6, -0.3),
    ('38-library-mysteries-cabinet', [-500, 600, 1920 + E], P / 2 + 0.3, -0.1),
    ('39-study', [-1500, -1300, 1920 + E], P + 0.3, -0.15),
    ('40-observatory', [-1600, -350, 1920 + E], P / 2, 0.2),
    ('41-observatory-box', [-1600, 700, 1920 + E], P - 0.4, -0.2),
    ('42-stairway-to-heaven', [-1900, 1700, 1920 + E], 0.15, 0.25),
    ('43-stairway-head', [-100, 1792, 2560 + E], P, -0.3),
    ('44-roof', [450, 1700, 2560 + E], -0.6, 0.0),
    ('45-roof-cloud-stair', [1536, 700, 2560 + E], P / 2, 0.15),
    ('46-roof-over-the-parapet', [1900, -1900, 2560 + E], -P / 4, -0.3),
]
name = sys.argv[1]
doc = {'output_dir': f'{X}/shots/{name}', 'settle_seconds': 2.0, 'exit': True,
       'shots': [{'name': n, 'position': p, 'yaw': round(y, 4), 'pitch': pt, 'commands': ['render hud off']}
                 for n, p, y, pt in S]}
yaml.safe_dump(doc, open(f'{X}/shots/{name}.yml', 'w'), sort_keys=False)
