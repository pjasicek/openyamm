#!/usr/bin/env python3
"""Prepare integration drafts from the measured, approved browser study. Never installs them."""

import hashlib
import html
import json
from pathlib import Path
import re
import shutil

import yaml


STUDY = Path(__file__).resolve().parent
REPO = STUDY.parents[2]
OUT = STUDY / 'runtime_stage'
G = json.loads((OUT / 'source/geometry.json').read_text())
CATALOG = json.loads((OUT / 'source/catalog.json').read_text())
SURFACES = json.loads((OUT / 'source/surfaces.json').read_text())
FACTOR = 480 / 900
LAYOUTS = []
HOOKS = []
SCROLLS = []
SOURCES = []


def number(value):
    return round(value * FACTOR, 4)


def title(value):
    return ''.join(part[:1].upper() + part[1:] for part in re.split(r'[-_ ]+', value))


def dump(path, data):
    path = OUT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=110))


def copy(source, target, purpose):
    source = Path(source)
    target_path = OUT / target
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target_path)
    target_path.chmod(0o644)
    SOURCES.append({'file': target, 'source': str(source.relative_to(REPO)), 'operation': 'unchanged copy',
                    'purpose': purpose, 'sha256': hashlib.sha256(target_path.read_bytes()).hexdigest()})


def changed(item, rect=None, **kwargs):
    return dict(item, **({'rect': rect} if rect is not None else {}), **kwargs)


def rect_item(rect, font='OpenYAMMLucida', font_size=17, color='rgb(194,182,155)', align='left'):
    return {'rect': rect, 'font': font, 'fontSize': font_size, 'color': color, 'align': align}


def color(value):
    components = [int(n) for n in re.findall(r'\d+', value)[:3]]
    return '#' + ''.join(f'{n:02x}' for n in components) if any(components) else '#e9d4a6'


def typography(item, value):
    family = item['font']
    font, cell, adjust = ('fondamento', 32, 1) if 'Fondamento' in family else (
        ('arrus', 19, 1.2) if 'Arrus' in family else ('lucida', 17, 1.2))
    text = {'value': value, 'font': font, 'color': color(item['color']),
            'align_x': item['align'] if item['align'] in ('left', 'center', 'right') else 'left',
            'align_y': 'middle', 'scale': round(item['fontSize'] * FACTOR * adjust / cell, 5)}
    if item.get('padding'):
        text['pad_x'] = number(float(item['padding'][3].removesuffix('px')))
    return text


