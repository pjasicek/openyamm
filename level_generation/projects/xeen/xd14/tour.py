"""XD-14 picture tour: writes output/studio_cal/xd14/shots.yml (positions on the party's floor, yaw in radians)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import math, yaml
X = _REPO_ROOT + '/output/studio_cal/xd14'
E, N, W, S = 0, math.pi / 2, math.pi, -math.pi / 2
SHOTS = [
    ('gatehouse', [0, -1400, 0], N), ('gate-out', [0, -1000, 0], S),
    ('hall-north', [0, -250, 0], N), ('hall-hearth', [0, 300, 0], N), ('hall-west', [1000, 380, 0], W),
    ('kennels', [1700, 800, 0], E), ('kennel-pens', [2400, 1150, 0], N), ('scriptorium', [-1700, 1000, 0], W),
    ('stores', [-1700, 1900, 0], W), ('west-stair', [-2368, -200, 0], S), ('west-landing', [-2500, -2000, 640], E),
    ('password-door', [-1792, -2200, 640], N), ('battlements', [-1200, -2048, 640], E),
    ('scroll-hall', [-700, -1100, 640], W), ('dormitory', [-100, -1024, 640], E), ('keep-stair', [1728, -450, 640], N),
    ('keep-landing', [2050, 1152, 1280], W), ('study', [1050, 1152, 1280], W), ('roof-walk', [700, 1984, 1280], E),
    ('moon-tower', [2450, 1100, 1280], E), ('dungeon-stair', [3600, 1216, 0], E), ('guard-room', [4800, 1216, -512], E),
    ('den', [5750, 1000, -512], E), ('cells', [5300, 384, -512], W), ('cell', [3776, 250, -512], S),
    ('bone-pit', [7100, 896, -512], E),
]
doc = {'output_dir': X + '/shots2', 'exit': True, 'settle_seconds': 1.5,
       'shots': [{'name': n, 'position': p, 'yaw': y, 'pitch': 0, 'commands': ['render hud off']}
                 for n, p, y in SHOTS]}
yaml.safe_dump(doc, open(X + '/shots.yml', 'w'), sort_keys=False)
print(len(SHOTS))
