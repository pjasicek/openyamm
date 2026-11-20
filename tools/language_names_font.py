#!/usr/bin/env python3
"""Builds the font the Settings language list draws its names with (menu_language_names, devdocs/LOCALIZATION.md):
every language pack's native name (Čeština, Русский, 简体中文 ...) must show whatever the interface language is, and
the interface faces of one language lack the others' letters (Fondamento has no Č, Cyrillic or CJK).

It is a subset of the Chinese pack's LXGW WenKai (SIL OFL 1.1) holding printable ASCII, Latin-1, Latin Extended-A,
basic Cyrillic and every character of the packs' names and of their translations of the list's texts ("English",
"{language} (download {size} MB)"), renamed
"OpenYAMM Language Names" (the OFL's Reserved Font Names may not be used by a subset outside web delivery). Writes,
into assets_dev/engine/fonts/truetype/: menu_language_names.ttf, .charset.txt, .yml and _ofl.txt. Run it again after
adding a language pack or changing a pack's name.

Needs fontTools (pip install fonttools):  python3 tools/language_names_font.py
"""
import re
import sys
from pathlib import Path

try:
    from fontTools import subset
    from fontTools.ttLib import TTFont
except ImportError:
    sys.exit('language_names_font.py needs fontTools: pip install fonttools')

REPO = Path(__file__).resolve().parents[1]
LANGUAGES = REPO / 'assets_dev/languages'
SOURCE = LANGUAGES / 'zh-cn/engine/fonts/truetype/lxgwwenkai.ttf'
SOURCE_LICENSE = LANGUAGES / 'zh-cn/engine/fonts/truetype/lxgwwenkai_ofl.txt'
OUT = REPO / 'assets_dev/engine/fonts/truetype'
NAME = 'menu_language_names'
FAMILY = 'OpenYAMM Language Names'
# The list's own texts, as each pack translates them.
LABELS = ['English', '{language} (download {size} MB)']

DESCRIPTOR = f"""\
# The Settings language list's names in every language's own script (tools/language_names_font.py): a renamed subset
# of LXGW WenKai (SIL OFL, {NAME}_ofl.txt) at Fondamento's height and baseline.
file: {NAME}.ttf
metrics: freetype
logical_height: 32
baseline: 25
encoding: utf-8
characters_file: {NAME}.charset.txt
max_raster_height: 64
"""


def characters():
    wanted = {chr(code) for code in range(0x20, 0x7f)}
    wanted |= {chr(code) for code in range(0xa0, 0x180)}      # Latin-1 and Latin Extended-A
    wanted |= {chr(code) for code in range(0x400, 0x460)}     # basic Cyrillic
    wanted |= set('English')
    for descriptor in sorted(LANGUAGES.glob('*/language.yml')):
        text = descriptor.read_text(encoding='utf-8')
        for key in ('name', 'english_name'):
            match = re.search(rf'^{key}:\s*(.+)$', text, re.MULTILINE)
            if match:
                wanted |= set(match.group(1).strip().strip('"\''))
        po = descriptor.parent / 'text/engine.po'
        if po.exists():
            text = po.read_text(encoding='utf-8')
            for label in LABELS:
                match = re.search(r'^msgid "' + re.escape(label) + r'"\nmsgstr "(.*)"$', text, re.MULTILINE)
                if match:
                    wanted |= set(match.group(1))
    return wanted


def main():
    font = TTFont(SOURCE)
    cmap = font.getBestCmap()
    wanted = characters()
    missing = sorted(character for character in wanted if ord(character) not in cmap and character.isprintable()
                     and not character.isspace() and character != '\xad')
    kept = sorted(character for character in wanted if ord(character) in cmap)
    if missing:
        print('not in the source font:', ''.join(missing))

    options = subset.Options()
    options.name_IDs = ['*']
    options.name_languages = ['*']
    options.notdef_outline = True
    options.hinting = False
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=[ord(character) for character in kept])
    subsetter.subset(font)

    # The OFL: a Modified Version must not carry the Reserved Font Names (LXGW, 霞鹜 ...).
    postscript = FAMILY.replace(' ', '') + '-Medium'
    names = {1: FAMILY, 2: 'Medium', 3: postscript, 4: FAMILY + ' Medium', 6: postscript, 16: FAMILY, 17: 'Medium'}
    table = font['name']
    for record in list(table.names):
        if record.nameID in (1, 2, 3, 4, 6, 16, 17, 21, 22):
            table.removeNames(nameID=record.nameID)
    for name_id, value in names.items():
        table.setName(value, name_id, 3, 1, 0x409)
        table.setName(value, name_id, 1, 0, 0)
    font.save(OUT / f'{NAME}.ttf')

    (OUT / f'{NAME}.charset.txt').write_text(''.join(kept), encoding='utf-8')
    (OUT / f'{NAME}.yml').write_text(DESCRIPTOR, encoding='utf-8')
    license_text = SOURCE_LICENSE.read_text(encoding='utf-8')
    (OUT / f'{NAME}_ofl.txt').write_text(
        f'{NAME}.ttf ("{FAMILY}") is a Modified Version of LXGW WenKai: a subset of its glyphs (see\n'
        f'tools/language_names_font.py), renamed as the license below requires.\n\n' + license_text,
        encoding='utf-8')
    print(f'{NAME}.ttf: {len(kept)} characters, {(OUT / f"{NAME}.ttf").stat().st_size // 1024} KB')


if __name__ == '__main__':
    main()
