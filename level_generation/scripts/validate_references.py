#!/usr/bin/env python3
"""Validate reference coverage, provenance, image outputs and local Markdown links.

This validates the study artifacts, not native exporter correctness or gameplay.
"""
import hashlib
import json
from pathlib import Path
import re
import struct

studyRoot = Path(__file__).resolve().parents[1]
repoRoot = studyRoot.parent
manifest = json.loads((studyRoot / 'reference_maps.json').read_text())
notes = json.loads((studyRoot / 'reference_notes.json').read_text())
failures = []
expectedKeys = set()
count = 0
decorationViewCount = 0
decodedFrames = set()


def check(condition, message):
    if not condition:
        failures.append(message)


def checkPng(path):
    if not path.exists():
        failures.append(f'Missing image: {path}')
        return
    header = path.read_bytes()[:24]
    check(header[:8] == b'\x89PNG\r\n\x1a\n' and len(header) == 24, f'Invalid PNG header: {path}')
    if len(header) == 24:
        check(min(struct.unpack('>II', header[16:24])) > 0, f'Empty image: {path}')


for kind, worlds in manifest.items():
    check(set(worlds) == {'mm6', 'mm7', 'mm8'}, f'Incomplete world coverage: {kind}')
    for world, maps in worlds.items():
        check(len(maps) >= 5 and len(set(maps)) == len(maps), f'Need five distinct maps: {kind}/{world}')
        for stem in maps:
            count += 1
            key = f'{world}/{stem}'
            expectedKeys.add(key)
            path = studyRoot / f'evidence/{key}.json'
            if not path.exists():
                failures.append(f'Missing evidence: {path}')
                continue
            j = json.loads(path.read_text())
            check(j['kind'] == kind and j['world'] == world, f'Wrong evidence identity: {key}')
            check(key in notes, f'Missing curated notes: {key}')
            for source in j['sources']:
                sourcePath = repoRoot / source['path']
                check(sourcePath.exists(), f'Missing source: {sourcePath}')
                if sourcePath.exists():
                    actual = hashlib.sha256(sourcePath.read_bytes()).hexdigest()
                    check(actual == source['sha256'], f'Stale evidence hash: {key}: {sourcePath}')
            lua = repoRoot / f'assets_dev/worlds/{world}/events/maps/{stem}.lua'
            events = {int(m[1]) for m in re.finditer(r'^Register(?:NoOp)?Event\((\d+),',
                                                    lua.read_text(encoding='latin-1'), re.M)}
            check(set(notes.get(key, {}).get('events', [])) <= events, f'Unknown selected event: {key}')
            check((studyRoot / f'case_studies/{kind}/{world}_{stem}.md').exists(), f'Missing study: {key}')
            for suffix in ('', '_blender'):
                checkPng(studyRoot / f'evidence/{key}{suffix}.png')
            viewPath = studyRoot / f'evidence/{key}_blender.json'
            check(viewPath.exists(), f'Missing Blender metadata: {key}')
            if viewPath.exists():
                view = json.loads(viewPath.read_text())
                check(not view['missing_textures'], f'Missing Blender textures: {key}: {view["missing_textures"]}')
            decorationPath = studyRoot / f'evidence/{key}_decorations.json'
            check(decorationPath.exists(), f'Missing decoration inspection: {key}')
            if decorationPath.exists():
                decoration = json.loads(decorationPath.read_text())
                records = decoration['records']
                check(decoration['counts']['native'] == j['entities'] == len(records),
                      f'Decoration native count mismatch: {key}')
                check(decoration['counts']['visible'] == sum(e['visible'] for e in records),
                      f'Decoration drawable count mismatch: {key}')
                check(not decoration['missing_sprites'], f'Missing decoration art: {key}')
                check(bool(notes.get(key, {}).get('population_study')), f'Missing population interpretation: {key}')
                for source in decoration['sources']:
                    sourcePath = repoRoot / source['path']
                    check(sourcePath.exists() and hashlib.sha256(sourcePath.read_bytes()).hexdigest()==source['sha256'],
                          f'Stale decoration source: {key}: {sourcePath}')
                for e in records:
                    if e.get('preview'):
                        decodedFrames.add(repoRoot / e['preview']['decoded_path'])
                        check((repoRoot/e['preview']['path']).exists(), f'Missing native sprite: {key}: {e["name"]}')
                checkPng(studyRoot / f'evidence/{key}_decorations.png')
                capturesPath = studyRoot / f'evidence/{key}_decor_views.json'
                check(capturesPath.exists(), f'Missing decoration captures: {key}')
                if capturesPath.exists():
                    captures = json.loads(capturesPath.read_text())
                    check(bool(captures['views']), f'No decoration capture views: {key}')
                    for capture in captures['views']:
                        decorationViewCount += 1
                        checkPng(repoRoot / capture['image'])
                        for label in capture['highlighted']:
                            matches = [e for e in records if e['index']==label['index']]
                            check(len(matches)==1 and matches[0]['name']==label['name']
                                  and matches[0]['position']==label['position'],
                                  f'Incorrect decoration highlight: {key}: {label}')
            if kind == 'outdoor':
                t = j['terrain']
                check(sum(t['tile_counts'].values()) == 16384, f'Wrong native tile count: {key}')
                check(not t['missing_preview_textures'], f'Missing tile preview textures: {key}')
                check(set(t['tile_counts']) <= set(t['palette']), f'Unresolved terrain IDs: {key}')
            else:
                check(j['sectors'][0]['faces'] == 0, f'Reference sector-0 convention changed: {key}')
        for suffix in ('', '_blender'):
            checkPng(studyRoot / f'evidence/{world}_{kind}{suffix}_overview.png')

check(set(notes) == expectedKeys, 'Curated notes do not match reference inventory')
for path in decodedFrames:
    checkPng(path)
for path in studyRoot.rglob('*.md'):
    for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
        if target.startswith(('https://', 'http://', '#')):
            continue
        local = target.split('#', 1)[0]
        check((path.parent / local).exists(), f'Broken local link in {path.relative_to(studyRoot)}: {target}')

if failures:
    raise SystemExit('\n'.join(failures))
print(f'PASS: {count} references/case studies, {count*2} base map images, 12 overview sheets, '
      f'{count} decoration inventories/plans, {decorationViewCount} annotated captures, '
      f'{len(decodedFrames)} decoded native frames, source hashes and local links.')
print('This does not validate native generation, runtime gameplay, or reference preview lighting.')
