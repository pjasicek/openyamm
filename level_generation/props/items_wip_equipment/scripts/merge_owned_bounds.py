"""Merge bounds for this worker's installed models, preserving every other binding and all lengths."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

project = Path(__file__).resolve().parents[1]
repo = project.parents[2]
sys.path.insert(0, str(repo / 'tools'))
import item_model_shapes as shapes


def updated_line(line, bounds):
    match = shapes.ENTRY.match(line)
    assert match
    body = re.sub(r',\s*bounds:\s*\[[^\]]*\]', '', match.group(2)).rstrip()
    values = ', '.join(f'{value:g}' for value in bounds)
    return f'{match.group(1)}{body}, bounds: [{values}]{match.group(3)}' + ('\n' if line.endswith('\n') else '')


fixture = '  - {icon: test, model: test.glb, length: 42, bounds: [0, 0, 0, 1, 1, 1]} # retained\n'
assert updated_line(fixture, [-1, -2, 0, 1, 2, 3]) == (
    '  - {icon: test, model: test.glb, length: 42, bounds: [-1, -2, 0, 1, 2, 3]} # retained\n')
ledger = json.loads((project / 'ledger.json').read_text())
owned = {entry['icon']: entry for entry in ledger if entry['replacement_installed']}
assert owned and not any(entry.get('external_install') for entry in owned.values())
binding = repo / 'assets_dev/engine/world_items/items.yml'
records, seen = [], set()
with (repo / 'assets_source/.cook-cache/install.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    original = binding.read_bytes()
    lines = original.decode().splitlines(keepends=True)
    for number, line in enumerate(lines):
        match = shapes.ENTRY.match(line)
        if not match:
            continue
        fields = shapes.parse_fields(match.group(2))
        icon = fields.get('icon')
        if icon not in owned:
            continue
        assert icon not in seen
        seen.add(icon)
        entry = owned[icon]
        assert float(fields['length']) == entry['binding_length']
        source = repo / 'assets_source' / fields['model']
        runtime = repo / 'assets_dev' / fields['model']
        for path, key in [(source, 'installed_source_sha256'), (runtime, 'installed_runtime_sha256')]:
            assert hashlib.sha256(path.read_bytes()).hexdigest() == entry[key], path
        bounds = shapes.item_bounds(runtime, entry['binding_length'])
        lines[number] = updated_line(line, bounds)
        after = shapes.parse_fields(shapes.ENTRY.match(lines[number]).group(2))
        assert {k: v for k, v in fields.items() if k != 'bounds'} == {k: v for k, v in after.items() if k != 'bounds'}
        records.append({'icon': icon, 'length': entry['binding_length'], 'previous_bounds': json.loads(fields['bounds']),
                        'bounds': bounds, 'changed': line != lines[number],
                        'source_sha256': entry['installed_source_sha256'], 'runtime_sha256': entry['installed_runtime_sha256']})
    assert seen == set(owned)
    result = ''.join(lines).encode()
    assert binding.read_bytes() == original, 'Bindings changed concurrently; retry from current file'
    apply = '--apply' in sys.argv
    if apply and result != original:
        with tempfile.NamedTemporaryFile(dir=binding.parent, delete=False) as stream:
            stream.write(result)
            temporary = Path(stream.name)
        temporary.chmod(0o644)
        os.replace(temporary, binding)
    report = {'applied': apply, 'icons_checked': len(records), 'changed_rows': sum(r['changed'] for r in records),
              'binding_sha256_before': hashlib.sha256(original).hexdigest(),
              'binding_sha256_after': hashlib.sha256(result if apply else original).hexdigest(), 'records': records}
    (project / 'review/bounds_merge_latest.json').write_text(json.dumps(report, indent=2) + '\n')
    if apply:
        (project / 'review/bounds_merge_applied.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Owned bounds:', len(records), 'checked;', report['changed_rows'], 'rows', 'merged' if apply else 'would change')
