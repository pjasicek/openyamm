#!/usr/bin/env python3
"""Render curated reference notes plus measured evidence into navigable case studies.

Edit reference_notes.json for interpretation, then rerun this script. Counts come from
inspect_references.py; this renderer never changes game assets or event scripts.
"""
import json
from pathlib import Path
import re

studyRoot = Path(__file__).resolve().parents[1]
repoRoot = studyRoot.parent
manifest = json.loads((studyRoot / 'reference_maps.json').read_text())
notes = json.loads((studyRoot / 'reference_notes.json').read_text())
referenceCount = sum(len(maps) for worlds in manifest.values() for maps in worlds.values())


def join(values):
    return ', '.join(str(v) for v in values) or 'none'


def sourceLink(path, label=None, line=None):
    suffix = f'#L{line}' if line else ''
    return f'[{label or path}](../../../{path}{suffix})'


index = ['# Reference case studies', '',
         'For regional roads read [transition calibration](../REGIONAL_TRANSITION_CALIBRATION.md): travel bounds, scenic continuation and native exit views.', '',
         f'{referenceCount} maps: at least five indoor and five outdoor from each of MM6, MM7 and MM8. Each study combines',
         'measured native geometry/scene/map-stat data, selected event entry points, a plan and a Blender isometric.',
         'The layout/lessons are curated interpretation; counts and palette data are reproducible measurements.', '',
         'The decoration revision adds native sprite inventories, terrain/placement measurements and annotated',
         'Blender captures. Start with [population and composition](../POPULATION_AND_COMPOSITION.md).', '',
         'For buildings use the [Ravenshore textured catalogue](../catalogues/mm8_ravenshore/README.md) and',
         '[visual calibration](../VISUAL_CALIBRATION.md). Ordinary outdoor work needs a quick static wiring check;',
         'the deeper runtime diagnostics below are conditional, not a per-service generation checklist.', '',
         'These are source studies, not recorded playthroughs. Read the [preview limits](../README.md#reproduce-and-extend-the-reference-inspection)',
         'and add runtime/state-specific views before using a reference as a final gameplay or lighting standard.', '',
         'For indoor work start with a lair, then a cave/temple, then a mechanism or multilevel example.',
         'For outdoor work choose by landform, roads, settlement density and hazards rather than map name alone.',
         'Read [Accepted outdoor calibration](../OUTDOOR_CALIBRATION.md) before planning a new settlement;',
         'it combines approved scale, variety, density, frontage, tile transitions, terrain and local decoration lessons.', '']

