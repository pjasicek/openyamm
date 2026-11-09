"""The four MM9 spellbook ground models: level_generation/props/items_claude/scripts/build_books.py (the shared book
of the MM6-MM8 spellbooks: boards, rounded spine, page block; 46 triangles) with this project's flat cover and spine
paintings (<mastery>/cover.png, spine.png, from BRIEF_TEXTURES.md) in place of books_hd/.
Writes work/mm9_spellbook_<mastery>_export.glb and textures/mm9_spellbook_<mastery>_book_basecolor.png.
Usage: blender --background --python build_models.py -- [mastery ...]"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUILDER = os.path.join(HERE, '..', '..', 'props', 'items_claude', 'scripts', 'build_books.py')
MASTERIES = ('normal', 'expert', 'master', 'grandmaster')

source = open(BUILDER).read()
source = source[:source.rindex('\nmain()')]          # the builder's functions, without its own run
namespace = {'__file__': os.path.abspath(BUILDER), '__name__': 'build_books'}
exec(compile(source, BUILDER, 'exec'), namespace)

sources = os.path.join(HERE, 'work', 'sources')
os.makedirs(sources, exist_ok=True)
namespace['SOURCES'] = sources
namespace['TEXTURES'] = os.path.join(HERE, 'textures')
os.makedirs(namespace['TEXTURES'], exist_ok=True)
pl = namespace['pl']
pl.TEXTURES = namespace['TEXTURES']
pl.WORK = os.path.join(HERE, 'work')
wanted = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
for mastery in wanted or MASTERIES:
    icon = f'mm9_spellbook_{mastery}'
    for part in ('cover', 'spine'):
        shutil.copyfile(os.path.join(HERE, mastery, f'{part}.png'), os.path.join(sources, f'{icon}_{part}.png'))
    pl.reset()
    namespace['atlas_for'](icon)
    material = pl.material(icon, f'{icon}_book', roughness=0.7)
    obj = pl.to_object(icon, namespace['build'](), [material], 40)
    print('BOOK', icon, len(obj.data.polygons), 'triangles')
    pl.export(obj, icon)
