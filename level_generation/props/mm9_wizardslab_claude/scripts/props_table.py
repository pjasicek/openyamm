r"""Wizard's Lab's prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place them,
and the ABC placement binding origins. The route is Drangheim City's (scripts copied and adapted; itself Sturmford
City's): MM9's own meshes, one material per skin, the isle's blib build and finish checks; props whose model and skin
match an installed decoration of another MM9 props project are reused (REUSED; work/registry.py lists the owners).

Classes placed: Prop, CandleProp, Barrel (MM9's stat barrels: dungeon/content.py puts them on the stat barrel rows),
BonePile, Cauldron and WellMMIX (the cauldron room's three cauldrons), TreasureChest (kind chest).

  - Built here: `relic` (the Saint's Relic pickup, Relic.scr; its DAT name is "barrel", a decoration's name, so
    placements.py writes it as barrel_<object> and citylua.py finds it by its script), `skeletonlaying1` (the lying
    skeleton with skeleton1.dtx; Ruined Temple's has skeleton2, Connecting Tunnels' skeleton), `ropecoilcauldron`
    (MM9 gives the three cauldrons RopeCoil.ABC with the cauldron01 skin, at Scale 2 and 3: a ring around each
    DirtyWater basin; the old import baked the same), `torchmetalunlit` (the four torch2 sconces that are Props, not
    CandleProps: MM9 burns no fire on a Prop) and `shelfitem02ha` (HidePiece Amulets1).
  - Lit models by class: a CandleProp torch2 is Ruined Temple's blue `torchmetal` with Blue 1 (53) and Hall of the
    Gods' `torchmetalorange` with Blue 0 (21); the CandleProp claw lamp (Blue 1) is Thjorgard City's `clawlampupblue`,
    the Prop claw lamps Sturmford City's `clawlampup` (Prop43's HidePiece Amulets1 names no piece of ClawLamp.ABC:
    ignored, as MM9 does).
  - Not placed (SKIPPED_SKINS): the seven invisible candles (candle.abc with invisible.dtx: MM9 shows no candle; their
    lights are the DAT Lights).

    python3 scripts/props_table.py            # work/raw_objects_compact.json, work/binding_origins.json, summary
"""
import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
PROPS_DIR = REPO / 'level_generation/props'
ISLE = PROPS_DIR / 'mm9_isleofashes_claude'
PROJECT = REPO / 'level_generation/projects/mm9r_wizardslab'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/wizardslab.raw_objects.yml'
ODM = REPO / 'assets_editor_dev/worlds/mm9/maps/wizardslab.odm'
SCENE = REPO / 'assets_dev/worlds/mm9/maps/wizardslab.scene.yml'
EXTRACTED = REPO / 'mm9/extracted'

