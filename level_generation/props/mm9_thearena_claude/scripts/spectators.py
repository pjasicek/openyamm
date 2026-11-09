r"""The Arena's 11 RUDEProp spectators (PropAnim.scr, the seated peasants of the stands): static decorations of MM9's
own seated peasant meshes in their script's pose, Sturmford City's route for its seated townsfolk
(../mm9_sturmfordcity_claude/: README "Townsfolk poses"). This module is a props table in the Sturmford City scripts'
shape (MODELS, SOURCES, LIBRARY, POSES, HIDDEN, source() with a skin list, built_props(), ...); `sturmford.load(name)`
runs a Sturmford script on it, with this project's directories.

  - PeasantMS2.abc and PeasantMS1.abc (the seated men) carry only MP_2s / MP_1s (T-poses): the scripts' `listen`
    is in PeasantSeated.abc (the same 43 nodes in the same order as both bodies).
  - PeasantFS2.abc (the seated woman) carries PeasantF2s and sewing_copy: `conv1` is in PeasantFSeated.abc (the women's
    seated library: sitting, conv1, conv2, conv4, fidget1, fidget2, sewing, sewingfidget; the same 54 nodes).
  - The shadow n-gon piece (`ngon_s`, PeasantFS2's `NGon01`) is stripped (HIDDEN).
  - PeasantMS2 with PeasantM2d in `listen` is Sturmford City's `peasantms2dlisten` (Halfdan): reused (REUSED).

Prop ids: <body><skin letter><animation>, as Sturmford's (peasantms2dlisten)."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import props_table as arena  # noqa: E402

REPO, ISLE, EXTRACTED, PROJECT = arena.REPO, arena.ISLE, arena.EXTRACTED, arena.PROJECT
STURMFORD = REPO / 'level_generation/props/mm9_sturmfordcity_claude'

# (model, skin) as in the DAT Filename / Skin, lower case, forward slashes -> source id (the unposed body and skin).
MODELS = {
    ('models/peasantms2.abc', 'skins/peasantm2a.dtx'): 'peasantms2a',
    ('models/peasantms2.abc', 'skins/peasantm2b.dtx'): 'peasantms2b',
    ('models/peasantms2.abc', 'skins/peasantm2c.dtx'): 'peasantms2c',
    ('models/peasantms2.abc', 'skins/peasantm2d.dtx'): 'peasantms2d',
    ('models/peasantms1.abc', 'skins/peasantm1a.dtx'): 'peasantms1a',
    ('models/peasantms1.abc', 'skins/peasantm1b.dtx'): 'peasantms1b',
    ('models/peasantfs2.abc', 'skins/peasantf2b.dtx'): 'peasantfs2b',
}
# The DAT's ScriptParams (PropAnim.scr's looping animation) -> the library holding it, per body.
LIBRARIES = {'models/peasantms2.abc': 'PEASANTSEATED.abc', 'models/peasantms1.abc': 'PEASANTSEATED.abc',
             'models/peasantfs2.abc': 'PEASANTFSEATED.abc'}
SHADOW = {'models/peasantms2.abc': 'ngon_s', 'models/peasantms1.abc': 'ngon_s', 'models/peasantfs2.abc': 'NGon01'}
# The posed props of the DAT's spectators (object_prop checks each against its object): prop -> (source, animation).
POSED = {'peasantms2alisten': ('peasantms2a', 'listen'), 'peasantms2blisten': ('peasantms2b', 'listen'),
         'peasantms2clisten': ('peasantms2c', 'listen'), 'peasantms2dlisten': ('peasantms2d', 'listen'),
         'peasantms1alisten': ('peasantms1a', 'listen'), 'peasantms1blisten': ('peasantms1b', 'listen'),
         'peasantfs2bconv1': ('peasantfs2b', 'conv1')}
SOURCES = {prop: source for prop, (source, _) in POSED.items()}
_BODY = {source: model for (model, _), source in MODELS.items()}
LIBRARY = {prop: (LIBRARIES[_BODY[source]], animation) for prop, (source, animation) in POSED.items()}
HIDDEN = {prop: [SHADOW[_BODY[source]]] for prop, (source, _) in POSED.items()}
POSES = {prop: (animation, 0) for prop, (_, animation) in LIBRARY.items()}
PLACE_POSES, CHECK_POSES, TILTS, SKIN_ORDER = {}, {}, {}, {}
REUSED = {'peasantms2dlisten': STURMFORD}


def key(path):
    return (path or '').replace('\\', '/').lower().strip()


def object_prop(o):
    """The posed prop of a RUDEProp spectator."""
    p = o['props']
    if key(p.get('ScriptName')) != 'scripts/propanim.scr':
        raise SystemExit(f"{p['Name']}: script {p.get('ScriptName')} is not PropAnim.scr")
    if any(p.get(f'HidePiece{k}') for k in range(5)):
        raise SystemExit(f"{p['Name']}: hides pieces")
    pair = (MODELS[(key(p['Filename']), key(p.get('Skin')))], p['ScriptParams'].strip().lower())
    return next(prop for prop, posed in POSED.items() if posed == pair)


def objects():
    return [o for o in arena.objects() if o['class'] == 'RUDEProp']


def placements():
    return [(o['index'], object_prop(o)) for o in objects()]


def source_prop(prop):
    return SOURCES.get(prop, prop)


def built_props():
    """The spectator props built here: the placed ones minus the reused."""
    return sorted({prop for _, prop in placements()} - set(REUSED))


def home(prop):
    return REUSED.get(prop, HERE)


def source(prop):
    """(model path, [skin path]) under mm9/extracted for a prop id."""
    model, skin = next(k for k, v in MODELS.items() if v == source_prop(prop))
    roots = {'models': 'MODELS/MODELS', 'skins': 'SKINS/SKINS'}

    def path(s):
        top, rest = s.split('/', 1)
        return EXTRACTED / roots[top] / rest
    return path(model), [path(skin)]


resolve = arena.resolve


def binding_origin(prop):
    return json.loads((home(prop) / 'work/binding_origins.json').read_text())[source_prop(prop)]


def main():
    """python3 scripts/spectators.py convert|textures|finish [prop ...] [--install] [--force]: Sturmford City's convert
    (library pose added, shadow n-gon stripped), textures (Lanczos x4) and finish steps on the spectators built here.
    The Blender build is scripts/build_spectators.py, the review scripts/review.py -- <prop ...>."""
    import sturmford
    step, args = sys.argv[1], sys.argv[2:]
    props = [a for a in args if not a.startswith('--')] or built_props()
    sys.argv = [sys.argv[0]] + props + [a for a in args if a.startswith('--')]
    sys.exit(sturmford.load({'convert': 'convert_all', 'textures': 'textures', 'finish': 'finish'}[step]).main())


if __name__ == '__main__':
    main()
