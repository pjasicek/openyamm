"""Prepare fixed-layout reference sheets and prompts. Never submits generation calls."""
import collections
import csv
import hashlib
import json
import math
import re
from pathlib import Path

from PIL import Image, ImageDraw

from finalize_classification import HERE, ROOT, digest, read, write


CHECKS = [
    'Every cell has the correct identity, state, colors, symbols and full silhouette, with no invented features.',
    'No clipped thin features, shifted anchors, changed margins, matte spill or contamination from adjacent cells.',
    'Each export is exactly twice its own native width and height; registration preserves the full native canvas.',
    'Restored detail survives at the final export size; a simple enlargement is not accepted restoration.',
    'Validate each native compositing profile and preserve transparent/opaque regions, soft glows and tiny strokes.',
    'Keep native animation timing and state aliases. Review related frames/states together at actual display scale.',
]

DIRECTIONS = {
    'inventory_items': 'Restore illustrated inventory objects. Keep each weapon, potion or item recognizable; '
                       'preserve narrow blades, inscriptions, highlights and native material colors.',
    'player_portrait_frames': 'Restore one player identity across the original expressions. Preserve face geometry, '
                              'age, skin, hair, eye direction, mouth pose and framing. Never average expressions.',
    'npc_portrait_family': 'Restore distinct NPC portraits; preserve every individual identity and original framing.',
    'fitted_equipment_variants': 'Restore one equipped item family across compatible body/hand poses. Preserve native '
                                 'registration and holes/occlusion. Do not straighten, symmetrize or fit to bounds.',
    'paperdoll_parts': 'Restore registered body/hand pieces for one character. Preserve anatomy, pose, cut edges and '
                      'the native attachment coordinates. Never recenter a limb.',
    'ui_animation_family': 'Restore consecutive frames of one native animation with stable materials and silhouette. '
                           'Preserve phase, movement and fading; use the accepted seed when supplied.',
    'spell_icon_pair': 'Restore normal/hover states in matched pairs using the accepted school-page crops supplied '
                       'as dependencies. Use identical background pixels outside the icon/state treatment. '
                       'Preserve existing pressed/hover aliases, native positions and baked-in page artwork.',
    'spellbook_page': 'Restore the complete native spellbook page, preserving its parchment, composition and baked '
                      'artwork. Do not add spell glyphs absent from the source. Dependent icons will use this page.',
    'ui_background': 'Restore this complete background with faithful composition, ornament and subdued materials.',
    'map_presentation': 'Restore this authored map image. Preserve every room, path, coastline, label and registration '
                        'exactly; do not invent geography or change the world-coordinate correspondence.',
    'ui_frame_or_panel': 'Restore the registered UI panel/border. Preserve join profiles, thickness, corner geometry '
                         'and baked lettering. Check adjoining pieces against each other.',
    'ui_state_set': 'Restore related UI control states. Preserve exact symbols/lettering and the native state contrast '
                    'without shifts, new shadows or changing the control geometry.',
    'legacy_ui_art': 'Faithfully restore these related historical UI images. Preserve all source motifs and states; '
                      'do not redesign them or invent missing frames. Retain the native key/alpha semantics.',
    'registered_arcomage_atlas': 'Restore registered Arcomage artwork regions. Preserve card identities, lettering, '
                                 'symbols, frame boundaries and source coordinates. Reassembly must retain all slots.',
}


def natural(value):
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', value)]


def family(target):
    name, treatment = target['runtime_name'], target['treatment']
    if treatment == 'spell_icon_pair':
        return target['page_dependencies'][0]['page_target']
    if treatment == 'player_portrait_frames':
        return target['frame']['family']
    if treatment == 'paperdoll_parts':
        return re.match(r'(?:[678])?pc\d+', name).group() if re.match(r'(?:[678])?pc\d+', name) else name
    if treatment == 'fitted_equipment_variants':
        return re.sub(r'v\d+[ab]?$', '', name)
    if treatment == 'ui_animation_family':
        frame = target.get('frame') or {}
        if frame.get('family'):
            return frame['family']
        if frame.get('families'):
            return frame['families'][0].get('animation', re.sub(r'\d+$', '', name))
    if treatment in {'spellbook_page', 'ui_background', 'map_presentation'}:
        return name
    if treatment == 'npc_portrait_family':
        return re.sub(r'\d+', '', name)
    if treatment == 'inventory_items':
        # Group actual item categories, not arbitrary consecutive numeric item IDs.
        tables = [u for u in target['usages'] if u['kind'] == 'item_table']
        if tables:
            row = (ROOT / tables[0]['source']).read_text(errors='replace').splitlines()[tables[0]['line'] - 1]
            fields = row.split('\t')
            return '-'.join(fields[4:6]).lower()
    if treatment == 'ui_frame_or_panel' and re.fullmatch(r'ib-(?:foot|l|t|r)-[abc]', name):
        return 'ib-frame-' + name[-1]
    if treatment == 'ui_state_set':
        elements = sorted({u['element'] for u in target['usages'] if u['kind'] == 'yaml'})
        if elements:
            return elements[0]
        return re.sub(r'(?:_default|_pressed|_active|_disabled|_dn|_ht|_up|[duh])$', '', name)
    return re.sub(r'\d+', '#', name)


