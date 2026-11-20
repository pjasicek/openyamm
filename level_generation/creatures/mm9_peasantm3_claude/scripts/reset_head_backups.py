#!/usr/bin/env python3
"""Reset the head paint chain (head_paint.sh): the preunify / preface / preear backups are moved to work/backups_old/
(kept, not deleted), the normal maps restored from their preneck originals and the shared head ORM from its preear
backup (fix_ear_pm3.py is the only step that writes it), so the chain re-runs from the composed heads."""
import shutil
from pathlib import Path
old = Path('work/backups_old'); old.mkdir(parents=True, exist_ok=True)
for p in ('pm3_tp', 'pm3b_tp'):
    orm, orm_bk = Path(f'textures/{p}_head_metal_rough_1k.png'), Path(f'textures/{p}_head_metal_rough_1k_preear.png')
    if orm_bk.exists():
        shutil.copyfile(orm_bk, orm)
    for s in ('head_basecolor_preunify', 'head_basecolor_preface', 'head_normal_1k_preface', 'head_basecolor_preear',
              'head_normal_1k_preear', 'head_metal_rough_1k_preear'):
        f = Path(f'textures/{p}_{s}.png')
        if f.exists():
            shutil.move(str(f), str(old / f.name))
    shutil.copyfile(f'textures/{p}_head_normal_1k_preneck.png', f'textures/{p}_head_normal_1k.png')
print('RESET head backups')