# (model file, skin files ';'-joined) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    # built here
    ('models/pickupitems/quest/relic.abc', 'skins/pickupitems/quest/relic.dtx'): 'relic',
    ('models/props/skeletonlaying.abc', 'skins/skeleton1.dtx'): 'skeletonlaying1',
    ('models/props/ropecoil.abc', 'skins/props/cauldron01.dtx'): 'ropecoilcauldron',
    ('models/props/torch2.abc', 'skins/props/torch_metal.dtx'): 'torchmetalunlit',
    ('models/props/shelfitem02.abc', 'skins/props/shelfitem02.dtx'): 'shelfitem02',
    # reused: built by other MM9 props projects (same ABC model and skin)
    ('models/props/barrel03.abc', 'skins/props/barrel03.dtx'): 'barrel03',
    ('models/props/barstool2.abc', 'skins/props/barstool1.dtx'): 'barstool2',
    ('models/props/beaker01.abc', 'skins/props/beaker01.dtx'): 'beaker01',
    ('models/props/bed.abc', 'skins/props/bed.dtx'): 'bed',
    ('models/props/bonepile.abc', 'skins/props/bonepile.dtx'): 'bonepile',
    ('models/props/book.abc', 'skins/props/book.dtx'): 'bookflat',
    ('models/props/bookcase01ew.abc', 'skins/props/bookcase01.dtx'): 'bookcase01ew',
    ('models/props/bookstack01.abc', 'skins/props/bookstack01.dtx'): 'bookstack01',
    ('models/props/burner.abc', 'skins/props/burner.dtx'): 'burner',
    ('models/props/chair.abc', 'skins/props/chairplain.dtx'): 'chair',
    ('models/props/chair02.abc', 'skins/props/chair02.dtx'): 'chair02',
    ('models/props/chest5.abc', 'skins/props/chest5.dtx'): 'chest5',
    ('models/props/clawlamp.abc', 'skins/props/clawlamp.dtx'): 'clawlampup',
    ('models/props/desk03.abc', 'skins/props/desk03b.dtx'): 'desk03b',
    ('models/props/herb-rack1.abc', 'skins/props/herb-rack1.dtx'): 'herbrack1',
    ('models/props/herb-rack2.abc', 'skins/props/herb-rack1.dtx'): 'herbrack2',
    ('models/props/podium01.abc', 'skins/props/podium01.dtx'): 'podium01',
    ('models/props/scroll-double.abc', 'skins/props/scrolldouble.dtx'): 'scrolldouble',
    ('models/props/scroll-open.abc', 'skins/props/scroll-open.dtx'): 'scroll',
    ('models/props/scroll1.abc', 'skins/props/scroll1.dtx'): 'scroll1',
    ('models/props/scroll2.abc', 'skins/props/scroll2.dtx'): 'scroll2',
    ('models/props/scroll3.abc', 'skins/props/scroll3.dtx'): 'scroll3',
    ('models/props/shelfitem01.abc', 'skins/props/shelfitem01.dtx'): 'shelfitem01',
    ('models/props/shelfitem03.abc', 'skins/props/shelfitem03.dtx'): 'shelfitem03',
    ('models/props/shelfitem05.abc', 'skins/props/shelfitem05.dtx'): 'shelfitem05',
    ('models/props/shelfitem06.abc', 'skins/props/shelfitem06.dtx'): 'shelfitem06',
    ('models/props/table01.abc', 'skins/props/table01.dtx'): 'table01',
    ('models/props/tableround4.abc', 'skins/props/tableround5.dtx'): 'tableround5',
    ('models/props/tabletrestle.abc', 'skins/props/tabletrestle2.dtx'): 'tabletrestle2',
    ('models/props/terrorlight1.abc', 'skins/props/terrorlight1.dtx'): 'terrorlight1',
    ('models/props/vials.abc', 'skins/props/vials.dtx'): 'vials',
}
ALIASES = {}
_OWNERS = {
    'barrel03': 'anskramkeep', 'barstool2': 'drangheimcity', 'beaker01': 'lichlab', 'bed': 'anskramkeep',
    'bonepile': 'beethoven', 'bookflat': 'templeofhonk', 'bookcase01ew': 'templeofhonk', 'bookstack01': 'lichlab',
    'burner': 'lichlab', 'chair': 'anskramkeep', 'chair02': 'anskramkeep', 'chest5': 'chasmofthedead',
    'clawlampup': 'sturmfordcity', 'clawlampupblue': 'thjorgardcity', 'desk03b': 'lindisfarnemonastery',
    'herbrack1': 'thronheimcity', 'herbrack2': 'thjorgardcity', 'podium01': 'lichlab', 'scrolldouble': 'lichlab',
    'scroll': 'anskramkeep', 'scroll1': 'tasaracademy', 'scroll2': 'lichlab', 'scroll3': 'lichlab',
    'shelfitem01': 'lichlab', 'shelfitem02': 'lichlab', 'shelfitem03': 'lichlab', 'shelfitem05': 'lichlab',
    'shelfitem06': 'drangheimprison', 'table01': 'lichlab', 'tableround5': 'klusoshouse',
    'tabletrestle2': 'klusoshouse', 'terrorlight1': '1000terrors', 'vials': 'sturmfordcity',
    'torchmetal': 'ruinedtemple', 'torchmetalorange': 'hallofthegods'}