def parts(target):
    width, height = target['native_size']
    rectangles = []
    deterministic = set()
    if target['treatment'] == 'registered_arcomage_atlas':
        # The first header blocks contain glyph libraries/counter digits; these are font work,
        # distinct from the card back, tower art and illustrated controls.
        rectangles.extend([[0, 0, 192, 220], [192, 0, 96, 128], [288, 0, 96, 128],
                           [192, 128, 192, 92], [384, 0, 68, 188], [384, 188, 68, 32],
                           [452, 0, 508, 220]])
        deterministic = {0, 2, 3, 5}
        for y in range(220, height, 128):
            for x in range(0, width, 96):
                rectangles.append([x, y, min(96, width - x), min(128, height - y)])
    else:
        rectangles = [[0, 0, width, height]]
    result = [dict(id=target['id'] + (f'--region-{i:03d}' if len(rectangles) > 1 else ''),
                 target=target['id'], source_path=target['source_path'], source_sha256=target['source_sha256'],
                 source_rect=rect, export_region=[v * 2 for v in rect],
                 context_native=16 if len(rectangles) > 1 else 0,
                 method='deterministic_font_regions' if i in deterministic else 'imagegen_sheet',
                 treatment=target['treatment'], cleanup=target['compositing']['cleanup'])
            for i, rect in enumerate(rectangles)]
    if target['treatment'] == 'registered_arcomage_atlas':
        with Image.open(ROOT / target['source_path']) as image:
            for member in result:
                x, y, w, h = member['source_rect']
                if y < 220:
                    continue
                slot = (y - 220) // 128 * 10 + x // 96
                member['card_slot'] = slot
                member['card_definitions'] = target['atlas']['card_slots'].get(str(slot), [])
                colors = image.convert('RGBA').crop((x, y, x + w, y + h)).getcolors(1)
                if colors:
                    assert not member['card_definitions'], f'Active card has no drawing: slot {slot}'
                    member['method'] = 'deterministic_uniform_regions'
                    member['source_color_rgba'] = list(colors[0][1])
    return result


