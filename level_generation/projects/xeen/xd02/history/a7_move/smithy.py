import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
#!/usr/bin/env python3
# Lane A7 (2026-11-20, orchestrator's request from A4): the Red Dwarf Smithy's door in the adit mouth (house 4851,
# towns/xd02.yml), barred until m3.done (111061).
import sys
L = _REPO_ROOT + '/devdocs/xeen/briefs/xd02/L4'
def rep(path, old, new):
    t = open(path).read()
    if t.count(old) != 1:
        sys.exit(f'{path}: {old[:60]!r} found {t.count(old)} times')
    open(path, 'w').write(t.replace(old, new))
rep(L + '/project.yml', '  x4_adit_open: 110020\n', '  x4_adit_open: 110020\n  m3_done: 111061\n')
old = ('          - {id: panel:clan_sign, offset: 176, length: 256, bottom: 160, height: 128, surface: {texture: xnclansgn, '
       'size: [256, 128], fit: true}, notes: "The clan\'s warning: skulls daubed on a board."}\n')
rep(L + '/rooms.yml', old, old +
    '      - wall: south\n'
    '        panels:\n'
    '          - {id: door:dwarf_smithy, offset: 764, length: 192, bottom: 0, height: 288, surface: {texture: t3dr1, '
    'size: [256, 256], fit: true}, notes: "The Red Dwarf Smithy\'s plank door (house 4851, A4\'s towns/xd02.yml) between '
    'two timber sets of the south wall: barred until M3 is done (wiring evt:dwarf_smithy)."}\n')
old = '  - id: evt:deep_barrel\n'
rep(L + '/wiring.yml', old,
    '  - id: evt:dwarf_smithy\n'
    '    preset: script\n'
    '    source: door:dwarf_smithy\n'
    '    title: Red Dwarf Smithy\n'
    '    condition: {qbit: m3_done}\n'
    '    effects:\n'
    '      - lua: "evt.EnterHouse(4851)"\n'
    '    else_effects:\n'
    '      - message: "The smithy is barred. Behind the door, someone is sharpening something and swearing at the Mad Clan."\n'
    '    notes: "The Red Dwarf Smithy (house 4851, A4\'s source/towns/xd02.yml; TOWNS_FORMAT 1, `opens: m3.done`): once '
    'M3 is done (m3.done 111061, A3\'s m3.yml, hook m3.dwarf_shop) the door opens the house; before, a message window '
    'with A4\'s closed text."\n' + old)
print('ok')
