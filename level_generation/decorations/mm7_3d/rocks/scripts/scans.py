"""Candidate Poly Haven CC0 scans for the MM7 rocks: key -> (glTF path, mesh node name or None for the whole file).
The MM6 rock sources are read in place (read only); the others are in ../source/ (fetch_scans.py)."""
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
DECO = os.path.join(REPO, 'level_generation', 'decorations')
MM6_ROCKS = os.path.join(DECO, 'mm6_new_sorpigal_3d', 'rocks', 'source')
MM6_ROCK = os.path.join(DECO, 'mm6_new_sorpigal_3d', 'rock', 'source')
SRC = os.path.join(HERE, 'source')
X2 = os.path.join(REPO, 'assets_legacy', 'decorations_x2_20261016')

SCANS = {
    'boulder_01': (os.path.join(MM6_ROCKS, 'boulder_01', 'boulder_01_2k.gltf'), None),
    'nb02': (os.path.join(SRC, 'namaqualand_boulder_02', 'namaqualand_boulder_02_2k.gltf'), None),
    'nb03': (os.path.join(MM6_ROCK, 'namaqualand_boulder_03', 'namaqualand_boulder_03_2k.gltf'), None),
    'nb04': (os.path.join(MM6_ROCK, 'namaqualand_boulder_04', 'namaqualand_boulder_04_2k.gltf'), None),
    'nb05': (os.path.join(MM6_ROCKS, 'namaqualand_boulder_05', 'namaqualand_boulder_05_2k.gltf'), None),
    'nb06': (os.path.join(MM6_ROCKS, 'namaqualand_boulder_06', 'namaqualand_boulder_06_2k.gltf'), None),
    'nbs01a': (os.path.join(MM6_ROCKS, 'namaqualand_boulders_01', 'namaqualand_boulders_01_a_2k.gltf'), None),
    'nbs01b': (os.path.join(MM6_ROCKS, 'namaqualand_boulders_01', 'namaqualand_boulders_01_b_2k.gltf'), None),
    'rock_09': (os.path.join(MM6_ROCKS, 'rock_09', 'rock_09_2k.gltf'), None),
    'rock_07': (os.path.join(SRC, 'rock_07', 'rock_07_2k.gltf'), None),
    'stone_01': (os.path.join(SRC, 'stone_01', 'stone_01_2k.gltf'), None),
}
for i in range(1, 8):
    SCANS[f'moon{i}'] = (os.path.join(SRC, f'moon_rock_0{i}', f'moon_rock_0{i}_2k.gltf'), f'moon_rock_0{i}_LOD0')
for c in 'abcd':
    SCANS[f'nr_{c}'] = (os.path.join(SRC, 'namaqualand_rocks_01', 'namaqualand_rocks_01_2k.gltf'),
                        f'namaqualand_rocks_02_{c}')
for c in 'abcde':
    SCANS[f'ns_{c}'] = (os.path.join(SRC, 'namaqualand_stones_01', 'namaqualand_stones_01_2k.gltf'),
                        f'namaqualand_stones_01_{c}')

# The eight MM7 rock sprites: sprite name -> art height in map units (inventory.json art_height).
SPRITES = {'7rock09': 66, '7rock08': 93, '7rock01': 100, '7rock02': 128, '7rock03': 88, '7rock05': 120,
           '7rock04': 116, '7rock07': 177}

# Meshy multi-image-to-3D of 7rock08 from Codex HD masters (rock08_meshy/, job crag_multiview_v1; paid job, output
# owned by the project's Meshy account).
SCANS['meshy08'] = (os.path.join(HERE, 'rock08_meshy', 'meshy', 'crag_multiview_v1', 'model_urls_glb.glb'), None)