class Layout:
    def __init__(self, screen, source, file):
        self.screen, self.source, self.file = screen, source, file
        self.geometry = G[source]
        self.children = []
        self.origin = (0, 0)
        self.root = {'id': screen + 'Root', 'anchor': 'center', 'anchor_space': 'screen',
                     'width': number(1600), 'height': 480, 'z_index': 0,
                     'scale': {'min': 0.1, 'max': 8.0, 'reference_width': number(1600), 'reference_height': 480},
                     'notes': 'Integration draft. Fit the complete 16:9 canvas; see contracts/theme.yml. '
                              'The current menu resolver does not yet honor this reference width.',
                     'children': self.children}

    def node(self, id, item, text=None, asset=None, interactive=False, notes=None, z=10):
        x, y, width, height = item['rect']
        node = {'id': id, 'anchor': 'top_left', 'offset_x': number(x - self.origin[0]),
                'offset_y': number(y - self.origin[1]), 'width': number(width), 'height': number(height),
                'z_index': z, 'visible': True, 'interactive': interactive}
        if asset:
            node['asset'] = {'default': asset} if isinstance(asset, str) else asset
        if text is not None:
            node['text'] = typography(item, text)
            if '{' in text:
                notes = (notes + ' ' if notes else '') + 'Controller supplies live text; braces are draft placeholders.'
        if notes:
            node['notes'] = notes
        self.children.append(node)
        return node

    def text(self, id, item, value=None, **kwargs):
        return self.node(id, item, item.get('text', '') if value is None else value, **kwargs)

    def skin(self, id, item, name, pad=0, z=2):
        x, y, width, height = item['rect']
        return self.node(id, changed(item, [x-pad, y-pad, width+pad*2, height+pad*2]),
                         asset='omenu_' + name, z=z)

    def action(self, id, item, action=None, value=None):
        classes = item.get('classes', '')
        family = next((name for name in ('square', 'small', 'danger', 'primary', 'quiet') if name in classes), '')
        family = 'omenu_button' + ('_' + family if family else '')
        assets = {field: family + '_' + state for field, state in
                  [('default', 'default'), ('highlighted', 'hover'), ('pressed', 'pressed')]}
        node = self.text(id, item, value, asset=assets, interactive=True,
                         notes='Live label; image padding, disabled and focus states: contracts/theme.yml.')
        node['text']['align_x'] = 'center'
        if action:
            HOOKS.append({'element': id, 'screen': self.screen, 'action': action, 'skin': family,
                          'arguments': {key: value for key, value in item.get('data', {}).items() if key != 'action'}})
        return node

    def scroll(self, name, item):
        node = self.node(self.screen + name, item, notes='Clip all descendant rendering and pointer hits to this '
                         'viewport. Scroll offset is controller-owned; YAML has no clipping/scroll primitive.')
        self.children = node.setdefault('children', [])
        self.origin = item['rect'][:2]
        SCROLLS.append({'element': node['id'], 'screen': self.screen,
                        'viewport': [number(n) for n in item['rect']],
                        'content_height': number(item.get('scroll', [0, item['rect'][3]])[1]),
                        'wheel': 'vertical', 'keyboard': 'keep focused row visible', 'clip_input': True})

    def end_scroll(self):
        self.children = self.root['children']
        self.origin = (0, 0)

    def chrome(self):
        g = self.geometry
        if self.source != 'pause':
            self.node(self.screen + 'Background', rect_item([0, 0, 1600, 900]),
                      asset='omenu_title_backdrop', z=0,
                      notes='Use the live dimmed game view instead when entered from Pause.')
        else:
            self.node('MenuBackground', rect_item([0, 0, 1600, 900]), z=0,
                      notes='Live frozen game frame with dark overlay; never use the study screenshot as an asset.')
        if g['frame']:
            self.skin(self.screen + 'Panel', g['frame'][0],
                      'party_frame' if self.source == 'creation' else 'frame', pad=16)
        for key, suffix in [('seal', 'Seal'), ('wordmark', 'Wordmark'), ('subtitle', 'Subtitle')]:
            if g[key]:
                item = g[key][0]
                if key == 'seal':
                    self.skin(self.screen + suffix, item, 'seal', z=8)
                else:
                    self.text(self.screen + suffix, item)
        if g['h1']:
            self.text(self.screen + 'Title', g['h1'][0], '{current_location}' if self.source == 'pause' else None)
        for index, key in enumerate(('head', 'footer')):
            if g[key]:
                r = g[key][0]['rect']
                y = r[1] + r[3] - 1 if key == 'head' else r[1]
                self.node(self.screen + title(key) + 'Rule', rect_item([r[0], y, r[2], 1]),
                          notes='Renderer primitive: 1px brass rule, #b5a47755, in the browser reference.')

    def finish(self):
        dump(self.file, {'screen': self.screen, 'elements': [self.root]})
        LAYOUTS.append({'file': self.file, 'screen': self.screen, 'source_screen': self.source,
                        'root': self.root['id']})


# Copy only the accepted fonts and art. Artist comparison backgrounds stay in the study.
for name, target in [('Fondamento-Regular.ttf', 'fondamento_regular.ttf'),
                     ('openyamm_arrus_faithful.ttf', 'openyamm_arrus_faithful.ttf'),
                     ('openyamm_lucida_faithful.ttf', 'openyamm_lucida_faithful.ttf'),
                     ('fondamento-OFL.txt', 'fondamento_ofl.txt')]:
    copy(STUDY / 'assets/fonts' / name, 'engine/fonts/truetype/' + target, 'Approved live menu typography')
for name in ('arrus', 'lucida'):
    copy(REPO / 'assets_dev/engine/fonts/truetype' / (name + '.yml'),
         'engine/fonts/truetype/' + name + '.yml', 'Existing native font descriptor; reuse if already mounted')
for name in ('enroth', 'antagarich', 'jadame'):
    copy(STUDY / 'assets' / (name + '.png'), 'engine/icons_x2/omenu_continent_' + name + '.png',
         'Unchanged original continent illustration; provenance retained in source/asset_sources.json')
for source, target in [('assets/generated/universe-dusk-v1.png', 'universe-dusk-v1.png'),
                       ('assets/stone-panel.png', 'stone-panel.png'), ('assets/button-grain.png', 'button-grain.png'),
                       ('style.css', 'style.css'), ('app.js', 'app.js'), ('index.html', 'index.html'),
                       ('data.js', 'data.js'), ('generated_art.json', 'generated_art.json'),
                       ('asset_sources.json', 'asset_sources.json'), ('background_sources.json', 'background_sources.json'),
                       ('settings_audit.json', 'settings_audit.json'), ('binding_audit.json', 'binding_audit.json'),
                       ('browser_validation_r03.json', 'browser_validation_r03.json')]:
    copy(STUDY / source, 'source/' + target, 'Frozen approved design source / provenance; not mounted runtime content')
