#!/usr/bin/env python3
"""Make the eye lens glow: emissiveFactor per tier on the RobotEye_A/B/C variant materials (the renderer adds the
material's emissive colour after lighting). Colours: the native eye core per palette (810 yellow, 811 and 812
magenta), a little below full so the lit lens still shows. Usage: eye_emissive.py in.glb out.glb"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as R

EMISSIVE = {'RobotEye_A': [0.95, 0.72, 0.18], 'RobotEye_B': [0.85, 0.16, 0.80], 'RobotEye_C': [0.90, 0.16, 0.72]}
doc, binary = R.read_glb(Path(sys.argv[1]))
done = 0
for material in doc['materials']:
    colour = EMISSIVE.get(material.get('name'))
    if colour:
        material['emissiveFactor'] = colour
        done += 1
if done != len(EMISSIVE):
    raise SystemExit(f'expected {len(EMISSIVE)} eye materials, found {done}')
R.write_glb(Path(sys.argv[2]), doc, binary)
print('EYE emissive set on', done, 'materials')
