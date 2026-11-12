"""Images for the review page's round-2 gallery: concept A, now, round 1 and round 2 per view (1600 x 900 JPEGs).

  python3 source/page_images.py review/<run>
"""
import shutil
import sys
from pathlib import Path

from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'source'))
from astra_review import concept_of  # noqa: E402

PAGE = PROJECT.parents[1] / 'geometry_study_20261111/page/img'
SHOTS = {  # shot: round-1 image on the page
    '03-14_EntranceN': 't_03-14_EntranceN_pilot', '39-town_walls': 't_39-town_walls_pilot',
    '40-dock_ship': 't_40-dock_ship_pilot', '48-tavern_v01': 'c_tavern_v01_pilot',
    '51-goblinwatch_v07': 'c_goblinwatch_v07_pilot', '50-bridge_v08': 'c_bridge_v08_pilot',
    '53-armory_v03': 'c_armory_v03_pilot', '20-52_TownE': 't_20-52_TownE_pilot',
    '37-84_AntiFlyE3W': 't_37-84_AntiFlyE3W_pilot', '16-48_MagicGS': 't_16-48_MagicGS_pilot',
    '13-44_HseR3W_1': 't_13-44_HseR3W_1_pilot', '06-32_HseP2aS_3': 't_06-32_HseP2aS_3_pilot',
    '36-83_SmKeepFrnt': 't_36-83_SmKeepFrnt_pilot', '46-temple': 't_46-temple_pilot',
    '29-73_SLuckN': 't_29-73_SLuckN_pilot', '31-75_D18N': 't_31-75_D18N_pilot',
}


def save(source, name):
    Image.open(source).convert('RGB').resize((1600, 900), Image.LANCZOS).save(PAGE / f'{name}.jpg', quality=86)


def main():
    run = Path(sys.argv[1])
    for shot, round1 in SHOTS.items():
        save(concept_of(shot), f'r2_{shot}_concept')
        save(PROJECT / 'review/town_original_v2' / f'{shot}.png', f'r2_{shot}_now')
        shutil.copyfile(PAGE / f'{round1}.jpg', PAGE / f'r2_{shot}_r1.jpg')
        save(run / f'{shot}.png', f'r2_{shot}_r2')
    print(len(SHOTS), 'views')


if __name__ == '__main__':
    main()
