"""Install a bake's <map>.lighting and <map>.bake.json beside the map: a new file, then a rename (never a hard link)."""
import os, shutil, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[5]
n = sys.argv[1]
src = REPO / f'output/studio_cal/{n}/a7_bake/bake'
dst = REPO / 'assets_dev/worlds/xeen/maps'
for name in (f'xeen_{n}.lighting', f'xeen_{n}.bake.json'):
    tmp = dst / (name + '.a7tmp')
    shutil.copyfile(src / name, tmp)
    os.chmod(tmp, 0o644)
    os.replace(tmp, dst / name)
    print('installed', dst / name, (dst / name).stat().st_size)
