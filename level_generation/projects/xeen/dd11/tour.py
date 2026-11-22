"""Write output/studio_cal/<key>/shots.yml from a list of (name, x, y, z, yaw_degrees, pitch_degrees)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math, sys, yaml
def write(key, shots):
    out = f'{_REPO_ROOT}/output/studio_cal/{key}/shots'
    doc = {'output_dir': out, 'exit': True, 'settle_seconds': 1.5, 'shots': []}
    for n, x, y, z, yaw, pitch in shots:
        doc['shots'].append({'name': n, 'position': [x, y, z], 'yaw': math.radians(yaw), 'pitch': math.radians(pitch),
                             'commands': ['render hud off']})
    open(f'{_REPO_ROOT}/output/studio_cal/{key}/shots.yml', 'w').write(yaml.safe_dump(doc, sort_keys=False))