REUSED = {prop: PROPS_DIR / f'mm9_{owner}_claude' for prop, owner in _OWNERS.items()}
OBJECT_PROP = {}
# Variants built here from another prop's source (MODELS id); the lit torches and lamps are reused models of the
# same ABC and skin as the unlit source (LIT_OF picks them by class and Blue).
SOURCES = {'shelfitem02ha': 'shelfitem02', 'torchmetal': 'torchmetalunlit', 'torchmetalorange': 'torchmetalunlit',
           'clawlampupblue': 'clawlampup'}
OWN_SOURCE = {'shelfitem02ha'}
# (unlit prop, class, Blue) -> the lit model MM9 shows
LIT_OF = {('torchmetalunlit', 'CandleProp', 1): 'torchmetal', ('torchmetalunlit', 'CandleProp', 0): 'torchmetalorange',
          ('clawlampup', 'CandleProp', 1): 'clawlampupblue'}
TILTS = {}
TILT_OF = {}
# HidePiece0-4 of the objects: their pieces stripped from the variant's raw GLBs (convert_all.strip).
HIDDEN = {'shelfitem02ha': ['Amulets1']}
HIDE_VARIANTS = {('shelfitem02', ('amulets1',)): 'shelfitem02ha'}
# HidePiece names that are not pieces of the model (ignored, as MM9 does): ClawLamp.ABC has Glow-Node and Claw-Lamp.
NO_SUCH_PIECE = {'clawlampup': {'amulets1'}}
LIBRARY = {}
POSES = {}
PLACE_POSES = {}
CHECK_POSES = {'torchmetalunlit': ('static_object', 0), 'torchmetalorange': ('static_object', 0),
               'torchmetal': ('static_object', 0)}
POSE_TURN = {}
SKIN_ORDER = {}
CLASSES = {'Prop', 'CandleProp', 'Barrel', 'BonePile', 'Cauldron', 'WellMMIX', 'TreasureChest'}
# Objects of those classes (and the other model-carrying objects of the DAT) that get no decoration: name -> reason.
SKIPPED = {}
SKIPPED_SKINS = {'textures/leveltextures/misc/invisible.dtx': 'invisible candle (MM9 shows no candle; its light is a '
                                                               'DAT Light)'}


def key(path):
    return ';'.join(part.replace('\\', '/').lower().strip() for part in (path or '').split(';'))


def objects():
    return json.loads((HERE / 'work/raw_objects_compact.json').read_text())


def tilt_degrees(p):
    r = p.get('Rotation') or [0, 0, 0]
    return int(round(math.degrees(float(r[0])))) % 360, int(round(math.degrees(float(r[2])))) % 360


def object_prop(o):
    p = o['props']
    pair = (key(p['Filename']), key(p.get('Skin')))
    prop = OBJECT_PROP.get(p.get('Name')) or MODELS[ALIASES.get(pair, pair)]
    prop = LIT_OF.get((prop, o['class'], int(p.get('Blue') or 0)), prop)
    hidden = tuple(sorted(x for x in (p[f'HidePiece{k}'].lower() for k in range(5) if p.get(f'HidePiece{k}'))
                          if x not in NO_SUCH_PIECE.get(prop, set())))
    if hidden:
        if (prop, hidden) not in HIDE_VARIANTS:
            raise SystemExit(f"{p['Name']}: {prop} hides {list(hidden)}: no variant")
        prop = HIDE_VARIANTS[(prop, hidden)]
    if source_prop(prop) not in MODELS.values() and prop not in REUSED and prop not in SOURCES:
        raise SystemExit(f"{p['Name']}: {prop} has no source")
    tilt = tilt_degrees(p)
    if tilt != (0, 0):
        if (prop, *tilt) not in TILT_OF:
            raise SystemExit(f"{p['Name']}: {prop} tilted pitch {tilt[0]} roll {tilt[1]} has no variant")
        prop = TILT_OF[(prop, *tilt)]
    return prop


