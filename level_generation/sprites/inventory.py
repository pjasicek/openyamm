"""Audit native MM6-MM8 sprite scope without generating or modifying artwork."""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import hashlib
import json
import re
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ASSETS = REPO / 'assets_dev'


def rows(name):
    return list(csv.reader((ASSETS / 'engine/data_tables' / name).open(), delimiter='\t'))


def frame_images(frame):
    name = frame['texture_name'].lower()
    if not name or name.startswith('atlas:'):
        return []
    flags = frame.get('flags', [])
    if 'Image1' in flags or name.endswith('0'):
        return [name]
    if 'Images3' in flags:
        return [name + str(i) for i in [0, 2, 4]]
    if 'Fidget' in flags:
        return [name + str(i) for i in [0, 1, 2]] + [name[:-3] + 'sta3', name[:-3] + 'sta4']
    return sorted({name + str(8-i if i and f'Mirror{i}' in flags else i) for i in range(8)})


def run():
    common = ASSETS / 'engine/rendering/sprite_frame_data_common.yml'
    groups = [(g, False) for g in yaml.load(common.read_text(), Loader=yaml.CSafeLoader)['sprites']]
    for path in sorted((ASSETS / 'engine/rendering/sprite_frames/monsters').glob('*.yml')):
        groups += [(g, True) for g in yaml.load(path.read_text(), Loader=yaml.CSafeLoader)['sprites']]
    actors = {v.lower() for r in rows('monster_descriptors.txt') if r and r[0].isdigit() for v in r[11:19]}
    # Orphan animation groups belonging to existing MM6 creatures, absent from current action bindings.
    unused_actor_groups = {'batsta', 'b2tsta', 'b3tsta', 'cdr1ata0', 'cdr2ata0', 'cdr3ata0',
                           'ske1dyf', 'ske2dyf', 'ske3dyf'}
    actors |= unused_actor_groups
    decorations = {int(r[12]): r[2] for r in rows('decoration_data.txt') if r and r[0].isdigit()}
    objects = defaultdict(list)
    for r in rows('object_list.txt'):
        if len(r) > 7 and r[2].isdigit():
            objects[int(r[7])].append(r[0])
    files = sorted([*(ASSETS / 'engine/sprites').glob('*.bmp'),
                    *(ASSETS / 'worlds/mm7/sprites').glob('*.bmp')])
    by_name = defaultdict(list)
    for path in files:
        by_name[path.stem.lower()].append(path)
    monster_names = set()
    for g, monster in groups:
        if monster or g['sprite_name'].lower() in actors:
            monster_names.update(n for f in g['frames'] for n in frame_images(f))
    uses = defaultdict(list)
    records = []
    for g, monster in groups:
        if monster or g['sprite_name'].lower() in actors or g['sprite_id'] == 0:
            continue
        name = g['sprite_name'].lower()
        names = sorted({n for f in g['frames'] for n in frame_images(f)})
        if g['sprite_id'] in decorations or re.match(r'^(?:[67])?(?:bush|tree|rock|dec)', name):
            category = 'decorations'
        elif re.match(r'^(?:(?:[367])?(?:obj|botl)|3)', name):
            category = 'world_items'
        elif name in {'newhand1', 'newglas1', 'c2_hero', 'c3_haste', 'c4_shild', 'c5_sskin', 'guardang',
                      'c1_bless', 'turnmode', 'wizeye', 'aframe1', 'fly1', 'watwalk1'} or re.match(r'^i[1-6]_', name):
            category = 'interface_overlays'
        else:
            category = 'effects_projectiles_other'
        record = dict(sprite_id=g['sprite_id'], name=name, category=category, timeline_frames=len(g['frames']),
                      animated=len(g['frames']) > 1, images=names, existing_images=[n for n in names if n in by_name],
                      missing_images=[n for n in names if n not in by_name],
                      palettes=sorted({f.get('palette_id', 0) for f in g['frames']}),
                      image_palette_pairs=sorted({(n, f.get('palette_id', 0)) for f in g['frames'] for n in frame_images(f)}),
                      object_names=objects[g['sprite_id']])
        records.append(record)
        for n in names:
            uses[n].append(record)
    # Additional unused creature poses: modern numbered families plus explicit legacy animation stems.
    legacy_orphans = re.compile(r'^(?:arc1atk|bldfi|bldwin|cktwnc|dmnfgt|dragfi|drg1|drr1|dru1fi|dwa1fi|ertfi|fgtfi|figcfi|'
                                r'hydsta|jak1fi|lzddet|mcac|min1|mnk1|natffi|natmfi|noblfi|ogrdie|oozfi|pfemfi|pmanfi|pmanwi|'
                                r'pmn2fi|ratfi|rob1fi|seasfi|skefi|skl1st|welfi|wfigt)')
    file_records = []
    for path in files:
        name = path.stem.lower()
        categories = sorted({u['category'] for u in uses[name]})
        if categories:
            classification = 'referenced_non_creature'
        elif name in monster_names:
            classification = 'creature'
        elif re.match(r'^[67]?m\d{3}', name) or legacy_orphans.match(name):
            classification = 'unused_creature_pose'
        else:
            classification = 'unreferenced_needs_review'
        file_records.append(dict(path=str(path.relative_to(REPO)), name=name, classification=classification,
                                 categories=categories, groups=sorted({u['sprite_id'] for u in uses[name]}),
                                 bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    totals = Counter(r['classification'] for r in file_records)
    categories = {}
    for category in sorted({r['category'] for r in records}):
        subset = [r for r in records if r['category'] == category]
        names = {n for r in subset for n in r['existing_images']}
        categories[category] = dict(groups=len(subset), animated_groups=sum(r['animated'] for r in subset),
                                   static_groups=sum(not r['animated'] for r in subset),
                                   distinct_image_names=len(names), physical_files=sum(len(by_name[n]) for n in names))
    selected = [r for r in file_records if r['classification'] == 'referenced_non_creature']
    priority = ['decorations', 'world_items', 'interface_overlays', 'effects_projectiles_other']
    for category in priority:
        categories[category]['exclusive_files'] = sum(
            next(c for c in priority if c in r['categories']) == category for r in selected)
    summary = dict(total_mm6_mm8_bmp_files=len(files), classifications=dict(totals), categories=categories,
                   referenced_unique_image_names=len({r['name'] for r in selected}),
                   referenced_exact_file_hashes=len({r['sha256'] for r in selected}),
                   referenced_bmp_bytes=sum(r['bytes'] for r in selected),
                   animated_groups_with_art=sum(r['animated'] and bool(r['existing_images']) for r in records),
                   groups=len(records), groups_with_art=sum(bool(r['existing_images']) for r in records),
                   unique_sequences_ignoring_palette=len({tuple(r['images']) for r in records if r['existing_images']}),
                   existing_image_palette_pairs=len({tuple(v) for r in records for v in r['image_palette_pairs'] if v[0] in by_name}),
                   missing_image_names=sorted({n for r in records for n in r['missing_images']}),
                   mm9_png_files_out_of_scope=len(list((ASSETS/'worlds/mm9/sprites').glob('*.png'))),
                   already_enhanced_new_sorpigal_images=19)
    (HERE / 'inventory.json').write_text(json.dumps(dict(summary=summary, groups=records, files=file_records), indent=2)+'\n')
    with (HERE / 'non_creature_files.csv').open('w') as stream:
        writer = csv.writer(stream);writer.writerow(['path', 'classification', 'categories', 'group_ids', 'bytes'])
        for r in file_records:
            if r['classification'] in {'referenced_non_creature','unreferenced_needs_review'}:
                writer.writerow([r['path'], r['classification'], '|'.join(r['categories']), '|'.join(map(str,r['groups'])),r['bytes']])
    print(json.dumps({**summary, 'missing_image_names': len(summary['missing_image_names'])},indent=2))


if __name__ == '__main__':
    run()
