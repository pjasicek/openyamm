#!/usr/bin/env python3
"""Build the Mixamo and Meshy animation catalogues kept next to this script.

- mixamo_motions.json: every Mixamo motion and motion pack from the public product API (no login needed for
  listing; downloading FBX still needs the user's Adobe account): id, name, description, duration, frames,
  loopable, in-place support, tweak parameters, animated preview GIF, plus derived MM action roles and tags.
- meshy_library.json: Meshy's animation library (GET /openapi/v1/animations/library, free; applying a clip to a
  Meshy rig costs 3 credits): action_id, name, category, sub_category, preview GIF, plus derived roles and tags.
- ANIMATION_CATALOGUES.md: how to use both, the clips this project already used, and per-role candidate lists.
Run from the repository root: python3 level_generation/creatures/claude_shared/catalogues/build_animation_catalogues.py
(about 5 minutes; `--offline` regenerates the Markdown and used flags from the saved JSON without network access).
"""
import json
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'tools'))
MIXAMO = 'https://www.mixamo.com/api/v1/products'
HEADERS = {'X-Api-Key': 'mixamo2', 'User-Agent': 'OpenYAMM-catalogue/1.0'}

# MM game actions (actors.yml clip roles) and the keywords that suggest a clip for them. Order matters for the
# primary role; every matching role is listed.
ROLES = [
    ('death', r'\b(death|dying|dies|die|killed|falling back death|knocked out)\b'),
    ('hit', r'\b(hit|hurt|react|reaction|impact|stagger|stumble|flinch|knockback|knocked)\b'),
    ('cast', r'\b(spell|cast|casting|magic|summon|conjur|incantation|heal|power ?up|buff)\b'),
    ('attack_ranged', r'\b(throw|throwing|shoot|shooting|bow|arrow|archer|rifle|pistol|gun|fire ball|fireball)\b'),
    ('attack_melee', r'\b(attack|punch|punching|slash|swipe|stab|strike|kick|hook|jab|uppercut|chop|smash|swing|'
                     r'bite|headbutt|combo|cut|hammer|claw)\b'),
    ('run', r'\b(run|running|sprint|jog|jogging|charge)\b'),
    ('walk', r'\b(walk|walking|strut|stroll|sneak|limp|crawl|crawling|creep)\b'),
    ('fly', r'\b(fly|flying|float|floating|hover|levitat)\b'),
    ('fidget', r'\b(look around|looking|scratch|stretch|yawn|bored|taunt|cheer|wave|gesture|shrug|fidget|'
               r'talking|laugh)\b'),
    ('idle', r'\b(idle|stand|standing|breathing|wait|waiting|ready|guard|stance)\b'),
]
TAGS = [
    ('two_handed', r'\b(two hand|two-hand|2 hand|great ?sword|greatsword|hammer|axe|halberd|heavy weapon)\b'),
    ('sword', r'\b(sword|blade|katana|slash)\b'), ('staff', r'\b(staff|wand)\b'), ('bow', r'\b(bow|arrow)\b'),
    ('shield', r'\bshield\b'), ('unarmed', r'\b(punch|kick|unarmed|boxing|fist|martial)\b'),
    ('zombie_monster', r'\b(zombie|mutant|monster|creature|beast|orc|goblin)\b'), ('crawl', r'\bcrawl'),
    ('in_place_hint', r'\bin place\b'), ('female', r'\b(woman|female|girl)\b'),
]
# Clips this project already used (keep in sync when a new project picks clips).
USED_MESHY = {
    219: 'goblin anim_lib_v1 candidate', 221: 'goblin anim_lib_v1 candidate', 242: 'goblin anim_lib_v1 candidate',
    179: 'goblin anim_lib_v1 candidate', 178: 'goblin anim_lib_v1 candidate', 184: 'goblin anim_lib_v1 candidate',
    189: 'goblin anim_lib_v1 candidate', 129: 'goblin anim_lib_v1 candidate',
}
USED_MIXAMO = {   # by Mixamo id; confirmed by matching the downloaded FBX duration
    'c9c6d01a-b96c-11e4-a802-0aaa78deedf9': 'flying demon (mm6_wdm_claude) Flight; mixamo/floating.fbx (3.6 s)',
    'c9cbd7ad-b96c-11e4-a802-0aaa78deedf9': 'flying demon Attack 0.35-1.45 s; mixamo/zombie_swipe_attack.fbx (2.63 s)',
}
# Downloaded files whose exact catalogue entry is ambiguous (several variants share name/duration).
UNIDENTIFIED_DOWNLOADS = [
    ('mm6_wdm_claude/mixamo/wide_arm_spell_casting.fbx', 3.53, 'flying demon Cast 0.25-1.40 s',
     'not "Wide Arm Spell Casting" (3.17 s); 3.53 s matches "Standing 2H Magic Attack 05"'),
    ('mm6_wdm_claude/mixamo/large_hit_reaction_front.fbx', 1.0, 'flying demon Hit',
     'not "Standing React Large From Front" (1.37 s); several 1.0 s "Standing React Large" bow variants'),
    ('mm6_wdm_claude/mixamo/treading_water.fbx', 3.0, 'flying demon legs reference',
     'not "Treading Water" (2.17 s); exact variant unknown'),
]


