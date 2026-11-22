"""Lane A8: install a map's files from an `oymap install --mount` staging folder into assets_dev, each as a new file
then a rename (never in place: assets_dev files may be hard-linked into scratch roots).
level_generation/projects/xeen/common/install/install_stage.py <stem> <stage dir>   e.g. install_stage.py xeen_xd12 output/studio_cal/xd12/stage_mp10
Only the map's own files (maps/<stem>.blv, .scene.yml, .studio.yml, .cinematics.yml if built, events/maps/<stem>.lua);
never data_tables. Any other staged file stops the install."""
import os, shutil, sys
from pathlib import Path

stem, stage = sys.argv[1], Path(sys.argv[2])
dev = Path(__file__).resolve().parents[5] / 'assets_dev/worlds/xeen'
pairs = [(stage / 'worlds/xeen/maps' / f'{stem}{ext}', dev / 'maps' / f'{stem}{ext}')
         for ext in ('.blv', '.scene.yml', '.studio.yml')]
pairs.append((stage / 'worlds/xeen/events/maps' / f'{stem}.lua', dev / 'events/maps' / f'{stem}.lua'))
# Optional map files the build writes only when the map has them (session 12: DD-17's cinematics were left behind).
for ext in ('.cinematics.yml',):
    src = stage / 'worlds/xeen/maps' / f'{stem}{ext}'
    if src.exists():
        pairs.append((src, dev / 'maps' / f'{stem}{ext}'))
others = sorted(str(f.relative_to(stage)) for f in stage.rglob('*') if f.is_file()
                and f not in [src for src, _ in pairs])
if others:
    sys.exit(f'staged files this script does not install: {others}')
for src, dst in pairs:
    if not src.exists():
        sys.exit(f'missing {src}')
for src, dst in pairs:
    tmp = dst.with_name(dst.name + '.a8tmp')
    shutil.copyfile(src, tmp)
    os.chmod(tmp, 0o664)
    os.replace(tmp, dst)
    print('installed', dst, dst.stat().st_size)