for source in sorted((STUDY / 'previews').glob('r03-*.png')):
    copy(source, 'reference/' + source.name, 'Approved browser reference; not a game texture')
seal_path = OUT / 'source/seal.svg'
seal_path.write_text(seal_path.read_text().replace('stroke:#b7a06a;stroke-width:1.4',
                                                 'stroke:#cbb47f;stroke-width:1.2'))


layout = Layout('MainMenu', 'main', 'engine/ui/menu/main_menu.yml')
layout.chrome()
layout.skin('MainMenuActionPanel', G['main']['titlePanel'][0], 'title_panel', pad=16)
for item in G['main']['actions']:
    action = item['data']['action']
    suffix = 'LoadGame' if action == 'load' else title(action)
    layout.action('MainMenu' + suffix + 'Button', item, action)
layout.text('MainMenuContinueInfo', G['main']['continueInfo'][0], '{latest_save_location} · {world_name}')
footer = G['main']['titleFooter'][0]
x, y, width, height = footer['rect']
layout.text('MainMenuFooterWorlds', changed(footer, [x, y, width/2, height]), 'Enroth · Antagarich · Jadame')
layout.text('MainMenuFooterName', changed(footer, [x+width/2, y, width/2, height], align='right'), 'OpenYAMM')
layout.finish()

layout = Layout('Menu', 'pause', 'engine/ui/gameplay/menu.yml')
layout.chrome()
layout.skin('MenuPanel', G['pause']['pausePanel'][0], 'pause_panel', pad=16)
layout.text('MenuWorldAndDate', G['pause']['fineprint'][0], '{world_name} · {game_date}')
pause_ids = {'resume': 'Return', 'save': 'SaveGame', 'load': 'LoadGame', 'settings': 'Settings',
             'new-game': 'NewGame', 'main-menu': 'MainMenu', 'quit': 'Quit'}
for item in G['pause']['actions']:
    action = item['data']['action']
    layout.action('MenuButton' + pause_ids[action], item, action)
layout.finish()

for source, screen in [('load', 'LoadGame'), ('save', 'SaveGame')]:
    layout = Layout(screen, source, f'engine/ui/gameplay/{source}_game.yml')
    g = G[source]
    layout.chrome()
    layout.scroll('ListViewport', g['saveList'][0])
    # Slots are row templates, not sample save records. Runtime recycles them for arbitrary list lengths.
    for index, row in enumerate(g['saveRows']):
        slot = screen + 'SlotRow' + str(index)
        layout.node(slot, row, asset={'default': 'omenu_save_row', 'selected': 'omenu_save_row_selected'},
                    interactive=True, notes='Controller binds an actual save or the New Save sentinel; see screen contracts.')
        x, y, width, height = row['rect']
        layout.text(slot + 'Number', rect_item([x+16, y+27, 37, 24]), '{slot_number}')
        layout.text(slot + 'Name', changed(g['saveNames'][index], [x+63, y+18, width-170, 27]), '{save_name}')
        layout.text(slot + 'Location', changed(g['saveLocations'][index], [x+63, y+48, width-80, 18]), '{location} · {world}')
        layout.text(slot + 'Kind', rect_item([x+width-121, y+29, 105, 24], font_size=15, align='right'), '{save_kind}')
    layout.end_scroll()
    layout.text(screen + 'SelectedWorldAndKind', g['eyebrow'][0], '{world_name} · {save_kind}')
    layout.text(screen + 'SelectedName', g['h2'][0], '{selected_location}')
    layout.node(screen + 'PreviewRect', g['savePreview'][0], notes='Save thumbnail texture; fit/crop as reference. '
                'Fallback is continent illustration plus No screenshot available. Never bake a demo screenshot.')
    for index, item in enumerate(g['saveMetaLabels']):
        layout.text(screen + 'PreviewLabel' + str(index+1), item)
        layout.text(screen + 'PreviewLine' + str(index+1), g['saveMetaValues'][index],
                    '{game_date}' if index == 0 else '{game_time}')
    if source == 'save':
        item = g['saveName'][0]
        layout.node(screen + 'NameField', item, text='{save_name}', asset='omenu_text_field', interactive=True,
                    notes='Editable name, maximum 40 characters; reject empty and reserved names in existing save controller.')
        x, y, width, _ = g['saveNameLabel'][0]['rect']
        layout.text(screen + 'NameLabel', rect_item([x, y, width, 20]), 'Save name')
    else:
        layout.text(screen + 'SelectedMetadata', g['fineprint'][0], '{save_name}\nSaved {saved_timestamp} · {save_kind} save')
    for item in g['actions']:
        action = item['data']['action']
        layout.action(screen + ('CancelButton' if action == 'back' else 'ConfirmButton'), item, action)
    layout.finish()

