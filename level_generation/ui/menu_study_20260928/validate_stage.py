#!/usr/bin/env python3
"""Verify the menu integration bundle, including the real C++ UI layout parser."""

import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from PIL import Image
import yaml


STUDY = Path(__file__).resolve().parent
REPO = STUDY.parents[2]
OUT = STUDY / 'runtime_stage'
KEYS = {'id', 'anchor', 'anchor_space', 'offset_x', 'offset_y', 'width', 'height', 'z_index', 'scale',
        'visible', 'interactive', 'asset', 'text', 'notes', 'children'}
TEXT_KEYS = {'value', 'font', 'color', 'align_x', 'align_y', 'scale', 'pad_x', 'pad_y'}
ASSET_KEYS = {'default', 'highlighted', 'pressed', 'selected', 'frame', 'health_bar', 'mana_bar'}
ids = {}
fonts = set()
references = set()
checks = []
contracts = yaml.safe_load((OUT / 'contracts/screens.yml').read_text())
scroll_ids = {entry['element'] for entry in contracts['scroll_regions']}
surfaces = json.loads((OUT / 'source/surfaces.json').read_text())
skin_keys = {entry['key'] for entry in surfaces['surfaces']}


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def walk(nodes, source, offset=(0, 0), in_scroll=False):
    for node in nodes:
        check(not (set(node) - KEYS), f'Unsupported layout keys in {node["id"]}: {set(node) - KEYS}')
        normalized = re.sub('[-_ ]', '', node['id'].lower())
        check(normalized not in ids, f'Duplicate normalized ID: {node["id"]}')
        ids[normalized] = node['id']
        check(node['width'] > 0 and node['height'] > 0, f'Empty rectangle: {node["id"]}')
        x, y = offset[0] + node.get('offset_x', 0), offset[1] + node.get('offset_y', 0)
        clipped = in_scroll or node['id'] in scroll_ids
        if 'Root' not in node['id'] and not clipped:
            check(x >= -0.01 and y >= -0.01 and x + node['width'] <= 853.34 and y + node['height'] <= 480.01,
                  f'Unclipped content leaves the canvas: {node["id"]} {(x,y,node["width"],node["height"])}')
        if 'asset' in node:
            check(not (set(node['asset']) - ASSET_KEYS), f'Unsupported asset state: {node["id"]}')
            for key in node['asset'].values():
                check((OUT / 'engine/icons_x2' / (key + '.png')).is_file(), f'Missing asset {key}')
                references.add(key)
        if 'text' in node:
            check(not (set(node['text']) - TEXT_KEYS), f'Unsupported text key: {node["id"]}')
            check(node['text']['font'] in ('fondamento', 'arrus', 'lucida'), f'Wrong font: {node["id"]}')
            check(node['text']['scale'] > 0, f'Invalid text scale: {node["id"]}')
            check(re.fullmatch(r'#[0-9a-f]{6}', node['text']['color']), f'Invalid text colour: {node["id"]}')
            fonts.add(node['text']['font'])
        walk(node.get('children', []), source, (x, y), clipped)


layouts = sorted((OUT / 'engine/ui').rglob('*.yml'))
check(len(layouts) == 13, 'Expected all 13 layouts')
for file in layouts:
    data = yaml.safe_load(file.read_text())
    check(set(data) == {'screen', 'elements'}, f'Unexpected root schema: {file}')
    walk(data['elements'], file)
checks.append(f'13 layouts, {len(ids)} globally unique elements, supported YAML fields and bounded/explicitly clipped geometry')
for entry in contracts['actions']:
    check(entry['element'] in ids.values(), 'Action points to missing element: ' + entry['element'])
    for state in ('default', 'hover', 'pressed', 'disabled'):
        check(entry['skin'] + '_' + state in skin_keys, 'Missing button state: ' + entry['skin'] + '_' + state)
for entry in contracts['scroll_regions']:
    check(entry['element'] in ids.values(), 'Scroll viewport missing: ' + entry['element'])
checks.append(f'{len(contracts["actions"])} action hooks and {len(scroll_ids)} scroll regions resolve')

for entry in surfaces['surfaces']:
    with Image.open(OUT / entry['file']) as image:
        check(list(image.size) == entry['imageSize'], 'Wrong image size: ' + entry['file'])
        image.verify()
    insets = entry['nineSliceInsets']
    if insets:
        top, right, bottom, left = insets
        check(left + right < entry['imageSize'][0] and top + bottom < entry['imageSize'][1],
              'Invalid nine-slice: ' + entry['key'])
    check(Path(entry['file']).name.islower(), 'Asset name is not lowercase: ' + entry['file'])
checks.append(f'{len(surfaces["surfaces"])} decoded surface exports with valid dimensions and slice bounds')

for name, expected in surfaces['sourceHashes'].items():
    check(hashlib.sha256((STUDY / name).read_bytes()).hexdigest() == expected, 'Study changed since export: ' + name)
    check(hashlib.sha256((OUT / 'source' / name).read_bytes()).hexdigest() == expected, 'Source snapshot drift: ' + name)
