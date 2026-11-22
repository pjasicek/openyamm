"""A5 s29 (2026-11-22, F16 / D-90 point 4): a way into a dungeon shows the standard MM6-MM8 entrance window; a door
with a row in Xeen's trans.txt (A3's `drafts/XEEN_TRANS_ROWS_DRAFT.md`, generated from source/entrances.yml) shows
that row's line in place of "Do you wish to enter X?" (`into.screen: {text: <id>}`). Shortcuts opened from inside
have no row and keep the standard window. Called by each A5 outdoor generator on its finished sketch."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import os

ROOT = _REPO_ROOT
TRANS = os.path.join(ROOT, 'assets_dev/worlds/xeen/data_tables/english/trans.txt')

ROWS = {
    'x1': {'thing:warehouse_door': 5001, 'thing:mine_portal': 5002, 'thing:witch_tower_door': 5004,
           'thing:orc_cave_mouth': 5005},
    'x2': {'thing:yak_temple': 5006, 'thing:darzog_tower': 5012, 'thing:den_door': 5021, 'thing:ogre_lair': 5027},
    'x3': {'thing:tomb': 5008, 'thing:high_magic': 5011, 'thing:xd13_stair': 5013, 'thing:coffin_open': 5024},
    'x4': {'thing:castle_gate': 5007, 'thing:xd25_stair': 5025, 'thing:xd26_eyrie': 5026},
    'x6': {'thing:castle_basenji': 5014, 'thing:northern_sphinx': 5015, 'thing:arena_gate': 5020,
           'thing:southern_sphinx': 5063},
    'x7': {'thing:xd16_mouth': 5016, 'thing:xd17_cleft': 5017, 'thing:xd18_mouth': 5018, 'thing:fd04_gate': 5065},
    'd3': {'thing:eastern_tower': 5035, 'thing:dd18_shaft': 5051, 'thing:dd19_gate': 5053},
}


def rows():
    out = {}
    for line in open(TRANS, encoding='utf-8'):
        parts = line.rstrip('\n').split('\t')
        if parts and parts[0].isdigit():
            out[int(parts[0])] = parts[1].strip('"').replace('""', '"')
    return out


def _intos(node):
    if isinstance(node, dict):
        into = node.get('into')
        if isinstance(into, dict) and str(into.get('map', '')).endswith('.blv'):
            yield into
        for key, value in node.items():
            if key != 'into':
                yield from _intos(value)
    elif isinstance(node, list):
        for value in node:
            yield from _intos(value)


def apply(sketch, key):
    """Sets `screen: {text: row}` on every way into a .blv whose structure has a row; returns notes."""
    table = ROWS.get(key, {})
    known = rows()
    notes, seen = [], set()
    for structure in sketch.get('structures') or []:
        sid = structure.get('id')
        for into in _intos(structure):
            row = table.get(sid)
            if row is None:
                notes.append('%s -> %s: the standard window (no trans row)' % (sid, into['map']))
                continue
            assert row in known, 'trans.txt has no row %d' % row
            if into.get('screen') != 'none':
                into['screen'] = {'text': row}
            seen.add(sid)
            notes.append('%s -> %s: window with trans %d' % (sid, into['map'], row))
    for sid in sorted(set(table) - seen):
        notes.append('%s: has a trans row but no way into a .blv in this sketch' % sid)
    return notes