for kind, worlds in manifest.items():
    index.extend([f'## {kind.title()}', ''])
    for world, names in worlds.items():
        index.extend([f'### {world.upper()}', '',
                      f'[Plans](../evidence/{world}_{kind}_overview.png) · '
                      f'[Blender overviews](../evidence/{world}_{kind}_blender_overview.png)', '',
                      '| Map | Useful reference for |', '| --- | --- |'])
        for stem in names:
            key = f'{world}/{stem}'
            n = notes[key]
            j = json.loads((studyRoot / f'evidence/{key}.json').read_text())
            s = j['map_stats']
            relativeEvidence = f'../../evidence/{world}/{stem}'
            mapSource = next(v['path'] for v in j['sources'] if v['path'].endswith(('.blv', '.odm')))
            luaSource = f'assets_dev/worlds/{world}/events/maps/{stem}.lua'
            lua = (repoRoot / luaSource).read_text(encoding='latin-1')
            eventLines = {int(m[1]): lua.count('\n', 0, m.start()) + 1
                          for m in re.finditer(r'^Register(?:NoOp)?Event\((\d+),', lua, re.M)}
            bound = {e['id']: e for e in j['bound_events']}
            lines = [f"# {s['name']} — {world.upper()} `{j['map']}`", '',
                     f"**Study focus:** {n['theme']}", '',
                     '[Index](../README.md) · [Generation playbook](../../README.md) · '
                     f'[Measured JSON]({relativeEvidence}.json) · [Blender view metadata]({relativeEvidence}_blender.json)', '',
                     '## Layout and visual reading', '', n['layout'], '',
                     f'![Measured plan of {s["name"]}]({relativeEvidence}.png)', '',
                     f'![Blender inspection view of {s["name"]}]({relativeEvidence}_blender.png)', '',
                     'The plan shows source geometry/terrain and selected bound POIs. The Blender view uses neutral study',
                     'lighting, excludes indoor ceilings and omits actors/decorations and scripted state. Outdoor water/shore',
                     'transparency is not composited in Blender; magenta edges are a preview limitation. Neither image is a game screenshot.', '',
                     '## Measured structure', '', '| Field | Value |', '| --- | --- |',
                     f"| Native container version | {j['source_version']} (current imported assets, not original-world version) |"]
            if kind == 'indoor':
                lines.extend([
                    f"| Vertices / faces | {j['vertices']} / {j['faces']} |",
                    f"| Occupied sectors / portal faces | {j['occupied_sectors']} / {j['portal_faces']} |",
                    f"| BSP nodes / automap outlines | {j['bsp_nodes']} / {j['outlines']} |",
                    f"| Native door state records | {len(j['doors'])} |",
                    f"| Explicit lights / radius range | {j['lights']} / {join(j['light_radius_range'])} |",
                    f"| Occupied-sector ambient values | {join(sorted({v['ambient'] for v in j['sectors'] if v['faces']}))} |",
                    f"| XYZ bounds, game units | {j['bounds'][0]} to {j['bounds'][1]} |"])
            else:
                t = j['terrain']
                lines.extend([
                    f"| BModels / BModel faces | {j['bmodels']} / {j['faces']} |",
                    '| Native terrain | 128 × 128 samples; 512-unit spacing; 32-unit height steps |',
                    f"| Terrain height range, game units | {join(t['height_range'])} |",
                    f"| Master tile / four lookup banks | {t['master_tile']} / {join(t['lookup'])} |",
                    f"| Distinct raw tile IDs / raw road-bank cells | {t['unique_tiles']} / {t['road_bank_cells']} |",
                    f"| Water-flag / burn-flag cells (may overlap) | {t['water_flag_cells']} / {t['burn_flag_cells']} |"])
            lines.extend([
                f"| Native entities / spawn records | {j['entities']} / {j['spawn_records']} |",
                f"| Initial scene actors / chest records | {j['scene_counts'].get('actors', 0)} / {j['scene_counts'].get('chests', 0)} |",
                f"| Directly bound chest slots | {join(j['bound_chest_slots'])} ({len(j['bound_chest_slots'])} distinct) |",
                f"| Directly bound / declared map events | {len(bound)} / {j['declared_event_count']} |",
                f"| Selected face flags | {'; '.join(f'{k}: {v}' for k,v in j['face_flags'].items())} |", '',
                'Face flags above are base geometry counts; scene overrides and Lua can change effective state. Spawn records,',
                'fixed actors and scripted summons are separate. Chest records include unused slots. Bound-event counts',
                'include face/decor bindings; they do not constitute a complete lifecycle/indirect-call analysis.', '',
                '## Materials and population', '',
                'Most frequent mesh texture keys (face counts, not surface area): ' +
                '; '.join(f'`{k}` ({v})' for k,v in list(j['textures'].items())[:8]) + '.', ''])
            if kind == 'outdoor':
                common = sorted(j['terrain']['tile_counts'].items(), key=lambda kv: -kv[1])[:6]
                lines.extend(['Common native tile assignments: ' + '; '.join(
                    f"`{tile}` → `{j['terrain']['palette'][tile]['texture']}` ({count} cells)"
                    for tile, count in common) + '. Full resolution/flags are in the JSON.', ''])
            lines.extend([
                f"Map-stat row: {sourceLink('assets_dev/engine/data_tables/map_stats.txt', str(s['id']) + ' / ' + s['name'], s['line'])}.", '',
                f"Treasure **{s['treasure']}**, Perception difficulty **{s['perception']}**, disarm **{s['disarm']}**, "
                f"trap d20 count **{s['trap_d20']}**, refill **{s['refill_days']} days**, encounter chance **{s['encounter_chance']}**.", '',
                '| Encounter slot | Family | Difficulty selector | Count range | Weight |', '| --- | --- | --- | --- | --- |'])
            for i, e in enumerate(s['encounters'], 1):
                lines.append(f"| {i} | {e['name']} | {e['difficulty']} | {e['count']} | {e['weight']} |")
            if world == 'mm6':
                lines.extend(['', 'The current merged MM6 treasure value is not evidence of original-game balance; choose new-map loot',
                              'deliberately and check chest-template remapping and active difficulty overrides.'])
            lines.extend(['', '## Event behavior to inspect', '', n['behavior'], '',
                          '| Selected event | Direct binding count | Calls / targets from scan |', '| --- | --- | --- |'])
            selected = [v for v in n['events'] if v in eventLines]
            if not selected:
                selected = list(bound)[:3]
            for eventId in selected:
                e = bound.get(eventId)
                label = sourceLink(luaSource, str(eventId), eventLines.get(eventId))
                if e:
                    info = join(e['calls'])
                    for field in ('doors', 'chests', 'houses', 'destinations'):
                        if e.get(field):
                            info += f"; {field}: {join(e[field])}"
                    lines.append(f"| {label} | {e['binding_count']} | {info} |")
                else:
                    lines.append(f'| {label} | Not directly bound in scan | Inspect lifecycle/indirect callers and conditions |')
            lines.extend(['', 'Read full control flow and metadata at these entry points. Helper calls and overlays may add behavior',
                          'that the direct `evt.*` scan does not list. Declared handlers can be unused templates.', ''])
            decorationPath = studyRoot / f'evidence/{key}_decorations.json'
            if decorationPath.exists():
                decoration = json.loads(decorationPath.read_text())
                counts = decoration['counts']
                lines.extend(['## Decoration, architecture and terrain study', '', n['population_study'], '',
                              'This reading is an interpretation of the measured arrangement, not a claim about the original authors’ documented intent.', '',
                              f'[Native placement and palette records]({relativeEvidence}_decorations.json) · '
                              f'[Capture poses and highlighted IDs]({relativeEvidence}_decor_views.json) · '
                              '[Generation rules](../../POPULATION_AND_COMPOSITION.md)', '',
                              f'![Decoration placement plan]({relativeEvidence}_decorations.png)', '',
                              f"Native entity records: **{counts['native']}**; initially drawable sprite records: **{counts['visible']}**; "
                              f"drawable decorations with descriptor light radius: **{counts['light_emitters']}**.", '',
                              'These exclude no-draw/start markers and initially hidden sprites. Emitter-only fire/smoke,',
                              'modeled furnishings, face textures, explicit map lights and later scripted changes are separate.', '',
                              '| Group | Drawable records |', '| --- | --- |'])
                for category, number in counts['categories'].items():
                    lines.append(f'| {category} | {number} |')
                if not counts['categories']:
                    lines.append('| No initially drawable sprites | 0 |')
                lines.extend(['', '| Asset | Hint | Count | Collision radius / height | Descriptor light radius |',
                              '| --- | --- | --- | --- | --- |'])
                byName = {e['name']: e for e in decoration['records']}
                for asset, number in list(counts['palette'].items())[:12]:
                    e = byName[asset]
                    lines.append(f"| `{asset}` | {e['hint']} | {number} | {e['radius']} / {e['height']} | {e['light_radius']} |")
                if kind == 'outdoor':
                    lines.extend(['', '| Group | Within 1,024 of BModel XY bounds | Grade ≤ 0.125 | Grade > 0.5 |',
                                  '| --- | --- | --- | --- |'])
                    for category, measurement in decoration['placement'].items():
                        if measurement['count']:
                            lines.append(f"| {category} | {measurement['within_1024_bmodel']} / {measurement['count']} | "
                                         f"{measurement['flat_grade_le_0125']} | {measurement['steep_grade_gt_05']} |")
                    lines.extend(['', 'Grade is rise/run on the sampled native terrain triangle. BModel distance is a geometric',
                                  'proximity measure, **not** a city boundary: it includes bridges, rocks and other models.',
                                  'Use these measurements with the actual view and context; they are not universal scatter quotas.', ''])
                viewsPath = studyRoot / f'evidence/{key}_decor_views.json'
                if viewsPath.exists():
                    for view in json.loads(viewsPath.read_text())['views']:
                        lines.extend(['', f"![{view['view']['name']} — annotated native decoration study](../../../{view['image']})", ''])
                        labels = [f"#{e['index']} `{e['name']}` at {e['position']}" for e in view['highlighted']]
                        lines.append('Highlighted source anchors: ' + ('; '.join(labels) if labels else 'none in this view') + '.')
                lines.extend(['', 'The annotated captures include native first-frame sprite art at source scale and coordinates, with',
                              'decoded transparency/palettes and neutral study lighting. Indoor sections label their cut height;',
                              'geometry above that plane is omitted. They are Blender captures, not game screenshots or proof',
                              'of light reach, post-load state, collision, actor behavior or performance. Review complete-ceiling',
                              'player views and active native state before final acceptance.', ''])
            if key == 'mm8/out02':
                lines.extend(['## Building, facade and scale calibration', '',
                    'Use the [complete native building catalogue](../../catalogues/mm8_ravenshore/README.md):',
                    'all 121 BModels inventoried, active versus label-only faces, house/NPC/service bindings,',
                    '84 textured part views and 10 complete/context assemblies. The [calibration](../../VISUAL_CALIBRATION.md)',
                    'matches driver screenshots to measured door/window/roof kits and explains the generated town’s scale error.',
                    'Use [settlement spacing calibration](../../SETTLEMENT_DENSITY.md) for market/lane density,',
                    'opposing fronts and same-scale native plans; count multipart blocks once.',
                    'The [house variety measurement](../../HOUSE_VARIETY.md) counts 44 ordinary house/storage instances',
                    'across 13 forms, separately from the unique service/landmark assemblies. Match repetition as well as variety.',
                    'Approve representative textured prototypes before duplicating them. Keep wells/fountains outside roads.', ''])
            lines.extend(['## Apply to a new map', '', n['lessons'], ''])
            if kind == 'outdoor':
                lines.extend(['## Default visual and wiring review', '',
                    'Inspect the relevant plan and street-height/oblique views for scale, facade coherence, terrain contact,',
                    'road clearance and placement. Apply [Accepted outdoor calibration](../../OUTDOOR_CALIBRATION.md):',
                    'choose the reference district/biome, check actual-door frontage and native tile joins, and inspect local',
                    'garden/prop groups as well as global totals. Check native output and face → event → target IDs once. Apply the',
                    '[visual review checklist](../../REVIEW_CHECKLIST.md); no per-service scenario runner is required.', '',
                    '## Optional deeper runtime diagnostics', '',
                    'Use the following only for new behavior, an observed defect or an explicit driver request:', '', n['checks'], ''])
            else:
                lines.extend(['## Follow-up review', '', n['checks'], '',
                    'Scope runtime checks to new mechanisms or unresolved behavior using the [review policy](../../REVIEW_CHECKLIST.md).', ''])
            lines.extend([
                          'These are review suggestions, not gameplay tests executed by this survey.', '',
                          '## Sources and provenance', '',
                          'Inspected local files; SHA-256 values are recorded in the measured JSON. GrayFace files are behavior',
                          'references only; do not copy their code. Generated EVT/STR Lua must not be edited for new-map logic.', ''])
            for source in j['sources']:
                lines.append('- ' + sourceLink(source['path']))
            lines.extend(['', 'Regenerate evidence with `inspect_references.py`, review/update `reference_notes.json` if behavior changes,',
                          'then run `build_case_studies.py`. Do not treat generated counts as a substitute for interpretation.', ''])
            folder = studyRoot / 'case_studies' / kind
            folder.mkdir(parents=True, exist_ok=True)
            (folder / f'{world}_{stem}.md').write_text('\n'.join(lines))
            index.append(f"| [{s['name']} ({stem})]({kind}/{world}_{stem}.md) | {n['theme']} |")
        index.append('')

index.extend(['## Focused follow-up calibration', '',
    '- [Garrote Gorge settlement density and enclosed courtyard](outdoor/mm8_out05_density.md): native assemblies,',
    '  open village versus compound spacing and actual stone paths inside the walls.',
    '- [Cross-map settlement spacing](../SETTLEMENT_DENSITY.md): reference districts and historical revisions.',
    '- [Accepted outdoor calibration](../OUTDOOR_CALIBRATION.md): the starting workflow for future maps.',
    '- [Ravage Roaming wilderness contrast](outdoor/mm8_out08_wilderness.md): a focused open-grassland follow-up.',
    '- [Landscape detail calibration](../LANDSCAPE_DETAIL_CALIBRATION.md): full bridge contact, ground detail, heatmaps and native landmarks.',
    '- [Wilderness calibration](../WILDERNESS_CALIBRATION.md): Ravenshore/Ravage Roaming/Shadowspire encounters, scenery, ponds, bridges and cave mouths.', ''])
(studyRoot / 'case_studies/README.md').write_text('\n'.join(index))
print(f'Wrote {referenceCount} case studies and index from measured evidence and curated notes.')
