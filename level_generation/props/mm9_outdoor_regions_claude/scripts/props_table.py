r"""The outdoor regions' props that no MM9 props project built yet: (source model, skin) -> prop id (work/raw/<prop>),
built here on Thjorgard City's route (scripts/convert_all.py, textures.py, build.py, finish.py: MM9's own meshes, one
material per skin; the skins then redrawn by ../mm9_skins_x4/skins.py), plus three the Isle of Ashes built (its props
table keys by model only, so inventory.py did not see them). Placed by scripts/placements.py.

Left out here: the posed figures (clan soldiers, Kira, Sven, the goose and the creatures: our new 3D models posed as
MM9 poses them, user 2026-11-05), MM9's two invisible `candle` CandleProps (a flame without a candle) and Barrel02
(Bootcamp: MM9 does not ship models\props\barrel02.abc).

    python3 scripts/props_table.py     # work/binding_origins.json, summary
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
PROPS_DIR = REPO / 'level_generation/props'
ISLE = PROPS_DIR / 'mm9_isleofashes_claude'
EXTRACTED = REPO / 'mm9/extracted'

# (model file, skin files ';'-joined) as in the DAT Filename / Skin properties, lower case, forward slashes, without a
# leading slash -> prop id.
MODELS = {
    # built here
    ('models/gibs/stone.abc', 'skins/gibs/stone.dtx'): 'stone',
    # the coloured stones (Thjorgard and Guberland, one of each)
    ('models/gibs/stone.abc', 'skins/gibs/red.dtx'): 'stonered',
    ('models/gibs/stone.abc', 'skins/gibs/blue.dtx'): 'stoneblue',
    ('models/gibs/stone.abc', 'skins/gibs/yellow.dtx'): 'stoneyellow',
    ('models/gibs/stone.abc', 'skins/gibs/orange.dtx'): 'stoneorange',
    ('models/gibs/stone.abc', 'skins/gibs/green.dtx'): 'stonegreen',
    ('models/props/arrow.abc', 'skins/props/arrow-bolt.dtx'): 'arrow',
    ('models/props/lantern1.abc', 'skins/props/lantern1.dtx'): 'lantern1',
    ('models/weapons/longsword.abc', 'skins/weapons/longswordnew.dtx'): 'longsword',
    ('models/weapons/longsword.abc', 'skins/weapons/longswordruneblade.dtx'): 'longswordrune',
    ('models/modelprops/dwarfaxe.abc', 'skins/modelprops/dwarfaxe.dtx'): 'dwarfaxe',
    ('models/weapons/broadsword.abc', 'skins/weapons/broadsword.dtx'): 'broadsword',
    ('models/props/haybale01.abc', 'skins/props/haybale01.dtx'): 'haybale01',
    ('models/props/stool03.abc', 'skins/props/stool03.dtx'): 'stool03',
    ('models/props/toyboat.abc', 'skins/props/boattoyred.dtx'): 'toyboatred',
    ('models/props/toyboat.abc', 'skins/props/boattoypirate.dtx'): 'toyboatpirate',
    ('models/props/toyboat.abc', 'skins/props/boattoygreen.dtx'): 'toyboatgreen',
    ('models/props/bell.abc', 'skins/props/bellnobeam.dtx'): 'bellnobeam',
    ('models/props/rectangle_banner.abc', 'textures/leveltextures/misc/cw_awning.dtx'): 'bannercw',
    ('models/props/rectangle_banner.abc', 'textures/leveltextures/misc/c_awning.dtx'): 'bannerc',
    ('models/props/tableround4.abc', 'skins/props/tableround4.dtx'): 'tableround4',
    ('models/props/woodshed01.abc', 'skins/props/stool03.dtx'): 'woodshed01',
    ('models/props/woodshed02.abc', 'skins/props/woodshed02.dtx'): 'woodshed02',
    ('models/pickupitems/quest/farmerplow.abc', 'skins/pickupitems/quest/farmerplow.dtx'): 'farmerplow',
    ('models/pickupitems/quest/girldolly.abc', 'skins/pickupitems/quest/girldolly.dtx'): 'girldolly',
    ('models/pickupitems/quest/greatbook.abc', 'skins/pickupitems/quest/greatbookreal.dtx'): 'greatbook',
    ('models/props/windmill.abc', 'skins/props/windmill.dtx'): 'windmill',
    ('models/props/hairbrush.abc', 'skins/props/hairbrush_hairy.dtx'): 'hairbrush',
    ('models/props/penancequest.abc', 'skins/props/penancequest1.dtx;skins/props/penancequest1.dtx'): 'penancequest',
    ('models/props/portal-broken.abc', 'skins/props/portaldirty.dtx'): 'portalbroken',
    # the stat stones (StatStone class: the region map script gives their timed bonus, outdoor_blv.stat_stones), one
    # skin per stat, and the battle witch blades stuck in Yorwick's and Afterworld's ground (tilted variants only)
    # (the red one is the Isle of Ashes' `statstone`; the others are its model with their skin and orb colour:
    # scripts/statstones.py)
    ('models/props/statstone.abc', 'skins/props/statstone.dtx'): 'statstoneplain',
    ('models/props/statstone.abc', 'skins/props/statstonegreen.dtx'): 'statstonegreen',
    ('models/props/statstone.abc', 'skins/props/statstonepurple.dtx'): 'statstonepurple',
    ('models/props/statstone.abc', 'skins/props/statstonered.dtx'): 'statstone',
    ('models/props/statstone.abc', 'skins/props/statstoneyellow.dtx'): 'statstoneyellow',
    ('models/weapons/battlewitch.abc', 'skins/weapons/battlewitch.dtx'): 'battlewitch',
    # Boot Camp's museum rune stone (a Cauldron object): Dark Passageway's runestone with the GM skin
    ('models/props/runestone.abc', 'skins/props/runestone_gm.dtx'): 'runestonegm',
    # the Green Man's tree in Frosgard (a non-solid Cauldron object; a unique landmark, MM9's own mesh, not swapped)
    ('models/props/plantsandtrees/greenmanstree.abc',
     'skins/props/plantsandtrees/bark.dtx;skins/props/plantsandtrees/realbranch.dtx'): 'greenmanstree',
    # reused: built by the Isle of Ashes props project (same model and skin)
    ('models/gibs/skeleton/bip01 head.abc', 'skins/skeleton1.dtx'): 'skull',
    ('models/props/vikingship-wreck.abc', 'skins/props/vikingship.dtx'): 'shipwreck',
    ('models/props/debris/stonedebris03.abc', 'skins/props/debris/lumberstonedebris.dtx'): 'stonedebris03',
    # reused from Drangheim Prison: only its tilted variant is built here
    ('models/props/axe-rusty.abc', 'skins/props/axe-rusty.dtx'): 'axerusty',
}
REUSED = {'skull': ISLE, 'shipwreck': ISLE, 'stonedebris03': ISLE, 'statstone': ISLE, 'axerusty': PROPS_DIR / 'mm9_drangheimprison_claude'}
# Tilted variants (MM9's pitch and roll, which a decoration cannot turn: baked in by build.py): <prop>p<pitch>[r<roll>]
# in whole degrees, at the DAT's exact angles (radians). The arrows and swords stick in Afterworld's and the regions'
# ground; Yorwick's windmill sails lean 25 degrees; Afterworld's rusty axes lie on their side.
TILTS = {
    'arrowp63': (1.0908308029174805, 0.0), 'arrowp76': (1.3351768255233765, 0.0),
    'arrowp78': (1.3631020784378052, 0.0), 'arrowp133': (2.316051959991455, 0.0),
    'broadswordp170': (2.970550298690796, 0.0), 'longswordp170': (2.9688050746917725, 0.0),
    'longswordp173': (3.02465558052063, 0.0), 'longswordrunep170': (2.9653143882751465, 0.0),
    'windmillp335': (5.85383415222168, 0.0), 'axerustyp128r90': (2.2340214252471924, 1.5760324001312256),
    'battlewitchp89': (1.5533430576324463, 0.0), 'battlewitchp136': (2.370157241821289, 0.0),
}
SOURCES = {name: name[:name.rindex('p')] for name in TILTS}
SKIN_ORDER = {}
ALIASES = {}
HIDDEN = {}
LIBRARY = {}
POSES = {}
PLACE_POSES = {}
CHECK_POSES = {}


def key(model: str, skin: str):
    """A DAT (Filename, Skin) pair as MODELS keys it."""
    norm = lambda s: s.replace('\\', '/').lower().strip().lstrip('/')  # noqa: E731
    return norm(model), ';'.join(norm(s) for s in skin.split(';') if s.strip())


def source_prop(prop):
    return SOURCES.get(prop, prop)


def built_props():
    return sorted((set(MODELS.values()) | set(SOURCES)) - set(REUSED))


def home(prop):
    return REUSED.get(prop, HERE)


def source(prop):
    """(model path, [skin paths]) under mm9/extracted for a prop id."""
    model, skins = next(k for k, v in MODELS.items() if v == source_prop(prop))
    roots = {'models': 'MODELS/MODELS', 'skins': 'SKINS/SKINS', 'textures': 'TEXTURES/TEXTURES',
             'spritetextures': 'SPRITETEXTURES/SPRITETEXTURES'}

    def path(s):
        top, rest = s.split('/', 1)
        return EXTRACTED / roots[top] / rest
    skins = skins.split(';')
    skins = [skins[k] for k in SKIN_ORDER.get(source_prop(prop), range(len(skins)))]
    return path(model), [path(s) for s in skins]


def resolve(path):
    """The extracted file of a case-insensitive path."""
    current = path.parents[len(path.parts) - len(EXTRACTED.parts) - 1]
    for part in path.parts[len(current.parts):]:
        match = next((c for c in current.iterdir() if c.name.lower() == part.lower()), None)
        if match is None:
            raise FileNotFoundError(path)
        current = match
    return current


def main():
    sys.path.insert(0, str(REPO / 'tools/mm9_import_discovery'))
    from convert_abc_model import read_abc
    from transcode_mm9_dat_to_odm import abc_static_model_placement_info
    origins, missing = {}, []
    for prop in sorted(set(built_props()) - set(SOURCES)):
        model, skins = source(prop)
        try:
            info = abc_static_model_placement_info(read_abc(resolve(model)))
            for skin in skins:
                resolve(skin)
        except FileNotFoundError as error:
            missing.append(f'{prop}: {error}')
            continue
        origins[prop] = list(info.binding_origin) if info else [0.0, 0.0, 0.0]
    for prop, base in SOURCES.items():
        if base in origins:
            origins[prop] = origins[base]
        else:
            model, _ = source(base)
            info = abc_static_model_placement_info(read_abc(resolve(model)))
            origins[base] = origins[prop] = list(info.binding_origin) if info else [0.0, 0.0, 0.0]
    (HERE / 'work').mkdir(exist_ok=True)
    (HERE / 'work/binding_origins.json').write_text(json.dumps(origins, indent=1))
    print(len(origins), 'props with origins;', 'missing:', missing or 'none')


if __name__ == '__main__':
    main()
