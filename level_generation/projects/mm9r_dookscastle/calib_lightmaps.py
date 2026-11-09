#!/usr/bin/env python3
"""Recompose the bake with given profile scales and print each zone's luminance ours/MM9's DAT lightmaps (the
hue_vs_lightmaps.py numbers). Usage: calib_lightmaps.py direct ambient [bounce]  (writes the profile)"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROFILE = ROOT / "tools/lighting/baked_indoors/profiles/mm9_dookscastle.yml"
profile = json.loads(PROFILE.read_text())
profile["direct_scale"], profile["ambient_scale"] = float(sys.argv[1]), float(sys.argv[2])
if len(sys.argv) > 3:
    profile["bounce_scale"] = float(sys.argv[3])
tmp = PROFILE.with_suffix(".yml.tmp")
tmp.write_text(json.dumps(profile, indent=2) + "\n")
tmp.replace(PROFILE)
subprocess.run([sys.executable, str(ROOT / "level_generation/projects/mm9r_common/dungeon/lighting.py"),
                str(ROOT / "level_generation/projects/mm9r_dookscastle"), "--recompose"], check=True,
               capture_output=True)
out = subprocess.run([sys.executable, str(ROOT / "level_generation/projects/mm9r_common/hue_vs_lightmaps.py"),
                      str(ROOT / "level_generation/projects/mm9r_dookscastle")], capture_output=True, text=True).stdout
rows = {}
for line in out.splitlines():
    m = re.match(r"(\w+)\s+(MM9|ours)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", line)
    if m:
        lum = 0.2126 * float(m[3]) + 0.7152 * float(m[4]) + 0.0722 * float(m[5])
        rows.setdefault(m[1], {})[m[2]] = (lum, float(m[6]), float(m[7]))
for zone, r in rows.items():
    print(f"{zone:15} lum ours/MM9 {r['ours'][0] / r['MM9'][0]:5.2f}  B/R {r['MM9'][1]:.2f}/{r['ours'][1]:.2f}  "
          f"G/R {r['MM9'][2]:.2f}/{r['ours'][2]:.2f}")