layout = Layout('ContinentSelection', 'worlds', 'engine/ui/gameplay/continent_selection.yml')
layout.chrome()
for index, world in enumerate(CATALOG['worlds']):
    prefix = 'ContinentSelection' + title(world['id'])
    layout.node(prefix + 'Button', G['worlds']['worlds'][index], interactive=True,
                asset={'default': 'omenu_world_card', 'selected': 'omenu_world_card_selected'},
                notes='Bind to mounted selectable world manifest; browser names are presentation examples.')
    layout.skin(prefix + 'Illustration', G['worlds']['worldImages'][index], 'continent_' + world['id'], z=12)
    layout.text(prefix + 'Name', G['worlds']['h2'][index], world['name'], z=13)
    layout.text(prefix + 'Game', G['worlds']['eyebrow'][index+1], world['game'], z=13)
    layout.text(prefix + 'Start', G['worlds']['worldTags'][index], 'Begin in ' + world['home'], z=13)
layout.text('ContinentSelectionStep', G['worlds']['stepNote'][0])
for item in G['worlds']['actions']:
    action = item['data']['action']
    layout.action('ContinentSelection' + ('CancelButton' if action == 'back' else 'ConfirmButton'), item, action)
layout.finish()

layout = Layout('CharacterCreation', 'creation', 'engine/ui/gameplay/character_creation.yml')
layout.chrome()
g = G['creation']
layout.text('CharacterCreationContinent', g['stepNote'][0], '{world_name} · {starting_location}')
layout.node('CharacterCreationPortraitImage', g['portrait'][0], notes='Native portrait texture from current character data.')
layout.node('CharacterCreationDoll', g['doll'][0], notes='Native paperdoll composition and layers from NewGameScreen; '
            'do not use the browser sample or replace its rules with study data.')
for key, prefix in [('h2', 'Section'), ('h3', 'Subsection')]:
    for index, item in enumerate(g[key]):
        layout.text('CharacterCreation' + prefix + str(index), item)
for index, item in enumerate(g['identityFields']):
    x, y, width, _ = item['rect']
    layout.text('CharacterCreation' + ('NameLabel' if index == 0 else 'ClassLabel'),
                changed(item, [x, y, width, 20]), 'Name' if index == 0 else 'Class')
layout.node('CharacterCreationNameField', g['fields'][0], '{character_name}', 'omenu_text_field', True,
            'Existing name input rules and encoding; browser mock limit is not authoritative.')
layout.node('CharacterCreationClassValue', g['selects'][0], '{class_name}', 'omenu_text_field', True,
            'Open a native choice list from available classes/races/world content; no browser hard-coded class restrictions.')
layout.text('CharacterCreationVoiceValue', g['voice'][0], 'Voice {voice_number} · {race_name}')
layout.text('CharacterCreationBonusPoolValue', g['pool'][0], '{bonus_points} points left')
for index, name in enumerate(CATALOG['stats']):
    layout.text('CharacterCreation' + name + 'Label', g['statNames'][index], name)
    layout.text('CharacterCreation' + name + 'Value', g['statValues'][index], '{' + name.lower() + '}')
layout.text('CharacterCreationAttributeHelp', g['fineprint'][0], 'Spend all {total_bonus_points} bonus points before beginning.')
for index, item in enumerate(g['assigned']):
    layout.node('CharacterCreationAssignedSkill' + str(index), item, '{assigned_skill_' + str(index) + '}',
                'omenu_assigned_skill', notes='Noninteractive class-granted skill. Preserve the stronger r03 tiles.')
for index, item in enumerate(g['skillChoices']):
    layout.node('CharacterCreationAvailableSkill' + str(index), item, '{optional_skill_' + str(index) + '}',
                {'default': 'omenu_skill', 'selected': 'omenu_skill_selected'}, True,
                'Two-column choices from class skill data; selection limit from character creation rules. '
                'Draw the plus/check as an icon, and dim unavailable choices.')
