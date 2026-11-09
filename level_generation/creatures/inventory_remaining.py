"""Count native actor-art families and completed direct-restoration packages."""
from pathlib import Path
from collections import defaultdict,Counter
import csv,hashlib,json,re,sys,yaml
P=Path(__file__).resolve().parent;ROOT=P.parents[1];A=ROOT/'assets_dev'
sys.path.insert(0,str(P.parent/'sprites'))
from inventory import frame_images as unpack_frame_images
from mm7_sampling_audit import audit as audit_mm7_sampling
from mm6_sampling_audit import audit as audit_mm6_sampling

def frame_images(frame):
    # Installation changes texture references, not native frame identities or view flags.
    # The general non-creature inventory intentionally skips atlases; this roster must still count them.
    name = frame['texture_name'].lower()
    if name.startswith('atlas:'):
        match = re.fullmatch(r'atlas:([a-z0-9_-]+)/([a-z0-9_-]+)', name)
        assert match, 'Invalid installed actor reference: ' + name
        frame = dict(frame, texture_name=match[2])
    return unpack_frame_images(frame)

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    sprite_indices={}
    for scope,folder in [('engine',A/'engine/sprites')]+[(w,A/'worlds'/w/'sprites') for w in ('mm6','mm7','mm8')]:
        sprite_indices[scope]={p.stem.lower():p for p in folder.glob('*.bmp')}
    groups={};group_sources=[]
    for path in [A/'engine/rendering/sprite_frame_data_common.yml',*sorted((A/'engine/rendering/sprite_frames/monsters').glob('*.yml'))]:
        group_sources.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path)))
        for g in yaml.load(path.read_text(),Loader=yaml.CSafeLoader)['sprites']:groups[g['sprite_name'].lower()]=g
    families={}
    for line in (A/'engine/data_tables/monster_descriptors.txt').read_text().splitlines():
        row=line.split('\t')
        if not row[0].isdigit() or int(row[0])>652:continue
        mid=int(row[0]);world='mm8' if mid<=198 else 'mm7' if mid<=474 else 'mm6'
        actions=[groups[n.lower()] for n in row[11:19]]
        standing=tuple(sorted({n for f in actions[0]['frames'] for n in frame_images(f)}))
        key=(world,standing)
        r=families.setdefault(key,dict(world=world,label=row[1],descriptors=[],standing_images=list(standing),images=set(),palettes=set()))
        r['descriptors'].append(dict(id=mid,label=row[1]))
        for g in actions:
            for f in g['frames']:
                names=[n for n in frame_images(f) if n not in {'null'+str(i) for i in range(8)}]
                r['images'].update(names)
                if names:r['palettes'].add(f.get('palette_id',0))
        r['images'].difference_update('null'+str(i) for i in range(8))
    packages=[]
    for path in [*sorted(P.glob('*/redo_2x/manifest.json')), *sorted(P.glob('*/*/redo_2x/manifest.json')),
                 *sorted(P.glob('*/manifest.json')),
                 P/'mm6_goblin/direct_complete/manifest.json']:
        m=json.loads(path.read_text())
        if not str(m.get('creature','')).startswith(('mm6:','mm7:','mm8:')):continue
        issues=[]
        detail_exceptions={}
        if str(m.get('creature','')).startswith('mm6:'):
            sampling=audit_mm6_sampling(path.parent)
            if path.parent.name=='redo_2x':
                registration=json.loads((path.parent/'registration.json').read_text())
                declared=m.get('generated_detail',{}).get('retained_detail_exceptions',{})
                if declared:
                    policy=json.loads((path.parent/'processing.json').read_text())
                    decision_path=path.parent/'review/decision.json'
                    decision=json.loads(decision_path.read_text()) if decision_path.exists() else {}
                    for name,exception in declared.items():
                        row=registration[name]
                        retained=row.get('retained_from',{})
                        source=ROOT/retained.get('project','')
                        if (exception.get('user_authorization') and exception.get('reason')
                                and policy.get('retained_detail_exceptions',{}).get(name)==exception
                                and decision.get('retained_detail_exceptions',{}).get(name)==exception
                                and row.get('retained_detail_exception')==exception
                                and source==path.parent.parent
                                and sha(source/'registration.json')==retained.get('registration_sha256')
                                and retained.get('assets')
                                and all(sha(source/asset)==digest and sha(path.parent/asset)==digest
                                        for asset,digest in retained['assets'].items())):
                            detail_exceptions[name]=dict(exception, sampling_xy=row['effective_sampling_xy'])
                    if set(detail_exceptions)!=set(declared):
                        issues.append('unverified retained detail exception')
            unresolved=[f for f in sampling['frames'] if f['status'] not in
                        ('at_least_2x_sampling','native_endpoint_preserved') and f['frame'] not in detail_exceptions]
            if unresolved or not sampling['frames']:
                failed=len(unresolved)
                issues.append(f'insufficient generated detail: {failed} frames below 2x; '
                              'see mm6_remaining/redo_2x/inventory.json')
            if path.parent.name=='redo_2x':
                registration = json.loads((path.parent/'registration.json').read_text())
                for frame in sampling['frames']:
                    if frame['status']=='native_endpoint_preserved':continue
                    if frame['frame'] in detail_exceptions:continue
                    if min(frame.get('sampling_x',0),frame.get('sampling_y',0))<=2:
                        retained = registration[frame['frame']].get('retained_from')
                        if retained and min(frame.get('sampling_x',0),frame.get('sampling_y',0)) >= 2:
                            source = ROOT/retained['project']
                            if (sha(source/'registration.json') == retained['registration_sha256']
                                    and all(sha(source/name) == digest and sha(path.parent/name) == digest
                                            for name,digest in retained['assets'].items())):
                                continue
                        issues.append('redo requires strictly greater than 2x: '+frame['frame'])
        if str(m.get('creature','')).startswith('mm7:'):
            sampling=audit_mm7_sampling(path.parent)
            if not sampling['passed']:
                failed=[k for k,v in sampling['batches'].items() if v['below_minimum_frames']]
                issues.append('actual generated detail below 2x or unverified: '+', '.join(failed))
        validation_path=path.parent/'validation.json'
        if not validation_path.exists():issues.append('missing validation.json')
        else:
            validation=json.loads(validation_path.read_text())
            issues.extend('failed validation: '+k for k,v in validation.items() if v is False)
            for key in ('exact_crop_reconstruction','exact_atlas_extraction'):
                if validation.get(key) is not True:issues.append('unverified '+key)
        for page in m.get('pages',[]):
            for key in ('base','mask'):
                if not (path.parent/page[key]).is_file():issues.append('missing '+page[key])
        if not m.get('pages'):issues.append('no atlas pages')
        if not m.get('animations'):issues.append('no animations')
        if not m.get('variants'):issues.append('no variants')
        # A viewer is optional; artifact-bound visual acceptance below remains required for new packages.
        review_path=path.parent/'review/acceptance.json'
        if m.get('review_record'):
            review_path=path.parent/m['review_record']
            if not review_path.exists():issues.append('visual review pending')
            else:
                review=json.loads(review_path.read_text())
                if review.get('status')!='accepted':issues.append('visual review not accepted')
                for name,digest in review.get('artifact_hashes',{}).items():
                    artifact=path.parent/name
                    if not artifact.is_file() or sha(artifact)!=digest:issues.append('review is stale: '+name)
                if 'manifest.json' not in review.get('artifact_hashes',{}):issues.append('review has no manifest hash')
        elif not (path.parent/'README.md').exists():issues.append('no retained visual review')
        source_path=path.parent/'sources.json'
        if not source_path.exists():issues.append('missing sources.json')
        else:
            source=json.loads(source_path.read_text())
            for name,record in source.get('sources',{}).items():
                original=ROOT/record['path']
                if not original.is_file() or sha(original)!=record['sha256']:
                    issues.append('changed/missing source: '+name)
        packages.append(dict(path=str(path.relative_to(ROOT)),frames=set(m['frames']),creature=m['creature'],
                             issues=issues,detail_exceptions=detail_exceptions))
    all_referenced={n for r in families.values() for n in r['images']}
    rows=[];by_world={};file_groups=defaultdict(list)
    for r in families.values():
        # Numbered MM7/MM8 actor names are resolved from descriptor-backed artwork, not group-file names.
        # Retain unused poses owned by those exact art stems without borrowing another family's live art.
        r['unreferenced_family_images']=[]
        if r['world'] in ('mm7','mm8'):
            stems={m.group() for n in r['images'] if (m:=re.match(r'^[67]?m\d{3}',n))}
            candidates=set(sprite_indices['engine'])|set(sprite_indices[r['world']])
            r['unreferenced_family_images']=sorted(n for n in candidates if n not in all_referenced
                and any(re.fullmatch(re.escape(stem)+(r'[a-z]+[0-7]' if r['world']=='mm8' else r'[a-z]{2}\d'),n) for stem in stems))
        required=set(r['images'])|set(r['unreferenced_family_images'])
        r['all_native_family_images']=sorted(required)
        matches=[p for p in packages if set(r['images'])<=p['frames']]
        partial_matches=[p['path'] for p in packages if set(r['standing_images'])<=p['frames'] and not set(r['images'])<=p['frames']]
        r['partial_packages']=partial_matches
        # Retain original and redo candidates; only validated full coverage counts.
        # Discovery puts redo packages first so an accepted replacement takes precedence.
        r['package_candidates']=[dict(path=p['path'],issues=p['issues'],detail_exceptions=p['detail_exceptions'],
            missing_frames=sorted(required-p['frames'])) for p in matches]
        complete=[p for p in matches if not p['issues'] and required<=p['frames']]
        r['completed_package']=complete[0]['path'] if complete else None
        r['accepted_detail_exceptions']=complete[0]['detail_exceptions'] if complete else {}
        r['images']=sorted(r['images']);r['palettes']=sorted(r['palettes'])
        # An identical source-art set can serve more than one world's descriptors.
        file_groups[tuple(r['standing_images'])].append(r)
        r['existing_images']=[];r['missing_images']=[]
        for n in r['all_native_family_images']:
            found=sprite_indices[r['world']].get(n) or sprite_indices['engine'].get(n)
            (r['existing_images'] if found else r['missing_images']).append(str(found.relative_to(ROOT)) if found else n)
        rows.append(r)
    for world in ('mm6','mm7','mm8'):
        part=[r for r in rows if r['world']==world]
        by_world[world]=dict(families=len(part),completed=sum(bool(r['completed_package']) for r in part),remaining=sum(not r['completed_package'] for r in part),remaining_referenced_image_names=len({n for r in part if not r['completed_package'] for n in r['images']}),remaining_all_native_family_image_names=len({n for r in part if not r['completed_package'] for n in r['all_native_family_images']}))
        by_world[world]['completed_with_detail_exceptions']=sum(bool(r['accepted_detail_exceptions']) for r in part)
    duplicates=[[dict(world=r['world'],label=r['label']) for r in rr] for rr in file_groups.values() if len(rr)>1]
    remaining=[rr for rr in file_groups.values() if not any(r['completed_package'] for r in rr)]
    summary=dict(by_world=by_world,world_family_total=len(rows),distinct_art_families=len(file_groups),completed_distinct_families=sum(any(r['completed_package'] for r in rr) for rr in file_groups.values()),remaining_distinct_families=len(remaining),shared_art=duplicates,remaining_referenced_image_names=len({n for rr in remaining for r in rr for n in r['images']}),missing_referenced_image_names=sorted({n for r in rows for n in r['missing_images']}),scope='Current MM6-MM8 merged native actor descriptor roster, including peasants, animals and special actors. Palette variants and repeated weak/strong entries share art. Custom enhanced descriptors 901+ excluded. Separate brown-ghost 3D remake is not counted as a completed native direct restoration. Referenced counts exclude unused poses. For MM7/MM8, all_native_family_images also includes unused numbered poses owned by descriptor-resolved art stems; these are required for completion but are not added to playback.')
    (P/'remaining_inventory.json').write_text(json.dumps(dict(summary=summary,families=rows,source_tables=group_sources),indent=2)+'\n')
    with (P/'remaining_families.csv').open('w') as f:
        w=csv.writer(f);w.writerow(['world','family','descriptors','source_images','completed_package'])
        for r in rows:w.writerow([r['world'],r['label'],';'.join(str(d['id']) for d in r['descriptors']),len(r['images']),r['completed_package'] or 'remaining'])
    print(json.dumps({**summary,'missing_referenced_image_names':len(summary['missing_referenced_image_names'])},indent=2))
if __name__=='__main__':main()
