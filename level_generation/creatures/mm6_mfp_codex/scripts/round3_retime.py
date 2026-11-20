"""Review 3: change only Death sampler timestamps; preserve every original binary byte."""
import copy
import hashlib
import json
import shutil
import sys
from pathlib import Path
import numpy as np

sys.dont_write_bytecode = True
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parents[2] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor

R = P / 'review/round3'
B = P / 'work/round3/before'
R.mkdir(parents=True, exist_ok=True)
B.mkdir(parents=True, exist_ok=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def save_json(p, data):
    p.write_text(json.dumps(data, indent=2) + '\n')
def backup(p):
    target = B / p.relative_to(P)
    if target.exists():
        assert sha(target) == sha(p), f'Already changed: {p}'
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, target)
def remap(t):
    return (np.minimum(t, 100 / 48) + np.maximum(t - 100 / 48, 0) / 1.5) / 1.25

for name in ['HANDOFF.md', 'README.md', 'creature_3d_progress.json', 'export/manifest.json',
             'export/export_info.json', 'export/mm6_mfp.blend', 'integration/actors.yml',
             'review/viewer/manifest.json', 'review/viewer/feedback/user_feedback.json',
             'review/sheets/Death.png', 'review/final_metrics.json', 'review/runtime_audit.json']:
    backup(P / name)

files = (list((P / 'export').glob('*.glb')) + list((P / 'review/viewer').glob('*.glb'))
         + list((P / 'work').glob('final_check*.glb')))
receipt = {'old_duration_s': 143 / 48, 'new_duration_s': float(remap(143 / 48)),
           'source_segment_frames_48fps': [100, 143], 'segment_speed': 1.5, 'overall_speed': 1.25,
           'new_breakpoint_s': 100 / 48 / 1.25, 'changed_files': {}, 'unchanged_files': {}}
for p in sorted(files):
    d, old_binary = read_glb(p)
    a = next((a for a in d.get('animations', []) if a['name'] == 'Death'), None)
    if a is None:
        receipt['unchanged_files'][str(p.relative_to(P))] = sha(p)
        continue
    backup(p)
    before = copy.deepcopy(d)
    binary = bytearray(old_binary)
    replacements = {}
    for i in sorted({s['input'] for s in a['samplers']}):
        times = np.frombuffer(accessor_bytes(d, old_binary, i), dtype='<f4').astype(float)
        # Existing 240 Hz samples include old frame 100 exactly (sample 500).
        assert len(times) in (2, 716) and abs(times[-1] - 143 / 48) < 1e-6
        if len(times) == 716:
            assert np.max(np.abs(times - np.arange(716) / 240)) < 2e-7
            times = np.arange(716) / 240
        else:
            times = np.array([0., 100 / 48, 143 / 48])
            # Exporter-compressed tracks have tiny numerical translation/scale drift.
            # Insert their interpolated boundary so even that drift follows the same path.
            outputs = {}
            for si, sampler in enumerate(a['samplers']):
                if sampler['input'] != i:
                    continue
                old_output = sampler['output']
                mode = sampler.get('interpolation', 'LINEAR')
                key = (old_output, mode)
                if key not in outputs:
                    values = np.frombuffer(accessor_bytes(d, old_binary, old_output), dtype='<f4').reshape(2, -1)
                    u = (100 / 48) / float(np.frombuffer(accessor_bytes(d, old_binary, i), dtype='<f4')[-1])
                    middle = values[0].astype(float)
                    if mode == 'LINEAR':
                        middle = (1-u)*values[0].astype(float) + u*values[1].astype(float)
                        paths = {c['target']['path'] for c in a['channels'] if c['sampler'] == si}
                        if 'rotation' in paths:
                            q0, q1 = values.astype(float)
                            dot = float(np.dot(q0, q1))
                            if dot < 0:
                                q1 = -q1
                                dot = -dot
                            theta = np.arccos(np.clip(dot, -1, 1))
                            middle = ((1-u)*q0 + u*q1 if theta < 1e-4 else
                                      (np.sin((1-u)*theta)*q0 + np.sin(u*theta)*q1)/np.sin(theta))
                            middle /= np.linalg.norm(middle)
                    else:
                        assert mode == 'STEP'
                    new_values = np.vstack([values[0], middle, values[1]]).astype('<f4')
                    source = copy.deepcopy(d['accessors'][old_output])
                    source['count'] = 3
                    source.pop('min', None)
                    source.pop('max', None)
                    outputs[key] = append_accessor(d, binary, source, new_values.tobytes())
                sampler['output'] = outputs[key]
        new_times = remap(times).astype('<f4')
        assert np.all(np.diff(new_times) > 0)
        source = copy.deepcopy(d['accessors'][i])
        source['count'] = len(new_times)
        source.update(min=[float(new_times[0])], max=[float(new_times[-1])])
        replacements[i] = append_accessor(d, binary, source, new_times.tobytes())
    for sampler in a['samplers']:
        sampler['input'] = replacements[sampler['input']]
    # No other metadata or accessor changed. Existing payload, including all pose values,
    # images, geometry, skin weights and the complete Dead clip, remains byte-identical.
    expected = copy.deepcopy(before)
    expected['accessors'] = d['accessors']
    expected['bufferViews'] = d['bufferViews']
    expected['animations'] = [a if x['name'] == 'Death' else x for x in expected['animations']]
    assert expected == d and binary[:len(old_binary)] == old_binary
    write_glb(p, d, bytes(binary))
    receipt['changed_files'][str(p.relative_to(P))] = {
        'before_sha256': sha(B / p.relative_to(P)), 'after_sha256': sha(p),
        'old_binary_bytes_preserved': len(old_binary), 'new_time_accessors': replacements,
        'only_death_timing_changed': True, 'sparse_tracks_boundary_interpolated': True,
        'other_clips_including_dead_identical': True}

m_path = P / 'review/viewer/manifest.json'
m = json.loads(m_path.read_text())
m['revision'] = 'mm6_mfp_codex_review3'
m['clips']['Death']['duration'] = receipt['new_duration_s']
m['clips']['Death']['provenance'] += '; review 3: frames 100–143 at 1.5x, then whole clip at 1.25x'
for model in m['models']:
    name = model['url'].split('?')[0]
    model.update(revision=m['revision'], sha256=sha(P / 'review/viewer' / name))
    model['url'] = name + '?v=' + model['sha256'][:12]
save_json(m_path, m)
info_path = P / 'export/export_info.json'
info = json.loads(info_path.read_text())
for lod in info.values():
    lod['durations']['Death'] = receipt['new_duration_s']
save_json(info_path, info)
assert sha(P / 'integration/actors.yml') == sha(B / 'integration/actors.yml')
receipt['actors_yml_changed'] = False
save_json(R / 'retime_receipt.json', receipt)

# Match the previous review cameras and source poses, changing only displayed time.
plan = json.loads((P / 'review/round2/capture_after.json').read_text())
plan = [row for row in plan if '/Death/' in row[0]]
for row in plan:
    row[2] = float(remap(row[2]))
save_json(R / 'capture_death.json', plan)
print(json.dumps(receipt, indent=2))