def layout(members):
    max_width = max(m['source_rect'][2] * 2 for m in members)
    max_height = max(m['source_rect'][3] * 2 for m in members)
    preferred_columns = 2 if members[0]['treatment'] == 'spell_icon_pair' else 3
    columns = min(len(members), preferred_columns, max(1, 2048 // (max_width + 32)))
    cell_width, cell_height = max_width + 32, max_height + 56
    width, height = cell_width * columns, 48 + cell_height * math.ceil(len(members) / columns)
    for i, member in enumerate(members):
        w, h = member['source_rect'][2] * 2, member['source_rect'][3] * 2
        x, y = (i % columns) * cell_width + 16, (i // columns) * cell_height + 80
        member['reference_cell_rect'] = [x, y, w, h]
    return [width, height]


def sheet(job):
    image = Image.new('RGB', job['reference_size'], (42, 43, 45))
    draw = ImageDraw.Draw(image)
    draw.text((16, 14), job['id'] + ' | native references at 2x nearest; not restored output', fill='white')
    for index, member in enumerate(job['members']):
        x, y, width, height = member['reference_cell_rect']
        sx, sy, sw, sh = member['source_rect']
        with Image.open(ROOT / member['source_path']) as source:
            crop = source.convert('RGBA').crop((sx, sy, sx + sw, sy + sh))
            image.paste(crop.resize((width, height), Image.Resampling.NEAREST), (x, y))
        draw.text((x, y - 20), f'{index + 1}: {Path(member["source_path"]).stem}', fill='white')
    return image


def main():
    manifest = read('expected_targets.json')
    manifest_sha = digest(HERE / 'expected_targets.json')
    targets = {t['id']: t for t in manifest['targets']}
    state_parents = {t['id']: t['id'] for t in targets.values() if t['treatment'] == 'ui_state_set'}
    state_elements = collections.defaultdict(list)
    def state_root(key):
        while state_parents[key] != key:
            key = state_parents[key]
        return key
    for target_id in state_parents:
        target = targets[target_id]
        for usage in target['usages']:
            if usage['kind'] == 'yaml' and usage['state'] in {'default', 'highlighted', 'pressed', 'selected'}:
                state_elements[(target['namespace'], usage['source'], usage['element'])].append(target_id)
    for members in state_elements.values():
        roots = sorted({state_root(member) for member in members})
        for root in roots[1:]:
            state_parents[root] = roots[0]
    state_linked = {member for members in state_elements.values() for member in members}
    buckets = collections.defaultdict(list)
    for target in targets.values():
        key = (target['namespace'], target['treatment'], family(target),
               tuple(target['compositing']['profiles']), target['compositing']['cleanup'])
        if target['treatment'] == 'spell_icon_pair':
            # A native state may contain more opaque page pixels than its sibling. Keep the pair together;
            # each member retains its own cleanup rule and final canvas.
            key = (*key[:3], ('paired_page_states',), 'per_state')
        if target['id'] in state_linked:
            key = (*key[:2], state_root(target['id']), ('related_control_states',), 'per_state')
        # Related states can differ in canvas size; do not split a pair just because its native sizes differ.
        for member in parts(target):
            buckets[(*key, member['method'])].append(member)
    jobs = []
    identity_seeds = {}
    for key, members in sorted(buckets.items()):
        members.sort(key=lambda m: natural(m['id']))
        treatment = key[1]
        limit = 8 if treatment == 'spell_icon_pair' else 6
        if treatment in {'inventory_items', 'npc_portrait_family', 'ui_state_set'}:
            # Small compatible families use the reviewed 3x3 policy. Never regenerate live frozen jobs
            # just to change packing; queue.batch_payload supplies inventory execution batches in place.
            limit = 9 if all(max(m['export_region'][2:]) <= 192 for m in members) else 4
        if treatment in {'ui_background', 'map_presentation', 'spellbook_page', 'ui_frame_or_panel'}:
            limit = 1
        if treatment in {'paperdoll_parts', 'fitted_equipment_variants'}:
            limit = 4
        if treatment == 'spell_icon_pair':
            pairs = collections.defaultdict(list)
            for member in members:
                pairs[targets[member['target']]['page_dependencies'][0]['element']].append(member)
            members = [m for _, pair in sorted(pairs.items()) for m in sorted(pair, key=lambda m: m['id'])]
            assert all(len(pair) == 2 for pair in pairs.values()), 'Split or incomplete spell pair'
        chunks = []
        for member in members:
            atlas_header = treatment == 'registered_arcomage_atlas' and member['source_rect'][1] == 0
            previous_header = (chunks and treatment == 'registered_arcomage_atlas'
                               and chunks[-1][0]['source_rect'][1] == 0)
            if not chunks or len(chunks[-1]) >= limit or atlas_header or previous_header:
                chunks.append([])
            candidate = chunks[-1] + [member]
            if chunks[-1] and max(layout(candidate)) > 2304:
                chunks.append([])
            chunks[-1].append(member)
        seed = identity_seeds.get(key[:3]) if key[-1] == 'imagegen_sheet' else None
        for chunk in chunks:
            job_id = treatment + '-' + hashlib.sha256('|'.join(m['id'] for m in chunk).encode()).hexdigest()[:12]
            reference_size = layout(chunk)
            dependencies = []
            if seed and treatment in {'player_portrait_frames', 'ui_animation_family', 'paperdoll_parts',
                                       'fitted_equipment_variants', 'registered_arcomage_atlas',
                                       'ui_state_set', 'ui_frame_or_panel'}:
                dependencies.append(dict(kind='accepted_seed_job', job=seed))
            for member in chunk:
                for recipe in targets[member['target']].get('page_dependencies', []):
                    entry = dict(kind='accepted_page_crop', target=recipe['page_target'], recipe=recipe)
                    if entry not in dependencies:
                        dependencies.append(entry)
            job = dict(id=job_id, treatment=treatment, family=list(key[:3]), kind=key[-1],
                       members=chunk, dependencies=dependencies, reference_size=reference_size,
                       reference_path=f'references/sheets/{job_id}.png', review_checks=CHECKS,
                       initial_state='pending', source_manifest_sha256=manifest_sha)
            lines = [
                'Faithful x2 restoration of existing Might and Magic UI artwork. Preserve the existing design; '
                'no redesign, photorealistic restyling, new symbols, objects, lettering or poses.',
                DIRECTIONS[treatment],
                f'Produce one registered sheet matching the supplied {reference_size[0]}x{reference_size[1]} '
                'reference composition. Keep every labeled cell in its recorded location and all gutters empty. '
                'Labels are reference metadata; omit lettering in the gutters from the art output.',
                'The source references are native pixels enlarged for legibility, not restored artwork. Add clear '
                'faithful detail at the final x2 size. Preserve the full native canvas and transparent margins.',
                'Keep the native matte/key regions distinguishable for cleanup. Preserve real colored details near '
                'the matte; do not paint matte-colored halos. Preserve translucent effects without opaque erosion.',
            ]
            for i, member in enumerate(chunk):
                target = targets[member['target']]
                lines.append(f'Cell {i + 1}: {member["id"]}; source {member["source_path"]}; '
                    f'native region xywh={member["source_rect"]}; sheet xywh={member["reference_cell_rect"]}; '
                    f'full final canvas={target["x2_size"]}; cleanup={member["cleanup"]}.')
            if any(m['context_native'] for m in chunk):
                lines.append('These are atlas/large-image regions. Consult the full original and the recorded '
                             '16-native-pixel surrounding context; lock shared boundaries before reconstruction.')
            if dependencies:
                lines.append('Accepted dependency images supplied at execution are authoritative for identity, '
                             'phase and page pixels. Do not proceed without them or use an unaccepted draft.')
            job['prompt'] = '\n\n'.join(lines)
            if job['kind'] == 'deterministic_font_regions':
                job['prompt'] = ('Deterministic font/counter-region work; do not call imagegen. Follow '
                    'tools/font_upscale/README.md. Preserve all native glyph positions, metrics, key colors and '
                    'source rectangles while reconstructing these atlas regions at exactly x2. These regions '
                    'are not an AI illustration job.\n\n' + '\n'.join(lines[5:]))
            elif job['kind'] == 'deterministic_uniform_regions':
                job['prompt'] = ('Deterministic unused atlas regions; do not call imagegen. Reconstruct each exact '
                    'x2 region using its recorded constant source_color_rgba. These empty regions are required '
                    'for complete atlas coverage but need no invented artwork.\n\n' + json.dumps(chunk, sort_keys=True))
            jobs.append(job)
            seed = seed or job_id
            if job['kind'] == 'imagegen_sheet':
                identity_seeds[key[:3]] = seed
    # One accepted pilot per treatment gates production; seed/page edges are added separately.
    pilots = {}
    for job in jobs:
        treatment = job['treatment']
        if job['kind'] != 'imagegen_sheet':
            job['pilot'] = False
        elif treatment not in pilots:
            pilots[treatment] = job['id']
            job['pilot'] = True
        else:
            job['pilot'] = False
            job['dependencies'].append(dict(kind='accepted_treatment_pilot', job=pilots[treatment]))
    output = HERE / 'references/sheets'
    output.mkdir(parents=True, exist_ok=True)
    previous = {j['id']: j for j in read('jobs.json')['jobs']} if (HERE / 'jobs.json').exists() else {}
    def reference_inputs(job):
        return [job['reference_size'], [(m['source_path'], m['source_sha256'], m['source_rect'],
                                         m['reference_cell_rect']) for m in job['members']]]
    for index, job in enumerate(jobs):
        path = HERE / job['reference_path']
        old = previous.get(job['id'])
        if not (old and path.is_file() and reference_inputs(old) == reference_inputs(job)
                and digest(path) == old['reference_sha256']):
            sheet(job).save(path)
        job['reference_sha256'] = digest(path)
        if index % 250 == 0:
            print(f'Prepared {index}/{len(jobs)} fixed reference sheets', flush=True)
    write('jobs.json', dict(schema_version=1, preparation_only=True,
        source_manifest_sha256=manifest_sha, jobs=jobs, pilots=pilots,
        summary=dict(jobs=len(jobs), cells=sum(len(j['members']) for j in jobs), targets=len(targets),
                     generation_started=False, accepted=0)))
    print(json.dumps(read('jobs.json')['summary'], indent=2))


if __name__ == '__main__':
    main()
