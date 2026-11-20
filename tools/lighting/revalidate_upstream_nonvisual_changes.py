"""Revalidate retained light pages after a narrowly checked, nonvisual upstream data migration.

This explicit migration accepts only MM7 initial actor hostility changes and new
MM9-only liquid definitions. Geometry, lights, materials for MM6-MM8 and existing
bake pages must remain unchanged. Run from the repository root.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bake_geometry import fnv


def old_bytes(revision, path):
    return subprocess.check_output(['git', 'show', f'{revision}:{path.as_posix()}'])


def without_hostility(document):
    value = copy.deepcopy(document)
    for actor in value.get('initial_state', {}).get('actors', []):
        actor.pop('hostility_type', None)
    return value


def replace_digest(data, name, before, after):
    encoded = name.encode('utf-8')
    record = struct.pack('<IQ', len(encoded), before) + encoded
    if data.count(record) != 1:
        raise ValueError(f'Expected exactly one original dependency: {name}')
    return data.replace(record, struct.pack('<IQ', len(encoded), after) + encoded)


def migrate(revision):
    targets = [('mm7', name, f'worlds/mm7/maps/{name}.scene.yml')
               for name in ('7out02', '7out03', '7out04', '7out06')]
    targets.append(('mm6', 'outa2', 'engine/liquids/liquids.yml'))
    prepared = []
    for world, name, dependency in targets:
        source = Path('assets_dev') / dependency
        before = old_bytes(revision, source)
        after = source.read_bytes().replace(b'\r\n', b'\n')
        old_document, new_document = yaml.safe_load(before), yaml.safe_load(after)
        if world == 'mm7':
            if without_hostility(old_document) != without_hostility(new_document):
                raise ValueError(f'Visual or other unapproved scene changes: {source}')
            reason = 'Only initial actor hostility fields changed; all visual scene data is identical.'
        else:
            original = old_document['liquids']
            current = new_document['liquids']
            if current[:len(original)] != original or not all(
                    entry.get('worlds') == ['mm9'] for entry in current[len(original):]):
                raise ValueError('Existing MM6-MM8 liquid definitions changed')
            reason = 'Existing liquid definitions are identical; only MM9-scoped entries were appended.'
        lighting = Path(f'assets_dev/worlds/{world}/maps/{name}.lighting')
        data = lighting.read_bytes()
        if data[:8] != b'OYMLIT1\0' or struct.unpack_from('<I', data, 8)[0] != 5:
            raise ValueError(f'Expected version-5 retained bake: {lighting}')
        data = replace_digest(data, dependency, fnv(before), fnv(after))
        recipe = lighting.with_suffix('.bake.json')
        recipe_before = recipe.read_bytes()
        # Earlier Windows bakes recorded CRLF recipe bytes; accept only the exact matching representation.
        recipe_name = recipe.relative_to('assets_dev').as_posix()
        candidates = [recipe_before, recipe_before.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')]
        record_prefix = struct.pack('<I', len(recipe_name.encode()))
        matching = [value for value in candidates if
                    record_prefix + struct.pack('<Q', fnv(value)) + recipe_name.encode() in data]
        if not matching:
            raise ValueError(f'Retained recipe does not match: {recipe}')
        recipe_data = json.loads(recipe_before)
        recipe_data['nonvisual_source_revalidation'] = {
            'before_revision': revision,
            'dependency': dependency,
            'before_sha256': hashlib.sha256(before).hexdigest(),
            'after_sha256': hashlib.sha256(after).hexdigest(),
            'reason': reason,
            'retained_lighting_sha256': hashlib.sha256(lighting.read_bytes()).hexdigest(),
        }
        recipe_after = (json.dumps(recipe_data, sort_keys=True, indent=2) + '\n').encode()
        data = replace_digest(data, recipe_name, fnv(matching[0]), fnv(recipe_after))
        prepared.append((source, after, recipe, recipe_after, lighting, data))
    # Validate every input before writing any result. Page payloads and all other binary bytes remain retained.
    for source, after, recipe, recipe_after, lighting, data in prepared:
        source.write_bytes(after)
        recipe.write_bytes(recipe_after)
        lighting.write_bytes(data)
        print(f'Revalidated nonvisual dependencies: {lighting}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before-revision', required=True)
    args = parser.parse_args()
    migrate(args.before_revision)
