"""Per-map paths and configuration. New Sorpigal (oute3), the pilot, keeps the folders it was built in.

  config      source/textures.yml (wall texture depth specs, shared) merged with source/maps/<stem>.yml
  build       build/<stem>/            stage      playtest/assets_dev (all maps; original bakes in playtest/rebake)
  concepts    concepts/<stem>/         original   review/<stem>/original (captures of the re-baked unchanged map)
  runs        review/<stem>/<run>
"""
from pathlib import Path

import yaml

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]
MAPS = ('oute3', 'outc1', 'outc2', 'outd1', 'outd3')
NAMES = {'oute3': 'New Sorpigal', 'outc1': 'Frozen Highlands', 'outc2': 'Free Haven', 'outd1': 'Silver Cove',
         'outd3': 'Castle Ironfist'}


def config(stem):
    shared = yaml.safe_load((PROJECT / 'source/textures.yml').read_text())
    own = yaml.safe_load((PROJECT / 'source/maps' / f'{stem}.yml').read_text())
    own['textures'] = {**shared['textures'], **(own.get('textures') or {})}
    own.setdefault('buildings', {})
    own['buildings'] = own['buildings'] or {}
    return own


def build(stem):
    return PROJECT / 'build' / stem


def concepts(stem):
    return PROJECT / 'concepts' if stem == 'oute3' else PROJECT / 'concepts' / stem


def original(stem):
    return PROJECT / 'review/town_original_v2' if stem == 'oute3' else PROJECT / 'review' / stem / 'original'


def run(stem, name):
    return PROJECT / 'review' / name if stem == 'oute3' else PROJECT / 'review' / stem / name


def odm(stem):
    return ROOT / 'assets_dev/worlds/mm6/maps' / f'{stem}.odm'