def skipped(o):
    """The reason an object of a placed class gets no decoration, or None."""
    p = o['props']
    return SKIPPED.get(p.get('Name')) or SKIPPED_SKINS.get(key(p.get('Skin')))


def placements():
    """(object index, prop id) of every decoration object (not the SKIPPED ones)."""
    return [(o['index'], object_prop(o)) for o in objects() if o['class'] in CLASSES and o['props'].get('Filename')
            and not skipped(o)]


def source_prop(prop):
    return SOURCES.get(prop, prop)


def built_props():
    """The props built here: the placed ones minus the reused."""
    try:
        placed = {prop for _, prop in placements()}
    except FileNotFoundError:
        placed = (set(MODELS.values()) | set(SOURCES)) - set(SOURCES.values())
    return sorted(placed - set(REUSED))


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


_origins = None


def binding_origin(prop):
    global _origins
    if _origins is None:
        _origins = json.loads((HERE / 'work/binding_origins.json').read_text())
    return _origins[source_prop(prop)]


def main():
    import yaml
    sys.path.insert(0, str(REPO / 'tools/mm9_import_discovery'))
    raw = yaml.load(RAW.read_text(), Loader=yaml.CSafeLoader)
    out = []
    for obj in raw['objects']:
        props = {}
        for p in obj['properties']:
            try:
                props[p['name']] = json.loads(p['value_json']) if p.get('value_json') is not None else None
            except ValueError:
                props[p['name']] = p.get('value_json')
        out.append({'index': obj['object_index'], 'class': obj['name'], 'props': props})
    (HERE / 'work').mkdir(exist_ok=True)
    (HERE / 'work/raw_objects_compact.json').write_text(json.dumps(out, indent=1))
    from convert_abc_model import read_abc
    from transcode_mm9_dat_to_odm import abc_static_model_placement_info
    origins = {}
    for prop in sorted(set(MODELS.values())):
        model, _ = source(prop)
        info = abc_static_model_placement_info(read_abc(resolve(model)))
        origins[prop] = list(info.binding_origin) if info else [0.0, 0.0, 0.0]
    for prop, src in SOURCES.items():
        origins[prop] = origins[src]
    (HERE / 'work/binding_origins.json').write_text(json.dumps(origins, indent=1))
    counts = Counter(prop for _, prop in placements())
    print(len(counts), 'props,', sum(counts.values()), 'placements;',
          Counter(o['class'] for o in out if o['class'] in CLASSES and o['props'].get('Filename')))
    print('built:', len(built_props()), [(p, counts[p]) for p in built_props()])
    print('reused:', len([p for p in REUSED if counts[p]]), [(p, counts[p]) for p in sorted(REUSED) if counts[p]])
    print('unused REUSED entries:', [p for p in sorted(REUSED) if not counts[p]])
    # every model-carrying object of the DAT: placed, or skipped with its reason; the DAT models MM9 does not ship
    missing = []
    for o in out:
        f = o['props'].get('Filename')
        if not f or not isinstance(f, str) or not f.lower().endswith('.abc'):
            continue
        parts = key(f).split('/')
        try:
            resolve(EXTRACTED / 'MODELS/MODELS' / '/'.join(parts[1:]))
        except FileNotFoundError:
            missing.append(f"{o['index']} {o['class']} {o['props'].get('Name')}: {f} not in mm9/extracted (MODELS.REZ)")
        if o['class'] not in CLASSES and not skipped(o):
            print('NOT A DECORATION CLASS (not placed):', o['index'], o['class'], o['props'].get('Name'), f)
    (HERE / 'work/missing_models.txt').write_text('\n'.join(missing) + '\n')
    print('DAT models not shipped:', *missing, sep='\n  ')
    print('skipped:', [(o['index'], o['props'].get('Name'), skipped(o)) for o in out
                       if o['class'] in CLASSES and o['props'].get('Filename') and skipped(o)])


if __name__ == '__main__':
    main()