def get(url, retries=4):
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(1.5 * (attempt + 1))


def classify(text):
    text = text.lower().replace('_', ' ')
    roles = [name for name, pattern in ROLES if re.search(pattern, text)]
    tags = [name for name, pattern in TAGS if re.search(pattern, text)]
    return roles, tags


def mixamo():
    first = get(f'{MIXAMO}?page=1&limit=96&type=Motion%2CMotionPack&query=')
    pages = first['pagination']['num_pages']
    items = list(first['results'])
    for page in range(2, pages + 1):
        items += get(f'{MIXAMO}?page={page}&limit=96&type=Motion%2CMotionPack&query=')['results']

    def detail(item):
        try:
            return get(f"{MIXAMO}/{item['id']}?similar=0").get('details', {})
        except Exception as error:
            return {'error': str(error)}

    with ThreadPoolExecutor(max_workers=6) as pool:
        details = list(pool.map(detail, items))
    out = []
    for item, info in zip(items, details):
        roles, tags = classify(f"{item['name']} {item.get('description', '')}")
        gms = info.get('gms_hash') or {}
        out.append({'id': item['id'], 'name': item['name'], 'description': item.get('description', ''),
                    'type': item['type'], 'character_type': item.get('character_type', ''),
                    'duration_s': info.get('duration'), 'frames': info.get('default_frame_length'),
                    'loopable': info.get('loopable'), 'supports_in_place': info.get('supports_inplace'),
                    'params': [p[0] for p in gms.get('params', [])] if isinstance(gms, dict) else [],
                    'preview_gif': item.get('thumbnail_animated', ''), 'roles': roles, 'tags': tags,
                    'used_in_project': ''})
    out.sort(key=lambda m: (m['name'].lower(), m['description'].lower()))
    return out


def mark_used(mixamo_items):
    for item in mixamo_items:
        item['used_in_project'] = USED_MIXAMO.get(item['id'], '')
    return mixamo_items


def meshy():
    import creature_meshy
    items = creature_meshy.api_request('GET', '/openapi/v1/animations/library')
    out = []
    for item in items:
        roles, tags = classify(f"{item['name']} {item.get('category', '')} {item.get('sub_category', '')}")
        out.append({**item, 'roles': roles, 'tags': tags, 'used_in_project': USED_MESHY.get(item['action_id'], '')})
    return sorted(out, key=lambda m: m['action_id'])