layout.text('CharacterCreationSkillCount', g['skillCounts'][0], '{chosen_count} / {required_count}')
layout.text('CharacterCreationReadiness', g['creationNote'][0], '{party_readiness_message}')
stat_right = g['stats'][0]['rect'][0] + g['stats'][0]['rect'][2]
layout.node('CharacterCreationColumnRule', rect_item([stat_right-1, g['stats'][0]['rect'][1], 1, 515]),
            notes='Renderer primitive: faint brass divider; keep the measured 48px extra section separation.')
for index in range(5):
    row = changed(g['partySlots'][0], [58+84*index, 695, 72, 77])
    layout.node(f'CharacterCreationPartySlot{index+1}Button', row,
                asset={'default': 'omenu_party_slot', 'selected': 'omenu_party_slot_selected'}, interactive=True,
                notes='Native portrait for an occupied slot; next available slot is Add. Capacity comes from engine rules.')
layout.text('CharacterCreationPartySummary', changed(g['partySummary'][0], [499, 715.5, 220, 40]),
            '{party_count} / {party_capacity} adventurers\n{ready_count} ready')
creation_ids = {'portrait-prev': 'PortraitLeftButton', 'portrait-next': 'PortraitRightButton',
                'voice-prev': 'VoiceLeftButton', 'voice-next': 'VoiceRightButton', 'hero-default': 'ResetCharacterButton',
                'remove-hero': 'RemoveCharacterButton', 'back': 'CancelButton', 'begin': 'ConfirmButton'}
for item in g['actions']:
    action = item['data']['action']
    suffix = creation_ids.get(action)
    if action == 'stat':
        suffix = CATALOG['stats'][int(item['data']['stat'])] + ('PlusButton' if item['data']['delta'] == '1' else 'MinusButton')
    layout.action('CharacterCreation' + suffix, item, action,
                  '-' if item['text'] == '−' else '<' if item['text'] == '‹' else '>' if item['text'] == '›' else None)
layout.finish()

for section in CATALOG['sections']:
    source, screen = section['id'], 'Settings' + title(section['id'])
    layout = Layout(screen, source, f'engine/ui/gameplay/settings_{source}.yml')
    g = G[source]
    layout.chrome()
    for item in g['tabs']:
        layout.node(screen + 'Tab' + title(item['data']['section']), item, item['text'],
                    {'default': 'omenu_tab', 'selected': 'omenu_tab_selected'}, True,
                    'Switch section without losing draft values. Selected state follows current section.')
    layout.text(screen + 'Heading', g['h2'][0])
    layout.text(screen + 'Description', g['settingSubtitle'][0])
    for item in g['actions']:
        action = item['data']['action']
        if action != 'keyboard':
            layout.action(screen + title(action) + 'Button', item, action)
    layout.text(screen + 'DirtyStatus', g['footerNote'][0], '{settings_status}')
    if source == 'keyboard':
        layout.node(screen + 'Search', g['fields'][0], '{search_query}', 'omenu_text_field', True,
                    'Search action/group/assigned-key name; do not search legacy page numbers.')
        layout.node(screen + 'GroupFilter', g['selects'][0], '{selected_group}', 'omenu_text_field', True)
        x, y, width, height = g['bindingHead'][0]['rect']
        for index, (text, offset, size) in enumerate([('Action', 12, 355), ('Assigned key', 383, 117),
                                                   ('Action', 522, 355), ('Assigned key', 891, 117)]):
            layout.text(screen + 'Column' + str(index), rect_item([x+offset, y, size, height], font_size=13), text)
    layout.scroll('ScrollViewport', g['settingScroll'][0])
    for item in g['actions']:
        if item['data']['action'] == 'keyboard':
            layout.action(screen + 'KeyboardButton', item, 'keyboard')
    for index, item in enumerate(g['groups']):
        layout.text(screen + 'Group' + str(index), item)
    if source == 'keyboard':
        for index, row in enumerate(g['bindingRows']):
            if index >= len(CATALOG['bindings']):
                # Fixed shortcuts remain data-driven; place them after filtered actions at runtime.
                name = 'Fixed' + str(index - len(CATALOG['bindings']))
                value = CATALOG['fixedBindings'][index-len(CATALOG['bindings'])]['key']
            else:
                binding_id = g['bindingKeys'][index]['data']['binding']
                binding = next(entry for entry in CATALOG['bindings'] if entry['id'] == binding_id)
                name = title(binding_id)
                value = '{key_' + binding_id + '}'
            x, y, width, height = row['rect']
            text_x, text_y, text_width, _ = g['bindingNames'][index]['rect']
            layout.text(screen + name + 'Label', changed(g['bindingNames'][index], [text_x, text_y, text_width, 25]),
                        binding['name'] if index < len(CATALOG['bindings'])
                        else CATALOG['fixedBindings'][index-len(CATALOG['bindings'])]['label'])
            layout.text(screen + name + 'Group', rect_item([text_x, text_y+28, text_width, 14.4],
                        font_size=12, color='rgb(160,170,153)'),
                        binding['group'] if index < len(CATALOG['bindings']) else 'Fixed shortcut')
            layout.node(screen + name + 'Key', g['bindingKeys'][index], value, 'omenu_keycap',
                        index < len(CATALOG['bindings']), 'Controller maps registry IDs, not browser KeyboardEvent codes.')
    else:
        settings = [setting for setting in CATALOG['settings'] if setting['section'] == source]
        for index, setting in enumerate(settings):
            prefix = screen + title(setting['id'])
            layout.text(prefix + 'Label', g['settingNames'][index])
            layout.text(prefix + 'Description', g['settingDescriptions'][index])
            controls = g['toggles'] + g['selects'] + g['ranges']
            control = next(item for item in controls if item['data'].get('setting') == setting['id'])
            if setting['type'] == 'toggle':
                asset = {'default': 'omenu_toggle_off', 'selected': 'omenu_toggle_on'}
            else:
                asset = 'omenu_text_field' if setting['type'] == 'select' else None
            layout.node(prefix + 'Control', control, '{' + setting['id'] + '}' if setting['type'] != 'range' else None,
                        asset, True, 'Bind to ' + setting['ini'] + '; see contracts/settings.yml. '
                        'Ranges need a track and thumb renderer; selection controls need native dropdown/focus behavior.')
            if setting['type'] == 'range':
                output = next(item for item in g['outputs'] if item['id'] == 'output-' + setting['id'])
                layout.text(prefix + 'Value', output, '{' + setting['id'] + '}' + setting.get('unit', ''))
    layout.end_scroll()
    layout.finish()

