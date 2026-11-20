"""Record the authorized whole-animation pixel-budget tradeoff without claiming added detail."""
import hashlib
from pathlib import Path


METHOD = 'packed_complete_animation_outline_only_detailed_appearance'
DEFAULT_POLICY = dict(
    priority='one_complete_animation_per_stored_view', allow_below_2x=True,
    user_authorization='Main decision is to have all the sprites for given animation (per rotation) on one sheet '
                       'submitted/returend by imagegen, so we need to live with certain monsters being < 2x.',
    authorized_date='2026-10-01',
    reason='Preserve every native animation step on one submitted and one returned sheet; report actual generated '
           'sampling separately from the physical 2x export. Normal visual and technical acceptance remains required.')


def validate_policy(policy, run, original, registration=None):
    if not policy:
        return
    assert policy['priority'] == 'one_complete_animation_per_stored_view'
    assert policy['allow_below_2x'] is True
    assert policy.get('user_authorization') and policy.get('reason')
    assert run['method'] == METHOD, 'This resolution policy applies only to complete-animation sheets'
    jobs = {job['id']: job for job in run['jobs']}
    for job in jobs.values():
        for binding in job['bindings']:
            native = original['animations'][binding['action']]['views'][str(binding['view'])]
            assert binding['native_frames'] == [step['frame'] for step in native], job['id']
            assert len(job['frames']) == len(native), 'One sheet must contain the complete native sequence'
    if registration is None:
        return
    for name, row in registration.items():
        if row.get('empty_native_endpoint') or 'retained_from' in row:
            continue
        job = jobs[row['batch']]
        assert row.get('generated_frame', name) in job['frames'], name
        assert row['raw_path'] == job['selected_raw'], 'Every animation uses one selected returned sheet'
        for path_key, sha_key in (('raw_path', 'raw_sha256'), ('clean_path', 'clean_sha256')):
            assert hashlib.sha256(Path(row[path_key]).read_bytes()).hexdigest() == row[sha_key], name


def record_detail_policy(manifest, policy, registration):
    """Use both on export and when accepting an already-reviewed package after a policy change."""
    detail = manifest['generated_detail']
    detail.pop('minimum_sampling_exclusive', None)
    detail.pop('below_minimum_frames', None)
    detail['target_sampling'] = 2
    detail['whole_animation_resolution_policy'] = policy
    below = sorted(name for name, row in registration.items()
                   if not row.get('empty_native_endpoint') and min(row['effective_sampling_xy']) < 2)
    detail['below_target_frames'] = below
    manifest['limitations'] = [line for line in manifest['limitations']
                               if not line.startswith('Complete native cycles retained, but actual generated sampling')]
    if below:
        manifest['limitations'].append('Complete native animation/view sheets take priority over the 2x detail target '
            'under the recorded user policy. Actual generated sampling is below 2x for ' + str(len(below)) +
            ' frames; the physical 2x export adds no generated detail.')
