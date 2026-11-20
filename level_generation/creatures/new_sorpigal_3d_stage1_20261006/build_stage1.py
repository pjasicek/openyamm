"""Rebuild this four-family native study and verify retained imagegen handoffs; no service calls."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import zipfile

from PIL import Image, ImageDraw, ImageFont
import yaml

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
FAMILIES = {'pmn2': ('MM6 mage', 610, 802), 'pman': ('MM6 male peasant', 607, 798),
            'pfem': ('MM6 female peasant', 595, 786), 'gua': ('MM6 New Sorpigal guard', 553, 748)}
ARCHIVE = REPO / 'assets_source/creatures/mm6/backups/20261004/native_runtime_retired/engine/sprites'
spec = importlib.util.spec_from_file_location('existing_native', ROOT.parent / 'mm6_peasants/prepare_family.py')
existing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(existing)


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def font(size=18):
    return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', size)


def contact(project, names, target, canvas, landmarks=None):
    """Code-owned evidence sheet. Original actor pixels and canvas are never warped."""
    cell = (canvas[0] * 2 + 20, canvas[1] * 2 + 64)
    out = Image.new('RGB', (cell[0] * 3, cell[1] * ((len(names) + 2) // 3)), '#343839')
    draw = ImageDraw.Draw(out)
    for i, name in enumerate(names):
        x, y = i % 3 * cell[0], i // 3 * cell[1]
        im = Image.open(project / 'source/frames' / (name + '.png')).convert('RGBA')
        bg = Image.new('RGBA', canvas, '#343839'); bg.alpha_composite(im)
        out.paste(bg.resize((canvas[0]*2, canvas[1]*2), Image.Resampling.NEAREST).convert('RGB'), (x+10, y+36))
        draw.text((x+10, y+7), name, font=font(), fill='white')
        if landmarks:
            for key, point in landmarks.get(name, {}).get('original', {}).items():
                xy = point.get('tracking_xy', point.get('xy'))
                if xy is None or None in xy or point.get('confidence', 0) < .8:
                    continue
                px, py = x+10+xy[0]*2, y+36+xy[1]*2
                color = '#ffcf6a' if key.startswith('head') else '#65d9fa'
                draw.ellipse((px-4, py-4, px+4, py+4), outline=color, width=2)
            draw.text((x+10, y+cell[1]-23), 'Existing 2D seeds; hidden joints remain unknown', font=font(13), fill='white')
    out.save(project / target)


def native():
    peasants = read(ROOT.parent / 'mm6_peasants/inventory.json')
    guard = read(ROOT.parent / 'mm6_gua/sources.json')
    table_path = REPO / 'assets_dev/engine/rendering/sprite_frame_data_common.yml'
    current_groups = {g['sprite_name'].lower(): g for g in yaml.load(table_path.read_text(), Loader=yaml.CSafeLoader)['sprites']}
    descriptor_path = REPO / 'assets_dev/engine/data_tables/monster_descriptors.txt'
    rows = {int(c[0]): line for line in descriptor_path.read_text().splitlines()
            for c in [line.split('\t')] if c[0].isdigit()}
    scene_path = REPO / 'assets_dev/worlds/mm6/maps/oute3.scene.yml'
    actors = yaml.load(scene_path.read_text(), Loader=yaml.CSafeLoader)['initial_state']['actors']
    for family, (label, first_id, base) in FAMILIES.items():
        project = ROOT / family
        for directory in ['source/frames', 'source/palettes', 'source/generation_inputs', 'guides']:
            (project / directory).mkdir(parents=True, exist_ok=True)
        inv = guard if family == 'gua' else peasants[family]
        canvas = inv['logical_canvas']
        paths = {}; verified = 0
        for name, record in inv['sources'].items():
            path = ARCHIVE / (name + '.bmp')
            assert digest(path) == record['sha256'], f'Changed original {path}'
            paths[name] = {**record, 'path': str(path.relative_to(REPO))}
            verified += 1
        relocated = {**inv, 'sources': paths}
        sources = []
        for name, record in paths.items():
            im = existing.native(name, base, canvas, relocated)
            retained = ROOT.parent / ('mm6_' + family) / 'native' / (name+'.png')
            assert im.tobytes() == Image.open(retained).convert('RGBA').tobytes(), f'Native decode mismatch {name}'
            target = project / 'source/frames' / (name + '.png'); im.save(target)
            sources.append({**record, 'png': str(target.relative_to(project)), 'png_sha256': digest(target),
                            'native_offset': [(canvas[0]-record['size'][0])//2, canvas[1]-record['size'][1]],
                            'visible_bounds': list(im.getbbox())})
        palettes = []
        for palette in inv['variants']:
            source = REPO / f'assets_dev/worlds/mm6/textures/pal{palette}.act'
            target = project / 'source/palettes' / source.name; shutil.copy2(source, target)
            palettes.append({'id': int(palette), 'path': str(source.relative_to(REPO)), 'sha256': digest(source),
                             'retained_path': str(target.relative_to(project))})
        actions = inv['variants'][str(base)]['actions']
        clips = []; covered = set()
        landmarks_path = ROOT.parent / 'mm6_packed_outline_collection_20261001/landmarks' / ('mm6_' + family + '.json')
        landmarks = read(landmarks_path)
        shutil.copy2(landmarks_path, project / 'source/native_landmarks.json')
        for action, group in actions.items():
            current = current_groups[group['sprite_name'].lower()]
            current_original_names = {**current, 'frames': [
                {**f, 'texture_name': f['texture_name'].removeprefix('atlas:mm6_' + family + '/')}
                for f in current['frames']]}
            assert current_original_names == group, f'Native timing or bindings changed {group["sprite_name"]}'
            single = 'Image1' in group['frames'][0]['flags']; frames = []; time = 0
            for frame in group['frames']:
                name = frame['texture_name'].lower()
                names = [name] if single else [name+str(v) for v in range(5)]
                assert set(names) <= set(paths)
                hold = frame['frame_length_raw'] * 62.5
                frames.append({**frame, 'time_ms': time, 'duration_ms': hold, 'names': names})
                time += hold; covered.update(names)
            if action == 'attack2':
                assert group == actions['attack']; continue
            clip = {'name': action, 'group': group['sprite_name'], 'native_duration_ms': time,
                    'native_length_raw': group['animation_length_raw'], 'frames': frames,
                    'current_runtime_texture_names': [f['texture_name'] for f in current['frames']],
                    'mode': 'hold' if action in ['standing', 'corpse'] else 'loop' if action in ['walk', 'fidget'] else 'once',
                    'genuine_views': ['front'] if single else ['front', 'front-right', 'right', 'back-right', 'back'],
                    'direction_reuse': 'Image1: frontal bitmap reused for every angle' if single else '5/6/7 mirror 3/2/1; not extra depth evidence'}
            clips.append(clip)
            names = [n for frame in frames for n in frame['names']]
            contact(project, names, f'source/{action}_native.png', canvas)
            contact(project, names, f'guides/{action}_landmarks.png', canvas, landmarks['frames'])
        assert covered == {name for name, item in paths.items() if item['referenced']}
        if inv['unreferenced']:
            contact(project, inv['unreferenced'], 'source/unused_artwork.png', canvas)
        (project / 'source/monster_descriptors_rows.tsv').write_text('\n'.join(rows[i] for i in range(first_id, first_id+3))+'\n')
        for relative in ['references/standing.png', 'references/native_variants.png',
                         'aligned_2x/' + ('guastaa0' if family == 'gua' else family+'sta0') + '.png']:
            original = ROOT.parent / ('mm6_'+family) / relative
            shutil.copy2(original, project / 'source/generation_inputs' / original.name)
        inventory = {'schema_version': 1, 'identity': label, 'family': family, 'descriptor_ids': list(range(first_id,first_id+3)),
                     'selected_palette': base, 'variants': inv['variants'], 'palettes': palettes,
                     'native_canvas': canvas, 'pivot': [canvas[0]/2, canvas[1]], 'transparent_index': 0,
                     'timing_raw_unit_ms': 62.5, 'placement': 'bottom-center; no Center flag; offsets preserved, body feet may not touch canvas bottom',
                     'images': sources, 'clips': clips, 'aliases': {'attack2': 'attack'}, 'unused_artwork': inv['unreferenced'],
                     'pixel_aliases': inv['pixel_aliases'], 'excluded': ['guardang.bmp'] if family == 'gua' else [],
                     'native_original_hashes_verified': verified, 'native_aligned_pngs_verified': verified,
                     'new_sorpigal_actors': [{k: a[k] for k in ['actor_index','monster_info_id','monster_id','position'] if k in a}
                                             for a in actors if first_id <= a['monster_info_id'] < first_id+3],
                     'provenance': {'sprite_table': {'path': str(table_path.relative_to(REPO)), 'sha256': digest(table_path)},
                                    'descriptors': {'path': str(descriptor_path.relative_to(REPO)), 'sha256': digest(descriptor_path)},
                                    'scene': {'path': str(scene_path.relative_to(REPO)), 'sha256': digest(scene_path)},
                                    'legacy_inventory_sha256': digest(ROOT.parent / ('mm6_gua/sources.json' if family=='gua' else 'mm6_peasants/inventory.json'))}}
        write(project / 'source_inventory.json', inventory)
        print(f'{family}: {verified} originals verified, {len(covered)} used files, {len(clips)} actions, '
              f'{sum(len(c["frames"]) for c in clips)} anchors, {len(inventory["new_sorpigal_actors"])} town actors')


def finish():
    runs = read(ROOT / 'generation_runs.json')
    output_map = {run['output']: ROOT/run['family']/'raw'/(run['id']+'.png') for run in runs}
    for run in runs:
        project = ROOT / run['family']; raw = output_map[run['output']]
        run['raw_file'] = str(raw.relative_to(ROOT)); run['raw_sha256'] = digest(raw)
        run['actual_sampling_size'] = list(Image.open(raw).size)
        run['export_resize_or_padding'] = 'None; selected PNG is a byte-identical copy of actual return.'
        inputs = []
        for supplied in run['inputs']:
            path = output_map.get(supplied)
            if path is None:
                path = project / 'source/generation_inputs' / Path(supplied).name
                assert digest(path) == digest(Path(supplied))
            inputs.append({'supplied_path': supplied, 'retained_path': str(path.relative_to(ROOT)), 'sha256': digest(path)})
        run['input_records'] = inputs
    write(ROOT / 'generation_runs.json', runs)
    for family, (label, _, _) in FAMILIES.items():
        project = ROOT / family; inv = read(project / 'source_inventory.json')
        motion = read(project / 'motion_spec.json'); anatomy = read(project / 'anatomy_targets.json')
        assert [c['name'] for c in motion['clips']] == [c['name'] for c in inv['clips']]
        count = 0
        for clip, native_clip in zip(motion['clips'], inv['clips']):
            assert len(clip['anchors']) == len(native_clip['frames'])
            for anchor, source in zip(clip['anchors'], native_clip['frames']):
                assert anchor['time_ms'] == source['time_ms'] and anchor['native_names'] == source['names']
                assert all(anchor.get(k) for k in ['phase','evidence','driver','right_arm','right_hand','left_arm',
                                                   'left_hand','body','support','head','secondary','transition','seeds','checks'])
                count += 1
        selected = []; review = Image.new('RGB',(2560,808),'#eeeeea'); draw=ImageDraw.Draw(review)
        family_runs = [r for r in runs if r['family']==family]
        for i, path in enumerate(sorted((project/'submission').glob('*.png'))):
            im=Image.open(path); assert im.mode=='RGBA'
            bounds=im.getchannel('A').point(lambda a:255 if a>128 else 0).getbbox()
            assert bounds and bounds[0]>4 and bounds[1]>4 and bounds[2]<im.width-4 and bounds[3]<im.height-4
            assert any(r['selected'] and r['raw_sha256']==digest(path) for r in family_runs)
            selected.append({'path':str(path.relative_to(project)),'sha256':digest(path),'size':list(im.size),
                             'alpha_bounds_threshold_128':list(bounds)})
            bg=Image.new('RGBA',im.size,'#eeeeea');bg.alpha_composite(im)
            review.paste(bg.resize((512,768)).convert('RGB'),(i*512,36));draw.text((i*512+8,8),path.stem,font=font(14),fill='black')
        assert len(selected)==5 and sum(r['selected'] for r in family_runs)==5
        review.save(project/'guides/selected_views_review.png')
        verification={'native_originals_verified':len(inv['images']),'aligned_native_decode_verified':len(inv['images']),
                      'used_original_files':len(inv['images'])-len(inv['unused_artwork']),'native_actions':len(inv['clips']),
                      'temporal_anchors':count,'selected_images':selected,'imagegen_returns':len(family_runs),
                      'technical_checks':'passed','scope':'Stage 1 only. No Meshy submission, model or rig.'}
        write(project/'verification.json',verification)
        write(project/'generation_runs.json',family_runs)
        review_notes=read(project/'visual_review.json')
        corrections=[{'finding':r['reason'],'cause':'Camera conversion reduced arm abduction.' if r['id']=='gua_primary_v3' else 'Modeling-reference arm/finger separation was insufficient.',
                      'superseded_return':str(Path(r['raw_file']).relative_to(family)),
                      'changed_region':'arm abduction and finger visibility; guard camera-related pose change when applicable',
                      'recheck':'All five selected views visually compared with native identity and each other; alpha/framing/provenance passed.'}
                     for r in family_runs if not r['selected']]
        record={'schema_version':1,'creature':label,'project':str(project.relative_to(REPO)),
                'requested_scope':'Prepare stage 1 weapon-free Meshy body images, native anatomy guides and all native animation studies.',
                'last_update_utc':datetime.now(timezone.utc).isoformat(),
                'selected_revision':'stage1_20261006','stage_1':{'status':'complete','native_inventory':'complete',
                'anatomy_guide':'complete','motion_study':'complete','submission_images':'complete'},
                'stage_2':{'status':'awaiting_external','substep':'user Meshy geometry generation; return unrigged GLB'},
                'stage_3':{'status':'not_started'},'furthest_artifact':'five body modeling images and complete native animation study',
                'earliest_unresolved_prerequisite':'Meshy base geometry has not been returned',
                'technical_verification':{'status':'passed','report':'verification.json'},
                'agent_visual_review':{'status':review_notes['status'],'report':'visual_review.json'},
                'user_artistic_acceptance':{'status':'not_recorded','applies_to_revision':'stage1_20261006'},
                'selected_artifacts':selected+[{ 'path':n,'sha256':digest(project/n)} for n in ['source_inventory.json',
                        'anatomy_targets.json','motion_spec.json','ANATOMY_GUIDE.md','ANIMATION_STUDY.md',
                        'visual_review.json','meshy_handoff.json','generation_runs.json']],
                'artifact_roles':{'meshy_body_input':'submission/00_smart_topology_three_quarter.png',
                    'correction_views':[s['path'] for s in selected[1:]],'native_evidence':'source_inventory.json',
                    'anatomy':'anatomy_targets.json','native_motion':'motion_spec.json','external_settings':'meshy_handoff.json'},
                'correction_ledger':corrections+review_notes.get('specification_corrections',[]),
                'next_action':{'owner':'user','action':'Generate one body with 00_smart_topology_three_quarter.png, Smart Topology, triangles, 15000 target, A-pose, no textures. Return unrigged GLB before auto-rig.'},
                'next_codex_action':'Ingest returned geometry; compare all views/anatomy targets, repair confirmed defects, then hand off accepted geometry for rigging.'}
        write(project/'creature_3d_progress.json',record)
        print(f'{family}: {count} motion anchors and five retained references verified')
    target=ROOT/'mm6_new_sorpigal_stage1_meshy_and_studies.zip'
    files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p!=target and '__pycache__' not in p.parts)
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as bundle:
        for path in files: bundle.write(path,ROOT.name+'/'+str(path.relative_to(ROOT)))
    with zipfile.ZipFile(target) as bundle: assert bundle.testzip() is None and len(bundle.namelist())==len(files)
    print(f'{len(files)} packaged files, {target.stat().st_size} bytes; ZIP CRC passed')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('operation',choices=['native','finish'])
    operation=parser.parse_args().operation
    native() if operation=='native' else finish()