layout = Layout('Credits', 'credits', 'engine/ui/menu/credits.yml')
layout.chrome()
for index, item in enumerate(G['credits']['creditHeadings']):
    layout.text('CreditsHeading' + str(index), item)
for index, item in enumerate(G['credits']['creditParagraphs']):
    value = item['text'].replace('developerWith', 'developer\nWith')
    layout.text('CreditsText' + str(index), item, value)
layout.text('CreditsProjectLink', G['credits']['creditLinks'][0], 'OpenYAMM on GitHub', interactive=True,
            notes='Explicit click opens https://github.com/pjasicek/OpenYAMM in the browser.')
layout.action('CreditsBackButton', G['credits']['actions'][0], 'back')
layout.finish()

layout = Layout('MenuConfirmation', 'confirmation', 'engine/ui/menu/confirmation.yml')
g = G['confirmation']
layout.skin('MenuConfirmationVeil', rect_item([0, 0, 1600, 900]), 'modal_veil', z=100)
layout.skin('MenuConfirmationPanel', g['modal'][0], 'modal', pad=16, z=101)
modal_seal = [item for item in g['seal'] if item['rect'][2] == 56][0]
layout.skin('MenuConfirmationSeal', modal_seal, 'seal', z=102)
layout.text('MenuConfirmationTitle', g['modalTitle'][0], '{confirmation_title}', z=103)
layout.text('MenuConfirmationBody', g['modalBody'][0], '{confirmation_body}', z=103)
for index, item in enumerate(g['modalActions']):
    node = layout.action('MenuConfirmation' + ('CancelButton' if index == 0 else 'ConfirmButton'), item,
                         'cancel-modal' if index == 0 else 'confirm-modal',
                         '{cancel_label}' if index == 0 else '{confirm_label}')
    node['z_index'] = 103
layout.root['notes'] += ' Modal is a reusable measured quit variant: relayout and expand for longer text, timer or third action.'
layout.finish()

settings = [{key: value for key, value in entry.items() if key not in ('value', 'options')}
            | ({'choices': entry['options']} if 'options' in entry else {}) for entry in CATALOG['settings']]
for item in settings:
    if item['id'] == 'resolution':
        item.pop('choices')
        item['choices_source'] = 'Enumerate supported monitor modes; examples in browser are not a device capability list.'
        item['disabled_when'] = 'window_mode == windowed_fullscreen'
    if item['id'] == 'terrain_anisotropy':
        item['paired_write'] = 'video.terrain_filtering = anisotropic, plus the selected terrain_anisotropy value'
    if item['id'] == 'bolster_monsters':
        item['apply_timing'] = 'Next area entry; deferred application is a new controller requirement.'
