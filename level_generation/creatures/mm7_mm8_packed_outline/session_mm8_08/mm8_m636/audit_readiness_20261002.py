"""Read-only MM8 roster audit, with a report saved in this family staging directory."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
import sys

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
CREATURES = REPO / 'level_generation/creatures'
PACKED = CREATURES / 'mm7_mm8_packed_outline'
sys.path.insert(0, str(CREATURES))
from mm8_restore_queue import resolve as resolve_native_view


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return str(path.resolve().relative_to(REPO))


def package_for(stem):
    if stem == 'm508':
        return PACKED / 'session_mm7_02/mm7_m508'
    found = list(PACKED.glob('session_*/mm8_' + stem))
    assert len(found) == 1, (stem, found)
    return found[0]


def handoff(stem, family):
    if stem in ['m504', 'm508', 'm624', 'm636']:
        pointer = load(family / 'current_handoff_20261002.json')
        base = REPO if pointer['manifest'].startswith('level_generation/') else family
        return base / pointer['manifest'], base / pointer['acceptance']
    if stem == 'm432':
        folder = family / 'death4_completion/redo_2x'
    elif stem in ['m496', 'm500', 'm516', 'm520', 'm524']:
        folder = family
        return folder / 'draft_manifest.json', folder / 'review/acceptance.json'
    elif (family / 'redo_2x/manifest.json').exists():
        folder = family / 'redo_2x'
    else:
        folder = family
    manifest = folder / 'manifest.json'
    acceptance = folder / 'review/acceptance.json'
    if not acceptance.exists():
        acceptance = folder / 'acceptance.json'
    return manifest, acceptance


inventory_path = CREATURES / 'remaining_inventory.json'
inventory = load(inventory_path)
descriptor_path = REPO / 'assets_dev/engine/data_tables/monster_descriptors.txt'
descriptors = {}
for line in descriptor_path.read_text().splitlines():
    columns = line.split('\t')
    if columns[0].isdigit():
        descriptors[int(columns[0])] = columns
table_paths = [REPO / 'assets_dev/engine/rendering/sprite_frame_data_common.yml']
table_paths += sorted((REPO / 'assets_dev/engine/rendering/sprite_frames/monsters').glob('*.yml'))
groups = {}
for path in table_paths:
    for group in yaml.load(path.read_text(), Loader=yaml.CSafeLoader)['sprites']:
        groups[group['sprite_name'].lower()] = group
sprites = {}
for folder in ['assets_dev/engine/sprites', 'assets_dev/worlds/mm8/sprites']:
    for path in (REPO / folder).glob('*'):
        if path.suffix.lower() == '.bmp':
            sprites[path.stem.lower()] = path

rows = []
checked_new_hashes = 0
for family in inventory['families']:
    if family['world'] != 'mm8':
        continue
    stem = re.match(r'm\d+', family['all_native_family_images'][0]).group()
    root = package_for(stem)
    manifest_path, acceptance_path = handoff(stem, root)
    manifest, acceptance = load(manifest_path), load(acceptance_path)
    assert 'accepted' in acceptance['status'] or acceptance['status'] == 'complete_local_acceptance', stem
    assert manifest['pixels_per_logical_pixel'] == 2, stem
    native_names = {n for n in sprites if re.fullmatch(stem + r'[a-z]+[0-7]', n)}
    assert native_names == set(family['all_native_family_images']), stem
    needed = set()
    current_atlas_aliases = {}
    steps = 0
    ids = []
    for descriptor in family['descriptors']:
        identifier = descriptor['id']
        ids.append(identifier)
        current = descriptors[identifier]
        assert current[1] == descriptor['label'], (identifier, current[1], descriptor['label'])
        for group_name in current[11:19]:
            group = groups[group_name.lower()]
            for view in range(8):
                for frame in group['frames']:
                    name, mirror = resolve_native_view(frame, view)
                    steps += 1
                    if name.startswith('atlas:'):
                        native_name = name.split('/', 1)[1]
                        current_atlas_aliases[name] = native_name
                        name = native_name
                    if not name.startswith('null'):
                        needed.add(name)
    assert needed == set(family['images']), stem
    restored = set(manifest['frames'])
    assert needed <= restored, (stem, sorted(needed - restored))
    missing_native = native_names - restored
    assert missing_native == ({'m624fa3', 'm624fb3', 'm624fc3', 'm624fd3'} if stem == 'm624' else set()), stem
    category = {'m504': 'mixed_imagegen_and_authorized_video_x3',
                'm624': 'latest_method_required_playback_scope',
                'm480': 'latest_method_with_approved_pose_substitution'}.get(stem, 'full_native_latest_method')
    sampling = manifest.get('actual_generated_detail', manifest.get('generated_detail',
                acceptance.get('sampling', acceptance.get('actual_generated_sampling', {}))))
    minimum = sampling.get('minimum_sampling', sampling.get('minimum', sampling.get('prior_imagegen_minimum')))
    if minimum is None:
        minima = []
        for record in manifest['frames'].values():
            xy = record.get('effective_generated_sampling_xy')
            if xy:
                minima.append(min(xy))
        minimum = min(minima) if minima else manifest.get('generated_sampling_min')
    # Recheck the newly frozen packages; the unchanged accepted packages were hash-audited earlier this turn.
    if stem in ['m504', 'm508', 'm624', 'm636']:
        for field in ['artifact_sha256', 'inherited_artifact_sha256']:
            for name, expected in acceptance.get(field, {}).items():
                path = Path(name)
                if not path.is_absolute():
                    path = REPO / path
                assert sha(path) == expected, str(path)
                checked_new_hashes += 1
        pointer = load(root / 'current_handoff_20261002.json')
        for key, path in [('manifest', manifest_path), ('acceptance', acceptance_path)]:
            if key + '_sha256' in pointer:
                assert sha(path) == pointer[key + '_sha256']
    rows.append({
        'stem': stem, 'label': family['label'], 'descriptor_ids': ids,
        'category': category, 'required_playback_ready': True,
        'native_images': len(native_names), 'enhanced_images': len(restored),
        'native_playback_images': len(needed), 'unused_native_images': len(native_names - needed),
        'excluded_unused_native_images': sorted(missing_native),
        'current_native_descriptor_view_steps': steps,
        'current_explicit_atlas_aliases': current_atlas_aliases,
        'physical_master_scale': 2, 'minimum_actual_generated_sampling': minimum,
        'manifest': rel(manifest_path), 'manifest_sha256': sha(manifest_path),
        'acceptance': rel(acceptance_path), 'acceptance_sha256': sha(acceptance_path),
        'local_acceptance_status': acceptance['status'], 'installed': False})

counts = Counter(row['category'] for row in rows)
assert len(rows) == 61
assert counts['full_native_latest_method'] == 58
report = {
    'audited_utc': datetime.now(timezone.utc).isoformat(),
    'status': 'all_mm8_required_playback_ready_under_user_authorized_exceptions',
    'inventory': {'path': rel(inventory_path), 'sha256': sha(inventory_path)},
    'current_native_descriptor_table': {'path': rel(descriptor_path), 'sha256': sha(descriptor_path)},
    'totals': {'families': len(rows), 'merged_descriptor_ids': sum(len(r['descriptor_ids']) for r in rows),
               'native_images': sum(r['native_images'] for r in rows),
               'enhanced_images': sum(r['enhanced_images'] for r in rows),
               'native_descriptor_view_steps_rechecked': sum(r['current_native_descriptor_view_steps'] for r in rows),
               'required_playback_ready_families': len(rows), 'family_categories': dict(counts),
               'new_and_inherited_completion_artifact_hashes_rechecked': checked_new_hashes},
    'prior_audit_this_turn': {'unchanged_accepted_artifact_hashes_verified': 92941,
                             'native_bindings_checked': 'Exact groups, timing, flags, aliases, scales and mirrors'},
    'exceptions': {
        'earth_elemental': 'MM6 six-frame walk does not match MM8 eight-frame walk. Eight missing native '
                           'walk-view-0 images use authorized realesr-animevideov3 at 3x, exported at 2x.',
        'naga': 'Four unused fidget-view-3 BMPs are outside all current native playback bindings and '
                'excluded by user instruction; all required playback art is restored.',
        'troll_peasant': 'Existing user-approved m480sa1 <- m480ah1 substitution retained.'},
    'repairs': {'air_elemental': '29 missing poses on five complete native+outline+detail imagegen sheets; '
                                'all 160 original native images complete.',
                'school_of_fish': 'All 130 images complete. Three swim views and death regenerated; '
                                  'all ten death poses retain twelve fish. Entire-school extraction fixed.'},
    'review_limits': 'New poses reviewed in static contacts, independent actual-art feature comparisons, '
                     '100% material/alpha patches and every native palette/mask pose. Timed playback not watched.',
    'full_native_original_pose_latest_method_families': 58,
    'full_native_original_pose_latest_method_for_every_family': False,
    'installed': False, 'shared_tools_skills_global_ledgers_runtime_assets_modified': False,
    'families': rows}
(HERE / 'readiness_audit_20261002.json').write_text(json.dumps(report, indent=2) + '\n')
lines = [
    '# MM8 restoration readiness after the requested repairs', '',
    'All **61 native MM8 families / 198 merged descriptors** have ready local handoffs for their required '
    'playback under the agreed exceptions. **58 families** have complete original-native-pose coverage with '
    'the latest packed whole-animation + attached OUTLINE-ONLY imagegen method. Earth Elemental uses a '
    'mixed-method fallback, Naga excludes four unused poses, and Troll Peasant retains its approved substitution.', '',
    '| Family | Result |', '|---|---|',
    '| Earth Elemental | 160/160 images. MM6 has six walk frames, MM8 eight; the missing eight use ESRGAN Video 3×. |',
    '| Air Elemental | 160/160 images. Five complete native+outline+detail sheets repair the missing 29 poses. |',
    '| Naga | 156/160 images, all required playback ready. Four unused fidget BMPs excluded as authorized. |',
    '| School of Fish | 130/130 images. All stored swim views and death complete, including all twelve fish in every death pose. |',
    '| Troll Peasant | Approved existing pose substitution retained. |', '',
    'Every repair has checked 2× physical masters, base/mask atlases, native palettes and exact placement/animation '
    'metadata. Actual generated sampling is measured separately: the Air family minimum is 1.711× '
    '(new attack sheet about 1.76×), and Fish is 1.335×. These complete cycles were accepted after visual '
    'review under the authorized whole-cycle priority. Native unused art stays outside playback.', '',
    'All new poses, independent actual-art placement features, material/alpha patches at 100%, and every '
    'palette/mask pose were inspected. Frozen acceptance records bind actual attached inputs, selected raw '
    'returns and exported artifacts by SHA-256. Timed playback was not watched. No gameplay installation.', '',
    '[Machine-readable 61-family roster](readiness_audit_20261002.json) · '
    '[Fish complete review](completion_20261002/review/index.html) · '
    '[Air complete review](../../session_mm7_02/mm7_m508/completion_20261002/review/index.html)', '',
    '| Native family | IDs | Enhanced / native images | Coverage | Manifest |',
    '|---|---|---|---|---|']
for row in rows:
    link = '/' + str(REPO / row['manifest']).lstrip('/')
    lines.append(f'| {row["label"]} | {", ".join(map(str, row["descriptor_ids"]))} | '
                 f'{row["enhanced_images"]}/{row["native_images"]} | {row["category"]} | '
                 f'[handoff]({link}) |')
(HERE / 'repair_summary_20261002.md').write_text('\n'.join(lines) + '\n')
print(json.dumps(report['totals'], indent=2))
