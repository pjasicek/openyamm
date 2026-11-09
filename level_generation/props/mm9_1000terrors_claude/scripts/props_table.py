"""The Thousand Terrors' prop table: (source model, skin) -> prop id (work/raw/<prop>), the DAT objects that place
them, and the ABC placement binding origins. Props whose model and skin match an installed decoration of another MM9
props project are reused (REUSED: prop -> owning project; their decoration rows, bindings and GLBs stay where they
are); the rest are built here (Lindisfarne Monastery's route, itself Dook's Castle's: one material per MM9 skin, the
isle's blib build and finish checks, plus the Anskram/Tasar flame cards for the fires).

Not placed (listed in work/not_placed.json): the 117 CandleProps with the Invisible skin (MM9's flicker-light anchors
under the translucent water-textured blue flame brushes WorldObjectN, 14 LT above each; the flame is that brush, a
static face of the map) and LeverHand (PeasantM1.ABC, WG_hand.scr: its Init clears Visible; it shows only in the
WinGame cutscene's SC07_Shot1 animation, which is not built).

    python3 scripts/props_table.py            # work/raw_objects_compact.json, work/binding_origins.json, summary
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
PROPS_DIR = REPO / 'level_generation/props'
ISLE = PROPS_DIR / 'mm9_isleofashes_claude'
ANSKRAM = PROPS_DIR / 'mm9_anskramkeep_claude'
TEMPLE = PROPS_DIR / 'mm9_templeofhonk_claude'
LICHLAB = PROPS_DIR / 'mm9_lichlab_claude'
CHASM = PROPS_DIR / 'mm9_chasmofthedead_claude'
TASAR = PROPS_DIR / 'mm9_tasaracademy_claude'
BEETHOVEN = PROPS_DIR / 'mm9_beethoven_claude'
TEMPLE = PROPS_DIR / 'mm9_templeofhonk_claude'
VERHOFFIN = PROPS_DIR / 'mm9_verhoffinruins_claude'
RUINED = PROPS_DIR / 'mm9_ruinedtemple_claude'
PROJECT = REPO / 'level_generation/projects/mm9r_1000terrors'
RAW = REPO / 'assets_editor_dev/worlds/mm9/maps/1000terrors.raw_objects.yml'
ODM = REPO / 'assets_editor_dev/worlds/mm9/maps/1000terrors.odm'

# (model file, skin files ';'-joined) as in the DAT Filename / Skin properties, lower case, forward slashes -> prop id.
MODELS = {
    # reused: built by other MM9 props projects (same ABC model and skin)
    ('models/props/coffinraised.abc', 'skins/props/coffinstone.dtx'): 'coffinraised',
    ('models/props/urngargoyle.abc', 'skins/props/urngargoyle.dtx'): 'urngargoyle',
    ('models/props/treasurechute.abc', 'skins/props/treasurechute.dtx'): 'treasurechute',
    # TREASURECHUTENS.abc: the same mesh, skin and bind as TREASURECHUTE.abc; its only animation's root turns it a
    # quarter (ANIM_TURN): the Chasm's treasurechute, turned
    ('models/props/treasurechutens.abc', 'skins/props/treasurechute.dtx'): 'treasurechute',
    ('models/props/treasurepile.abc', 'skins/props/treasurepile.dtx'): 'treasurepile',
    ('models/props/blackchest.abc', 'skins/props/blackchest.dtx'): 'blackchest',
    ('models/props/chest5.abc', 'skins/props/chest5.dtx'): 'chest5',
    ('models/props/brazier.abc', 'skins/props/brazier.dtx'): 'brazier',
    ('models/props/sconce1.abc', 'skins/props/sconce1.dtx'): 'sconce1',
    ('models/props/genielamp.abc', 'skins/props/genielamp_old.dtx'): 'genielamp',
    ('models/props/scroll-open.abc', 'skins/props/scroll-open.dtx'): 'scroll',
    # built here
    ('models/props/treasureopening.abc', 'skins/props/treasureopening.dtx'): 'treasureopening',
    ('models/props/terrorlight1.abc', 'skins/props/terrorlight1.dtx'): 'terrorlight1',
    ('models/props/brazierbowl.abc', 'skins/props/brazierbowl.dtx'): 'brazierbowl',
    ('models/props/sconce1.abc', 'skins/props/walltorch.dtx'): 'sconce1torch',     # Verhoffin's sconce1 has sconce1
    ('models/evilsorcerer.abc', 'skins/props/crystal.dtx'): 'sorcererstatue',      # the crystal Sorceress statues
    ('models/props/dragonpharoah.abc', 'skins/props/dragonpharoahstatue.dtx'): 'dragonpharoah',
    ('models/props/1000skulls.abc', 'skins/props/1000skulls1.dtx'): 'skulls1000a',
    ('models/props/1000skulls.abc', 'skins/props/1000skulls2.dtx'): 'skulls1000b',
    ('models/props/switch03.abc', 'skins/props/switch03.dtx'): 'switch03',
}
REUSED = {'coffinraised': BEETHOVEN, 'urngargoyle': BEETHOVEN, 'treasurechute': CHASM, 'treasurepile': CHASM,
          'blackchest': LICHLAB, 'chest5': CHASM, 'brazier': TEMPLE, 'sconce1': VERHOFFIN, 'genielamp': RUINED,
          'scroll': ANSKRAM}
# Tipped in MM9 (decorations turn about z only): the pitch and roll baked into a model of their own (Verhoffin's
# scrollp268 route). ChessNote0 (BootGive.scr 598) has pitch pi/2.
OBJECT_PROP = {'ChessNote0': 'scrollp90'}
TILTED = {'scrollp90': ('scroll',)}
TILTS = {'scrollp90': (1.5707963705062866, 0.0)}
BOOK_PROPS = {}
CLASSES = {'Prop', 'Torch', 'Brazier', 'CandleProp', 'TreasureChest'}
# DAT objects of those classes that get no decoration (module docstring): name -> reason. The invisible candles are
# matched by skin in skipped().
SKIP_NAMES = {'LeverHand': 'PeasantM1.ABC with WG_hand.scr: Init clears Visible (shown only in the WinGame cutscene)'}
OWNERS = {}
# PropAnim.scr's animation (the raised coffins' and stone benches' "ns", a quarter turn from Static_Model) is posed by
# the map converter for every map (mm9r_common/dungeon/prop_pose.py, 2026-11-07); placements.py writes the placement
# as baked. This table stays empty.
POSE_TURN = {}
# MM9 shows a model in its first animation's pose; the old map baked the ABC's bind pose. Where the two roots differ
# (LT angle about y, anim0 minus bind) the old bake is turned against MM9 (work/ns_turn_probe.py, work/wall_probe.py):
#  - ANIM_TURN, by DAT model file: the placed decoration is the bind-pose model (a reused one), checked against the
#    bake as it is, then turned about the DAT origin (the NS chutes: root -90 deg against the bind's 180: +90, the
#    turn PropAnim 'ns' gives the coffins; with it every chute's back plate is on its wall, 15-71 units away);
#  - BUILT_TURN, by prop: the model built here already carries its first animation's root (Blender's glTF import
#    poses the first animation): checked against the bake turned back, then placed unturned (DragonPharoah's
#    Static_Model root +90 deg against the bind's 180: -90; its back slab then faces its wall).
ANIM_TURN = {'models/props/treasurechutens.abc': 90.0}
BUILT_TURN = {'dragonpharoah': -90.0}
# Models built in an animation pose (full export, posed in Blender): (action, frame).
# ABCs with non-finite texture coordinates, converted through scripts/abc_finite.py.
FINITE_UV = {'dragonpharoah'}
# The Sorceress statues: 1000T_SorcStatues.scr plays fidget2 once half a second after load (PlayAnim fidget2,
# DoNothing) and holds its last frame until the party wakes them (then fidget2/Taunt loop while their shooters fire):
# fidget2's end (2.366 s, frame 57 at the glTF import's 24 fps) is the pose MM9 shows; the bind pose is a T-pose.
POSES = {'sorcererstatue': ('fidget2', 57)}


def key(path):
    return ';'.join(part.replace('\\', '/').lower().strip() for part in (path or '').split(';'))


def objects():
    return json.loads((HERE / 'work/raw_objects_compact.json').read_text())


def object_prop(o):
    p = o['props']
    if p.get('Name') in OBJECT_PROP:
        return OBJECT_PROP[p['Name']]
    return MODELS[(key(p['Filename']), key(p.get('Skin')))]


def skip_reason(o):
    p = o['props']
    if p.get('Name') in SKIP_NAMES:
        return SKIP_NAMES[p['Name']]
    if o['class'] == 'CandleProp' and 'invisible' in key(p.get('Skin')):
        return 'invisible candle: flicker-light anchor under a translucent blue flame brush (static map face)'
    return None


def placements():
    """(object index, prop id) of every decoration object."""
    return [(o['index'], object_prop(o)) for o in objects()
            if o['class'] in CLASSES and o['props'].get('Filename') and skip_reason(o) is None]


def skipped():
    return [o for o in objects() if o['class'] in CLASSES and o['props'].get('Filename') and skip_reason(o)]


def built_props():
    """The props built in this project (not reused)."""
    return sorted((set(MODELS.values()) | set(TILTED)) - set(REUSED))


def home(prop):
    return REUSED.get(prop, HERE)


def source_prop(prop):
    """The MODELS id whose source a built prop converts (the tilted variants share their upright model's)."""
    return TILTED[prop][0] if prop in TILTED else prop


def source(prop):
    """(model path, [skin paths]) under mm9/extracted for a prop id."""
    model, skins = next(k for k, v in MODELS.items() if v == source_prop(prop))
    roots = {'skins': 'SKINS/SKINS', 'textures': 'TEXTURES/TEXTURES'}

    def skin_path(s):
        top, rest = s.split('/', 1)
        return REPO / 'mm9/extracted' / roots[top] / rest
    return (REPO / 'mm9/extracted/MODELS/MODELS' / model[len('models/'):], [skin_path(s) for s in skins.split(';')])


def resolve(path):
    """The extracted file of a case-insensitive path."""
    current = path.parents[len(path.parts) - len((REPO / 'mm9/extracted').parts) - 1]
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
    (HERE / 'work/binding_origins.json').write_text(json.dumps(origins, indent=1))
    skipped_out = [{'source_object': o['index'], 'source_name': o['props'].get('Name'), 'class': o['class'],
                    'model': o['props'].get('Filename'), 'skin': o['props'].get('Skin'),
                    'pos_lt': o['props'].get('Pos'), 'reason': skip_reason(o)} for o in skipped()]
    (HERE / 'work/not_placed.json').write_text(json.dumps(skipped_out, indent=1) + '\n')
    print('not placed:', len(skipped_out))
    counts = Counter(prop for _, prop in placements())
    print(len(counts), 'props,', sum(counts.values()), 'placements;',
          Counter(o['class'] for o in out if o['class'] in CLASSES))
    print('built:', [(p, counts[p]) for p in built_props()])
    print('reused:', [(p, counts[p]) for p in sorted(REUSED)])


if __name__ == '__main__':
    main()
