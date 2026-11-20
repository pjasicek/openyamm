"""Writes tools/mm9_import_discovery/mm9_spellbook_art.yml: each mastery's reviewed x2 icon and its sha256, which
import_mm9_items.py checks before installing it. Usage: python3 -I register_icons.py"""
import hashlib
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
lines = ['# MM9 spellbook icons by mastery (tools/mm9_import_discovery/mm9_spellbooks.py), installed by import_mm9_items.py',
         '# as icons_x2/mm9_spellbook_<mastery>.png. Art: level_generation/ui/mm9_spellbooks_20261108/ (git-ignored),',
         '# written by its register_icons.py.', 'icons:']
for mastery in ('normal', 'expert', 'master', 'grandmaster'):
    path = os.path.join(HERE, mastery, 'icon_x2.png')
    digest = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    lines += [f'  {mastery}:', f'    source: {os.path.relpath(path, REPO)}', f'    sha256: {digest}']
with open(os.path.join(REPO, 'tools', 'mm9_import_discovery', 'mm9_spellbook_art.yml'), 'w') as stream:
    stream.write('\n'.join(lines) + '\n')
print('\n'.join(lines))