dump('contracts/settings.yml', {'status': 'Integration contract, not UiLayoutManager input',
                               'initial_values': 'Read GameSettings and KeyboardBindings; never copy browser review defaults.',
                               'transaction': 'One shared draft across all five tabs. Apply persists; Revert restores committed values.',
                               'display_changes': {'confirmation_seconds': 15, 'timeout_action': 'Restore previous display configuration'},
                               'defaults': 'Use engine default constructors/presets; reset only the current section after confirmation.',
                               'settings': settings})
dump('contracts/keyboard.yml', {'status': 'Integration contract, not UiLayoutManager input',
                               'registry': 'game/app/KeyboardBindings.cpp', 'bindings_per_action': 1,
                               'actions': [{k: v for k, v in b.items() if k != 'code'} for b in CATALOG['bindings']],
                               'fixed_shortcuts': CATALOG['fixedBindings'],
                               'reserved_capture': ['Escape', 'F9', 'F10', '1', '2', '3', '4', '5', 'Backquote'],
                               'capture': {'escape': 'cancel', 'clear': 'Unbind through an explicit Clear action',
                                           'conflict': 'Name both actions; offer swap or cancel',
                                           'mouse': 'Current capture supports keyboard/left mouse; additional buttons need native input work.'},
                               'list': 'Two columns, search and group filter, no two-page limit. Reflow after filtering.',
                               'excluded_unimplemented_registry_actions': ['yell', 'combat', 'pass']})
dump('contracts/theme.yml', {'status': 'Integration contract, not engine font descriptors or UiLayoutManager input',
                            'design': 'Carved Obsidian menus r03, approved 2026-09-28',
                            'canvas': {'browser_pixels': [1600, 900], 'logical_units': [number(1600), 480],
                                       'pixel_to_logical': FACTOR,
                                       'fit': 'min(screenWidth / 853.333333, screenHeight / 480); center; same transform for input.',
                                       'aspect': 'Keep content visible at 4:3 and ultrawide; extend the background beyond fitted canvas.'},
                            'fonts': {
                                'fondamento': {'file': 'engine/fonts/truetype/fondamento_regular.ttf', 'role': 'Actions, headings, wordmark',
                                               'proposed_layout_cell_height': 32,
                                               'requires': 'Standalone TrueType loading/metrics. Current FontAsset replacement requires legacy FNT metrics.'},
                                'arrus': {'file': 'engine/fonts/truetype/openyamm_arrus_faithful.ttf', 'role': 'Body, values, skills, save names',
                                          'existing_descriptor': 'arrus.yml', 'logical_height': 19, 'baseline': 14, 'browser_size_adjust': 1.2},
                                'lucida': {'file': 'engine/fonts/truetype/openyamm_lucida_faithful.ttf', 'role': 'Metadata, help, keys, form labels',
                                           'existing_descriptor': 'lucida.yml', 'logical_height': 17, 'baseline': 13, 'browser_size_adjust': 1.2}},
                            'live_text': 'All labels and the wordmark remain text. Preserve per-face advance widths; no bitmap-label fallback.',
                            'wordmark': {'gradient': ['#fff0c9', '#ceb483', '#8d754e', '#ebd9ad'], 'fallback_solid': '#e9d4a6'},
                            'text_states': {'normal': '#e8d1a4', 'primary': '#ffe4ac', 'hover': '#fff0c0',
                                            'disabled_opacity': 0.34, 'pressed_offset_browser_pixels': [0, 1]},
                            'focus': 'Gold 2px outline, offset 4px. Preserve keyboard navigation/focus separately from selected state.',
                            'button_drawing': 'Element rect is the hit/text content box. Expand image destination by recorded padding '
                                              'and retain corner/edge sizes with nine-slice; convert image pixels by pixel_to_logical.',
                            'panel_drawing': 'Panel elements already include image padding; do not expand twice. Reference-size exports '
                                             'can draw as one quad. Modal resizing uses source border slices, not stretched carved corners.',
                            'source_panel_slices': {'file': 'source/stone-panel.png', 'source_pixels_trbl': [72, 65, 75, 65],
                                                   'target_browser_pixels': 23},
                            'range_controls': {'track': '#0d1713', 'track_border': '#766747', 'fill': '#ac935c',
                                               'thumb': '#d8ba7b', 'instruction': 'Draw native range/scroll primitives at the measured rectangles.'},
                            'surfaces': SURFACES['surfaces']})
