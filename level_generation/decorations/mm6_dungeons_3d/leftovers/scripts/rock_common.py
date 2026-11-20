"""Shared constants for the leftover rocks: the Poly Haven CC0 scans (outdoor rock sources, read only)."""
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDOOR = os.path.abspath(os.path.join(HERE, '..', '..', 'mm6_new_sorpigal_3d'))
SCANS = {
    'boulder_01': os.path.join(OUTDOOR, 'rocks', 'source', 'boulder_01', 'boulder_01_2k.gltf'),
    'nb03': os.path.join(OUTDOOR, 'rock', 'source', 'namaqualand_boulder_03', 'namaqualand_boulder_03_2k.gltf'),
    'nb04': os.path.join(OUTDOOR, 'rock', 'source', 'namaqualand_boulder_04', 'namaqualand_boulder_04_2k.gltf'),
    'nb05': os.path.join(OUTDOOR, 'rocks', 'source', 'namaqualand_boulder_05', 'namaqualand_boulder_05_2k.gltf'),
    'nb06': os.path.join(OUTDOOR, 'rocks', 'source', 'namaqualand_boulder_06', 'namaqualand_boulder_06_2k.gltf'),
    'nbs01a': os.path.join(OUTDOOR, 'rocks', 'source', 'namaqualand_boulders_01', 'namaqualand_boulders_01_a_2k.gltf'),
    'nbs01b': os.path.join(OUTDOOR, 'rocks', 'source', 'namaqualand_boulders_01', 'namaqualand_boulders_01_b_2k.gltf'),
    'rock_09': os.path.join(OUTDOOR, 'rocks', 'source', 'rock_09', 'rock_09_2k.gltf'),
}