for entry in json.loads((OUT / 'source/copy_receipt.json').read_text()):
    check(hashlib.sha256((OUT / entry['file']).read_bytes()).hexdigest() == entry['sha256'], 'Copy drift: ' + entry['file'])
    check(hashlib.sha256((REPO / entry['source']).read_bytes()).hexdigest() == entry['sha256'], 'Source drift: ' + entry['source'])
check(not any('references' in str(file) for file in (OUT / 'engine').rglob('*')), 'Comparison art entered runtime payload')
for file in (OUT / 'engine').rglob('*'):
    if file.is_file():
        check((file.stat().st_mode & 0o777) == 0o644, 'Runtime file mode is not 0644: ' + str(file))
checks.append('Approved source snapshots, copied fonts/materials/reference images and 0644 payload modes match receipts')

settings = yaml.safe_load((OUT / 'contracts/settings.yml').read_text())['settings']
keyboard = yaml.safe_load((OUT / 'contracts/keyboard.yml').read_text())['actions']
check(len(settings) == 30 and len({item['ini'] for item in settings}) == 30, 'Settings audit incomplete')
check(len(keyboard) == 26 and len({item['id'] for item in keyboard}) == 26, 'Keyboard registry incomplete')
check(all('value' not in item for item in settings), 'Browser defaults leaked into settings contract')
check(all('code' not in item for item in keyboard), 'Browser key codes leaked into registry contract')
keyboard_layout = yaml.safe_load((OUT / 'engine/ui/gameplay/settings_keyboard.yml').read_text())
keyboard_text = (OUT / 'engine/ui/gameplay/settings_keyboard.yml').read_text()
for action in keyboard:
    check('{key_' + action['id'] + '}' in keyboard_text, 'Missing key binding placeholder: ' + action['id'])
checks.append('30 unique INI-backed settings and all 26 implemented binding IDs; no browser-only defaults promoted')

# Link the actual parser, discarding the unused AssetFileSystem file-loading function.
cpp = r'''#include "game/ui/UiLayoutManager.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
int main(int argc, char **argv)
{
    OpenYAMM::Game::UiLayoutManager manager;
    for (int i = 1; i < argc; ++i)
    {
        std::ifstream file(argv[i]);
        std::ostringstream content;
        content << file.rdbuf();
        if (!file || !manager.loadLayoutText(argv[i], content.str()))
        {
            std::cerr << "Rejected layout: " << argv[i] << '\n';
            return 1;
        }
    }
    size_t textCount = 0;
    for (const auto &[key, element] : manager.elements())
    {
        if (!element.parentId.empty() && manager.findElement(element.parentId) == nullptr)
        {
            return 2;
        }
        if (!element.fontName.empty())
        {
            ++textCount;
        }
    }
    std::cout << manager.elements().size() << " elements; " << textCount << " live text elements\n";
}
'''
with tempfile.TemporaryDirectory(prefix='openyamm-menu-yaml-') as temp:
    source, binary = Path(temp) / 'check.cpp', Path(temp) / 'check'
    source.write_text(cpp)
    result = subprocess.run(['c++', '-std=c++20', '-ffunction-sections', '-fdata-sections', '-I' + str(REPO),
                             '-I' + str(REPO / 'build/_deps/yaml-cpp-src/include'), str(source),
                             str(REPO / 'game/ui/UiLayoutManager.cpp'),
                             str(REPO / 'build/_deps/yaml-cpp-build/libyaml-cpp.a'),
                             '-Wl,--gc-sections', '-o', str(binary)], capture_output=True, text=True)
    check(result.returncode == 0, 'Parser checker compilation failed: ' + result.stderr)
    parsed = subprocess.run([str(binary), *[str(file) for file in layouts]], capture_output=True, text=True)
    check(parsed.returncode == 0, 'Native parser rejected a layout: ' + parsed.stderr)
    check(parsed.stdout.startswith(str(len(ids)) + ' elements;'), 'Native parser lost or overwrote elements')
checks.append('Actual UiLayoutManager.cpp accepted every draft: ' + parsed.stdout.strip())

files = []
for file in sorted(OUT.rglob('*')):
    if not file.is_file() or file.name in ('manifest.json', 'validation.json'):
        continue
    relative = file.relative_to(OUT).as_posix()
    record = {'file': relative, 'bytes': file.stat().st_size, 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()}
    if relative.startswith('engine/'):
        record['candidate_destination'] = 'assets_dev/' + relative
        record['virtual_path'] = 'Data/' + relative.removeprefix('engine/')
        record['status'] = 'Staged; activation requires the documented runtime changes'
    files.append(record)
(OUT / 'manifest.json').write_text(json.dumps({'design': 'Carved Obsidian menus r03', 'runtime_activated': False,
                                              'files': files}, indent=2) + '\n')
(OUT / 'validation.json').write_text(json.dumps({'status': 'passed', 'checks': checks,
                                                'native_parser_source': 'game/ui/UiLayoutManager.cpp',
                                                'layout_count': len(layouts), 'element_count': len(ids),
                                                'surface_count': len(surfaces['surfaces']),
                                                'referenced_graphics': len(references),
                                                'runtime_rendered': False,
                                                'browser_baseline': 'source/browser_validation_r03.json'}, indent=2) + '\n')
print('\n'.join(checks))
print(f'Manifest: {len(files)} files, {sum(file["bytes"] for file in files):,} bytes. Staging validation passed.')