dump('contracts/screens.yml', {'status': 'Integration handoff; these contracts are not parsed by current UI code',
                              'layouts': LAYOUTS, 'actions': HOOKS, 'scroll_regions': SCROLLS,
                              'navigation': {'main': ['continue', 'new-game', 'load', 'settings', 'credits', 'quit'],
                                             'pause': ['resume', 'save', 'load', 'settings', 'new-game', 'main-menu', 'quit'],
                                             'settings_back': 'Return to entry origin; dirty draft prompts Apply / Discard / Stay.',
                                             'creation_cancel': 'Return to Main Menu, including when entered from Pause.',
                                             'creation_complete': 'Begin Adventure directly; no review step.',
                                             'escape': 'Close modal first; cancel key capture; otherwise use current screen Back/Resume semantics.'},
                              'saves': {'continue': 'Most recent valid save; Continue and Load disabled when none are loadable.',
                                        'load': 'All compatible saves; single select, double-click load; confirm if replacing an active session.',
                                        'save': 'New Save sentinel plus manual saves. Protect auto/quick slots and reserved names. Confirm overwrite.',
                                        'rows': 'Measured visible row pool is not storage capacity; recycle under viewport clipping.',
                                        'details': 'Actual save metadata, calendar, texture preview; missing preview uses matching continent art.'},
                              'party': {'authority': 'NewGameScreen plus merged class/race/skill/character tables; not source/data.js mock logic.',
                                        'slots': 'Engine party capacity; one occupied slot minimum, dynamic native portraits and doll layers.',
                                        'skills': 'Prominent fixed skills; optional choices in two columns without scrolling for reviewed classes.',
                                        'validation': 'Use native point costs, pool, class/race/voice availability, limits and readiness.',
                                        'footer': 'Roster summary follows current occupied slots; five slot anchors are supplied for the maximum state.'},
                              'confirmations': ['overwrite', 'load active session', 'new game from pause', 'return to main menu',
                                                'quit to desktop', 'dirty settings', 'restore defaults', 'key capture',
                                                'binding conflict', 'display keep/revert countdown'],
                              'credits_url': 'https://github.com/pjasicek/OpenYAMM'})

(OUT / 'source/copy_receipt.json').write_text(json.dumps(SOURCES, indent=2) + '\n')
dump('approval.yml', {'status': 'User-approved design, staged for future runtime integration', 'date': '2026-09-28',
                      'revision': 'r03', 'user_statement': 'Yes, I like all of this. please "stage" it or something. '
                      'you can sketch the ui ymls, stage the graphics etc. for usage.',
                      'default_background': 'Generated universe-dusk-v1; retained from the approved composition.',
                      'comparison_backgrounds': 'Preserved in the study gallery and provenance; no specific alternate selected for runtime.',
                      'source_hashes': SURFACES['sourceHashes'], 'runtime_activation': False})

# A file://-friendly graphic catalogue, with no libraries or network dependencies.
cards = []
for record in SURFACES['surfaces']:
    path = record['file']
    cards.append(f'<figure><a href="{path}"><img src="{path}" alt="{html.escape(record["key"])}"></a>'
                 f'<figcaption>{html.escape(record["key"])}<small>{record["imageSize"][0]} × '
                 f'{record["imageSize"][1]} · {record["kind"]}</small></figcaption></figure>')
(OUT / 'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8">
<title>OpenYAMM · Staged menu graphics</title><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{margin:32px;background:#111c19;color:#eadfc6;font:17px system-ui}h1{font-weight:500}
a{color:#d6bd83}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:20px}
figure{margin:0;padding:16px;background:#202b26;border:1px solid #665b43}img{display:block;object-fit:contain;
width:100%;height:180px;background:repeating-conic-gradient(#26332c 0% 25%,#334036 0% 50%) 0/20px 20px}
figcaption{overflow-wrap:anywhere;margin-top:14px}small{display:block;color:#bab6a3;margin-top:5px}p{max-width:950px}</style>
<h1>OpenYAMM · Staged menu graphics</h1><p>Approved Carved Obsidian menus, revision 03. These are blank surfaces;
labels use Fondamento, OpenYAMM Arrus and OpenYAMM Lucida at runtime.</p>
<p><a href="README.md">Integration handoff</a> · <a href="../index.html">Interactive design</a> ·
<a href="contracts/screens.yml">Screen and action contracts</a> · <a href="contracts/theme.yml">Drawing and font contracts</a></p>
<main>''' + '\n'.join(cards) + '</main></html>\n')
for file in (OUT / 'engine').rglob('*'):
    if file.is_file():
        file.chmod(0o644)
print(f'Prepared {len(LAYOUTS)} UI layout drafts, {len(HOOKS)} action hooks, {len(SCROLLS)} scroll regions and {len(SOURCES)} source copies.')