def markdown(mixamo_items, meshy_items):
    def role_counts(items):
        return {name: sum(1 for i in items if name in i['roles']) for name, _ in ROLES}

    lines = [
        '# Animation catalogues (Mixamo and Meshy)', '',
        'Generated by `build_animation_catalogues.py` (rerun to refresh). Full data: `mixamo_motions.json` '
        f'({len(mixamo_items)} entries) and `meshy_library.json` ({len(meshy_items)} clips). Roles are keyword guesses '
        'from names and descriptions (MM actor clip roles: idle, walk, run, attack_melee, attack_ranged, cast, hit, death, '
        'fidget, fly); always look at the preview GIF before choosing.', '',
        '## How to use', '',
        '- **Meshy library** (humanoid/biped only): applies to a Meshy auto-rig (`rigging` job) as an `animation` job, '
        '3 credits per clip, e.g. `{"rig_task_id": ..., "action_ids": [...], "post_process": {"operation_type": '
        '"change_fps", "fps": 24}}` (`mm6_gob_claude/requests/anim_lib_v1.json`). Clips play on Meshy\'s skeleton '
        'without retarget loss; they carry the source body\'s wrist flex and foot posture (humanoid playbook).',
        '- **Mixamo** (humanoid only): free FBX downloads through the user\'s Adobe account (Claude cannot download; ask '
        'the user with the exact clip names, "Without Skin", 24 fps, In Place where offered). Retarget by direction + '
        'twist (`mm6_pmn2_claude/scripts/retarget_fbx.py`); an FBX import switches the scene frame rate, reset it to 24. '
        'Mixamo kept two-handed grips better than Meshy clips (mage hammer swing). Several Mixamo motions share a '
        'name (variants differ in description); the downloaded FBX is named after the description, and the `id` is '
        'the unique key. Motion packs (42) bundle clips and have no single duration.',
        '- Quadrupeds, flyers and spiders use procedural clips (quadruped playbook); neither library has non-biped '
        'motion.', '',
        '## Already used in this project', '',
        '| Library | Clip | Id | Used for |', '|---|---|---|---|']
    for item in meshy_items:
        if item['used_in_project']:
            lines.append(f"| Meshy | {item['name']} | {item['action_id']} | {item['used_in_project']} |")
    for item in mixamo_items:
        if item['used_in_project']:
            lines.append(f"| Mixamo | {item['name']} ({item['duration_s']} s) | `{item['id']}` | {item['used_in_project']} |")
    lines += ['', 'Other downloaded Mixamo files (exact catalogue entry not identified; match a new download by its '
              'duration before recording it):', '']
    for path, seconds, use, note in UNIDENTIFIED_DOWNLOADS:
        lines.append(f'- `{path}` ({seconds} s, {use}): {note}')
    lines += ['', '## Role counts', '', '| Role | Meshy | Mixamo |', '|---|---|---|']
    mc, xc = role_counts(meshy_items), role_counts(mixamo_items)
    for name, _ in ROLES:
        lines.append(f'| {name} | {mc[name]} | {xc[name]} |')
    lines += ['', '## Meshy library by category', '']
    categories = {}
    for item in meshy_items:
        categories.setdefault(item['category'], {}).setdefault(item['sub_category'], []).append(item)
    for category in sorted(categories):
        lines += [f'### {category}', '']
        for sub in sorted(categories[category]):
            clips = ', '.join(f"{i['action_id']} {i['name']}" for i in categories[category][sub])
            lines.append(f'- **{sub}**: {clips}')
        lines.append('')
    lines += ['## Mixamo candidates per MM role', '',
              'Loopable motions first, then by duration. Columns: name, description, duration, loop, in-place.', '']
    for name, _ in ROLES:
        picks = [i for i in mixamo_items if i['roles'] and i['roles'][0] == name and i['type'] == 'Motion']
        picks.sort(key=lambda i: (not i['loopable'], i['duration_s'] or 0))
        lines += [f'### {name} ({len(picks)})', '', '| Name | Description | s | Loop | In place |', '|---|---|---|---|---|']
        for i in picks:
            description = i['description'].replace('|', '/')
            lines.append(f"| {i['name']} | {description} | {i['duration_s']} | {'yes' if i['loopable'] else ''} | "
                         f"{'yes' if i['supports_in_place'] else ''} |")
        lines.append('')
    return '\n'.join(lines) + '\n'


def main():
    if '--offline' in sys.argv:          # regenerate the Markdown/used flags from the saved JSON, no network
        meshy_items = json.loads((HERE / 'meshy_library.json').read_text())
        for item in meshy_items:
            item['used_in_project'] = USED_MESHY.get(item['action_id'], '')
        mixamo_items = mark_used(json.loads((HERE / 'mixamo_motions.json').read_text()))
        (HERE / 'meshy_library.json').write_text(json.dumps(meshy_items, indent=1) + '\n')
        (HERE / 'mixamo_motions.json').write_text(json.dumps(mixamo_items, indent=1) + '\n')
        (HERE / 'ANIMATION_CATALOGUES.md').write_text(markdown(mixamo_items, meshy_items))
        print('regenerated offline')
        return
    meshy_items = meshy()
    (HERE / 'meshy_library.json').write_text(json.dumps(meshy_items, indent=1) + '\n')
    print('meshy', len(meshy_items))
    mixamo_items = mark_used(mixamo())
    (HERE / 'mixamo_motions.json').write_text(json.dumps(mixamo_items, indent=1) + '\n')
    print('mixamo', len(mixamo_items), 'detail errors', sum(1 for i in mixamo_items if i['duration_s'] is None))
    (HERE / 'ANIMATION_CATALOGUES.md').write_text(markdown(mixamo_items, meshy_items))
    print('written', HERE / 'ANIMATION_CATALOGUES.md')


if __name__ == '__main__':
    main()
